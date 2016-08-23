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

# 计算不同投机头寸对应的盈亏
# 输入：CFTC的投机性多头、空头和总头寸，对应品种每日价格的OCLH
# 输出：投机头寸Z-score的分布，和不同分布对应的盈亏
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
    selDatePrice = price.ix[priceDate].copy()

    # 计算pos的Z-SCORE
    pos['LONG NPOI'] = pos.ix[:,0] / pos.ix[:,2]
    pos['SHORT NPOI'] = pos.ix[:,1] / pos.ix[:,2]
    colNames = ['LONG NPOI','SHORT NPOI']
    newColNames = ['LONG Z-SCORE','SHORT Z-SCORE']
    funcList = [tf.zscore, tf.zscore]
    pos = tf.rolling(pos, -25, funcList, colNames, newColNames)
    pos.dropna(inplace = True)
    
    # 把pos和price连接, 按周五的公布日期连接
    pos.index = pos.index.shift(3, 'D') # pos的日期是周二，要改成release date周五
    selDatePrice.index = selDatePrice.index.shift(-3, 'D') # price的日期是下周一，也改成周五
    subPos = pos.ix[:, 0:2].copy() #原始CFTC投机头寸数据
    subPos[['LONG Z-SCORE', 'SHORT Z-SCORE']] = pos[['LONG Z-SCORE', 'SHORT Z-SCORE']].copy()
    subSelPrice = selDatePrice[['NEXT_5D_RETURN', 'NEXT_5D_LOW', 'NEXT_5D_HIGH']].copy()
    result = pd.concat([subPos, subSelPrice], axis = 1, join = 'inner')
    
    # 按Z-score分组，生成每个分组的统计数据（2维矩阵）
    step = 0.5
    result['LONG ZS KEY'] = tf.histoCut(result['LONG Z-SCORE'], step) #产生分组用的key
    result['SHORT ZS KEY'] = tf.histoCut(result['SHORT Z-SCORE'], step)
    matCount = result.groupby(['LONG ZS KEY', 'SHORT ZS KEY'])['NEXT_5D_RETURN'].count().unstack()
    matAveRet = result.groupby(['LONG ZS KEY', 'SHORT ZS KEY'])['NEXT_5D_RETURN'].mean().unstack()
    matWinProb = result.groupby(['LONG ZS KEY', 'SHORT ZS KEY'])['NEXT_5D_RETURN'].apply(tf.posPct).unstack()
    matCount = tf.histoSort(matCount)
    matCount = tf.histoSort(matCount.T)
    matAveRet = tf.histoSort(matAveRet)
    matAveRet = tf.histoSort(matAveRet.T)
    matWinProb = tf.histoSort(matWinProb)
    matWinProb = tf.histoSort(matWinProb.T)
    
    # 找到以前同一个Z-SCORE分组的数据
    long_zs_key = tf.histoCutKey(pos.ix[-1, 'LONG Z-SCORE'], step)
    short_zs_key= tf.histoCutKey(pos.ix[-1, 'SHORT Z-SCORE'], step)
    histRef = pd.DataFrame()
    i = 0    
    while i < len(result.index):
        if result['LONG ZS KEY'][i] == long_zs_key and result['SHORT ZS KEY'][i] == short_zs_key:
            histRef = histRef.append(result.ix[i])
        i += 1
        
    # 输出
    writer = pd.ExcelWriter('output.xlsx')
    matCount.to_excel(writer, 'matCount')
    matAveRet.to_excel(writer, 'matAveRet')
    matWinProb.to_excel(writer, 'matWinProb')
    histRef.to_excel(writer, 'historyRef')
    writer.save()

    a = 1