import gevent
import mongo
import time
import datetime
import requests
import copy
import csv

from bson.objectid import ObjectId
from scrader_logger import LOG

from gevent import monkey

monkey.patch_all()


def get_all_companies():
    # returns a list of all companies
    companies = mongo.fetch_collection('companies')
    return [comp['name'] for comp in companies]


def company_typed_search(company):

    company_found = None
    companies = mongo.fetch_collection('companies')
    all_companies = [comp['name'] for comp in companies]
    for company_name in all_companies:
        company_name_net = company_name.split()[0]
        if company in company_name_net.lower():
            return company_name

    return company_found


def company_news_type(company_given):
    # list of news type a company has
    news_cursor = mongo.find_matches('articles', {'company': company_given})
    comp_type_of_news = []
    for new in news_cursor:
        if 'POS' in new['direction']:
            comp_type_of_news.append('good_companies')
        elif 'NEG' in new['direction']:
            comp_type_of_news.append('bad_companies')

    return list(set(comp_type_of_news))


def total_articles():

    total_cursor = mongo.find_matches_not_containing('articles', 'direction', ['NEU', 'NEUTRAL'])
    return total_cursor.count()


def companies_by_type(news_type):
    # list of companies names , type can be good_companies bad_companies

    if news_type == 'good_companies':
        match = ['POS', 'POSITIVE']
    elif news_type == 'bad_companies':
        match = ['NEG', 'NEGATIVE']

    articles_cursor = list(mongo.find_matches_containing_many('articles', 'direction', match))
    companies_new_list = []
    for article in articles_cursor:
        comp_dict = mongo.find_one_match('companies', {'name': article.get('company')})
        if not any(d['company_name'] == comp_dict.get('name') for d in companies_new_list):
            comp_dict['company_name'] = comp_dict.pop('name')
            companies_new_list.append(comp_dict)

    return companies_new_list


def get_news_by_direction_and_company(company, direction_list):
    # list of news by their direction good bad

    news_list = list(mongo.find_matches_two_fields('articles', 'company',
                     [company], 'direction', direction_list))
    return news_list


def get_companies_articles(company):
    return list(mongo.find_matches('articles', {'company': company}))


def manually_tag_article(article_id, value, user):
    article = mongo.find_one_match('dev_articles',
                                   {"_id": ObjectId(article_id)})

    if value == 'Skip':
        mongo.delete_one_from('dev_articles', ObjectId(article_id))
    else:
        if value == 'Wrong':
            if article.get('direction') == "POS":
                mongo.insert_one_in('dev_articles',
                                    {"_id": ObjectId(article_id)},
                                    {'direction': 'NEG'})
            else:
                mongo.insert_one_in('dev_articles',
                                    {"_id": ObjectId(article_id)},
                                    {'direction': 'POS'})
        mongo.insert_one_in('dev_articles', {"_id": ObjectId(article_id)},
                                            {'checked': True})
        mongo.insert_one_in('dev_articles', {"_id": ObjectId(article_id)},
                                            {'User': user})


def find_num_of_tagged():
    num_of_positive = 0
    num_of_negative = 0
    with open('scraderdata.csv') as csvfile:
        reader = csv.DictReader(csvfile)
        for article in reader:
            if article.get('direction') == 'POS':
                num_of_positive += 1
            else:
                num_of_negative += 1

    positive_cursor = mongo.find_matches_three_fields('dev_articles',
                                                      'checked', [True],
                                                      'direction',
                                                      ['POS'],
                                                      'appended',
                                                      ['False'])
    num_of_positive += positive_cursor.count()
    negative_cursor = mongo.find_matches_three_fields('dev_articles',
                                                    'checked', [True],
                                                    'direction',
                                                    ['NEG'],
                                                    'appended',
                                                    ['False'])
    num_of_negative += negative_cursor.count()
    return num_of_positive, num_of_negative


def article_from_excel():

    from xlrd import open_workbook
    book = open_workbook('Scrader-Sample_1-12.xlsx')
    sheet = book.sheet_by_index(0)
    keys = dict((i, sheet.cell_value(0, i)) for i in range(sheet.ncols))
    articles = (dict((keys[j], sheet.cell_value(i, j)) for j in keys) for i in range(1, sheet.nrows))
    mongo.delete_many('articles')
    for article in articles:
        new_article = {}
        new_article['title'] = article.get('Title')
        new_article['image_url'] = article.get('image url')
        new_article['subtitle'] = '10/5/2017'
        new_article['item_url'] = article.get('URL')
        new_article['direction'] = article.get('Sentiment')
        new_article['company'] = article.get('Company')
        new_article['website'] = article.get('Website')
        new_article['website_url'] = article.get('Website url')
        new_article['false_estims'] = 0
        mongo.insert_one('articles', new_article)


