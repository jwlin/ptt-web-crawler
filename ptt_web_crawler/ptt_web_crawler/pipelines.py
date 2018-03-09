# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: http://doc.scrapy.org/en/latest/topics/item-pipeline.html
import os
import json

from datetime import datetime


class PttWebCrawlerPipeline(object):

    def open_spider(self, spider):
        self.runtime_file = os.path.abspath('./.tmp.json.swp')
        check_path = os.sep.join(self.runtime_file.split(os.sep)[:-1])

        if not os.path.exists(check_path):
            os.makedirs(check_path)

        self.runtime_file = open(self.runtime_file, 'w+', encoding='utf8')
        self.runtime_file.write('[')
        self.__runtime_file_first_item = True

    def close_spider(self, spider):
        '''
        if crawling by article id: filename=[article_id]
        else: filename=[begin_date]_[end_date]
        '''
        self.runtime_file.write(']')
        self.runtime_file.close()
        *check_path, runtime_file = self.runtime_file.name.split(os.sep)
        #*check_path, runtime_file = self.runtime_file.split(os.sep)

        if spider.article_id:
            runtime_file = spider.article_id + '.json'
        elif spider.dates:
            begin_date, end_date = spider.dates
            begin_date = datetime.strftime(begin_date, '%Y%m%d')
            end_date = datetime.strftime(end_date, '%Y%m%d')
            runtime_file = begin_date + '_' + end_date + '.json'
        elif spider.pages:
            begin_page, end_page = spider.crawl_index
            runtime_file = '{}_page_{}_{}.json'.format(spider.board, begin_page, end_page)
        else:
            runtime_file = datetime.now().strftime('%Y%m%d') + '.json'

        new_filename = os.path.join(os.sep.join(check_path), runtime_file)
        new_filename = os.path.join(spider.saved_repo, new_filename.split(os.sep)[-1])
        os.rename(self.runtime_file.name, new_filename)

    def process_item(self, item, spider):
        item.setdefault('board', '')
        item.setdefault('article_id', '')
        item.setdefault('article_title', '')
        item.setdefault('author', '')
        item.setdefault('date', '')
        item.setdefault('content', '')
        item.setdefault('ip', '')
        item.setdefault('message_count', 0)
        item.setdefault('messages', '')
        item.setdefault('error', '')

        if not isinstance(item, dict):
            item = dict(item)

        if self.__runtime_file_first_item:
            self.__runtime_file_first_item = False
        else:
            self.runtime_file.write(',\n')

        self.runtime_file.write(json.dumps(item, ensure_ascii=False))

        return item
