# from opdata.mongoconnect import * 
# from opdata import opdata
from mongoconnect import *
import opdata
import pandas as pd

def JP_VALUATION_FINANCE(code, start_date='2009-01-01', end_date='2017-12-31'):
    def drop_y(df):
        # list comprehension of the cols that end with '_y'
        to_drop = [x for x in df if x.endswith('_y')]
        df.drop(to_drop, axis=1, inplace=True)

    cursor = financetable.find({'code':code}).sort('date')
    struct = equitystructure.find({'code': code}).sort('report_date')
    struct_df = pd.DataFrame(list(struct))
    opcf = pd.DataFrame(list(cursor))
    # print(opcf)
    if opcf.empty:
        return opcf
    del opcf['_id']
    del struct_df['_id']
    # print(opcf['net_raise_cf'])
    if struct_df.empty:
        struct_df['date'] = opcf['date']
        struct_df['restrict_equity'] = 0
        struct_df['general_equity'] = 0
        struct_df['executive_equity'] = 0
    else:
        struct_df.rename(columns={'report_date':'date'}, inplace = True)
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
    # print(opcf)
    # print(struct_df)
    # exit()
    T=T.merge(opcf,on='date',how='left', suffixes=('', '_y'))
    drop_y(T)  
    T=T.merge(struct_df, on='date', how='left', suffixes=('', '_y'))
    drop_y(T)  
    T=T.drop_duplicates(['date'])
    columns_lis = list(opcf.columns)
    columns_lis = columns_lis +  ['restrict_equity', 'executive_equity', 'flow_equity', 'general_equity']
    for column in columns_lis:
        T[column]=T[column].apply(commaEliminate) 
    for column in columns_lis:        
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
    # exit()
    price = opdata.get_day(code, start_date, end_date)
    if price.empty:
        return price
    T=T.reset_index()
    price=price.reset_index()
    # print(price)
    out = pd.DataFrame()
    out['code'] = code
    out['date'] = price['date']
    
    out['SY'] = T['total_profit'].div(price['close'], axis = 0)
    out['BVY'] = T['net_asset_ps'].div(price['close'], axis = 0)
    
    out['CF2TA'] = T['net_raise_cf'].div(T['total_assets'], axis = 0)
    out['CF2TA'] = out['CF2TA'] + T['net_invest_cf'].div(T['total_assets'] , axis = 0)
    out['CF2TA'] = out['CF2TA'] + T['net_op_cf'].div(T['total_assets'], axis = 0)
    
    out['EBITDA2TA'] = T['total_profit'].div(T['total_assets'], axis = 0)
    out['EBITDA2TA'] = out['EBITDA2TA'] + T['amortization'].div(T['total_assets'], axis = 0)
    out['EBITDA2TA'] = out['EBITDA2TA'] +T['depreciation'].div(T['total_assets'], axis = 0)
    out['EBITDA2TA'] = out['EBITDA2TA'] + T['long_term_amortization'].div(T['total_assets'], axis = 0)
    out['EBITDA2TA'] = out['EBITDA2TA'] + T['pay_intest'].div(T['total_assets'], axis = 0)
    out['EBITDA'] = out['EBITDA2TA'].mul(T['total_assets'], axis = 0)
    out['EBT2TA'] = T['op_income'].div(T['total_assets'], axis = 0)
    out['EBITDA2'] = T['op_income']
    out['EBIT'] = T['total_profit'] + T['pay_intest']
    out['general_equity'] = T['general_equity']
    out['flow_equity'] = T['flow_equity']
    # print(out['EBT2TA'], T['op_income'])
    # print(out)
    return out


if __name__ == '__main__':
    dff=JP_VALUATION_FINANCE('000001')
    # print(dff[dff.date == '2015-03-05'])
