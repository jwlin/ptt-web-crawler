# ptt-web-crawler (PTT 網路版爬蟲) [![Build Status](https://travis-ci.org/jwlin/ptt-web-crawler.svg?branch=master)](https://travis-ci.org/jwlin/ptt-web-crawler)

### [Live demo](http://app.castman.net/ptt-web-crawler)

特色

* 支援單篇及多篇文章抓取
* 過濾資料內空白、空行及特殊字元
* JSON 格式輸出
* 支援 Python 2.7 - 3.6

輸出 JSON 格式
```
{
    "article_id": 文章 ID,
    "article_title": 文章標題 ,
    "author": 作者,
    "board": 板名,
    "content": 文章內容,
    "date": 發文時間,
    "ip": 發文位址,
    "message_conut": { # 推文
        "all": 總數,
        "boo": 噓文數,
        "count": 推文數-噓文數,
        "neutral": → 數,
        "push": 推文數
    },
    "messages": [ # 推文內容
      {
        "push_content": 推文內容,
        "push_ipdatetime": 推文時間及位址,
        "push_tag": 推/噓/→ ,
        "push_userid": 推文者 ID
      },
      ...
      ]
}
```

### 參數說明

```commandline
python crawler.py -b 看板名稱 -i 起始索引 結束索引 (設為負數則以倒數第幾頁計算) 
python crawler.py -b 看板名稱 -a 文章ID 
```

### 範例

爬取 PublicServan 板第 100 頁 (https://www.ptt.cc/bbs/PublicServan/index100.html) 
到第 200 頁 (https://www.ptt.cc/bbs/PublicServan/index200.html) 的內容，
輸出至 `PublicServan-100-200.json`

* 直接執行腳本

```commandline
cd PttWebCrawler
python crawler.py -b PublicServan -i 100 200
```
    
* 呼叫 package

```commandline
python setup.py install
python -m PttWebCrawler -b PublicServan -i 100 200
```

* 作為函式庫呼叫

```python
from PttWebCrawler.crawler import *

c = PttWebCrawler(as_lib=True)
c.parse_articles(100, 200, 'PublicServan')
```

### 測試
```commandline
python test.py
```

***

ptt-web-crawler is a crawler for the web version of PTT, the largest online community in Taiwan. 

    usage: python crawler.py [-h] -b BOARD_NAME (-i START_INDEX END_INDEX | -a ARTICLE_ID) [-v]
    optional arguments:
      -h, --help                  show this help message and exit
      -b BOARD_NAME               Board name
      -i START_INDEX END_INDEX    Start and end index
      -a ARTICLE_ID               Article ID
      -v, --version               show program's version number and exit

Output would be `BOARD_NAME-START_INDEX-END_INDEX.json` (or `BOARD_NAME-ID.json`)
