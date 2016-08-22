# -*- coding: utf-8 -*-
"""
Created on Thu Aug 18 14:25:08 2016

@author: yiran.zhou
"""

import pandas as pd
import numpy as np
import sys
sys.path.append('..')
import taifook.taifook as tf


# main process
if __name__ == '__main__':
    # 读入数据
    pos = pd.read_excel('CLA COT.xls', sheetname = 'Sheet1 (2)')
    pos.set_index('Date', inplace = True)
    price = pd.read_excel('CLA COT.xls', sheetname = 'Sheet2')
    label = price.columns[0]
    price.set_index(label, inplace = True)

    # 调整价格数据
    posDate = pos.index #统计pos的日期是周二，但是release是周末
    priceDate = posDate.shift(6, 'D') #所以下个周一（6天后）是第一个公布数据后的交易日
    # 新建一列，周一到周四是open price，周五是close price
    price['OPEN_CLOSE'] = price['PX_OPEN']
    friday = posDate.shift(3, 'D') # 下个周五是公布数据（周二）的3天后
    price.ix[friday, 'OPEN_CLOSE'] = price.ix[friday, 'PX_LAST'] 
    # 计算统计要用到的数据
    colNames = ['OPEN_CLOSE', 'PX_LOW', 'PX_HIGH']
    newColNames = ['NEXT_5D_RETURN', 'NEXT_5D_LOW','NEXT_5D_HIGH']
    fret = lambda x : x[-1] / x[0] - 1
    fmin = lambda x : x.min()
    fmax = lambda x : x.max()   
    funcList = [fret, fmin, fmax]
    price = tf.rolling(price, 5, funcList, colNames, newColNames)
    selDatePrice = price.ix[priceDate]

    # 计算pos的Z-SCORE
    pos['LONG NPOI'] = pos.ix[:,0] / pos.ix[:,2]
    pos['SHORT NPOI'] = pos.ix[:,1] / pos.ix[:,2]
    colNames = ['LONG NPOI','SHORT NPOI']
    newColNames = ['LONG Z-SCORE','SHORT Z-SCORE']
    funcList = [tf.zscore, tf.zscore]
    pos = tf.rolling(pos, -25, funcList, colNames, newColNames)
    pos.dropna(inplace = True)

    # 按Z-score分组
    pos['LONG ZS KEY'] = tf.histoCut(pos['LONG Z-SCORE'], 0.5) #生产分组用的key
    pos['SHORT ZS KEY'] = tf.histoCut(pos['SHORT Z-SCORE'], 0.5)
    matCount = pos.groupby(['LONG ZS KEY', 'SHORT ZS KEY'])['LONG NPOI'].count().unstack()
    matCount = tf.histoSort(matCount)

    a = 1