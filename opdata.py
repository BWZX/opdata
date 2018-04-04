﻿# -*- coding: utf-8 -*-
import json
import pandas as pd
import tushare as ts
from datetime import datetime as dt
from datetime import timedelta as td
import calendar as cal
import numpy as np
import os
from tqdm import tqdm
import talib

from opdata.mongoconnet import *    
# from mongoconnet import *

__T = ts.trade_cal()

def get_day(code, start_date='2001-02-01', end_date='2017-10-10'):
    # if not start_date:
    #     start_date='2001-01-01'
    # if not end_date:
    #     end_date='2020-10-10'
    T= __T
    cursor = security.find({'code':code, 'date':{'$gte':start_date, '$lte': end_date}}).sort('date')
    df = pd.DataFrame(list(cursor))
    if df.empty:
        return df  

    lastvalue = 0.0
    def setValue(v):
        nonlocal lastvalue
        if pd.isnull(v) or v == 'None':
            return lastvalue
        else:
            lastvalue = v
            return lastvalue
    T.rename(columns={'calendarDate':'date'}, inplace=True)
    T=T[T.date > '2001-01-01']
    T=T.merge(df,on='date',how='left')
    T=T.drop_duplicates(['date'])
    T[['open']] = T[['open']].astype(float)
    T[['close']] = T[['close']].astype(float)
    T[['high']] = T[['high']].astype(float)
    T[['low']] = T[['low']].astype(float)
    T[['volume']] = T[['volume']].astype(float)
    lastvalue = 0.0
    T['high']=T['high'].apply(setValue)
    lastvalue = 0.0
    T['low']=T['low'].apply(setValue)
    lastvalue = 0.0
    T['close']=T['close'].apply(setValue)
    lastvalue = 0.0
    T['open']=T['open'].apply(setValue)
    lastvalue = 0.0
    T['volume']=T['volume'].apply(setValue)
    del T['_id']
    T = T[T.isOpen >0.5]
    T = T[T.date >= start_date]
    T = T[T.date <= end_date]
    del T['isOpen']
    return T    
    
    # del df['_id']
    # firstdate=df.loc[0].date
    # t=__T[(__T.isOpen==1)&(__T.calendarDate>=firstdate)&(__T.calendarDate<=end_date)]   
    # t.columns=['date','isOpen']
    # r=pd.merge(df,t,on='date',how='right')
    # r=r.sort_values('date').reset_index()
    # del r['index']
    # del r['isOpen']
    # # print(r)
    # k=r.isnull()
    # k=list(k[k.open==True].index)
    # k.sort()
    # ii=list(r.columns).index('date')
    # for i in k:
    #     date=r.iloc[i].date
    #     r.iloc[i]=r.iloc[i-1]
    #     r.iat[i, ii] = date    
    # return r

def macrodata(start=None, end=None):
    """macroeconomics data : Shibor | Reserve Ratio | M2 | GDP | CPI | Loan Rate.
    the data start from 2006-10-08. Cause it is when the shibor data start on Tushare.

    parameters:
    ---------
        start: a string present a date indicates the return data start from. for example: '2011-01-22'
        end  : refer to start
    return: 
    --------
        pandas.DataFrame        
    """
    T = __T
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

    rrr = ts.get_rrr()[['date','now']]  # 准备金率
    rrr.rename(columns={'now':'rrr'}, inplace=True)
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

    # shibor=ts.shibor_data(2006)[['date','ON']]
    # for y in range(2007,2018):
    #     shibor=pd.merge(shibor,ts.shibor_d
    # ata(y)[['date','ON']],'outer')
    # shibor.rename(columns={'ON':'shibor'}, inplace=True)
    # shibor[['date']] = shibor[['date']].astype(str)

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
    
    # T=shibor.merge(T,on='date',how='left')
    T = T[T.isOpen >0.5]
    T = T[T.date >= '2006-10-08']
    del T['isOpen']
    if start and end:
        T = T[T.date >= start]
        T = T[T.date <= end]
    
    T[['rrr']] = T[['rrr']].astype(float)
    T[['m2']] = T[['m2']].astype(float)
    T[['rate']] = T[['rate']].astype(float)
    T[['gdp']] = T[['gdp']].astype(float)
    T[['cpi']] = T[['cpi']].astype(float)

    return T

