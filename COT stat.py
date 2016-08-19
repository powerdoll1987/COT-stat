# -*- coding: utf-8 -*-
"""
Created on Thu Aug 18 14:25:08 2016

@author: yiran.zhou
"""

import pandas as pd
import numpy as np


# dataframe的rolling函数, 对指定的列做rolling，生产新的列，返回一个新的df
# colNames指定df里面需要rolling的列，newColNames是新生成的列的名字，funcList是处理rolling的函数
# funcList,colNames和newColNames的数量需相等
# span有正负，正表示未来的x days，负表示过去的x days
def rolling(df, span, funcList, colNames, newColNames):
    i = 0
    # 对每一个需要处理的列进行循环
    while i < len(colNames):
        col = df[colNames[i]]
        newCol = newColNames[i]
        # 根据span设定初始rolling范围
        if span < 0: # 往前rolling过去的数据
            idx = 0 - span - 1 # 指向当前的日期
            startIdx = 0 # rolling开始的日期
            endIdx = idx # rolling结束的日期
        else: # 往后rolling未来的数据
            idx = 0
            startIdx = idx
            endIdx = startIdx + span - 1
        # 对列进行rolling操作
        while endIdx < len(col):
            interval = np.arange(startIdx, endIdx + 1)
            rollingData = col.ix[col.index[interval]]
            df.ix[idx, newCol] = funcList[i](rollingData)
            idx +=1
            startIdx +=1
            endIdx +=1
        # 继续下一列   
        i += 1
    return df

# main process
if __name__ == '__main__':
    # 读入数据    
    pos = pd.read_excel('CLA COT.xls', sheetname = 'Sheet1 (2)')
    pos.set_index('Date', inplace = True)
    price = pd.read_excel('CLA COT.xls', sheetname = 'Sheet2')
    label = price.columns[0]
    price.set_index(label, inplace = True)
    
    posDate = pos.index #统计pos的日期是周二，但是release是周末
    priceDate = posDate.shift(6, 'D') #所以下个周一（6天后）是第一个公布数据后的交易日
    colNames = ['PX_LOW', 'PX_HIGH']
    newColNames = ['NEXT_5D_LOW','NEXT_5D_HIGH']
    fmin = lambda x : x.min()
    fmax = lambda x : x.max()
    funcList = [fmin, fmax]  
    price = rolling(price, 5, funcList, colNames, newColNames)
    
    
    selDatePrice = price.ix[priceDate] 
    
    a = 1