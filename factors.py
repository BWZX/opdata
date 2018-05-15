from opdata.mongoconnect import * 
from opdata import opdata
# from mongoconnect import *
# import opdata
import pandas as pd

def JP_VALUATION_FINANCE(code, start_date='2009-01-01', end_date='2017-12-31'):
    cursor = financetable.find({'code':code}).sort('date')
    opcf = pd.DataFrame(list(cursor))
    if opcf.empty:
        return opcf
    del opcf['_id']
    # print(opcf['net_raise_cf'])
    lastvalue = 0
    def setValue(v):
        nonlocal lastvalue
        if pd.isnull(v) or v == 'None' or v == '--' or v=='nan':
            return lastvalue
        else:
            try:
                float(v)
            except Exception:                
                return lastvalue
            lastvalue = v
            return lastvalue
    commaEliminate = lambda x: str(x).replace(',','')
    T = opdata.__T
    T.rename(columns={'calendarDate':'date'}, inplace=True)
    # T = T[T.date > '2003-01-01']
    T=T.merge(opcf,on='date',how='left')
    T=T.drop_duplicates(['date'])   
    for column in opcf:
        T[column]=T[column].apply(commaEliminate) 
    for column in opcf:        
        lastvalue = '0'
        if column != 'code' and column != 'date': 
            T[column]=T[column].apply(setValue)         
            try:
                T[[column]] = T[[column]].astype(float)
            except ValueError:
                pass 
    T = T[T.isOpen >0.5]
    T = T[T.date >= start_date]
    T = T[T.date <= end_date]
    T['code']=str(code)
    del T['isOpen']
    # print(T)
    price = opdata.get_day(code, start_date, end_date)
    # print(price)
    # print(T)
    T=T.reset_index()
    price=price.reset_index()
    # print(price)
    out = pd.DataFrame()
    out['code'] = price['code']
    out['date'] = price['date']
    # print(out)
    # print(T)
    # print(price)
    
    out['SY'] = T['total_profit'].div(price['close'], axis = 0)
    # print(out)
    # print(code)
    # print(T['net_asset_ps'])
    # T[['net_asset_ps']] = T[['net_asset_ps']].astype(float)
    out['BVY'] = T['net_asset_ps'].div(price['close'], axis = 0)
    
    out['CF2TA'] = T['net_raise_cf'].div(T['total_assets'], axis = 0)
    out['CF2TA'] = out['CF2TA'] + T['net_invest_cf'].div(T['total_assets'] , axis = 0)
    out['CF2TA'] = out['CF2TA'] + T['net_op_cf'].div(T['total_assets'], axis = 0)
    
    out['EBITDA2TA'] = T['total_profit'].div(T['total_assets'], axis = 0)
    out['EBITDA2TA'] = out['EBITDA2TA'] + T['amortization'].div(T['total_assets'], axis = 0)
    out['EBITDA2TA'] = out['EBITDA2TA'] +T['depreciation'].div(T['total_assets'], axis = 0)
    out['EBITDA2TA'] = out['EBITDA2TA'] + T['long_term_amortization'].div(T['total_assets'], axis = 0)
    out['EBITDA2TA'] = out['EBITDA2TA'] + T['pay_intest'].div(T['total_assets'], axis = 0)
    out['EBT2TA'] = T['op_income']
    # print(out['EBT2TA'], T['op_income'])
    # print(out)
    return out


if __name__ == '__main__':
    dff=JP_VALUATION_FINANCE('000027')
    print(dff[dff.date == '2015-03-05'])