def _fetch_finance():
    for year in range(2004,2018):
        set_year = lambda x: str(year)+'-'+ x
        for quarter in range(1,5): 
            print(year,' year ','quarter ',quarter)           
            rep = ts.get_report_data(year, quarter)[['code','eps','bvps','epcf','report_date']]
            pro = ts.get_profit_data(year,quarter)[['code', 'roe', 'net_profit_ratio', 'gross_profit_rate', 'net_profits', 'business_income', 'bips']]
            ope = ts.get_operation_data(year,quarter)[['code', 'arturnover', 'arturndays', 'inventory_turnover', 'currentasset_turnover', 'currentasset_days']]
            gro = ts.get_growth_data(year,quarter)[['code', 'mbrg', 'nprg', 'nav', 'epsg', 'seg']]
            deb = ts.get_debtpaying_data(year,quarter)[['code', 'currentratio', 'quickratio', 'cashratio', 'icratio', 'sheqratio', 'adratio']]
            cas = ts.get_cashflow_data(year,quarter)[['code', 'cf_sales', 'rateofreturn', 'cf_nm', 'cf_liabilities', 'cashflowratio']]
            
            rep.rename(columns={'report_date':'date'}, inplace=True)            
            rep['date']=rep['date'].apply(set_year)
            rep=rep.merge(pro,on='code',how='left')
            rep=rep.merge(ope,on='code',how='left')
            rep=rep.merge(gro,on='code',how='left')
            rep=rep.merge(deb,on='code',how='left')
            rep=rep.merge(cas,on='code',how='left')
            finance.insert(rep.to_dict('record'))
            print(year, quarter)

def get_finance(code, start_date='2004-04-01', end_date='2017-10-10'):
    lastvalue = 0.0
    def setValue(v):
        nonlocal lastvalue
        if pd.isnull(v) or v == 'None' or v == '--':
            return lastvalue
        else:
            lastvalue = v
            return lastvalue
    cursor = finance.find({'code':str(code), 'date':{'$gte':'2004-01-01', '$lte': end_date}}).sort('date')
    df = pd.DataFrame(list(cursor))
    if df.empty:
        return df
    del df['_id']
    del df['code']
    T = __T    
    T.rename(columns={'calendarDate':'date'}, inplace=True)
    T = T[T.date > '2003-01-01']
    T=T.merge(df,on='date',how='left')
    T=T.drop_duplicates(['date'])
    for column in T:
        if column != 'code' and column != 'date':
            try:
                T[[column]] = T[[column]].astype(float)
            except ValueError:
                pass            
            lastvalue = 0.0
            T[column]=T[column].apply(setValue)
            
    # T[['bvps']] = T[['bvps']].astype(float)
    # T[['epcf']] = T[['epcf']].astype(float)  
    # T[['eps']] = T[['eps']].astype(float)
    # lastvalue = 0.0
    # T['bvps']=T['bvps'].apply(setValue)
    # lastvalue = 0.0
    # T['epcf']=T['epcf'].apply(setValue)
    # lastvalue = 0.0
    # T['eps']=T['eps'].apply(setValue)
    T = T[T.isOpen >0.5]
    T = T[T.date >= start_date]
    T = T[T.date <= end_date]
    T['code']=str(code)
    del T['isOpen']
    return T


# __INDUSTRY_CLASSIFIED = ts.get_industry_classified()
# __CONCEPT_CLASSIFIED = ts.get_concept_classified()
# get_industry = lambda code:__INDUSTRY_CLASSIFIED[__INDUSTRY_CLASSIFIED.code==code].iloc[0].c_name 
# get_concept = lambda code:__CONCEPT_CLASSIFIED[__CONCEPT_CLASSIFIED.code==code].iloc[0].c_name   


