PTTcrawler
==========

A crawler for web PTT

ptt 的網路爬蟲，解析其中資料，爬完會自動產生 data.json，格式如下

    "board_看板名稱": 看板名稱,
    "a_ID": 編號,
    "b_作者": 作者名,
    "c_標題": 標題,
    "d_日期": 發文時間,
    "e_ip": 發文ip,
    "f_內文": 內文,
    "g_推文": {
        "推文編號": {
            "狀態": 推 or 噓 or →,
            "留言內容": 留言內容,
            "留言時間": 留言時間,
            "留言者": 留言者
        }
    },
    "h_推文總數": {
        "all": 推文數目,
        "b": 噓數,
        "g": 推數,
        "n": →數
    }
###執行環境
python 3.x

###如何使用
--------------

    $ python3 pttcrawler.py start end (boardname)

start 和 end 是網址index的數字
https://www.ptt.cc/bbs/Gossiping/index.html
可自由決定要爬取的index範圍
board : 可輸入指定的看板名稱，預設為八卦版(Gossiping)
Note. 可參考 https://www.ptt.cc/bbs

###example
--------------

    $ python3 pttcrawler.py 200 500
    
則會爬取
https://www.ptt.cc/bbs/Gossiping/index200.html 至
https://www.ptt.cc/bbs/Gossiping/index500.html
之間的內容。
    
    $ python3 pttcrawler.py 200 500 NBA

則會爬取
https://www.ptt.cc/bbs/NBA/index200.html 至
https://www.ptt.cc/bbs/NBA/index500.html
之間的內容。

