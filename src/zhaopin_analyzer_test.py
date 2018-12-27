__author__ = 'HuangFangZhi'
__time__ = '2018-11-13
__description__ = '智联招聘网的数据分析与数据可视化 启动(测试)文件'

from zhaopin_analyzer import *
from config import *

# 分析指定的关键字

ana = Analysis('python')
ana.easyRun()

# 分析所有的关键字
'''
for keyword in KEYWORDS:
    ana = Analysis(keyword)
    ana.easyRun()'''