def get_local_future(code, start_date='2009-10-01', end_date='2018-03-02'):
    # if not start_date:
    #     start_date='2001-01-01'
    # if not end_date:
    #     end_date='2020-10-10'
    T= __T
    cursor = future.find({'code':code, 'date':{'$gte':start_date, '$lte': end_date}}).sort('date')
    df = pd.DataFrame(list(cursor))
    if df.empty:
        return df  

    lastvalue = 0.0
    def setValue(v):
        nonlocal lastvalue
        if pd.isnull(v) or v == 'None':
            return lastvalue
        else:
            lastvalue = v
            return lastvalue
    T.rename(columns={'calendarDate':'date'}, inplace=True)
    T=T[T.date > '2001-01-01']
    T=T.merge(df,on='date',how='left')
    T=T.drop_duplicates(['date'])
    T[['open']] = T[['open']].astype(float)
    T[['close']] = T[['close']].astype(float)
    T[['high']] = T[['high']].astype(float)
    T[['low']] = T[['low']].astype(float)
    T[['volume']] = T[['volume']].astype(float)
    lastvalue = 0.0
    T['high']=T['high'].apply(setValue)
    lastvalue = 0.0
    T['low']=T['low'].apply(setValue)
    lastvalue = 0.0
    T['close']=T['close'].apply(setValue)
    lastvalue = 0.0
    T['open']=T['open'].apply(setValue)
    lastvalue = 0.0
    T['volume']=T['volume'].apply(setValue)
    del T['_id']
    T = T[T.isOpen >0.5]
    T = T[T.date >= start_date]
    T = T[T.date <= end_date]
    del T['isOpen']
    return T    

def get_future(code, start_date='2009-10-01', end_date='2018-03-02'):    
    cursor = future.find({'code':code, 'date':{'$gte':start_date, '$lte': end_date}}).sort('date')
    df = pd.DataFrame(list(cursor))
    if df.empty:
        return df 
    del df['_id']
    if df.iloc[0].volume == 'n/a':
        df['volume'] = 0
    return df  

def __get_predictors(data):
    open_list = np.asarray(data["open"].tolist())
    close_list = np.asarray(data["close"].tolist())
    high_list = np.asarray(data["high"].tolist())
    low_list = np.asarray(data["low"].tolist())
    volume_list = np.asarray(data["volume"].tolist())

    adj_close = close_list
    obv = talib.OBV(close_list, volume_list)
    rsi6 = talib.RSI(close_list, timeperiod=6)
    rsi12 = talib.RSI(close_list, timeperiod=12)
    sma3 = talib.SMA(close_list, timeperiod=3)
    ema6 = talib.EMA(close_list, timeperiod=6)
    ema12 = talib.EMA(close_list, timeperiod=12)
    atr14 = talib.ATR(high_list, low_list, close_list, timeperiod=14)
    mfi14 = talib.MFI(high_list, low_list, close_list, volume_list, timeperiod=14)
    adx14 = talib.ADX(high_list, low_list, close_list, timeperiod=14)
    adx20 = talib.ADX(high_list, low_list, close_list, timeperiod=20)
    mom1 = talib.MOM(close_list, timeperiod=1)
    mom3 = talib.MOM(close_list, timeperiod=3)
    cci12 = talib.CCI(high_list, low_list, close_list, timeperiod=14)
    cci20 = talib.CCI(high_list, low_list, close_list, timeperiod=20)
    rocr3 = talib.ROCR(close_list, timeperiod=3)
    rocr12 = talib.ROCR(close_list, timeperiod=12)
    macd, macd_sig, macd_hist = talib.MACD(close_list)
    willr = talib.WILLR(high_list, low_list, close_list)
    tsf10 = talib.TSF(close_list, timeperiod=10)
    tsf20 = talib.TSF(close_list, timeperiod=20)
    trix = talib.TRIX(close_list)
    bbandupper, bbandmiddle, bbandlower = talib.BBANDS(close_list)
    return [adj_close[-1], obv[-1], rsi6[-1], rsi12[-1], sma3[-1], ema6[-1], ema12[-1], atr14[-1], mfi14[-1], adx14[-1], adx20[-1], mom1[-1], mom3[-1], cci12[-1], cci20[-1], \
            rocr3[-1], rocr12[-1], macd[-1], macd_sig[-1], macd_hist[-1], willr[-1], tsf10[-1], tsf20[-1], trix[-1], bbandupper[-1], bbandmiddle[-1], bbandlower[-1]]

