import datetime
import os
import re

import requests
from bs4 import BeautifulSoup
from six import u

import scrapy
from ptt_web_crawler.items import PttWebCrawlerItem
from scrapy.conf import settings
from scrapy.exceptions import CloseSpider
from scrapy.http import FormRequest
from scrapy.spidermiddlewares.httperror import HttpError
from twisted.internet.error import DNSLookupError
from twisted.internet.error import TCPTimedOutError
from twisted.internet.error import TimeoutError


class PttWebSpider(scrapy.Spider):
    name = 'ptt-web'
    allowed_domains = ['ptt.cc']

    def __init__(self,
                 board='Gossiping',
                 pages=None,
                 dates=None,
                 article_id=None,
                 max_requests=None,
                 *args,
                 **kwargs):
        super().__init__(*args, **kwargs)

        # const
        self._domain = 'https://www.ptt.cc'
        self._cookies = {'over18': '1'}

        self.board = board
        self.article_id = article_id
        self.pages = None
        self.dates = None
        self.max_requests = None

        self.url = '{}/bbs/{}/index.html'.format(self._domain, self.board)
        self.saved_repo = os.path.abspath(os.sep.join(['data', self.board]))
        self.last_page_index = None
        self.search_steps = None
        self.search_index = None

        if not os.path.exists(self.saved_repo):
            os.makedirs(self.saved_repo)

        if dates:
            dates = dates.split(',')
            dates = list(map(str.strip, dates))
            self.dates = (self.ISO8061_ptime(dates[0]), self.ISO8061_ptime(dates[1]))

        if pages:
            page_index = pages.split(',')
            page_index = list(map(str.strip, page_index))
            if len(page_index) == 2 and all([i.isdigit() or i == '-1' for i in page_index]):
                self.pages = (int(page_index[0]), int(page_index[1]))

        if max_requests and max_requests.isdigit() and int(max_requests) > 0:
            self.max_requests = int(max_requests)

    def ptt_article_ptime(self, date_string):
        try:
            return datetime.datetime.strptime(date_string, '%a %b %d %H:%M:%S %Y')
        except Exception as e:
            self.logger.exception('{}'.format(e))

    def ISO8061_ptime(self, date_string):
        try:
            return datetime.datetime.strptime(date_string, '%Y%m%d')
        except Exception as e:
            self.logger.exception('{}'.format(e))

    def ISO8061_ftime(self, datetime_object):
        try:
            assert isinstance(datetime_object, datetime.date)
            return datetime_object.strftime('%Y%m%d')
        except Exception as e:
            self.logger.exception('{}'.format(e))

    def start_requests(self):
        yield scrapy.Request(
            url=self.url,
            callback=self.parse,
            errback=self.handle_errback,
            cookies=self._cookies)

    def request_by_article_id(self, article_id):
        self.logger.info('Processing article {}'.format(article_id))
        url = '{}/bbs/{}/{}.html'.format(self._domain, self.board, article_id)
        return scrapy.Request(
            url=url,
            callback=self.parse_article,
            errback=self.handle_errback,
            cookies=self._cookies)

    def request_by_index(self, index):
        assert isinstance(index, int)
        self.logger.info('Processing page {}'.format(index))
        url = '{}/bbs/{}/index{}.html'.format(self._domain, self.board, index)
        return scrapy.Request(
            url=url,
            callback=self.parse_page,
            errback=self.handle_errback,
            cookies=self._cookies)

    def handle_errback(self, failure):
        self.logger.error(repr(failure))

        if failure.check(HttpError):
            response = failure.value.response
            self.logger.error('HttpError on %s', response.url)
        elif failure.check(DNSLookupError):
            request = failure.request
            self.logger.error('DNSLookupError on %s', request.url)
        elif failure.check(TimeoutError, TCPTimedOutError):
            request = failure.request
            self.logger.error('TimeoutError on %s', request.url)

    def parse(self, response):
        '''
        parse by date - binary search to locate then async crawling
        parse by page - async crawling
        parse by article id - crawl article
        '''

        # if showing the over-18 alert
        if len(response.xpath('//div[@class="over18-notice"]')) > 0:
            requests_retries = 0
            if requests_retries < self.setting.attributes['REQUEST_RETRY_MAX'].value:
                requests_retries += 1
                self.logger.warning('Retry {} times'.format(requests_retries))
                yield FormRequest.from_response(
                    response,
                    formdata={'yes': 'yes'},
                    callback=self.parse,
                    errback=self.handle_errback)
            else:
                self.logger.error('You cannot pass')
                raise CloseSpider('You cannot pass over18-form')

        # get current ptt last page index
        if not self.last_page_index:
            self.last_page_index = self.get_last_page(response.body)

        # parse by article id
        if self.article_id:
            yield self.request_by_article_id(self.article_id)

        # parse by dates
        elif self.dates:
            if not self.search_index:
                self.search_index = self.last_page_index
            if not self.search_steps:
                self.search_steps = self.last_page_index

            try:
                begin_date, end_date = self.dates
                begin_index = self.binary_search(begin_date, 0, self.search_index, self.search_steps)
                end_index = self.binary_search(end_date, 1, self.search_index, self.search_steps)
            except Exception as e:
                self.logger.exception('{}'.format(e))
            for i in range(begin_index, end_index + 1):
                yield self.request_by_index(i)

        # parse by pages
        else:
            begin_index, end_index = self.pages
            for i in range(begin_index, end_index + 1):
                yield self.request_by_index(i)

    def parse_article(self, response):
        data = PttWebCrawlerItem()
        check_str = lambda x: x.string if x else ''
        article_id = '.'.join((response.url.split('/')[-1].split('.')[:-1]))

        if response.status != 200:
            self.logger.warning('Invalid url: {}'.format(response.url))
            data['error'] = 'invalid url'
            yield data

        soup = BeautifulSoup(response.body, 'lxml')
        main_content = soup.find(id="main-content")
        metas = main_content.select('div.article-metaline')
        author, title, date = '', '', ''

        if metas:
            author = check_str(metas[0].select('span.article-meta-value')[0])
            title = check_str(metas[1].select('span.article-meta-value')[0])
            date = check_str(metas[2].select('span.article-meta-value')[0])

            # remove meta nodes
            for meta in metas:
                meta.extract()
            for meta in main_content.select('div.article-metaline-right'):
                meta.extract()

        if self.dates and date:
            begin_date, end_date = self.dates
            article_date = self.ptt_article_ptime(date)
            begin_delta = article_date - begin_date
            end_delta = article_date - end_date
            if begin_delta.days < 0 or end_delta.days > 0:
                return

        # remove and keep push nodes
        pushes = main_content.find_all('div', class_='push')
        for push in pushes:
            push.extract()

        try:
            ip = main_content.find(text=re.compile(u'※ 發信站:'))
            ip = re.search(r'[0-9]*.[0-9]*.[0-9]*.[0-9]*', ip).group()
        except:
            ip = "None"

        # 移除 '※ 發信站:' (starts with u'\u203b'),
        #      '◆ From:' (starts with u'\u25c6'),
        #      空行及多餘空白
        # 保留英數字, 中文及中文標點, 網址, 部分特殊符號
        filtered = [
            v for v in main_content.stripped_strings
            if v[0] not in [u'※', u'◆'] and v[:2] not in [u'--']
        ]
        expr = re.compile(u(r'[^\u4e00-\u9fa5\u3002\uff1b\uff0c\uff1a\u201c\u201d\uff08\uff09\u3001\uff1f\u300a\u300b\s\w:/-_.?~%()]'))

        for i, v in enumerate(filtered):
            v = re.sub(expr, '', v)
            filtered[i] = re.sub(expr, '', filtered[i])

        # remove empty strings
        filtered = [v for v in filtered if v]

        # remove last line containing the url of the article
        filtered = [v for v in filtered if article_id not in v]
        content = ' '.join(filtered)
        content = re.sub(r'(\s)+', ' ', content)

        # push message
        p, b, n = 0, 0, 0
        messages = []
        for push in pushes:
            push_tag = push.find('span', 'push-tag')
            if not push_tag: continue
            push_tag = push_tag.string.strip(' \t\n\r')
            push_userid = push.find('span', 'push-userid').string.strip(' \t\n\r')

            # if find is None: find().strings -> list -> ' '.join; else the current way
            push_content = push.find('span', 'push-content').strings

            # remove ':'
            push_content = ' '.join(push_content)[1:].strip(' \t\n\r')
            push_ipdatetime = push.find('span', 'push-ipdatetime').string.strip(' \t\n\r')
            messages.append({
                'push_tag': push_tag,
                'push_userid': push_userid,
                'push_content': push_content,
                'push_ipdatetime': push_ipdatetime
            })
            if push_tag == u'推':
                p += 1
            elif push_tag == u'噓':
                b += 1
            else:
                n += 1

        # count: 推噓文相抵後的數量; all: 推文總數
        message_count = {
            'all': p + b + n,
            'count': p - b,
            'push': p,
            'boo': b,
            "neutral": n
        }

        data['board'] = self.board
        data['article_id'] = article_id
        data['article_title'] = title
        data['author'] = author
        data['date'] = date
        data['content'] = content
        data['ip'] = ip
        data['message_count'] = message_count
        data['messages'] = messages

        yield data

    def parse_page(self, response):
        soup = BeautifulSoup(response.body, 'lxml')
        divs = soup.find_all('div', attrs={'class': ['r-ent', 'r-list-sep']})
        for div in divs:
            if div['class'][0] == 'r-list-sep':
                break
            try:
                url = '{}{}'.format(self._domain, div.find('a')['href'])
                article_id = re.sub(r'.html', '', url.split('/')[-1])
                self.logger.info('Processing article {}'.format(article_id))
                yield scrapy.Request(
                    url=url,
                    callback=self.parse_article,
                    errback=self.handle_errback,
                    cookies=self._cookies)
            except Exception as e:
                self.logger.exception('{}'.format(e))

    def _binary_search_forward(self, target_dt, method, index, step):
        step = step // 2 or 1
        index = min(index + step, self.last_page_index)
        return self.binary_search(target_dt, method, index, step)

    def _binary_search_backward(self, target_dt, method, index, step):
        step = step // 2 or 1
        index = max(index - step, 0)
        return self.binary_search(target_dt, method, index, step)

    def binary_search(self, target_dt, method, index, step):
        '''
        :params target_dt   target datetime object
        :params method      0 to present the head page and 1 is the end of page
        :params index       index to begin with
        :params step        steps to search
        '''
        assert isinstance(target_dt, datetime.datetime)

        # current page
        page_url = '{}/bbs/{}/index{}.html'.format(self._domain, self.board, index)
        resp_page = requests.get(page_url, cookies=self._cookies)

        # find the head page
        if not method:
            last_article_date = self.get_nth_date_in_page(resp_page.text, -1)
            last_date_delta = last_article_date - target_dt

            if last_date_delta.days > 0:
                return self._binary_search_backward(target_dt, method, index, step)
            elif last_date_delta.days < 0:
                return self._binary_search_forward(target_dt, method, index, step)
            else:
                first_article_date = self.get_nth_date_in_page(resp_page.text, 0)
                first_date_delta = first_article_date - target_dt

                if first_date_delta.days < 0:
                    return index
                elif first_date_delta.days == 0:
                    prev_page_url = '{}/bbs/{}/index{}.html'.format(self._domain, self.board, index - 1)
                    resp_prev_page = requests.get(prev_page_url, cookies=self._cookies)
                    prev_last_article_date = self.get_nth_date_in_page(resp_prev_page.text, -1)
                    prev_last_date_delta = prev_last_article_date - target_dt
                    if prev_last_date_delta.days < 0:
                        return index
                    else:
                        return self._binary_search_backward(target_dt, method, index, step)
        else:
            first_article_date = self.get_nth_date_in_page(resp_page.text, 0)
            first_date_delta = first_article_date - target_dt

            if first_date_delta.days > 0:
                return self._binary_search_backward(target_dt, method, index, step)
            elif first_date_delta.days < 0:
                return self._binary_search_forward(target_dt, method, index, step)
            else:
                end_article_date = self.get_nth_date_in_page(resp_page.text, -1)
                end_date_delta = end_article_date - target_dt

                if end_date_delta.days > 0:
                    return index
                elif end_date_delta.days == 0:
                    next_page_url = '{}/bbs/{}/index{}.html'.format(self._domain, self.board, index + 1)
                    resp_next_page = requests.get(next_page_url, cookies=self._cookies)
                    next_first_article_date = self.get_nth_date_in_page(resp_next_page.text, 0)
                    next_first_date_delta = next_first_article_date - target_dt
                    if next_first_date_delta.days > 0:
                        return index
                    else:
                        return self._binary_search_forward(target_dt, method, index, step)

    def get_last_page(self, page_content):
        content = page_content.decode('utf-8')
        pattern = 'href="/bbs/{}/index(\d+).html">&lsaquo;'.format(self.board)
        last_page = re.search(pattern, content)
        return int(last_page.group(1)) + 1 if last_page else 1

    def get_nth_date_in_page(self, page_html, n):
        soup = BeautifulSoup(page_html, 'lxml')
        divs = soup.find_all('div', attrs={'class': ['r-ent', 'r-list-sep']})
        clear_divs = []
        for cdiv in divs:
            if cdiv['class'][0] == 'r-list-sep':
                break
            clear_divs.append(cdiv)
        n = len(clear_divs) - 1 if n == -1 else n

        for i, div in enumerate(clear_divs):
            if div['class'][0] == 'r-list-sep':
                break
            if i != n:
                continue

            article_href = div.find('a')['href']
            article_url = '{}{}'.format(self._domain, article_href)
            resp_year = requests.get(article_url, cookies=self._cookies)
            soup_year = BeautifulSoup(resp_year.text, 'lxml')
            main_content = soup_year.find(id='main-content')
            metas = main_content.select('div.article-metaline')

            if metas:
                date = metas[2].select('span.article-meta-value')[0]
                date = date.string if date else ''
                date = self.ptt_article_ptime(date)
                return date
            else:
                last_date = soup.select('div.date')[n]
                last_date = last_date.text.strip(' ')
                last_date = datetime.strptime(last_date, '%m/%d')
                return last_date