def article_from_csv():

    with open('Scrader4.csv') as csvfile:
        reader = csv.DictReader(csvfile)
        for article in reader:
            new_article = {}
            new_article['title'] = article.get('Title')
            new_article['image_url'] = article.get('Image')
            new_article['subtitle'] = article.get('Date')
            new_article['item_url'] = article.get('Article')
            new_article['direction'] = article.get('Sentiment')
            new_article['company'] = article.get('Company')
            new_article['website'] = article.get('Website')
            new_article['website_url'] = article.get('Website url')
            new_article['false_estims'] = 0
            mongo.insert_one('articles', new_article)


def send_user_news(user):
    # print("sending staff for user" + user.get('name'))
    url = 'https://api.chatfuel.com/bots/591189a0e4b0772d3373542b/' \
          'users/{}/' \
          'send?chatfuel_token=vnbqX6cpvXUXFcOKr5RHJ7psSpHDRzO1hXBY8dkvn50ZkZyWML3YdtoCnKH7FSjC' \
          '&chatfuel_block_id=5a1aae94e4b0c921e2a89115&last%20name={}'.format(user.get('user_id'), user.get('name'))

    try:
        r = requests.post(url)
    except requests.exceptions.RequestException as e:
        pass


def start_scheduler():
    while True:
        time_now = str(datetime.datetime.now().time())
        formatted_time = (str(int(time_now.split(':')[0]) + 2)) + ":" + (time_now.split(':')[1])
        # print(formatted_time)
        users = mongo.find_matches('users', {'datetime': formatted_time})
        for user in users:
            send_user_news(user)
        time.sleep(60)


def start_scheduler_task():
    gevent.spawn(start_scheduler)


def get_development_news(news_type, page_num, user):
    elements = []
    element = {
        "title": '',
        "image_url": '',
        "subtitle": '',
        "item_url": '',
        "buttons": [{
            "type": "web_url",
            "url": '',
            "title": ''
        },
         {
            "type": "web_url",
            "url": '',
            "title": ''
        },
         {
           "type": "web_url",
           "url": '',
           "title": ''
        }]
    }

    messages = []
    message = {
        "attachment": {
            "type": "template",
            "payload": {
                "template_type": "generic",
                "elements": elements
            }
        }
    }

    quick_replies = []
    quick_reply = {"title": '', "url": '', "type": "json_plugin_url"}

    requested_news = list(mongo.find_matches_two_fields('dev_articles',
                                                        'checked', [False],
                                                        'direction',
                                                        [news_type]))
    # print(len(requested_news))

    f = lambda A, n=3: [A[i:i + n] for i in range(0, len(A), n)]
    news_per_page = f(requested_news)
    # print(news_per_page)
    news_to_show = news_per_page[int(page_num) - 1]
    # print(news_to_show)
    all_quick_replies_page_numbers = [
        i + 1 for i, _ in enumerate(news_per_page)
    ]
    # print(all_quick_replies_page_numbers)
    quick_replies_page_numbers_to_show = filter(lambda x: x != int(page_num),
                                                all_quick_replies_page_numbers)
    # print(quick_replies_page_numbers_to_show)

    for new in news_to_show:
        element = copy.deepcopy(element)
        element['title'] = new.get('title')[0:79]
        element['image_url'] = str(new.get('image_url'))
        element['subtitle'] = new.get('subtitle')
        element['item_url'] = str(new.get('item_url'))
        id = str(new.get('_id'))
        element['buttons'][0]['url'] = "http://146.185.138.240/checked_article/{}/{}/{}/{}/{}".\
            format(news_type, id, 'Correct', page_num, user)
        element['buttons'][0]['title'] = "Correct Estim"
        element['buttons'][0]['type'] = "json_plugin_url"
        element['buttons'][1]['url'] = "http://146.185.138.240/checked_article/{}/{}/{}/{}/{}".\
            format(news_type, id, 'Wrong', page_num, user)
        # print(element['buttons'][1]['url'])
        element['buttons'][1]['title'] = "Wrong Estim"
        element['buttons'][1]['type'] = "json_plugin_url"
        element['buttons'][2]['url'] = "http://146.185.138.240/checked_article/{}/{}/{}/{}/{}".\
            format(news_type, id, 'Skip', page_num, user)
        element['buttons'][2]['title'] = "Skip Estim"
        element['buttons'][2]['type'] = "json_plugin_url"
        elements.append(element)
    num = 0
    for page_number in quick_replies_page_numbers_to_show:
        num += 1
        if num > 11:
            break
        quick_reply = copy.deepcopy(quick_reply)
        quick_reply['title'] = "Page {}".format(page_number)
        quick_reply['url'] = "http://146.185.138.240/dev_news/{}/{}/{}".format(
            news_type, page_number, user)
        quick_replies.append(quick_reply)

    if quick_replies:
        message['quick_replies'] = quick_replies

    message['attachment']['payload']['elements'] = elements

    top_message = {"text": '{} unchecked articles found'.
                   format(len(requested_news))}

    if int(page_num) == 1:
        messages.append(top_message)

    LOG.info(message)
    # print(message)
    messages.append(message)
    response_data = {"messages": messages}
    return response_data
