# vim: set ts=4 sw=4 et: -*- coding: utf-8 -*-
import unittest
import crawler
import codecs, json, os

class TestCrawler(unittest.TestCase):
    def setUp(self):
        self.link = 'https://www.ptt.cc/bbs/PublicServan/M.1413618360.A.4F0.html'
        self.article_id = 'M.1413618360.A.4F0'
        self.board = 'PublicServan'


    def test_parse(self):
        jsondata = crawler.parse(self.link, self.article_id, self.board)
        #print jsondata
        self.assertEqual(jsondata['article_id'], self.article_id)
        self.assertEqual(jsondata['board'], self.board)
        self.assertEqual(jsondata['message_count']['count'], 30)
    

    def test_crawler(self):
        crawler.crawler(['-b', 'PublicServan', '-i', '1', '2'])
        filename = 'PublicServan-1-2.json'
        with codecs.open(filename, 'r', encoding='utf-8') as f:
            data = json.load(f)
            self.assertEqual(len(data['articles']), 40)
            os.remove(filename)


if __name__ == '__main__':
    unittest.main()
