#!/usr/bin/python3
# -*- coding: utf8 -*-

import re
import json
import requests
from bs4 import BeautifulSoup


SITEURL = 'https://spb.leroymerlin.ru'


def download_image(url):
    img_name = url.split('/')[-1]  # TODO: check existance
    r = requests.get(url)
    with open(img_name, "wb") as f:
        f.write(r.content)


def get_product_availability_info(sku, api_key):
    '''Gets availability at stores. API key is needed'''
    r = requests.post(
        'https://api.leroymerlin.ru/aem_api/v1/getProductAvailabilityInfo',
        data={'productId': sku, 'productSource': 'E-COMMERCE', 'regionId': '506'},
        headers={'x-api-key': api_key},
    )
    d = r.json()
    amount = {}
    for store in d['stores'].values():
        amount[store.get('storeName')] = store.get('stock')
    return amount


if __name__ == '__main__':
    r = requests.get(f'{SITEURL}/catalogue/dreli-shurupoverty/')  # Catalogue URL
    bs = BeautifulSoup(r.text, 'html.parser')
    lst_items = bs.findAll(
        'a', attrs={'href': re.compile('^/product/')}
    )  # Finding all the product URLs
    item = lst_items[0]  # any item, could be

    item_url = f"{SITEURL}{item.get('href')}"
    r = requests.get(item_url)
    bs = BeautifulSoup(r.text, 'html.parser')
    sre = re.search(' data-apiorchestrator-apikey="([^"]+)" ', r.text)
    if sre:
        api_key = sre.group(1)

    sku = bs.find('span', attrs={'itemprop': 'sku'}).get(
        'content'
    )  # need it for amount & images

    item_info = {
        'link': r.url,
        'title': bs.find('h1').text,
        'sku': sku,
        'price': re.sub('\s', '', bs.find('span', attrs={'slot': 'price'}).text), # space in int
        'amount': get_product_availability_info(sku, api_key),
        'props': {},
        #'images': [] # if needed
    }

    lst_images = bs.findAll(
        'img',
        attrs={
            'alt': 'product image',
            'src': re.compile(item_info['sku']),
        },  # regex could be changed if needed
    )
    lst_image_links = [x['src'] for x in lst_images]

    download_image(lst_image_links[0])  # just one picture

    for div in bs.findAll('div', attrs={'class': 'def-list__group'}):
        item_info['props'][div.dt.text] = div.dd.text.strip()

    json.dump(item_info, open('test1.json', 'w'), indent=2, ensure_ascii=False)