def get_month(mdate):
    checkm = mdate.split('-')
    year = int(checkm[0])
    month = int(checkm[1])      
    dfM = pd.read_csv(os.path.join(os.path.dirname(os.path.realpath(__file__)),'hs300.csv'))
    date = checkm[0]+checkm[1]
    if len(checkm)==2 and 200607 <= int(date) <=201802:
        pass
    else:
        print('data not in the range')
        return

    lastyear = year-1
    start_date = '1995-01-31'    
    columns=['code', 'date', 'open', 'close', 'high', 'low', 'volume', 'momentum', 'adj_close', 'obv', 'rsi6', 'rsi12', 'sma3', 'ema6', 'ema12', 'atr14', 'mfi14', 'adx14', 'adx20', 'mom1', 'mom3', 'cci12', 'cci20', 'rocr3', 'rocr12', 'macd', 'macd_sig', 'macd_hist', 'willr', 'tsf10', 'tsf20', 'trix', 'bbandupper', 'bbandmiddle', 'bbandlower']
    T = pd.DataFrame([], columns=columns)
    thedate=''
    for d in dfM:
        thedate = str(d)
        if int(date) < int(d):
            break
    temk=__T[(__T.calendarDate >=mdate+'-01') & (__T.calendarDate<=mdate+'-31') & (__T.isOpen ==1)]
    end_date = temk.iloc[-1]['calendarDate']
    for code in tqdm(dfM[thedate]):         
        code = str(code)
        if len(code) <6:
            code = '000000'+code
            code = code[-6:]
        # print(code)
        cursor = securityM.find({'code':code, 'date':{'$gte':start_date, '$lte': end_date}}).sort('date')
        df = pd.DataFrame(list(cursor))

        if df.empty:
            print(code)
            df_M=ts.get_k_data(code,ktype='M') 
            records = json.loads(df_M.T.to_json()).values()
            if securityM.count({'code':code}) <=0:
                securityM.insert(records)
                print('insert new data to database at stock code .',code)
            else:
                print('the stock {0} has no data at this month.'.format(code))
                continue
            cursor = securityM.find({'code':code, 'date':{'$gte':start_date, '$lte': end_date}}).sort('date')
            df = pd.DataFrame(list(cursor))

        if(len(df)>=12):
            momentum = (df.iloc[-1]['close'] - df.iloc[-12]['close'])/df.iloc[-12]['close']
        else:
            momentum = 0.0
            # continue
        #assert(not df.empty)
        last = df.iloc[-1].to_dict()
        out = [last['code'],mdate,last['open'],last['close'],last['high'],last['low'],last['volume']]
        out.append(momentum)
        out = out + __get_predictors(df) 
        T.loc[len(T)] = out
        #print(T)
    return T
    
def get_ts_finance(code, period):
    """period will be just 3d, 1w, 2w, 1m, 3m, 6m
    
    Arguments:
        code {string} -- stock code
        period {string} -- string present period
    """    
    df = get_finance(code)
    if period =='3d':
        return df[df.index%3==0]
    
    if period =='1w':
        return df[df.index%5==0]

    if period == '2w':
        return df[df.index%10==0]

    if period == '1m':
        return df[df.index%22==0]

    if period == '3m':
        return df[df.index%64==0]
    
    if period == '6m':
        return df[df.index%128==0]
    pass

