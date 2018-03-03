import csv

with open('company_list_18-2.csv') as csvfile:
    reader = csv.DictReader(csvfile)
    company_names = []
    company_names_urls = []
    for company in reader:
        if company.get('COMPANY LIST') != '':
            company_names.append(company.get('COMPANY LIST'))
            company_names_urls.append(company.get('URL TERM'))


print(company_names)
print(company_names_urls)
