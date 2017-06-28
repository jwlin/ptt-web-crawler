# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/items.html

import scrapy


class PttWebCrawlerItem(scrapy.Item):
    board = scrapy.Field()
    article_id = scrapy.Field()
    article_title = scrapy.Field()
    author = scrapy.Field()
    date = scrapy.Field()
    content = scrapy.Field()
    ip = scrapy.Field()
    message_count = scrapy.Field()
    messages = scrapy.Field()
    error = scrapy.Field()