def __make_period__(period, start_date, end_date):
    T = __T
    T.rename(columns={'calendarDate':'date'}, inplace=True)    
    if period =='3d':
        T = T[T.index%3==0]
        T = T[T.isOpen >0.5]
        del T['isOpen']
        T = T[T.date <= end_date]
        return T
    
    if period.endswith('w'):
        # endtime = dt.strptime(end_date, '%Y-%m-%d')
        # week = endtime.weekday()
        # if week <4:
        #     w = int(end_date[-2:])
        #     w = w - week -3
        #     end_date = end_date[:-2] + str(w)
        
        # starttime = dt.strptime(start_date, '%Y-%m-%d')
        # week = starttime.weekday()
        # if week == 5:
        #     start_date = start_date[:-2] + str(int(start_date[-2:])+2)
        # if week == 6:
        #     start_date = start_date[:-2] + str(int(start_date[-2:])+1)
        # if week in [1,2,3,4]:
        #     stime = starttime - td(week,0,0)
        #     start_date = dt.strftime(stime, '%Y-%m-%d')
        T = T[T.date >= '2001-01-01'] # this date is monday
        T = T.reset_index()
        del T['index']        
        T = T[T.index%7==4] #it will select the friday.
        T = T[T.isOpen > 0.5]
        del T['isOpen']
        T = T[T.date <= end_date]
        return T
    
    if period.endswith('m'):
        T = ts.get_k_data('000001', ktype='M', index=True)[['date']]
        T = T[T.date <= (end_date+'-31')]
        return T

