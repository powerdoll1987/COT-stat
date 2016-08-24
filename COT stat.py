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

# 计算未来时间段内的平均最大下跌和最大上涨
# 输入：price的dataframe
def riskReturn(df):
    strUpPct = str(df['NEXT_ND_MAX_UP'].mean() * 100)[0:3] + '%'
    strDownPct = str(df['NEXT_ND_MAX_DOWN'].mean() * 100)[0:4] + '%'
    return strDownPct + ' / ' + strUpPct

def test(df):
    return 1

# 计算不同投机头寸对应的盈亏
# 输入：CFTC的投机性多头、空头和总头寸，对应品种每日价格的OCLH
# 输出：投机头寸Z-score的分布，和不同分布对应的盈亏
# main process
if __name__ == '__main__':
    # 列名称常量
    # for price dataframe
    str_NEXT_ND_RETURN = 'NEXT_5D_RETURN'
    str_NEXT_ND_MAX_UP = 'NEXT_ND_MAX_UP'
    str_NEXT_ND_MAX_DOWN = 'NEXT_ND_MAX_DOWN'
    const_zs_roll_span = -100
    # for pos dataframe
    str_LONG_ZSCORE = 'LONG Z-SCORE'
    str_SHORT_ZSCORE = 'SHORT Z-SCORE'
    str_LONG_ZS_KEY = 'LONG ZS KEY'
    str_SHORT_ZS_KEY = 'SHORT ZS KEY'
    str_LONG_NPOI = 'LONG NPOI'
    str_SHORT_NPOI = 'SHORT NPOI'
    const_price_roll_span = 20
    
    # 读入数据
    pos = pd.read_excel('CLA COT.xls', sheetname = 'Sheet1 (2)')
    pos.set_index('Date', inplace = True)
    price = pd.read_excel('CLA COT.xls', sheetname = 'Sheet2')
    label = price.columns[0]
    price.set_index(label, inplace = True)

    # 调整价格数据
    fret = lambda x : x.ix[-1, 'PX_LAST'] / x.ix[0, 'PX_OPEN'] - 1
    fminRet = lambda x : x['PX_LOW'].min() / x.ix[0, 'PX_OPEN'] - 1
    fmaxRet = lambda x : x['PX_HIGH'].max() / x.ix[0, 'PX_OPEN'] - 1
    # 生成需要的数据列
    price = tf.rollingND(price, const_price_roll_span, fret, ['PX_OPEN','PX_LAST'], str_NEXT_ND_RETURN)
    price = tf.rollingND(price, const_price_roll_span, fminRet, ['PX_OPEN','PX_LOW'], str_NEXT_ND_MAX_DOWN)
    price = tf.rollingND(price, const_price_roll_span, fmaxRet, ['PX_OPEN','PX_HIGH'], str_NEXT_ND_MAX_UP)
    # 选取每周一的数据，准备和pos矩阵连接
    posDate = pos.index #统计pos的日期是周二，但是release是周末
    priceDate = posDate.shift(6, 'D') #所以下个周一（6天后）是第一个公布数据后的交易日
    selDatePrice = price.ix[priceDate].copy()

    # 计算pos的Z-SCORE
    pos[str_LONG_NPOI] = pos.ix[:,0] / pos.ix[:,2]
    pos[str_SHORT_NPOI] = pos.ix[:,1] / pos.ix[:,2]
    colNames = [str_LONG_NPOI,str_SHORT_NPOI]
    newColNames = [str_LONG_ZSCORE, str_SHORT_ZSCORE]
    funcList = [tf.zscore, tf.zscore]
    pos = tf.rolling(pos, -25, funcList, colNames, newColNames)
    pos.dropna(inplace = True)
    
    # 把pos和price连接, 按周五的公布日期连接
    pos.index = pos.index.shift(3, 'D') # pos的日期是周二，要改成release date周五
    selDatePrice.index = selDatePrice.index.shift(-3, 'D') # price的日期是下周一，也改成周五
    subPos = pos.ix[:, 0:3].copy() #原始CFTC投机头寸数据
    subPos[[str_LONG_ZSCORE, str_SHORT_ZSCORE]] = pos[[str_LONG_ZSCORE, str_SHORT_ZSCORE]].copy()
    subSelPrice = selDatePrice[[str_NEXT_ND_RETURN, str_NEXT_ND_MAX_DOWN, str_NEXT_ND_MAX_UP]].copy()
    result = pd.concat([subPos, subSelPrice], axis = 1, join = 'inner')
    
    # 按Z-score分组，生成每个分组的统计数据（2维矩阵）
    step = 0.5
    result[str_LONG_ZS_KEY] = tf.histoCut(result[str_LONG_ZSCORE], step) #产生分组用的key
    result[str_SHORT_ZS_KEY] = tf.histoCut(result[str_SHORT_ZSCORE], step)
    matCount = result.groupby([str_LONG_ZS_KEY, str_SHORT_ZS_KEY])[str_NEXT_ND_RETURN].count().unstack()
    matAveRet = result.groupby([str_LONG_ZS_KEY, str_SHORT_ZS_KEY])[str_NEXT_ND_RETURN].mean().unstack()
    matUpProb = result.groupby([str_LONG_ZS_KEY, str_SHORT_ZS_KEY])[str_NEXT_ND_RETURN].apply(tf.posPct).unstack()
    matRiskRet = result.groupby([str_LONG_ZS_KEY, str_SHORT_ZS_KEY]).apply(riskReturn).unstack()
    matCount = tf.histoSort(matCount)
    matCount = tf.histoSort(matCount.T)
    matAveRet = tf.histoSort(matAveRet)
    matAveRet = tf.histoSort(matAveRet.T)
    matUpProb = tf.histoSort(matUpProb)
    matUpProb = tf.histoSort(matUpProb.T)
    matRiskRet = tf.histoSort(matRiskRet)
    matRiskRet = tf.histoSort(matRiskRet.T)
    
    # 按照最后的Z-score找到以前同一个Z-SCORE分组的数据
    long_zs_key = tf.histoCutKey(pos.ix[-1, str_LONG_ZSCORE], step)
    short_zs_key= tf.histoCutKey(pos.ix[-1, str_SHORT_ZSCORE], step)
    histRef = pd.DataFrame()
    i = 0    
    while i < len(result.index):
        if result[str_LONG_ZS_KEY][i] == long_zs_key and result[str_SHORT_ZS_KEY][i] == short_zs_key:
            histRef = histRef.append(result.ix[i])
        i += 1
        
    # 输出
    writer = pd.ExcelWriter('output.xlsx')
    matCount.to_excel(writer, 'matCount')
    matAveRet.to_excel(writer, 'matAveRet')
    matUpProb.to_excel(writer, 'matUpProb')
    matRiskRet.to_excel(writer, 'matRiskRet')
    histRef.to_excel(writer, 'histRef')
    writer.save()

    a = 1