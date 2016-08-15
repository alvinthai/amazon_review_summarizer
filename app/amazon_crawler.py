#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (C) 2016 Andrea Esuli (andrea@esuli.it)
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

from contextlib import closing
from time import sleep
import argparse
import codecs
import numpy as np
import os
import re
import socket
import sys


if sys.version_info[0] >= 3:
    import urllib
    import urllib.request as request
    import urllib.error as urlerror
else:
    import urllib2 as request
    import urllib2 as urlerror


def download_page(url, referer, maxretries, timeout, pause):
    tries = 0
    htmlpage = None
    while tries < maxretries and htmlpage is None:
        try:
            user_agent = \
                ['Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, '
                 'like Gecko) Chrome/41.0.2228.0 Safari/537.36',
                 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1)AppleWebKit/'
                 '537.36 (KHTML, like Gecko) Chrome/41.0.2227.1 Safari/537.36',
                 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, '
                 'like Gecko) Chrome/41.0.2227.0 Safari/537.36',
                 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 '
                 '(KHTML, like Gecko) Chrome/41.0.2227.0 Safari/537.36',
                 'Mozilla/5.0 (Windows NT 6.3; WOW64) AppleWebKit/537.36 '
                 '(KHTML, like Gecko) Chrome/41.0.2225.0 Safari/537.36',
                 'Mozilla/5.0 (Windows NT 5.1) AppleWebKit/537.36 (KHTML, '
                 'like Gecko) Chrome/35.0.3319.102 Safari/537.36',
                 'Mozilla/5.0 (Windows NT 6.2; Win64; x64) AppleWebKit/537.36 '
                 '(KHTML, like Gecko) Chrome/32.0.1667.0 Safari/537.36',
                 'Mozilla/5.0 (Macintosh; PPC Mac OS X x.y; rv:10.0) '
                 'Gecko/20100101 Firefox/10.0',
                 'Mozilla/5.0 (Windows NT x.y; rv:10.0) Gecko/20100101'
                 'Firefox/10.0',
                 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, '
                 'like Gecko) Chrome/33.0.1750.517 Safari/537.36',
                 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, '
                 'like Gecko) Chrome/34.0.1847.137 Safari/4E423F',
                 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 '
                 '(KHTML, like Gecko) Chrome/36.0.1985.67 Safari/537.36']

            choice = np.random.choice(user_agent)
            # print choice

            code = 404
            req = request.Request(url)
            req.add_header('Referer', referer)
            req.add_header('User-agent', choice)
            with closing(request.urlopen(req, timeout=timeout)) as f:
                code = f.getcode()
                htmlpage = f.read()
                sleep(pause)
        except (urlerror.URLError, socket.timeout, socket.error):
            tries += 1
    if htmlpage:
        return htmlpage.decode('utf-8'), code
    else:
        return None, code


def main():
    # sys.stdout = codecs.getwriter('utf8')(sys.stdout.buffer)
    parser = argparse.ArgumentParser()
    parser.add_argument('-d', '--domain',
                        help='Domain from which to download the reviews. '
                        'Default: com',
                        required=False,
                        type=str, default='com')
    parser.add_argument('-f', '--force',
                        help='Force download even if already successfully '
                        'downloaded', required=False,
                        action='store_true')
    parser.add_argument(
        '-r', '--maxretries',
        help='Max retries to download a file. Default: 3',
        required=False, type=int, default=3)
    parser.add_argument(
        '-t', '--timeout', help='Timeout in seconds for http connections.'
        ' Default: 180',
        required=False, type=int, default=180)
    parser.add_argument(
        '-p', '--pause', help='Seconds to wait between http requests. '
        'Default: 1', required=False, default=1,
        type=float)
    parser.add_argument(
        '-m', '--maxreviews', help='Maximum number of reviews per item to'
        'download. Default:unlimited',
        required=False,
        type=int, default=-1)
    parser.add_argument(
        '-o', '--out', help='Output base path. Default: amazonreviews',
        type=str, default='amazonreviews')
    parser.add_argument('-c', '--captcha',
                        help='Retry on captcha pages until captcha is not '
                        'asked. Default: skip', required=False,
                        action='store_true')
    parser.add_argument('ids', metavar='ID', nargs='+',
                        help='Product IDs for which to download reviews')
    args = parser.parse_args()

    basepath = args.out + os.sep + args.domain

    counterre = re.compile('cm_cr_arp_d_paging_btm_([0-9]+)')
    robotre = re.compile('images-amazon\.com/captcha/')

    for id_ in args.ids:

        if not os.path.exists(basepath + os.sep + id_):
            os.makedirs(basepath + os.sep + id_)

        pause = args.pause + np.random.random() * 2.75

        urlPart1 = "http://www.amazon." + args.domain + "/product-reviews/"
        urlPart2 = "/?ie=UTF8&showViewpoints=0&pageNumber="
        urlPart3 = "&sortBy=helpful"

        referer = urlPart1 + str(id_) + urlPart2 + "1" + urlPart3

        page = 1
        lastPage = 1
        while page <= lastPage:
            if not page == 1 and not args.force and os.path.exists(
                basepath + os.sep + id_ + os.sep + id_ + '_' + str(
                    page) + '.html'):
                print('Already got page ' + str(page) + ' for product ' + id_)
                page += 1
                continue

            url = urlPart1 + str(id_) + urlPart2 + str(page) + urlPart3
            print(url)
            htmlpage, code = download_page(url, referer, args.maxretries,
                                           args.timeout, pause)

            if htmlpage is None or code != 200:
                if code == 503:
                    page -= 1
                    args.pause += 2
                    print('(' + str(code) +
                          ') Retrying downloading the URL: ' +
                          url)
                else:
                    print user_ag
                    print('(' + str(code) + ') Done downloading the URL: ' +
                          url)
                    break
            else:
                print('Got page ' + str(page) + ' out of ' + str(lastPage) +
                      ' for product ' + id_ + ' timeout=' + str(
                    args.pause))
                if robotre.search(htmlpage):
                    print('ROBOT! timeout=' + str(args.pause))
                    if args.captcha or page == 1:
                        # break if robot detected
                        return None
                    else:
                        args.pause += 2
                for match in counterre.findall(htmlpage):
                    try:
                        value = int(match)
                        if value > lastPage:
                            lastPage = value
                    except:
                        pass
                with codecs.open(basepath + os.sep + id_ + os.sep + id_ + '_' +
                                 str(page) + '.html', mode='w',
                                 encoding='utf8') as file:
                    file.write(htmlpage)
                if args.pause >= 2:
                    args.pause -= 1
            referer = urlPart1 + str(id_) + urlPart2 + str(page) + urlPart3
            if args.maxreviews > 0 and page * 10 >= args.maxreviews:
                return page
            page += 1

if __name__ == '__main__':
    main()
