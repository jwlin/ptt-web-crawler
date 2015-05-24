import json, requests
import crawler
from django.shortcuts import render
from django.http import HttpResponse
from django.utils.html import escape
from bs4 import BeautifulSoup

PTT_URL = 'https://www.ptt.cc'
requests.packages.urllib3.disable_warnings()

def home(request):
    if request.method == 'GET':
        return render(
            request,
            'demo/demo.html',
        )
    elif request.method == 'POST' and request.is_ajax():
        bname = escape(request.POST.get('board_name'))
        aid = escape(request.POST.get('article_id'))
        link = PTT_URL + '/bbs/' + bname + '/' + aid + '.html'
        if not (bname and aid):
            return HttpResponse(json.dumps({'data': {'error': 'invalid url'}, 'link': link}), content_type='application/json')
        if aid.lower() == 'latest' or aid.lower() == 'index':
            resp = requests.get(
                url=PTT_URL + '/bbs/' + bname + '/index.html',
                cookies={'over18': '1'}, verify=False
            )
            if resp.status_code == 200:
                soup = BeautifulSoup(resp.text)
                divs = soup.find_all("div", "r-ent")
                aid = divs[-1].select("div.title > a")[0]['href'].split("/")[3].replace(".html", "")
        link = PTT_URL + '/bbs/' + bname + '/' + aid + '.html'
        data = json.loads(
            crawler.parse(link, aid, bname)
        )
        return HttpResponse(json.dumps({'data': data, 'link': link}), content_type='application/json')


