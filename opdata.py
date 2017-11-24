# -*- coding: utf8 -*-
import json
import pandas as pd
import tushare as ts
from datetime import datetime as dt
from mongoconnet import *

__T = ts.trade_cal()

def get_day(code, start_date='2001-01-01', end_date='2017-10-10'):
    # if not start_date:
    #     start_date='2001-01-01'
    # if not end_date:
    #     end_date='2020-10-10'

    cursor = security.find({'code':code, 'date':{'$gte':start_date, '$lte': end_date}}).sort('date')
    df = pd.DataFrame(list(cursor))
    if df.empty:
        return df    
    del df['_id']
    firstdate=df.loc[0].date
    t=__T[(__T.isOpen==1)&(__T.calendarDate>=firstdate)&(__T.calendarDate<=end_date)]   
    t.columns=['date','isOpen']
    r=pd.merge(df,t,on='date',how='right')
    r=r.sort_values('date').reset_index()
    del r['index']
    del r['isOpen']
    # print(r)
    k=r.isnull()
    k=list(k[k.open==True].index)
    k.sort()
    ii=list(r.columns).index('date')
    for i in k:
        date=r.iloc[i].date
        r.iloc[i]=r.iloc[i-1]
        r.iat[i, ii] = date    
    return r

def macrodata(start=None, end=None):
    """
    parameters:
        start: a string present a date indicates the return data start from. for example: '2011-01-22'
        end  : refer to start
    return: 
        macroeconomics data : Shibor | Reserve Ratio | M2 | GDP | CPI | Loan Rate.
        the data start from 2006-10-08. Cause it is when the shibor data start on Tushare.
    """
    T = ts.trade_cal()
    T.rename(columns={'calendarDate':'date'}, inplace=True)
    today = dt.today()
    today = dt.strftime(today,'%Y-%m-%d')
    T = T[T.date > '2006-04-01']
    T = T[T.date <= today]

    loan = ts.get_loan_rate()   #date loan_type rate
    loan = loan[loan.date > '2006-06-01']
    rate = pd.DataFrame()
    for i in range(len(loan)):
        if loan.iloc[i].loan_type == '短期贷款(六个月以内)':
            rate = rate.append(loan.iloc[i][['date','rate']])

    rrr = ts.get_rrr()[['date','changed']]  # 准备金率
    rrr.rename(columns={'changed':'rrr'}, inplace=True)
    rrr = rrr[rrr.date > '2006-08-01']

    dataScale = ['15','09']
    dataindex = 0
    def makeDate(raw_date):
        raw_date = str(raw_date)
        raw_date = raw_date.split('.')
        if int(raw_date[1]) <=9:
            raw_date[1] = '0'+raw_date[1]
        return raw_date[0] + '-' + raw_date[1] + '-' + dataScale[dataindex]

    def makeQuarter(raw_date):
        raw_date = str(raw_date)
        raw_date = raw_date.split('.')
        p = raw_date[1]
        q={
            '1': '01',
            '2': '04',
            '3': '07',
            '4': '10'
        }
        return raw_date[0] + '-' + q[p] + '-' + '15'

    supply = ts.get_money_supply()[['month','m2_yoy']]   #15th.
    supply.rename(columns={'month': 'date', 'm2_yoy':'m2'}, inplace=True)
    if type(supply.iloc[1]['date']) == type(''):
        supply = supply[supply.date > '2006.6']
    else:
        supply = supply[supply.date > 2006.6]
    supply['date']=supply['date'].apply(makeDate)
    dataindex=dataindex+1
    m2=supply

    gdp = ts.get_gdp_quarter()[['quarter','gdp_yoy']]   # gdp will available at 15th.
    gdp.rename(columns={'quarter': 'date','gdp_yoy':'gdp'}, inplace=True)
    if type(gdp.iloc[1]['date']) == type(''):
        gdp = gdp[gdp.date > '2006.1']
    else:
        gdp = gdp[gdp.date > 2006.1]
    gdp['date']=gdp['date'].apply(makeQuarter)

    cpi = ts.get_cpi()  #month , cpi,  available at 9th.
    cpi.rename(columns={'month': 'date'}, inplace=True)
    if type(cpi.iloc[1]['date']) == type(''):
        cpi = cpi[cpi.date > '2006.6']
    else:
        cpi = cpi[cpi.date > 2006.6]
    cpi['date']=cpi['date'].apply(makeDate)

    shibor=ts.shibor_data(2006)[['date','ON']]
    for y in range(2007,2018):
        shibor=pd.merge(shibor,ts.shibor_data(y)[['date','ON']],'outer')
    shibor.rename(columns={'ON':'shibor'}, inplace=True)
    shibor[['date']] = shibor[['date']].astype(str)

    lastvalue = 0.0
    def setValue(v):
        nonlocal lastvalue
        if pd.isnull(v) or v == 'None':
            return lastvalue
        else:
            lastvalue = v
            return lastvalue

    T=T.merge(cpi,on='date',how='left')
    lastvalue = cpi.iloc[-1]['cpi']
    T['cpi']=T['cpi'].apply(setValue)

    T=T.merge(gdp,on='date',how='left')
    lastvalue = gdp.iloc[-1]['gdp']
    T['gdp']=T['gdp'].apply(setValue)

    T=T.merge(m2,on='date',how='left')
    lastvalue = m2.iloc[-1]['m2']
    T['m2']=T['m2'].apply(setValue)

    T=T.merge(rrr,on='date',how='left')
    lastvalue = rrr.iloc[-1]['rrr']
    T['rrr']=T['rrr'].apply(setValue)

    T=T.merge(rate,on='date',how='left')
    lastvalue = rate.iloc[-1]['rate']
    T['rate']=T['rate'].apply(setValue)
    
    T=shibor.merge(T,on='date',how='left')
    T = T[T.isOpen >0.5]
    del T['isOpen']
    if start and end:
        T = T[T.date >= start]
        T = T[T.date <= end]

    return T

if __name__ == '__main__':
    print(macrodata())
    # print(get_day('002236','2007-08-05','2010-08-05'))

    