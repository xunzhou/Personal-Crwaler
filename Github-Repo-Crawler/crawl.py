import csv, requests, json, getpass, subprocess, datetime, time, sys, os
from collections import OrderedDict
from multiprocessing import Pool
import traceback

currUser = (); users = []
data = []; data2 = []

today = datetime.date.today()
lastSUN = today-datetime.timedelta(today.weekday()+1 % 7)
OneYrAgo = (lastSUN-datetime.timedelta(weeks=52)).strftime('%Y-%m-%d')

def verifyUser(user):
    verify = requests.get('https://api.github.com', auth=user)
    if(verify.status_code == 200):
        print(user[0] + " Login Successfully.")
        users.append(user)
    else:
        print(user[0]+': '+verify.headers['Status']) 

# def login():
#     while len(users) <= 0:
#         if sys.version_info[0] < 3:
#             username = raw_input("Github Username: ")
#         else:
#             username = input("Github Username: ")
#         password = getpass.getpass("Github Password: ") 
#         user = (username, password)
#         verifyUser(user)

def loginAll():
    if not os.path.isfile('keys.csv'):
        print('Please put at least two users in keys.csv')
        # login()
    else:
        with open('keys.csv') as inFile:
            for line in inFile:
                tmp = line.strip().split(',')
                user = (tmp[0],tmp[1])
                verifyUser(user) 
    if len(users) > 0:
        return users  
    else:
        print('No valid Github Users in keys.csv') 
        exit(1)     

# TODO: if CheckQuota failed, switchUser
#TODO: periodically checkQuota
def checkQuota(user):
    rate_lim = requests.get('https://api.github.com/rate_limit', auth=user)
    if(rate_lim.ok):
        data = rate_lim.json()
        remaining = data['rate']['remaining']
        if(remaining >= 0):
            print("Remaining API requests of " + user[0] + ": " + str(remaining))
            return True
    return False

#TODO: call switch user whenever for all request failed.
def switchUser():
    global currUser
    lastusr = currUser
    currUser = users[((users.index(currUser)+1)%len(users))]
    print('Switching user: '+str(lastusr[0])+' -> '+str(currUser[0]))

# Create users
loginAll()
currUser = users[0]

def dictInit(start, name, proj):
    dict = OrderedDict({})
    month = ['0','01','02','03','04','05','06','07','08','09','10','11','12']
    strtYr = start[0]
    strtMo = start[1].lstrip('0')
    currYr = today.year
    currMo = today.month

    for m in range(int(strtMo),12+1):
        dict[str(strtYr)+month[m]] = [name,proj,str(strtYr)+month[m]]

    for y in range(int(strtYr)+1, currYr):
        for m in range(1,12+1):
            dict[str(y)+month[m]] = [name,proj,str(y)+month[m]]
    
    for m in range(1,currMo+1):
        dict[str(currYr)+month[m]] = [name, proj,str(currYr)+month[m]]

    return dict

def getContrib(dict, url, createdAt):
    while 1:
        contrib = requests.get(url, auth=currUser)
        # print('[contrib] '+str(contrib.status_code))
        if(contrib.status_code == 202):
            # print(contrib.headers)
            continue
        elif(contrib.ok):
            if not('all' in contrib.json()):
                print(contrib.json())
                exit(1)
            data = contrib.json()['all']
            break
        else:
            if(contrib.status_code == 403): # Status might be 202
                switchUser()
            # else:
                # print(contrib.headers)
            continue
    sun = lastSUN
    dict[sun.strftime('%Y%m')].append(data[0])
    cY = int(createdAt[0]); cM = int(createdAt[1]); cD =int(createdAt[2])
    cDate = datetime.date(cY,cM,cD)
    ctr = 1 
    # print(dict.keys())
    # print('creation date: '+str(cDate))
    while (ctr < 52 and sun-datetime.timedelta(7) >= cDate):
        sun -= datetime.timedelta(7)
        key = sun.strftime('%Y%m')
        if len(dict[key]) == 3:
            dict[key].append(data[ctr])
        elif len(dict[key]) == 4:
            dict[key][3] += data[ctr]
        else:
            print("Should not be here!")
            exit(1)
        ctr += 1

    for k in dict: 
        if len(dict[k]) == 3:
            dict[k].append("0")

