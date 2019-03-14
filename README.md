# ptt-web-crawler 

This repository is a crawler for the web version of PTT, the largest online community in Taiwan. 

### License
MIT 

Forked from [jwlin](https://github.com/jwlin/ptt-web-crawler)

References include [CrawlerTutorial](https://github.com/leVirve/CrawlerTutorial#advanced) by leVirve

### Usage

    usage: python crawler.py [-h] -b BOARD_NAME (-i START_INDEX END_INDEX | -k KEYWORD | -a ARTICLE_ID) [-v]
    
    optional arguments:
      -h, --help                  show this help message and exit
      -b BOARD_NAME               Board name
      -i START_INDEX END_INDEX    Start and end index
      -k KEYWORD                  Search for keyword
      -a ARTICLE_ID               Article ID
      -v, --version               show program's version number and exit

Output file name formats:

* `BOARD_NAME-START_INDEX-END_INDEX.json`
* `BOARD_NAME-KEYWORD.json`
* `BOARD_NAME-ID.json`

### Required Packages
pip install

* argparse
* beautifulsoup4
* requests
* six
* pyOpenSSL

## 特色

* 支援單篇及多篇文章抓取、關鍵字搜尋
* 過濾資料內空白、空行及特殊字元
* JSON 格式輸出
* 支援 Python 2.7, 3.4-3.6


## 操作說明

### 測試
```commandline
python test.py
```

### 參數
```commandline
python crawler.py -b 看板名稱 -i 起始索引 結束索引 (設為負數則以倒數第幾頁計算) 
python crawler.py -b 看板名稱 -k 關鍵字
python crawler.py -b 看板名稱 -a 文章 ID 
```

### 輸出格式
```
{
    "article_id": 文章 ID,
    "article_title": 文章標題 ,
    "author": 作者,
    "board": 板名,
    "content": 文章內容,
    "date": 發文時間,
    "ip": 發文位址,
    "message_count": { # 推文
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


## 範例

### 頁面索引

爬取 PublicServan 板第 100 頁到第 200 頁的所有文章。

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

資料內容會輸出至 `PublicServan-100-200.json`

### 關鍵字搜尋

爬取 Gossiping 板中所有標題有「罷工」一詞的所有文章。

* 直接執行腳本

```commandline
cd PttWebCrawler
python crawler.py -b Gossiping -k 罷工
```
    
* 呼叫 package

```commandline
python setup.py install
python -m PttWebCrawler -b Gossiping -k 罷工
```

* 作為函式庫呼叫

```python
from PttWebCrawler.crawler import *

c = PttWebCrawler(as_lib=True)
c.parse_keyword('罷工', 'Gossiping')
```

後續 index 皆重複出現 invalid url 時以 ctrl + C 終止 Python 程序，資料內容會輸出至 `Gossiping-罷工.json`


### 單篇文章 ID
已知該文章網址，欲下載該篇內容並格式化所撈取的資料。

**注意：並非井字號文章代碼，而是網址中用於區辨文章的部分**

以 https://www.ptt.cc/bbs/Gossiping/M.1550896718.A.6C7.html 為例

* 直接執行腳本

```commandline
cd PttWebCrawler
python crawler.py -b Gossiping -a M.1550896718.A.6C7
```
    
* 呼叫 package

```commandline
python setup.py install
python -m PttWebCrawler -b Gossiping -a M.1550896718.A.6C7
```

* 作為函式庫呼叫

```python
from PttWebCrawler.crawler import *

c = PttWebCrawler(as_lib=True)
c.parse_article('M.1550896718.A.6C7', 'Gossiping')
```

資料內容會輸出至 `Gossiping-M.1550896718.A.6C7.json`