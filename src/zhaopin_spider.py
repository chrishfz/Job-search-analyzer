__author__ = 'HuangFangZhi'
__time__ = '2018-11-13 16:17'
__Description__ = '从智联招聘网站爬取数据'

import time
from datetime import datetime
from itertools import product
from multiprocessing import Pool
from urllib.parse import urlencode

import pymongo
import requests
from bs4 import BeautifulSoup

from config import *

# 连接 MongoDB URL
client = pymongo.MongoClient(MONGO_URL)
# MongoDB 数据库
db = client[MONGO_DB]


# 模拟浏览器地址栏输入 url
def download(url):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36'}
    
    response = requests.get(url, headers=headers)
    # 返回响应的文本 (网页的 html 结构)
    return response.text


#提取html中的重要信息
def get_content(html):
    # save date
    date = datetime.now().date()
    date = datetime.strftime(date, '%Y-%m-%d')  # to string
    soup = BeautifulSoup(html, 'lxml')
    body = soup.body
    data_main = body.find('div', {'class': 'newlist_list_content'})
    if data_main:
        tables = data_main.find_all('table')
        for i, table_info in enumerate(tables):
            if i == 0:
                continue
            tds = table_info.find('tr').find_all('td')
            zwmc = tds[0].find('a').get_text()  # 职位名称
            zw_link = tds[0].find('a').get('href')  # 职位链接
            fkl = tds[1].find('span').get_text()  # 反馈率
            gsmc = tds[2].find('a').get_text()  # 公司名称
            zwyx = tds[3].get_text()  # 职位月薪
            gzdd = tds[4].get_text()  # 工作地点
            gbsj = tds[5].find('span').get_text()  # 发布日期
            tr_intro = table_info.find('tr', {'class': 'newlist_tr_detail'})  # 招聘简介
            brief = tr_intro.find('li', {'class': 'newlist_deatil_last'}).get_text()

            yield {'zwmc': zwmc,  # 职位名称
                   'fkl': fkl,  # 反馈率
                   'gsmc': gsmc,  # 公司名称
                   'zwyx': zwyx,  # 职位月薪
                   'gzdd': gzdd,  # 工作地点
                   'gbsj': gbsj,  # 公布时间
                   'brief': brief,  # 招聘简介
                   'zw_link': zw_link,  # 网页链接
                   'save_date': date  # 记录信息保存的日期
                   }


def main(args):
    basic_url = 'http://sou.zhaopin.com/jobs/searchresult.ashx?'
    for keyword in KEYWORDS:
        # 关键字作为 MongoDB 的集合(表)
        mongo_table = db[keyword]
        paras = {'jl': args[0],
                 'kw': keyword,
                 # 'el':EDUCATION_BACKGROUND,
                 'p': args[1]  # page
                 }
        url = basic_url + urlencode(paras)
        # http://sou.zhaopin.com/jobs/searchresult.ashx?jl=全国&kw=python&p=30
        # print(url)

        # 爬虫模拟浏览器,下载网页源码
        html = download(url)
        # print(html)
        if html:
            data = get_content(html)
            # 循环抓取的数据,保存到 mongodb
            for item in data:
                if mongo_table.update({'zw_link': item['zw_link']}, {'$set': item}, True):
                    print('Saved', item)


if __name__ == '__main__':
    start = time.time()

    # 模拟爬虫爬数据时所耗时间
    # time.sleep(2)

    number_list = list(range(PAGES))
    # 100 range(0, 100) [0, 1, 2, 3...99]
    # print(PAGES,range(PAGES),list(range(PAGES)))
    args = product(ADDRESS, number_list)

    # Pool会创建固定数目的工作进程,并向这些工作进程传递作业,直到再没有更多作业为止
    pool = Pool()
    # args:address-page的笛卡尔积 多任务处理
    pool.map(main, args)

    end = time.time()
    print('Finished. task runs %s seconds.' % (end - start))
