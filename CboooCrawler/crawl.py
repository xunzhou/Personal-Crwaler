import csv, requests, random, string, io, sys, datetime
from multiprocessing import Pool
from bs4 import BeautifulSoup
from fake_useragent import UserAgent
from requests.exceptions import ProxyError, SSLError

# CONFIGURATION
STARTYEAR = 2014  # Starting year for fetching boxoffice from cbooo.

sys.setrecursionlimit(5000)

area = {}; year = []

# get attributes 
# 0 for all, must specify area
r = requests.get('http://www.cbooo.cn/movies')
print(str(r.status_code)+' '+'http://www.cbooo.cn/movies')
soup = BeautifulSoup(r.text, 'html.parser')
selArea = soup.find(id='selArea').contents
selYear = soup.find(id='selYear').contents
# selType for genre
for row in selArea[1::2]:
    area[row.string] = row['value']
for row in selYear[1::2]:
    year.append(row.string)

def buildLn(d, c):
    res = [d[item] for item in d.keys()]
    res.append(c)
    return res

def get(a):
    lines = []
    ses = requests.Session()
    baseUrl = 'http://www.cbooo.cn/Mdata/getMdata_movie?area='+area[a[1]]+'&type=0&year='+a[0]+'&initial=%E5%85%A8%E9%83%A8&pIndex='
    totPg = ses.get(baseUrl).json()['tPage']
    for pg in range(1,totPg+1):
        u = baseUrl+str(pg)
        r = ses.get(u)
        print(str(r.status_code)+' '+ u)
        for m in r.json()['pData']:
            lines.append(buildLn(m, a[1]))
    if len(lines) != 0:
        print("Got "+str(len(lines))+" movies in "+str(a[0])+" from "+a[1]+'.')
    return (lines, len(lines))

def buildInput(countryLst,startYr):
    ret = []
    for i in range(startYr, datetime.date.today().year+1):
        for j in countryLst:
            ret.append((str(i),j))
    return ret

def fetch():
    pool = Pool()
    allAreas = [key for key in area.keys()]
    args = buildInput(allAreas,STARTYEAR)
    # args = buildInput(['中国','美国'],2017)
    res = pool.map(get, args)
    pool.terminate(); pool.join()
    return res

def parse(res):
    with io.open('cbooo.csv','w') as f:
            sum = 0
            writer = csv.writer(f)
            writer.writerow(['Ranking(in area)','ID','Name','EngName','Year','Image','BoxOffice','Area'])

            print("\n------------------------------")
            for i in res:
                sum += i[1]
                for j in i[0]:
                    writer.writerow(j)
    
    print('Stored '+str(sum)+" movies to cbooo.csv")


parse(fetch())