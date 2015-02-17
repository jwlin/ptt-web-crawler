# vim: set ts=4 sw=4 et: -*- coding: utf-8 -*-

import re
import sys
import json
import requests
import codecs
from time import sleep
from bs4 import BeautifulSoup  

# if python 3: remove "verify=False" and disable_warnings()
requests.packages.urllib3.disable_warnings()

def crawler(start,end,boardname):
    page = start; times = end-start+1; g_id = 0;
    for a in range(times):
        print('index is '+ str(page))
        resp = requests.get(
            url="http://www.ptt.cc/bbs/"+str(boardname)+"/index"+str(page)+".html", 
            cookies={"over18": "1"}, verify=False
        )
        soup = BeautifulSoup(resp.text)
        for tag in soup.find_all("div","r-ent"):
            try:
                # ex. link would be <a href="/bbs/PublicServan/M.1127742013.A.240.html">Re: [問題] 職等</a>
                href = tag.find('a')['href']
                link = "https://www.ptt.cc" + href
                g_id = re.sub('\.html', '', href.split('/')[-1])
                parseGos(link,g_id,boardname)
            except:
                pass
        sleep(0.2)
        page += 1

def parseGos(link, g_id, boardname):
    resp = requests.get(url=str(link),cookies={"over18":"1"}, verify=False)
    soup = BeautifulSoup(resp.text)
    main_content = soup.find(id="main-content")
    metas = main_content.select('div.article-metaline')
    author = metas[0].select('span.article-meta-value')[0].string
    title = metas[1].select('span.article-meta-value')[0].string
    date = metas[2].select('span.article-meta-value')[0].string
    
    # remove unused nodes
    for meta in metas:
        meta.extract()
    for meta in main_content.select('div.article-metaline-right'):
        meta.extract()
    
    # remove and keep push nodes
    pushes = main_content.find_all('div', class_='push')
    for push in pushes:
        push.extract()

    try:
        ip = main_content.find(text=re.compile('※ 發信站:'))
        ip = re.search("[0-9]*\.[0-9]*\.[0-9]*\.[0-9]*",str(ip)).group()
    except:
        ip = "None"
    
    # 移除 '※ 發信站:', '◆ From:', 空行及多餘空白, 保留英數字, 中文, 網址
    filtered = [ v for v in main_content.stripped_strings if v[0] not in [u'※', u'◆'] and v[:2] not in [u'--'] ]
    for i in range(len(filtered)):
        filtered[i] = re.sub(ur'[^\u4e00-\u9fa5\s\w:/-_.?~%]', '', filtered[i])
    
    filtered = filter(None, filtered) # remove empty strings
    content = ' '.join(filtered)
    content = re.sub(r'(\s)+', ' ', content)
    #print 'content', content
    
    # message
    num , all , g , b , n ,message = 0,0,0,0,0,{}
    for push in pushes:
        num += 1
        push_tag = push.find('span','push-tag').string.replace(' ', '')
        push_userid = push.find('span','push-userid').string.replace(' ', '')
        push_content = push.find('span','push-content').string.replace(' ', '').replace('\n', '').replace('\t', '')
        push_ipdatetime = push.find('span','push-ipdatetime').string.replace('\n', '')

        message[num]={"狀態":push_tag,"留言者":push_userid,"留言內容":push_content,"留言時間":push_ipdatetime}
        if push_tag == u'推 ':
            g += 1
        elif push_tag == u'噓 ':
            b += 1
        else:
            n += 1          
    messageNum = {"g":g,"b":b,"n":n,"all":num}
    # json-data
    #d={ 'board_看板名稱': boardname,"a_ID":g_id , "b_作者":author , "c_標題":title , "d_日期":date , "e_ip":ip , "f_內文":content , "g_推文":message, "h_推文總數":messageNum }
    d={ 'board_': boardname,"a_ID":g_id , "b_":author , "c_":title , "d_":date , "e_ip":ip , "f":content , "g_":message, "h_":messageNum }
    print 'json'
    print d
    print json.dumps(d, indent=4, sort_keys=True, ensure_ascii=False)
    json_data = json.dumps(d, indent=4, sort_keys=True, ensure_ascii=False) + ','
    print 'end'
    store(json_data)
    
def store(data):
    with codecs.open('data.json', 'a', encoding='utf-8') as f:
        f.write(data)

store('[') 

try:
    crawler(int(sys.argv[1]),int(sys.argv[2]),str(sys.argv[3]))
except:
    crawler(int(sys.argv[1]),int(sys.argv[2]),"Gossiping")


store(']') 
with codecs.open('data.json', 'r', encoding='utf-8') as f:
    p = f.read()
    print 'lalal', p
#with codecs.open('data.json', 'w', 'utf-8') as f:
#    f.write(p.replace(',]',']'))
