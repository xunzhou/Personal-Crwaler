import csv, requests, random, string, io
from multiprocessing import Pool
from bs4 import BeautifulSoup
from fake_useragent import UserAgent
from requests.exceptions import ProxyError, SSLError

# CONFIGURATION
# NOTE: not checking when step > end
END = 500  # number of pages to be processed.
STEP = 25 # fetch this number of pages with each cookies.

def listProxies():
    proxies = []
    r = requests.get('https://www.sslproxies.org/', headers={'User-Agent':UserAgent().random})
    soup = BeautifulSoup(r.text, 'html.parser')
    proxies_table = soup.find(id='proxylisttable')
    for row in proxies_table.tbody.find_all('tr'):
        proxies.append(row.find_all('td')[0].string+':'+row.find_all('td')[1].string)

    return proxies

proxiesList = listProxies()
getProxy = {'https':random.choice(proxiesList)}

cookies = {
    'gsScrollPos-1764': '0',
    'bid': '3PK86OZCL0E',
    'ps': 'y',
    'dbcl2': '181553596:n30dgBK8Ffk',
    'll': '108258',
    'ck': 'Z2NK',
    'push_noty_num': '0',
    'push_doumail_num': '0',
}

headers = {
    'DNT': '1',
    'Accept-Encoding': 'gzip, deflate, br',
    'Accept-Language': 'en-US,en;q=0.9,zh-CN;q=0.8,zh;q=0.7,zh-TW;q=0.6',
    'User-Agent':UserAgent().random,
    'Accept': 'application/json, text/plain, */*',
    'Referer': 'https://movie.douban.com/tag/',
    'Connection': 'keep-alive',
}

def getPg(session, start):
    cookies['bid']="".join(random.sample(string.ascii_letters + string.digits, 11))
    url = 'https://movie.douban.com/j/new_search_subjects?sort=R&range=0,10&tags=%E7%94%B5%E5%BD%B1&start='+str(start)
    while True:
        try:
            r = session.get(url, headers=headers, cookies=cookies, proxies=getProxy) # '69.43.44.215:53281' for debug
        except (ProxyError, SSLError) as e:
            print('['+e+']Switching proxy...')
            getProxy['https']=random.choice(proxiesList) #'69.43.44.215:53281' for debug
            continue
        else:
            if (r.status_code == 200):
                break
            else:
                print("requests from douban returned: "+r.status_code)

    print('['+str(r.status_code)+"] "+url)
    return r.json()['data']

def getAll(i):
    result = []
    session = requests.Session()
    for j in range(STEP):
        result.append(getPg(session, (i+j)*20))
    return result

def fetch():
    pool = Pool()
    res = pool.map(getAll, range(0,END,STEP))
    pool.terminate(); pool.join()
    return res

res = fetch()

def buildLine(d):
    # TODO: Need to use python3 for easier encoding, if py2 is prefered, then a fix is needed here.
    return [d['id'],d['title'],d['rate'],d['url'],d['directors'],d['casts'],d['star'],d['cover'],d['cover_x'], d['cover_y']]


def buildAll(res):
    ret = []
    for i in range(len(res)):
        for j in range(len(res[i])):
            for k in range(len(res[i][j])):
                ret.append(buildLine(res[i][j][k]))
    return ret

def parse():
    with io.open('douban.csv','w') as f:
        writer = csv.writer(f)
        writer.writerow(['ID','Title','Rate','URL','Directors','Casts','Star','Cover','Cover_X','Cover_Y'])
        
        lines = buildAll(res)

        print("\n------------------------------")
        print("Got "+str(len(lines))+" movies from douban.")

        for i in lines:
            writer.writerow(i)
        print("Stored "+str(len(lines))+" movies to douban.csv")


parse()