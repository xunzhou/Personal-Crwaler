import csv, requests, json
pg1 = requests.get('https://api.github.com/search/repositories?q=blockchain&sort=stars&per_page=100')
writer = csv.writer(open('lgInput.csv','w'))
if(pg1.ok):
    data = pg1.json()
    for i in data['items']:
        writer.writerow([i['name'].capitalize(), i['html_url']])

pg1 = requests.get('https://api.github.com/search/repositories?q=cryptocurrency&sort=stars&per_page=100')
writer = csv.writer(open('lgInput.csv','a'))
if(pg1.ok):
    data = pg1.json()
    for i in data['items']:
        writer.writerow([i['name'].capitalize(), i['html_url']])