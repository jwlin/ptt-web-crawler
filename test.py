# -*- coding: utf-8 -*-
import unittest
from PttWebCrawler.crawler import PttWebCrawler as crawler
import codecs, json, os


class TestCrawler(unittest.TestCase):
    def test_parse(self):
        self.link = 'https://www.ptt.cc/bbs/PublicServan/M.1409529482.A.9D3.html'
        self.article_id = 'M.1409529482.A.9D3'
        self.board = 'PublicServan'

        jsondata = json.loads(crawler.parse(self.link, self.article_id, self.board))
        self.assertEqual(jsondata['article_id'], self.article_id)
        self.assertEqual(jsondata['board'], self.board)
        self.assertEqual(jsondata['message_conut']['count'], 57)
    
    def test_parse_with_structured_push_contents(self):
        self.link = 'https://www.ptt.cc/bbs/Gossiping/M.1119222660.A.94E.html'
        self.article_id = 'M.1119222660.A.94E'
        self.board = 'Gossiping'

        jsondata = json.loads(crawler.parse(self.link, self.article_id, self.board))
        self.assertEqual(jsondata['article_id'], self.article_id)
        self.assertEqual(jsondata['board'], self.board)
        isCatched = False
        for msg in jsondata['messages']:
            if u'http://tinyurl.com/4arw47s' in msg['push_content']:
                isCatched = True
        self.assertTrue(isCatched)

    def test_parse_with_push_without_contents(self):
        self.link = 'https://www.ptt.cc/bbs/Gossiping/M.1433091897.A.1C5.html'
        self.article_id = 'M.1433091897.A.1C5'
        self.board = 'Gossiping'

        jsondata = json.loads(crawler.parse(self.link, self.article_id, self.board))
        self.assertEqual(jsondata['article_id'], self.article_id)
        self.assertEqual(jsondata['board'], self.board)

    def test_parse_without_metalines(self):
        self.link = 'https://www.ptt.cc/bbs/NBA/M.1432438578.A.4B0.html'
        self.article_id = 'M.1432438578.A.4B0'
        self.board = 'NBA'

        jsondata = json.loads(crawler.parse(self.link, self.article_id, self.board))
        self.assertEqual(jsondata['article_id'], self.article_id)
        self.assertEqual(jsondata['board'], self.board)

    def test_crawler(self):
        crawler(['-b', 'PublicServan', '-i', '1', '2'])
        filename = 'PublicServan-1-2.json'
        with codecs.open(filename, 'r', encoding='utf-8') as f:
            data = json.load(f)
            # M.1127808641.A.C03.html is empty, so decrease 1 from 40 articles
            self.assertEqual(len(data['articles']), 39)
        data = crawler.get(filename)
        self.assertEqual(len(data['articles']), 39)
        os.remove(filename)

    def test_getLastPage(self):
        boards = ['NBA', 'Gossiping', 'b994060work']  # b994060work for 6259fc0 (pull/6)
        for board in boards:
            try:
                _ = crawler.getLastPage(board)
            except:
                self.fail("getLastPage() raised Exception.")


if __name__ == '__main__':
    unittest.main()
