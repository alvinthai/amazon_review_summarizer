from __future__ import division
from bs4 import BeautifulSoup
from pipeline import summarize
from summarizer import *
import json
import numpy as np
import requests


def displayed_aspects(polarizer1, polarizer2=None, n=10):
    '''
    INPUT: Polarizer, Polarizer, int
    OUTPUT: list, list, list

    args:
        n (int): number of aspects to match between two products

    Returns a list of top n aspects between two products, a list of top n
    aspects with review frequency, and an enumerated list of top n aspects
    '''
    if polarizer2:
        aspectsf, aspects = common_features(polarizer1, polarizer2,
                                            printing=False)
        aspectsf, aspects = aspectsf[0:10, 1:].tolist(), aspects[0:10]
    else:
        aspects = polarizer1.top_asps[0][0:10]
        aspectsf = polarizer1.top_asps[1][0:10]

    if not aspectsf:
        return None, None, None

    en_aspects = [[x[0], x[1]] for x in enumerate(aspects)]

    return aspects, aspectsf, en_aspects


def model_data(polarizer, aspects=None):
    '''
    INPUT: Polarizer, list
    OUTPUT: list, list

    Given a list of aspects, return a list of sentiment class percentage data
    (raw data, and visualizion normalized data) and a list of average rating
    data for aspect
    '''
    if not aspects:
        aspects = polarizer.top_asps[0]

    aspects_pct = np.array([polarizer.aspect_pct[x] for x in aspects])
    aspects_pct_vis = np.apply_along_axis(lambda x: 5 + x / sum(x) * 85, 1,
                                          aspects_pct)

    aspects_pct_all = np.hstack([aspects_pct, aspects_pct_vis]).tolist()
    mean_ratings = [np.mean(polarizer.ratings[x]) for x in aspects]

    return aspects_pct_all, mean_ratings


def product_info(polarizer, head=0):
    '''
    INPUT: Polarizer, int
    OUTPUT: str, str, str, str

    args:
        head (int): index of which user agent header to use

    Gets image url, price, title, and product url of product
    '''
    asin = polarizer.asin
    url = 'https://www.amazon.com/dp/{}/'.format(asin)
    headers = ['Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_2) ' +
               'AppleWebKit/600.3.18 (KHTML, like Gecko) Version/8.0.3' +
               'Safari/600.3.18',
               'Mozilla/5.0 (compatible; MSIE 10.0; Windows NT 6.1; ' +
               'Trident/6.0)']

    html = requests.get(url, headers={'User-Agent': headers[head]}).content
    soup = BeautifulSoup(html, 'html.parser')

    try:
        img = soup.find("div", {"id": "imgTagWrapperId"}).find("img")
        img_url = json.loads(img["data-a-dynamic-image"]).keys()[0]

        price = soup.find("span", {"id": "priceblock_ourprice"})
        if not price:
            price = soup.find_all("span", {"class": "a-color-price"})[0].text
        else:
            price = price.text

        title = soup.find("span", {"id": "productTitle"}).text.strip()
    except:
        img_url = 'http://placehold.it/800x300'
        title = polarizer.name
        price = 'N/A'

    return img_url, price, title, url


def collect(url1, url2=None):
    '''
    INPUT: str, str
    OUTPUT: dict

    Runs functions to pass data for product1 and product2 (if applicable)
    into flask application. Returns a dictionary of lists.
    '''
    try:
        polarizer1, data1 = summarize(url1)

        if url2:
            polarizer2, data2 = summarize(url2)
        else:
            polarizer2 = None
    except RuntimeError:
        return "Scraping failed"

    aspects, aspectsf, en_aspects = displayed_aspects(polarizer1, polarizer2)
    if not aspectsf:
        return "No matches"

    aspects_pct_all1, mean_ratings1 = model_data(polarizer1, aspects)
    img_url1, price1, title1, url1 = product_info(polarizer1)

    if not url2:
        aspects_pct, ratings = [aspects_pct_all1], [mean_ratings1]
        img_urls, prices, titles, urls = [img_url1], [price1], [title1], [url1]
        data1 = [[lst] for lst in data1]
        authors_lst, headlines_lst, ratings_lst, reviews_lst = data1
    else:
        aspects_pct_all2, mean_ratings2 = model_data(polarizer2, aspects)
        img_url2, price2, title2, url2 = product_info(polarizer2, 1)

        aspects_pct = [aspects_pct_all1, aspects_pct_all2]
        ratings = [mean_ratings1, mean_ratings2]
        img_urls = [img_url1, img_url2]
        prices = [price1, price2]
        titles = [title1, title2]
        urls = [url1, url2]

        authors_lst = [data1[0], data2[0]]
        headlines_lst = [data1[1], data2[1]]
        ratings_lst = [data1[2], data2[2]]
        reviews_lst = [data1[3], data2[3]]

    html_str, js_arr = flask_output_iter(aspects, polarizer1, polarizer2, 105)

    output_dic = {'aspectsf': aspectsf,
                  'aspects_pct': aspects_pct,
                  'en_aspects': en_aspects,
                  'ratings': ratings,
                  'html_str': html_str,
                  'js_arr': js_arr,
                  'img_urls': img_urls,
                  'prices': prices,
                  'titles': titles,
                  'urls': urls,
                  'authors_lst': authors_lst,
                  'headlines_lst': headlines_lst,
                  'ratings_lst': ratings_lst,
                  'reviews_lst': reviews_lst}

    return output_dic
