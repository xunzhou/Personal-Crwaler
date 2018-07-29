import csv, requests, random, string, io, sys, datetime, time
from multiprocessing import Pool
from bs4 import BeautifulSoup
from requests.exceptions import ProxyError, SSLError
from tqdm import tqdm

sys.setrecursionlimit(10000)

mcookies = {
    '_lxsdk_cuid': '164be98958cc8-0a354f2a6ad8b6-1e2e130c-1fa400-164be98958dc8',
    'v': '3',
    'iuuid': '1A6E888B4A4B29B16FBA1299108DBE9C28EE9E858957201B2631E9F139534609',
    'webp': 'true',
    'ci': '10%2C%E4%B8%8A%E6%B5%B7',
    'selectci': 'true',
    '__mta': '147231624.1532206030660.1532294560602.1532294665245.13',
    '_lxsdk': '3936BE108D2711E88F6FF1EA8E6CBE28CBC6A11748404FC695CA3DBC78A6E9BA',
    '_lxsdk_s': '164c3df7b4e-0ad-db0-329%7C%7C57',
}
mheaders = {
    'Connection': 'keep-alive',
    'Cache-Control': 'max-age=0',
    'Upgrade-Insecure-Requests': '1',
    'DNT': '1',
    'User-Agent': 'Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/67.0.3396.99 Mobile Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
    'Accept-Encoding': 'gzip, deflate',
    'Accept-Language': 'en-US,en;q=0.9,zh-CN;q=0.8,zh;q=0.7,zh-TW;q=0.6',
}
dcookies = {
    'gsScrollPos-1936': '0',
    'uuid_n_v': 'v1',
    'uuid': '3936BE108D2711E88F6FF1EA8E6CBE28CBC6A11748404FC695CA3DBC78A6E9BA',
    '_csrf': '699853ea311cfb6b49821e19a29ae7bbc75c3be32901e12f82c5e75edc9e44e0',
    '_lxsdk_cuid': '164be98958cc8-0a354f2a6ad8b6-1e2e130c-1fa400-164be98958dc8',
    'gsScrollPos-1933': '0',
    '_lxsdk': '3936BE108D2711E88F6FF1EA8E6CBE28CBC6A11748404FC695CA3DBC78A6E9BA',
    'gsScrollPos-1590': '0',
    'gsScrollPos-1717': '0',
    '__mta': '147231624.1532206030660.1532318633859.1532321049926.114',
    '_lxsdk_s': '164c573abca-2fc-0ab-80d%7C%7C2',
}

dheaders = {
    'Connection': 'keep-alive',
    'Cache-Control': 'max-age=0',
    'Upgrade-Insecure-Requests': '1',
    'DNT': '1',
    'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/67.0.3396.99 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
    'Accept-Encoding': 'gzip, deflate',
    'Accept-Language': 'en-US,en;q=0.9,zh-CN;q=0.8,zh;q=0.7,zh-TW;q=0.6',
}


def listProxies():
    proxies = []
    r = requests.get('https://www.sslproxies.org/')
    soup = BeautifulSoup(r.text, 'html.parser')
    proxies_table = soup.find(id='proxylisttable')
    for row in proxies_table.tbody.find_all('tr'):
        proxies.append(row.find_all('td')[0].string+':'+row.find_all('td')[1].string)

    return proxies

proxiesList = listProxies()

def getProxy():
    return {'https':random.choice(proxiesList)}

cat={}; source={}; year={}

def getattr():
    r = requests.get('http://maoyan.com/films', headers=dheaders, cookies=dcookies, proxies={'https': 'http://69.43.44.215:53281'})
    print(str(r.status_code)+' http://maoyan.com/films')
    soup = BeautifulSoup(r.text,'lxml')
    print(soup.title)
    tagsLst = soup.find_all('ul',{'class':'tags'}) # ul [cat, source, year]
    for li in tagsLst[0].find_all('li'):
        cat[li.a.get_text()] = '&'+li.a['href'][1:]
    for li in tagsLst[1].find_all('li'):
        source[li.a.get_text()] = '&'+li.a['href'][1:]
    for li in tagsLst[2].find_all('li'):
        year[li.a.get_text()] = '&'+li.a['href'][1:]
    cat['全部'] = ''; source['全部'] = ''; year['全部'] = ''

id = []
def getID(cat, src, yr):
    currPg = 0; nextPg = 1
    session = requests.Session()
    while nextPg != 0:
        u = 'http://maoyan.com/films?sortId=2'+cat+src+yr+'&offset='+str(currPg*30)
        r = session.get(u, headers=dheaders, cookies=dcookies)#, proxies=getProxy())
        print(str(r.status_code)+' '+u)
        soup = BeautifulSoup(r.text,'lxml')
        divs = soup.find_all('div', {'class':'movie-item'})
        for div in divs:
            id.append(div.a['data-val'].split(':')[1][:-1])
        if (len(divs) < 30): # just one page
            break
        else: 
            nextPg = soup.find('ul',{'class':'list-pager'}).find('li',{'class':'active'}).findNext('li')
        currPg += 1

def get(id):
    u = 'http://m.maoyan.com/movie/'+str(id)
    r = requests.get(u, headers=mheaders, cookies=mcookies)
    # print(str(r.status_code)+' '+u)
    if(len(r.text) > 20000):
        soup = BeautifulSoup(r.text, 'lxml')
        box = soup.find_all('div',{'class':'movie-box', 'class':'cell'})
        rt = soup.find('meta',{'itemprop':'name'})['content'][-4:-1]
        if len(rt) == 0:
            rating = None
        elif not (rt[-1:].isdigit()):
            rating = None
        else: 
            rating = rt

        title = soup.find('title').get_text()
        if(len(box) != 0):
            firstWk = box[0].p.get_text().replace(',','')
            tot = box[1].p.get_text().replace(',','')
        else:
            firstWk = None
            tot = None

        return [id,title,rating,firstWk,tot]
    else:
        print("[debug] "+u)

def fetch():
    pool = Pool(20)
    res = list(tqdm(pool.imap(get, id),total=len(id)))
    pool.terminate(); pool.join()
    return res

def fromSearch():
    print("Getting attributes...")
    getattr()
    print("Getting ids...")
    for s in source:
        getID('',source[s],year['2018'])
    # getID('',source['大陆'],year['2018']) #'中国香港'
    # getID('','&sourceId=2','&yearId=13') # source = 10
    print("Got "+str(len(id))+" ids.")

def getIDPro(yr):
    u = 'http://piaofang.maoyan.com/rankings/year?year='+yr
    r = requests.get(u)
    soup = BeautifulSoup(r.text, 'lxml')
    rank_list = soup.find('div',{'id':"ranks-list"})
    ul = rank_list.find_all('ul')
    for li in ul:
        id.append(li['data-com'][20:-1])
    print("Got "+str(len(ul))+" ids for movies in "+yr)


def fromPro():
    year = ['2018','2017','2016','2015','2014','2013','2012','2011']
    print("Getting ids...")
    for y in year:
        getIDPro(y)    
    print("Got "+str(len(id))+" ids from Maoyan Pro.")
    

if __name__ == "__main__":
    # fromSearch()    # search currently not working
    fromPro()

    print("Fetching movies...")
    res = fetch()
    print("Parsing results...")
    with io.open('maoyan.csv','w') as f:
        count = 0
        writer = csv.writer(f)
        writer.writerow(['ID','Name','Rating','1stWk Box','Total Box'])

        for i in res:
            if i:
                count += 1
                writer.writerow(i)

        print('Stored '+str(count)+" movies to maoyan.csv")