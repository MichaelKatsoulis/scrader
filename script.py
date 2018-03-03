import os
from pymongo import MongoClient
import pandas as pd
import copy
from bson.objectid import ObjectId
# converts mongodb collection to csv


def convert_collection_to_df(mongo_cli, collection, field1, match1,
                             field2, match2):
    dbcli = mongo_cli
    scrader_db = dbcli['scrader']
    cursor = scrader_db[collection].find({'$and': [{field1: {'$in': match1}},
                                         {field2: {'$in': match2}}]})

    cursor_list = list(cursor)
    print(len(cursor_list))
    copied_list = copy.deepcopy(cursor_list)
    for d in cursor_list:
        title = d['title']
        times = 0
        for dic in copied_list:
            if dic['title'] == title:
                times += 1
                if times == 2:
                    print(title)
                    copied_list.remove(dic)
                    break

    print(len(copied_list))
    reduced_list = []
    sampledict = {'direction': '',
                  'title': ''}

    for article in copied_list:
        scrader_db[collection].\
            update({"_id": ObjectId(article['_id'])},
                   {'$set': {'appended': True}})
        newarticle = copy.deepcopy(sampledict)
        newarticle['direction'] = article.get('direction')
        newarticle['title'] = article.get('title')
        reduced_list.append(newarticle)

    return pd.DataFrame(reduced_list)


def main():
    dataframe = convert_collection_to_df(MongoClient(), 'dev_articles',
                                                        'checked', [True],
                                                        'appended', [False])
    if dataframe.empty:
        pass
    # if file does not exist write header
    if not os.path.isfile('scraderdata.csv'):
        dataframe.to_csv('scraderdata.csv', encoding='utf-8', index=False)
    else:  # else it exists so append without writing the header
        dataframe.to_csv('scraderdata.csv', mode='a', header=False,
                         index=False, encoding='utf-8')


if __name__ == '__main__':
    main()
