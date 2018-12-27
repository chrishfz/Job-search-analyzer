__author__ = 'HuangFangZhi'
__time__ = '2018-11-13'
__description__ = '智联招聘网的数据分析与数据可视化 模块'

import os

import PIL.Image as Image
import jieba
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import pymongo
from wordcloud import WordCloud, ImageColorGenerator

from config import *


class Analysis:
    def __init__(self, keyword, city=None):
        self.__keyword = keyword
        self.__df_city = None
        self.__city = city
        self.__df_city_main = self.__preference()

    def __preference(self):
        plt.style.use('ggplot')
        # to solve problem of displaying Chinese
        # default font
        plt.rcParams['font.sans-serif'] = ['SimHei']
        # to solve the problem of displaying the box
        plt.rcParams['axes.unicode_minus'] = False

        client = pymongo.MongoClient(MONGO_URL)
        db = client[MONGO_DB]
        table = db[self.__keyword]

        columns = ['zwmc',  # 职位名称
                   'gsmc',  # 公司名称
                   'zwyx',  # 职位月薪
                   'gbsj',  # 公布时间
                   'gzdd',  # 工作地点
                   'fkl',  # 反馈率
                   'brief',  # 招聘简介
                   'zw_link',  # 网页链接
                   '_id',  # 主键 id
                   'date_saved']  # 保存日期

        df = pd.DataFrame([records for records in table.find()], columns=columns)
        print('Total records: {}'.format(df.shape[0]))

        df.head(2)
        df['date_saved'] = pd.to_datetime(df['date_saved'])
        df_clean = df[[
            'zwmc',  # 职位名称
            'gsmc',  # 公司名称
            'zwyx',  # 职位月薪
            'gbsj',  # 公布时间
            'gzdd',  # 工作地点
            'fkl',  # 反馈率
            'brief',  # 招聘简介
            'zw_link',  # 网页链接
            'date_saved'
        ]]

        # 删除工资不明确的记录，比如面议
        df_clean = df_clean[df_clean['zwyx'].str.contains('\d+-\d+', regex=True)]

        print('Total records after cleaning: {}'.format(df_clean.shape[0]))

        s_min, s_max = df_clean.loc[:, 'zwyx'].str.split('-', 1).str
        df_min = pd.DataFrame(s_min)
        df_min.columns = ['zwyx_min']
        df_max = pd.DataFrame(s_max)
        df_max.columns = ['zwyx_max']

        df_clean_concat = pd.concat([df_clean, df_min, df_max], axis=1)
        df_clean_concat['zwyx_min'] = pd.to_numeric(df_clean_concat['zwyx_min'])
        df_clean_concat['zwyx_max'] = pd.to_numeric(df_clean_concat['zwyx_max'])
        df_clean_concat.head(2)

        if self.__city is not None:
            df_city = df_clean_concat[df_clean_concat['gzdd'].str.contains(self.__city + '.*', regex=True)]
            print('These are ' + '{}'.format(df_city.shape[0]) + ' positions in ' + self.__city)
        else:
            df_city = df_clean_concat.copy()
        self.__df_city = df_city

        for city in ADDRESS:
            df_city['gzdd'] = df_city['gzdd'].replace([(city + '.*')], regex=True)

        df_city_main = df_city[df_city['gzdd'].isin(ADDRESS)]
        # print(df_city_main)

        return df_city_main

    # 前十城市 饼图 ***********************************************
    def top10City(self):
        try:
            if self.__city is not None:
                raise NameError('one city')
        except NameError:
            print('You are analysing only one city.')
            return

        df_city_main_count = self.__df_city_main.groupby('gzdd')['zwmc', 'gsmc'].count()

        df_city_main_count['gsmc'] = df_city_main_count['gsmc'] / (df_city_main_count['gsmc'].sum())

        df_city_main_count.columns = ['number', 'percentage']

        # 按位置排序
        df_city_main_count.sort_values(by='number', ascending=False, inplace=True)

        # 添加标签和百分比
        df_city_main_count['label'] = df_city_main_count.index + ' ' + (
            (df_city_main_count['percentage'] * 100)).astype('int').astype('str') + '%'

        # 排名前十的职位分布
        top10 = df_city_main_count.head(10)
        print(top10)

        with open(os.path.dirname(__file__) + '/../data/' + self.__keyword + '_top10_positions_nums.txt', 'w',
                  encoding='utf-8') as f:
            f.write(top10.to_string())

        label = df_city_main_count['label']
        sizes = df_city_main_count['number']
        # 设置图形大小
        fig, axes = plt.subplots(figsize=(10, 6), ncols=2)
        ax1, ax2 = axes.ravel()
        # 太多的城市标签和百分比将不会显示。
        patches, texts = ax1.pie(sizes, shadow=False, startangle=0, colors=None)

        ax1.axis('equal')
        ax1.set_title(self.__keyword + '职位数量主要城市分布', loc='center')
        # ax2 只展示图列
        ax2.axis('off')
        ax2.legend(patches, label, loc='center left', fontsize=9)
        plt.savefig(os.path.dirname(__file__) + '/../images/' + self.__keyword + '_positions_distribution.png')

    # 职位月薪 柱状图
    def salaryAnalysis(self):
        df_zwyx_adjust = self.__df_city[self.__df_city['zwyx_max'] <= 35000]
        if self.__city is not None:
            excel_filename = os.path.dirname(
                __file__) + '/../data/' + self.__keyword + '_zhilian_' + self.__city + '.xlsx'
        else:
            excel_filename = os.path.dirname(
                __file__) + '/../data/' + self.__keyword + '_zhilian_全国.xlsx'

        # 生成 excel 文件
        self.__df_city.to_excel(excel_filename)

        fig, ax2 = plt.subplots(figsize=(10, 8))
        y1 = df_zwyx_adjust['zwyx_max']
        bins = [3000, 6000, 9000, 12000, 15000, 18000, 21000, 32000]
        counts, bins, patches = ax2.hist(y1, bins, density=True, histtype='bar', facecolor='#87CEFA', rwidth=0.8)

        if self.__city is None:
            ax2.set_title(self.__keyword + ' 全国最高月薪直方图', size=14)
        else:
            ax2.set_title(self.__keyword + ' ' + self.__city + '最高月薪直方图', size=14)

        ax2.set_yticklabels('')
        ax2.set_xlabel('月薪(RMB)')

        ax2.set_xticks(bins)
        ax2.set_xticklabels(bins, rotation=-90)

        bin_centers = 0.5 * np.diff(bins) + bins[:-1]

        for count, x in zip(counts, bin_centers):
            percent = '%0.0f%%' % (100 * float(count) / counts.sum())

            ax2.annotate(percent,
                         xy=(x, 0),
                         xycoords=('data', 'axes fraction'),
                         xytext=(0, -40),
                         textcoords='offset points',
                         va='top',
                         ha='center',
                         rotation=-90,
                         color='b',
                         size=14)

        if self.__city is not None:
            fig_name = os.path.dirname(
                __file__) + '/../images/' + self.__keyword + '_salary_distribution_' + self.__city + '.png'
        else:
            fig_name = os.path.dirname(
                __file__) + '/../images/' + self.__keyword + '_salary_distribution_全国.png'

        fig.savefig(fig_name)

    def saveBrief(self):
        brief_list = list(self.__df_city['brief'])
        brief_str = ''.join(brief_list)
        if self.__city is None:
            filename = os.path.dirname(__file__) + '/../data/' + self.__keyword + '_brief_全国.txt'
        else:
            filename = os.path.dirname(__file__) + '/../data/' + self.__keyword + '_brief_' + self.__city + '.txt'

        with open(filename,'w', encoding='utf-8') as f:
            f.write(brief_str)

    # 招聘简介 词云图 **************************************
    def wordCloud(self):
        self.saveBrief() 

        if self.__city is None:
            filename = os.path.dirname(__file__) + '/../data/' + self.__keyword + '_brief_全国.txt'
        else:
            filename = os.path.dirname(__file__) + '/../data/' + self.__keyword + '_brief_' + self.__city + '.txt'

        # 读取文件内容
        with open(filename, 'rb') as f:
            text = f.read()
            f.close()

        # 用jieba 截取字符
        wordlist = jieba.cut(text, cut_all=False)
        wordlist_space_split = ' '.join(wordlist)
        d = os.path.dirname(__file__)
        alice_coloring = np.array(Image.open(os.path.join(d, '../res/colors.jpg')))
        mask = np.array(Image.open(os.path.join(d, '../res/mask.png')))
        my_wordcloud = WordCloud(
            font_path=os.path.dirname(__file__) + '/../res/' + FONT,
            background_color='#F0F8FF',
            max_words=100,
            mask=mask,
            max_font_size=300,
            random_state=42
        ).generate(wordlist_space_split)

        image_color = ImageColorGenerator(alice_coloring)
        # 以图片的形式显示词云
        plt.imshow(my_wordcloud)
        # 关闭坐标轴
        plt.axis('off')

        if self.__city is not None:
            cloud_filename = os.path.dirname(
                __file__) + '/../images/' + self.__keyword + '_words_cloud_' + self.__city + '.png'
        else:
            cloud_filename = os.path.dirname(
                __file__) + '/../images/' + self.__keyword + '_words_cloud_全国.png'

        my_wordcloud.to_file(os.path.join(d, cloud_filename))

    # 指挥官
    def easyRun(self):
        self.top10City()
        self.salaryAnalysis()
        self.wordCloud()