def getCommitsReleases(dict, giturl, projname):
    pn = projname.capitalize()
    # clone git folder, not project, --no-checkout
    ret = subprocess.call('git clone --no-checkout '+giturl, shell=True)
    print('['+pn+"] gitclone return: "+str(ret))

    # create intermediate file with montly commits count
    ret = subprocess.call('cd '+projname+'/ && git log --pretty="%ad" --date=short| sed "s/.\{3\}$//" | sort | uniq -c | sed "s/^[[:blank:]]*//;s/-//" > ../commits_tmp.txt' , shell=True)
    print('['+pn+"] gitlog commits return: "+str(ret))
    
    ret = subprocess.call('cd '+projname+'/ && git log --no-walk --tags --pretty="%ad" --date=short | sed "s/.\{3\}$//" | sort | uniq -c | sed "s/^[[:blank:]]*//;s/-//" > ../release_tmp.txt', shell=True)
    print('['+pn+"] gitlog release return: "+str(ret))

    # remove git folder 
    ret = subprocess.call('rm -rf '+projname, shell=True)
    print('['+pn+"] rm-rf return: "+str(ret))
    
    # parse commitByMonth.txt into dictionary.
    with open('commits_tmp.txt') as tmpFile:
        for line in tmpFile:
            tmp = line.strip('\n').split(' ')
            # if dict.has_key(tmp[1]):
            if tmp[1] in dict:
                dict[tmp[1]].append(tmp[0])
        # check if a month has no commits?
        for k in dict: 
            if len(dict[k]) == 4:
                dict[k].append("0")
    
    with open('release_tmp.txt') as tmpFile:
        for line in tmpFile:
            tmp = line.strip('\n').split(' ')
            # if dict.has_key(tmp[1]):
            if tmp[1] in dict: 
                dict[tmp[1]].append(tmp[0])
        # check if a month has no commits?
        for k in dict:
            if len(dict[k]) == 5:
                dict[k].append("0")

# TODO: Use relative pagination, while next != last 
def buildUrlSet(apiurl):
    urls = []
    while 1:
        firstPg = requests.get(apiurl, auth=currUser)
        if(firstPg.ok):
            if('Link' in firstPg.headers):
                lastPg = int(firstPg.headers['Link'].split(', ')[1].split('; ')[0][1:-1].split('&page=')[1])
                pg = 1 
                while(pg <= lastPg):
                    urls.append(apiurl+'&page='+str(pg))    
                    pg += 1
            else:
                # Small proj with a single page.
                urls.append(apiurl)
            break
        else:
            if(firstPg.status_code == 403):
                switchUser()
                continue
    return urls

def millis():
  return int(round(time.time() * 1000))

def http_get(url):
  list = [] 
  pullList = []
  start_time = millis()
  while 1:
    req = requests.get(url,auth=currUser)
    if(req.ok):
        for i in req.json():
            # Distinguish if an issue is pull request
            if('pull_request' in i):
                pullList.append(i['created_at'])
            else:
                # list.append(i['created_at'])
                list.append(i['updated_at'])
        result = {'pg': url[-2:], 'status': req.status_code, 'list': list, 'pullList': pullList}
        break
    else:
        # print('[HTTP Get] '+str(req.status_code)+': '+req.json()['message'])
        if(req.status_code == 403):
            switchUser()
            continue
            # time.sleep(30)
  print(url[-7:] + " took " + str(millis() - start_time) + " ms")
  return result

def getAllUrls(urls):
    pool = Pool(25)
    res = pool.map(http_get, urls)
    pool.terminate(); pool.join()
    return res

def fillZero(dict, col):
    for k in dict:
        if len(dict[k]) == col:
            dict[k].append('0')