def get_all(pool, period, start_date, factors=[], count=0, index=True, **args):
    """get all factors within a stocks pool
    
    Arguments:
        pool {string} -- pool name, such as 'hs300'        
        period {string} -- a string indicates data period, could be one of them: nd, nw, nm
        start_date {string} -- a string presents start time, for example: daily: '2012-01-01',
            weekly: '2012-12-01', monthly: '2012-12'
        factors {list} -- a list contain factors you want to get, default to get all.
        count {int} --a number presents the length of return list, default 10. 
        index {bool} -- default to be True, whether contain index in pool or not.
        args {dict}  -- dict of keyword, support rsi1, rsi2 etc
    """   
    temdate = start_date.split('-')
    date = temdate[0]+temdate[1]
    if pool=='hs300' and 200607 <= int(date) <=201802:
        pass
    else:
        print('data not in the range')
        return    
    dfM = pd.read_csv(os.path.join(os.path.dirname(os.path.realpath(__file__)),'hs300.csv'))
    if not index:
        dfM = dfM[1:]
    columns=['code', 'date', 'open', 'close', 'high', 'low', 'volume', 'momentum', 'adj_close', 'obv', 'rsi6', 'rsi12', 'sma3', 'ema6', 'ema12', 'atr14', 'mfi14', 'adx14', 'adx20', 'mom1', 'mom3', 'cci12', 'cci20', 'rocr3', 'rocr12', 'macd', 'macd_sig', 'macd_hist', 'willr', 'tsf10', 'tsf20', 'trix', 'bbandupper', 'bbandmiddle', 'bbandlower']
    T = pd.DataFrame([], columns=columns)
    thedate=''
    nextdate=''
    end_date=''
    for d in dfM:
        thedate = str(d)
        if int(date) < int(d):
            break
    if thedate.endswith('01'):
        nextdate=thedate[:-1] + '6'
        end_date = nextdate[:4]+'-'+nextdate[4:]+'-'+'30'
    else:
        nextdate=thedate[:-2] + '12'
        end_date = nextdate[:4]+'-'+nextdate[4:]+'-'+'31'
    
    outT=[]
    for code in tqdm(dfM[thedate]):         
        code = str(code)
        if len(code) <6:
            code = '000000'+code
            code = code[-6:]
        # print(code)        
        df_price = get_day(code, '1995-01-01', end_date)
        df_finance = get_finance(code, '1995-01-01', end_date)
        #merge

        if df_price.empty:
            print('code {} has no data'.format(code))
            continue

        df = df_price.merge(df_finance, how='left', on ='date')

        #make period
        T = __make_period__(period, start_date, end_date)
        df = df.merge(T,how='right', on = 'date')
        df = df.reset_index()
        del df['index']
        PERIOD = int(period[:-1])
        df = df[df.index%PERIOD==0]
        df = df.reset_index()
        del df['index']
        del df['open']
        del df['high']
        del df['low']
        del df['volume']
        #calculate tech indicators
        close_list = np.asarray(df["close"].tolist()) 
        ind_dict={}       
        ind_dict['rsi2'] = talib.RSI(close_list, timeperiod=(args.get('rsi2') or 12))
        ind_dict['rsi1'] = talib.RSI(close_list, timeperiod=(args.get('rsi1') or 6))
        ind_dict['sma1'] = talib.SMA(close_list, timeperiod=(args.get('sma1') or 3))
        ind_dict['sma2'] = talib.SMA(close_list, timeperiod=(args.get('sma2') or 6))
        ind_dict['ema1'] = talib.EMA(close_list, timeperiod=(args.get('ema1') or 6))
        ind_dict['ema2'] = talib.EMA(close_list, timeperiod=(args.get('ema2') or 12))
        ind_dict['mom1'] = talib.MOM(close_list, timeperiod=(args.get('mom1') or 1))
        ind_dict['mom2'] = talib.MOM(close_list, timeperiod=(args.get('mom2') or 3))
        ind_dict['rocr1'] = talib.ROCR(close_list, timeperiod=(args.get('rocr1') or 3))
        ind_dict['rocr2'] = talib.ROCR(close_list, timeperiod=(args.get('rocr2') or 12))
        ind_dict['macd'], ind_dict['macd_sig'], ind_dict['macd_hist'] = talib.MACD(close_list,\
            fastperiod=(args.get('macd_fast') or 12), \
            slowperiod=(args.get('macd_slow') or 26), signalperiod=(args.get('macd_signal') or 9))
        ind_dict['tsf1'] = talib.TSF(close_list, timeperiod=(args.get('tsf1') or 10))
        ind_dict['tsf2'] = talib.TSF(close_list, timeperiod=(args.get('tsf2') or 20))
        ind_dict['trix1'] = talib.TRIX(close_list, timeperiod=(args.get('trix1') or 30))
        ind_dict['trix2'] = talib.TRIX(close_list, timeperiod=(args.get('trix2') or 50))
        ind_dict['bbandupper'], ind_dict['bbandmiddle'], ind_dict['bbandlower'] = \
            talib.BBANDS(close_list,timeperiod=(args.get('bands_period') or 5), \
            nbdevup=(args.get('bands_up') or 2), nbdevdn=(args.get('bands_dn') or 2), matype=(args.get('bands_ma') or 0))
        
        #pick up data
        ind_df = pd.DataFrame(ind_dict)
        rangedf = df[df.date> start_date]
        rangelen = len(rangedf)  # the total output, list length of outT
        for i in range(rangelen): #the nth output
            c_dt = df.iloc[i].to_dict()
            ind_dt = ind_df.iloc[-rangelen+i].to_dict()
            dict_merge = dict(c_dt, **ind_dt)

            if len(outT) ==0:
                for jj in range(rangelen):
                    outT.append(pd.DataFrame([],columns=dict_merge.keys()))
            
            outT[i].loc[len(outT[i])] = dict_merge
    if len(factors)>0:
        outT = outT[factors]
    if count > 0 and count <= len(outT):
        outT[0:count]
    return outT, end_date, rangelen

if __name__ == '__main__':
    # print(macrodata())
    # print(get_day('002236','2007-08-05','2010-08-05'))
    # _fetch_finance()
    # print(get_finance('000001'))
    # print(get_local_future('A99'))
    # print(get_future('XAU/USD'))
    # print(get_month('2010-01'))
    # print(get_ts_finance('000001','1m'))
    print(get_all('hs300','1w','2008-08-08', index=False))
    
