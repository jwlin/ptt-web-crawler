# vim: set ts=4 sw=4 et: -*- coding: utf-8 -*-
from __future__ import absolute_import
from __future__ import print_function

import os
import re
import sys
import json
import requests
import argparse
import time
import codecs
from datetime import datetime
from bs4 import BeautifulSoup
from six import u

__version__ = '1.0'

# if python 2, disable verify flag in requests.get()
VERIFY = True
if sys.version_info[0] < 3:
    VERIFY = False
    requests.packages.urllib3.disable_warnings()

class PttWebCrawler(object):
    """docstring for PttWebCrawler"""
    def __init__(self, cmdline=None):
        parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter, description='''
            A crawler for the web version of PTT, the largest online community in Taiwan.
            Input: board name and page indices (or articla ID)
            Output: BOARD_NAME-START_INDEX-END_INDEX.json (or BOARD_NAME-ID.json)
        ''')
        parser.add_argument('-b', metavar='BOARD_NAME', help='Board name', required=True)
        parser.add_argument('-t', metavar=('START_DATE', 'END_DATE'), type=str, nargs=2, help="Start and end date (YYMMDD)")
        group = parser.add_mutually_exclusive_group(required=True)
        group.add_argument('-i', metavar=('START_INDEX', 'END_INDEX'), type=int, nargs=2, help="Start and end index")
        group.add_argument('-a', metavar='ARTICLE_ID', help="Article ID")
        parser.add_argument('-v', '--version', action='version', version='%(prog)s ' + __version__)

        args = parser.parse_args(cmdline) if cmdline else parser.parse_args()
        self.url = 'https://www.ptt.cc'
        self.__board = args.b
        self.__dirname = os.path.join('data', self.__board)
        start_page, end_page = (1, -1)
        start_date, end_date = (None, None)

        if args.i:
            start_page, end_page = args.i[0], args.i[1]
        end_page = self.getLastPage(self.__board) if end_page == -1 else end_page

        if args.t:
            start_date, end_date = (args.t[0], args.t[1])

        if args.a:
            article_id = args.a
            link = self.url + '/bbs/' + self.__board + '/' + article_id + '.html'
            filename = self.__board + '-' + article_id + '.json'
            self.store(filename, self.parse(link, article_id, self.__board), 'w')

        else:
            for i in range(start_page, end_page+1):
                print('Processing index:', str(i))
                resp = requests.get(
                    url=self.url + '/bbs/' + self.__board + '/index' + str(i) + '.html',
                    cookies={'over18': '1'}, verify=VERIFY
                )
                if resp.status_code != 200:
                    print('invalid url:', resp.url)
                    continue
                soup = BeautifulSoup(resp.text, 'html.parser')
                divs = soup.find_all("div", "r-ent")
                check_page_time_duration = False
                for div in divs:
                    try:
                        # ex. link would be <a href="/bbs/PublicServan/M.1127742013.A.240.html">Re: [問題] 職等</a>
                        data = self.__parseTag(div)
                        article_id = data['article_id']

                        if start_date and end_date:
                            timedelta = self.timeDuration(start_date, end_date, self.pttftime(data['date']))
                            if not check_page_time_duration and (timedelta[0].days < 0 or timedelta[1].days < 0):
                                print('Article out of date: {}'.format(article_id))
                                check_page_time_duration = True
                                last_data_in_page = self.__parseTag(divs[-1])
                                last_data_timedelta = self.timeDuration(start_date, end_date, self.pttftime(last_data_in_page['date']))
                                if last_data_timedelta[0].days < 0 or last_data_timedelta[1].days < 0:
                                    print('Page {} out of date'.format(i))
                                    break

                        filename = os.path.join(self.__dirname, self.pttftime(data['date']), str(article_id)+'.json')
                        self.checkExist(filename)
                        self.store(filename, json.dumps(data, sort_keys=True, ensure_ascii=False), 'a')
                    except Exception as e:
                        exc_type, exc_obj, exc_tb = sys.exc_info()
                        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
                        print('{}::L:{}: {} {}'.format(fname, exc_tb.tb_lineno, exc_type, e))
                time.sleep(0.1)

    def __parseTag(self, tag):
        href = tag.find('a')['href']
        link = self.url + href
        article_id = re.sub('\.html', '', href.split('/')[-1])
        data = self.parse(link, article_id, self.__board, out='dict')
        return data

    @staticmethod
    def pttftime(date):
        return datetime.strptime(date, '%a %b %d %H:%M:%S %Y').strftime('%Y%m%d')

    @staticmethod
    def timeDuration(begin, end, check_date):
        try:
            begin = datetime.strptime(begin, '%Y%m%d')
            end = datetime.strptime(end, '%Y%m%d')
            check_date = datetime.strptime(check_date, '%Y%m%d')
            check_begin = check_date - begin
            check_end = end - check_date
            return check_begin, check_end
        except Exception as e:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            print('{}::L:{}: {} {}'.format(fname, exc_tb.tb_lineno, exc_type, e))

    @staticmethod
    def checkExist(filename):
        dirname = os.sep.join(filename.split(os.sep)[:-1])
        if not os.path.exists(dirname):
            os.makedirs(dirname)

    @staticmethod
    def parse(link, article_id, board, out='json'):
        print('Processing article:', article_id)
        resp = requests.get(url=link, cookies={'over18': '1'}, verify=VERIFY)
        if resp.status_code != 200:
            print('invalid url:', resp.url)
            return json.dumps({"error": "invalid url"}, sort_keys=True, ensure_ascii=False)
        soup = BeautifulSoup(resp.text, 'html.parser')
        main_content = soup.find(id="main-content")
        metas = main_content.select('div.article-metaline')
        author = ''
        title = ''
        date = ''
        if metas:
            author = metas[0].select('span.article-meta-value')[0].string if metas[0].select('span.article-meta-value')[0] else author
            title = metas[1].select('span.article-meta-value')[0].string if metas[1].select('span.article-meta-value')[0] else title
            date = metas[2].select('span.article-meta-value')[0].string if metas[2].select('span.article-meta-value')[0] else date

            # remove meta nodes
            for meta in metas:
                meta.extract()
            for meta in main_content.select('div.article-metaline-right'):
                meta.extract()

        # remove and keep push nodes
        pushes = main_content.find_all('div', class_='push')
        for push in pushes:
            push.extract()

        try:
            ip = main_content.find(text=re.compile(u'※ 發信站:'))
            ip = re.search('[0-9]*\.[0-9]*\.[0-9]*\.[0-9]*', ip).group()
        except:
            ip = "None"

        # 移除 '※ 發信站:' (starts with u'\u203b'), '◆ From:' (starts with u'\u25c6'), 空行及多餘空白
        # 保留英數字, 中文及中文標點, 網址, 部分特殊符號
        filtered = [ v for v in main_content.stripped_strings if v[0] not in [u'※', u'◆'] and v[:2] not in [u'--'] ]
        expr = re.compile(u(r'[^\u4e00-\u9fa5\u3002\uff1b\uff0c\uff1a\u201c\u201d\uff08\uff09\u3001\uff1f\u300a\u300b\s\w:/-_.?~%()]'))
        for i in range(len(filtered)):
            filtered[i] = re.sub(expr, '', filtered[i])

        filtered = [_f for _f in filtered if _f]  # remove empty strings
        filtered = [x for x in filtered if article_id not in x]  # remove last line containing the url of the article
        content = ' '.join(filtered)
        content = re.sub(r'(\s)+', ' ', content)
        # print 'content', content

        # push messages
        p, b, n = 0, 0, 0
        messages = []
        for push in pushes:
            if not push.find('span', 'push-tag'):
                continue
            push_tag = push.find('span', 'push-tag').string.strip(' \t\n\r')
            push_userid = push.find('span', 'push-userid').string.strip(' \t\n\r')
            # if find is None: find().strings -> list -> ' '.join; else the current way
            push_content = push.find('span', 'push-content').strings
            push_content = ' '.join(push_content)[1:].strip(' \t\n\r')  # remove ':'
            push_ipdatetime = push.find('span', 'push-ipdatetime').string.strip(' \t\n\r')
            messages.append( {'push_tag': push_tag, 'push_userid': push_userid, 'push_content': push_content, 'push_ipdatetime': push_ipdatetime} )
            if push_tag == u'推':
                p += 1
            elif push_tag == u'噓':
                b += 1
            else:
                n += 1

        # count: 推噓文相抵後的數量; all: 推文總數
        message_count = {'all': p+b+n, 'count': p-b, 'push': p, 'boo': b, "neutral": n}

        # print 'msgs', messages
        # print 'mscounts', message_count

        # json data
        data = {
            'board': board,
            'article_id': article_id,
            'article_title': title,
            'author': author,
            'date': date,
            'content': content,
            'ip': ip,
            'message_conut': message_count,
            'messages': messages
        }
        # print 'original:', d
        if out == 'json':
            return json.dumps(data, sort_keys=True, ensure_ascii=False)
        else:
            return data

    @staticmethod
    def getLastPage(board):
        content = requests.get(
            url= 'https://www.ptt.cc/bbs/' + board + '/index.html',
            cookies={'over18': '1'}
        ).content.decode('utf-8')
        first_page = re.search(r'href="/bbs/' + board + '/index(\d+).html">&lsaquo;', content)
        if first_page is None:
            return 1
        return int(first_page.group(1)) + 1

    @staticmethod
    def store(filename, data, mode):
        with codecs.open(filename, mode, encoding='utf-8') as f:
            f.write(data)

    @staticmethod
    def get():
        with codecs.open(filename, mode, encoding='utf-8') as f:
            j = json.load(f)
            print(f)

if __name__ == '__main__':
    c = PttWebCrawler()