def parseAll(dict, set):
    for i in set:
        for j in i['list']:
            tmp = j.split('-')
            d = str(tmp[0]+tmp[1])
            if len(dict[d]) == 6:
                dict[d].append(1)
            elif len(dict[d]) == 7:
                dict[d][6] += 1
            else:
                print("Should not be here!")
                exit(1)
    fillZero(dict, 6)
    for i in set:
        for j in i['pullList']:
            tmp = j.split('-')
            d = str(tmp[0]+tmp[1])
            if len(dict[d]) == 7:
                dict[d].append(1)
            elif len(dict[d]) == 8:
                dict[d][7] += 1
            else:
                print("Should not be here!")
                exit(1)
    fillZero(dict, 7)

def buildDict(name, proj):
    line = []; line.append(name); line.append(proj)
    dict = {}
    repo = proj.replace('github.com', 'api.github.com/repos')
    # OneYrAgo = (lastSUN-datetime.timedelta(weeks=52)).strftime('%Y-%m-%d')
    wklyContrib = '/stats/participation' # Last Years' weekly commit count for the repository owner and everyone else
    # issues = '/issues?filter=all&state=all&since='+OneYrAgo+'&per_page=100'
    issues = '/issues?filter=all&state=all&per_page=100'
    # pulls = '/pulls?state=all&&since='+OneYrAgo+'&per_page=100'

    while 1:
        # Build watch_stars.csv
        #TODO: checkQuota?
        wtcstr = requests.get(repo, auth=currUser)
        if(wtcstr.ok):
            data = wtcstr.json()
            line.append(str(data['subscribers_count']))
            line.append(str(data['watchers_count']))
            # line.append(str(data['forks_count']))
            proj_name = data['name']
            tmp = data['created_at'].split("-")
            proj_createdAt = (tmp[0],tmp[1],tmp[2].split('T')[0])
            git_url = data['git_url']
            break
        else:
            # print('[BuildDict] '+str(wtcstr.status_code)+': '+wtcstr.json()['message'])
            if(wtcstr.status_code == 403):
                switchUser()
                continue
                # time.sleep(30)
    
    dict = dictInit(proj_createdAt, name, proj)
    # tmp = OneYrAgo.split('-')
    # strtTm = (tmp[0],tmp[1])
    # dict = dictInit(strtTm, name, proj)
    getContrib(dict, repo+wklyContrib, proj_createdAt)
    print('['+name+'] getContrib finished.')
    getCommitsReleases(dict, git_url, proj_name)
    print('['+name+'] getCommitsReleases finished.')

    issUrls = buildUrlSet(repo+issues)
    # pulUrls = buildUrlSet(repo+pulls)  
    print('['+name+'] buildUrlSet finished.')  
    issSet = getAllUrls(issUrls)
    parseAll(dict, issSet)
    print('['+name+'] getIssuesPulls finished.')
    # pulSet = getAllUrls(pulUrls)
    # parseAll(dict, pulSet, 7)
    # print('getPulls finished.')
    for u in users:    
        checkQuota(u)
    print('['+name+'] buildDict finished.')

    return dict, line

# Output: Write CSV from dictionary
t1writer = csv.writer(open('monthly.csv','w'))
t2writer = csv.writer(open('watch_stars.csv','w'))
# Header, comment out if not needed.
t1writer.writerow(['Proj','URL','YYYYMM','Contributions','Commits','Releases','Issues','Pull Reqs'])
t2writer.writerow(['Proj','URL','# Watches','# Stars'])

begin = time.time()
with open('input.csv') as inputFile:
    rdr = csv.reader(inputFile, delimiter=',')
    ctr = 0
    for row in rdr:
        if(len(row) == 0):
            exit(0)
        name = row[0]
        proj = row[1]
        t1, t2 = buildDict(name, proj)
        for k in t1.keys():
            t1writer.writerow(t1[k])
        t2writer.writerow(t2)
        print('-------'+name+" Done-------")
        ctr+=1

print("Crawled "+str(ctr)+" repos in "+str(datetime.timedelta(seconds=round(time.time() - begin))))
# rm tmp file
subprocess.call('rm *_tmp.txt', shell=True)