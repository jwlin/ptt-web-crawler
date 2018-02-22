import os
import re
import scrapy
import requests
import datetime as dt

from six import u
from bs4 import BeautifulSoup
from datetime import datetime
from scrapy.conf import settings
from scrapy.http import FormRequest
from scrapy.exceptions import CloseSpider
from ptt_web_crawler.items import PttWebCrawlerItem
from scrapy.spidermiddlewares.httperror import HttpError
from twisted.internet.error import DNSLookupError
from twisted.internet.error import TimeoutError, TCPTimedOutError


class PttWebSpider(scrapy.Spider):
    name = 'ptt-web'
    allowed_domains = ['ptt.cc']

    def __init__(self, board=None, page=None, date=None, article_id=None, max_requests=None, *args, **kwargs):

        super(PttWebSpider, self).__init__(*args, **kwargs)
        self.__domain = 'https://www.ptt.cc'
        self.__request_retries = 0
        self.__cookies = {'over18': '1'}
        self.__board = board or 'Gossiping'
        self.__article_id = article_id
        self.__page = None
        self.__date = None
        self.__max_requests = None

        if date:
            dates = date.split(',')
            dates = list(map(str.strip, dates))
            if len(dates) == 2:
                # store datetime object
                self.__date = (self.ISO8061_ptime(dates[0]), self.ISO8061_ptime(dates[1]))

        if page:
            page_index = page.split(',')
            page_index = list(map(str.strip, page_index))
            if len(page_index) == 2 and all([i.isdigit() or i == '-1' for i in page_index]):
                self.__page = (int(page_index[0].strip()), int(page_index[1]))

        if max_requests and max_requests.isdigit() and int(max_requests) > 0:
            self.__max_requests = int(max_requests)

        self.url = '{}/bbs/{}/index.html'.format(self.__domain, self.__board)
        self.saved_repo = os.path.abspath(os.sep.join(['data', self.__board]))
        self.last_page_index = None
        self.search_steps = None
        self.search_index = None

        if not os.path.exists(self.saved_repo):
            os.makedirs(self.saved_repo)

    @property
    def board(self):
        return self.__board

    @property
    def article_id(self):
        return self.__article_id

    @property
    def crawl_date(self):
        return self.__date

    @property
    def crawl_index(self):
        return self.__page

    def ptt_ptime(self, date_string):
        try:
            return datetime.strptime(date_string, '%a %b %d %H:%M:%S %Y')
        except Exception as e:
            self.logger.exception('{}'.format(e))

    def ISO8061_ptime(self, date_string):
        try:
            return datetime.strptime(date_string, '%Y%m%d')
        except Exception as e:
            self.logget.exception('{}'.format(e))

    def ISO8061_ftime(self, datetime_object):
        try:
            assert isinstance(datetime_object, dt.date)
            return datetime_object.strftime('%Y%m%d')
        except Exception as e:
            self.logger.exception('{}'.format(e))

    def request_by_index(self, index, cb, dont_filter=False):
        assert isinstance(index, int)
        self.logger.info('Processing page {}'.format(index))
        url = '{}/bbs/{}/index{}.html'.format(self.__domain, self.__board, index)
        return scrapy.Request(url=url,
                              callback=cb,
                              errback=self.handle_errback,
                              cookies=self.__cookies,
                              dont_filter=dont_filter)

    def request_by_article_id(self, id, cb, dont_filter=False):
        self.logger.info('Processing article {}'.format(id))
        url = '{}/bbs/{}/{}.html'.format(self.__domain, self.__board, id)
        return scrapy.Request(url=url,
                              callback=cb,
                              errback=self.handle_errback,
                              cookies=self.__cookies,
                              dont_filter=dont_filter)

    def start_requests(self):
        yield scrapy.Request(url=self.url,
                             callback=self.parse,
                             errback=self.handle_errback,
                             cookies=self.__cookies)

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

        if len(response.xpath('//div[@class="over18-notice"]')) > 0:
            if self.__request_retries < self.setting.attributes['REQUEST_RETRY_MAX'].value:
                self.__request_retries += 1
                self.logger.warning('Retry {} times'.format(self.__request_retries))
                yield FormRequest.from_response(response,
                                                formdata={'yes': 'yes'},
                                                callback=self.parse,
                                                errback=self.handle_errback)
            else:
                self.logger.error('You cannot pass')
                raise CloseSpider('You cannot pass over18-form')
        else:

            if not self.last_page_index:
                self.last_page_index = self.get_last_page(response.body)

            # crawling by article id
            if self.__article_id:
                yield self.request_by_article_id(self.__article_id, self.parse_article)

            # crawling by article date
            elif self.__date:

                if not self.search_index:
                    self.search_index = self.last_page_index
                if not self.search_steps:
                    self.search_steps = self.last_page_index

                begin_date, end_date = self.__date
                end_date = end_date + dt.timedelta(days=1)
                first_date_in_page = self.get_nth_date_in_page(response.body, 0)
                last_date_in_page = self.get_nth_date_in_page(response.body, -1)

                # binary search
                self.logger.info('Binary search - step={}, index={}'.format(self.search_steps, self.search_index))
                if self.search_steps > 1:
                    self.search_steps = int(self.search_steps/2)
                    check_time_delta = first_date_in_page - end_date
                    self.logger.info('=====> time delta of {} ~ {}: {}'.format(first_date_in_page, end_date, check_time_delta))

                    if check_time_delta.days < 0:
                        check_last_time = last_date_in_page - end_date
                        if check_last_time.days == 0:
                            self.search_steps = 1
                        # go foreward
                        self.search_index += self.search_steps
                        self.search_index = min(self.search_index, self.last_page_index)
                    else:
                        # go backward
                        self.search_index -= self.search_steps
                        self.search_index = max(self.search_index, 1)

                    yield self.request_by_index(
                        self.search_index, self.parse, dont_filter=True)

                # crawling
                else:
                    yield self.request_by_index(
                        self.search_index, self.parse_until_end_date)

            # crawling by page index
            else:
                begin_page, end_page = 1, self.last_page_index

                if self.__page:
                    is_last = lambda x, y: x if x != -1 else y
                    begin_page, end_page = self.__page
                    begin_page = is_last(begin_page, self.last_page_index)
                    begin_page = min(begin_page, self.last_page_index)
                    end_page = is_last(end_page, self.last_page_index)
                    end_page = min(end_page, self.last_page_index)

                for i in range(begin_page, end_page+1):
                    yield self.request_by_index(i, self.parse_page)

    def parse_until_end_date(self, response):
        soup = BeautifulSoup(response.body, 'lxml')
        divs = soup.find_all('div', attrs={'class': ['r-ent', 'r-list-sep']})
        parse_previous_page = False

        try:
            begin_date, end_date = self.__date
        except Exception as e:
            self.logger.exception('{}'.format(e))

        for div in divs:
            if div['class'][0] == 'r-list-sep':
                break
            try:
                date = div.find_all('div', 'date')[0].text.strip()
                date = datetime.strptime('{}/{}'.format(
                    datetime.now().year ,date), '%Y/%m/%d')
                check_begin_date = date - begin_date
                check_end_date = end_date - date

                if check_begin_date.days < 0 and check_end_date.days > 0:
                    # before begin date
                    if div == divs[0]:
                        parse_previous_page = False
                    continue
                elif check_begin_date.days >= 0 and check_end_date.days >= 0:
                    # in time duration
                    if div == divs[0]:
                        parse_previous_page = True
                    url = '{}{}'.format(self.__domain, div.find('a')['href'])
                    article_id = re.sub(r'.html', '', url.split('/')[-1])
                    yield self.request_by_article_id(article_id, self.parse_article)
                elif check_begin_date.days > 0 and check_end_date.days < 0:
                    # after end date
                    parse_previous_page = True
                    continue
                else:
                    parse_previous_page = False
                    pass

            except Exception as e:
                self.logger.exception('{}'.format(e))

        self.logger.info('parse next page={}'.format(parse_previous_page))
        if parse_previous_page:
            self.search_index -= 1
            yield self.request_by_index(self.search_index, self.parse, dont_filter=True)

    def parse_page(self, response):
        soup = BeautifulSoup(response.body, 'lxml')
        divs = soup.find_all('div', attrs={'class': ['r-ent', 'r-list-sep']})

        for div in divs:
            if div['class'][0] == 'r-list-sep':
                break
            try:
                # ex. link would be <a href="/bbs/PublicServan/M.1127742013.A.240.html">Re: [問題] 職等</a>
                url = '{}{}'.format(self.__domain, div.find('a')['href'])
                article_id = re.sub(r'.html', '', url.split('/')[-1])
                self.logger.info('Processing article {}'.format(article_id))
                yield scrapy.Request(url=url,
                                    callback=self.parse_article,
                                    errback=self.handle_errback,
                                    cookies=self.__cookies)
            except Exception as e:
                self.logger.exception('{}'.format(e))

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
        author = ''
        title = ''
        date = ''

        if metas:
            author = check_str(metas[0].select('span.article-meta-value')[0])
            title = check_str(metas[1].select('span.article-meta-value')[0])
            date = check_str(metas[2].select('span.article-meta-value')[0])

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
            messages.append( {'push_tag': push_tag, 'push_userid': push_userid, 'push_content': push_content, 'push_ipdatetime': push_ipdatetime} )
            if push_tag == u'推':
                p += 1
            elif push_tag == u'噓':
                b += 1
            else:
                n += 1

        # count: 推噓文相抵後的數量; all: 推文總數
        message_count = {'all': p+b+n, 'count': p-b, 'push': p, 'boo': b, "neutral": n}

        data['board'] = self.__board
        data['article_id'] = article_id
        data['article_title'] = title
        data['author'] = author
        data['date'] = date
        data['content'] = content
        data['ip'] = ip
        data['message_count'] = message_count
        data['messages'] = messages

        yield data

    def get_last_page(self, page_content):
        content = page_content.decode('utf-8')
        last_page = re.search(r'href="/bbs/' + self.__board + r'/index(\d+).html">&lsaquo;',content)
        return int(last_page.group(1)) + 1 if last_page else 1

    def get_nth_date_in_page(self, page_content, n):
        '''
        return datetime object but year is unreliable
        '''
        content = page_content.decode('utf-8')
        soup = BeautifulSoup(content, 'lxml')

        sep_line = soup.find('div', {'class': 'r-list-sep'})

        # get the page year by first article on the page
        divs = soup.find_all('div', attrs={'class': ['r-ent', 'r-list-sep']})
        year = None
        for div in divs:
            if div['class'][0] == 'r-list-sep':
                break
            # ex. link would be <a href="/bbs/PublicServan/M.1127742013.A.240.html">Re: [問題] 職等</a>
            url = '{}{}'.format(self.__domain, div.find('a')['href'])
            article_id = re.sub(r'.html', '', url.split('/')[-1])
            self.logger.info('Processing article {}'.format(article_id))
            year_resp = requests.get(url, cookies=self.__cookies)
            year_soup = BeautifulSoup(year_resp.text, 'lxml')
            main_content = year_soup.find(id="main-content")
            metas = main_content.select('div.article-metaline')

            if metas:
                date = metas[2].select('span.article-meta-value')[0]
                date = date.string if date else ''
                date = self.ptt_ptime(date)
                year = date.year
            else:
                year = datetime.now().year
            break

        last_date = None

        try:
            if not sep_line:
                last_date = soup.select('div.date')[n]
            else:
                # last page, last date
                last_row = sep_line.find_previous_sibling('div')
                last_date = last_row.find('div', {'class': 'date'})

            last_date = last_date.text.strip(' ')
            last_date = datetime.strptime('{}/{}'.format(year, last_date), '%Y/%m/%d')
            return last_date

        except Exception as e:
            self.logger.excpetion('{}'.format(e))
