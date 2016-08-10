from __future__ import division
from bs4 import BeautifulSoup
from scripts.polarizer import *
from scripts.summarizer import *
from flask import Flask, request, render_template
import cPickle
import json
import numpy as np
import requests


app = Flask(__name__)

with open('data/polarizer3.pkl', 'rb') as f:
    pol1 = cPickle.load(f)
with open('data/polarizer4.pkl', 'rb') as f:
    pol2 = cPickle.load(f)

# asin1, asin2 = pol1.asin, pol2.asin
# url1 = 'https://www.amazon.com/dp/{}/'.format(asin1)
# url2 = 'https://www.amazon.com/dp/{}/'.format(asin2)
#
# header1 = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_2) ' \
#           'AppleWebKit/600.3.18 (KHTML, like Gecko) Version/8.0.3' \
#           'Safari/600.3.18'
# header2 = 'Mozilla/5.0 (compatible; MSIE 10.0; Windows NT 6.1; Trident/6.0)'
#
# html1 = requests.get(url1, headers={'User-Agent': header1}).content
# html2 = requests.get(url2, headers={'User-Agent': header2}).content
#
# soup1 = BeautifulSoup(html1, 'html.parser')
# soup2 = BeautifulSoup(html2, 'html.parser')
#
# try:
#     img1 = soup1.find("div", {"id": "imgTagWrapperId"}).find("img")
#     img_url1 = json.loads(img1["data-a-dynamic-image"]).keys()[0]
#
#     img2 = soup2.find("div", {"id": "imgTagWrapperId"}).find("img")
#     img_url2 = json.loads(img2["data-a-dynamic-image"]).keys()[0]
#
#     price1 = soup1.find("span", {"id": "priceblock_ourprice"})
#     price2 = soup2.find("span", {"id": "priceblock_ourprice"})
#
#     if not price1:
#         price1 = soup1.find_all("span", {"class": "a-color-price"})[0]
#     if not price2:
#         price1 = soup2.find_all("span", {"class": "a-color-price"})[0]
#
#     price1, price2 = price1.text, price2.text
#
#     title1 = soup1.find("span", {"id": "productTitle"}).text.strip()
#     title2 = soup2.find("span", {"id": "productTitle"}).text.strip()
# except:
#     img_url1 = 'http://placehold.it/800x300'
#     title1 = pol1.name
#     price1 = 'N/A'
#
#     img_url2 = 'http://placehold.it/800x300'
#     title2 = pol2.name
#     price2 = 'N/A'

title1, title2 = pol1.name, pol2.name
url1, url2 = "", ""
price1, price2 = "$1", "$1"
img_url1 =  "https://images-na.ssl-images-amazon.com/images/I/71rHYqOkvNL._SX466_.jpg"
img_url2 = "https://images-na.ssl-images-amazon.com/images/I/91L30nswRuL._SY450_.jpg"

aspectsf, aspects = common_features(pol1, pol2, printing=False)
aspectsf, aspects = aspectsf[0:10, 1:].tolist(), aspects[0:10]
en_aspects = [[x[0], x[1]] for x in enumerate(aspects)]

aspects1_pct = np.array([pol1.aspect_pct[x] for x in aspects])
aspects1_pct_vis = np.apply_along_axis(lambda x: 5 + x / sum(x) * 85, 1,
                                       aspects1_pct)
aspects2_pct = np.array([pol2.aspect_pct[x] for x in aspects])
aspects2_pct_vis = np.apply_along_axis(lambda x: 5 + x / sum(x) * 85, 1,
                                       aspects2_pct)

aspects1_pct = np.hstack([aspects1_pct, aspects1_pct_vis]).tolist()
aspects2_pct = np.hstack([aspects2_pct, aspects2_pct_vis]).tolist()
aspects_pct = [aspects1_pct, aspects2_pct]

ratings1 = [np.mean(pol1.ratings[x]) for x in aspects]
ratings2 = [np.mean(pol2.ratings[x]) for x in aspects]
ratings = [ratings1, ratings2]

html_str, js_arr = flask_output_iter(aspects, pol1, pol2, 105)


# Form page to submit
@app.route('/')
def index():
    return render_template('app_results.html', aspects=en_aspects,
                           aspects_f=aspectsf, aspects_pct=aspects_pct,
                           ratings=ratings, html_str=html_str,
                           review_txt=js_arr, img_url1=img_url1,
                           img_url2=img_url2, title1=title1, title2=title2,
                           price1=price1, price2=price2, url1=url1, url2=url2)


@app.route('/full-review')
def generate():
    return render_template('full_review.html')


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True)
