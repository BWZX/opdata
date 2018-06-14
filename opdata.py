# -*- coding: utf-8 -*-
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

from opdata import factors as _factors
from opdata.mongoconnect import *  
# import factors as _factors  
# from mongoconnect import *

__T = ts.trade_cal()
__TM = ts.get_k_data('000001', ktype='M', index=True)[['date']]

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
    T=T.merge(df,on='date',how='left', copy=False)
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
    T = T.reset_index()
    del T['index']
    del T['code'] 
    T['code'] = code
    return T        

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
    T = T.reset_index()
    del T['index']
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
    # T = T[T.date > '2003-01-01']
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
            
    T = T[T.isOpen >0.5]
    T = T[T.date >= start_date]
    T = T[T.date <= end_date]
    T['code']=str(code)
    T = T.reset_index()
    del T['index']
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
    if period.endswith('d'):
        T = T[T.isOpen >0.5]
        T = T[T.index%int(period[:-1])==0]
        del T['isOpen']
        T = T[T.date <= end_date]
        T = T[T.date >= '2001-01-01'] # this date is monday
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
        T = T.reset_index()
        del T['index']       
        T = T[T.index%int(period[:-1])==0]
        del T['isOpen']
        T = T[T.date <= end_date]
        return T
    
    if period.endswith('m'):
        T = __TM
        T = T[T.date >= '2001-01-01'] # this date is monday
        T = T[T.index%int(period[:-1])==0]
        T = T[T.date <= (end_date+'-31')]
        return T

def __parse_factors(factors, period):
    """factors format: rsi_{arg}_{period}  or macd_{arg1}_{arg2}_{arg3}_{period}   
    """
    compare={'d':0, 'w':1, 'm':2}
    indicator = ['rsi', 'sma', 'ema', 'mom', 'rocr', 'macd', 'tsf', 'trix', 'bbandupper', 'atr', \
        'mfi' ,'adx' ,'cci', 'willr', 'obv']
    outT = {}
    for f in factors:
        k = f.split('_')        
        if k[0] in indicator: 
            if compare[k[-1][-1]] > compare[period[-1]]:
                print('it will be confusion when the tech indicator has less data length than finance indicator.\n ignore this item.')
                continue           
            if outT.get(k[0]):
                outT[k[0]].append(k[1:])
            else:
                outT[k[0]] = [k[1:]]
                
    return outT

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
    Returns:
        list of dataframe,  end date, count
    """ 
    filenames = ['test', 'allstocks', 'hs300']
    if pool not in filenames:
        class_df = ts.get_industry_classified()
        clsname = list(set(class_df['c_name']))
        if pool in clsname:
            dfM = class_df[class_df.c_name == pool]
            dfM['200607'] = dfM['code']
            dfM['201801'] = dfM['code']
            dfM = dfM.reset_index()
            del dfM['index']
            del dfM['code']
            del dfM['name']
            del dfM['c_name']
            # print(dfM)
        else:
            return
        pass
    else:
        dfM = pd.read_csv(os.path.join(os.path.dirname(os.path.realpath(__file__)),pool+'.csv'))
    # print(dfM)
    indicator_paras = __parse_factors(factors, period)
    temdate = start_date.split('-')
    date = temdate[0]+temdate[1]
    if not index:
        dfM = dfM[1:]
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
    def drop_y(df):
        # list comprehension of the cols that end with '_y'
        to_drop = [x for x in df if x.endswith('_y')]
        df.drop(to_drop, axis=1, inplace=True)

    def name_tool(nlist):
        kk=''
        for it in nlist:
            kk=kk+it+'_'
        return kk[:-1]

    all_columns=['cashratio', 'name', 'currentasset_days', 'adratio', \
        'roe', 'net_profits', 'icratio', 'open', 'close', 'volume', 'currentasset_turnover', \
        'nav', 'gross_profit_rate', 'BVY', 'epsg', 'date', 'CF2TA', 'SY', 'currentratio', \
        'sheqratio','bvps','high', 'cashflowratio', 'inventory_turnover', \
        'rateofreturn', 'seg', 'cf_liabilities', 'cf_nm', 'arturndays', 'epcf', 'code', \
        'mbrg', 'nprg', 'business_income', 'EBT2TA', 'cf_sales', 'eps', 'arturnover', \
        'net_profit_ratio', 'EBITDA2TA', 'quickratio', 'bips', 'low', 'EBITDA', 'EBIT', \
        'general_equity', 'flow_equity', 'EBITDA2', 'pe']
    code_list = list(dfM[thedate])
    # print(code_list)
    # exit()
    for code in tqdm(dfM[thedate]):         
        code = str(code)
        # print(code)
        if len(code) <6:
            code = '000000'+code
            code = code[-6:]
        # print(code)        
        df_price = get_day(code, '1995-01-01', end_date)
        if code == 'sh000300':
            df_price['name'] = 'sh300'
        df_finance = get_finance(code, '1995-01-01', end_date)
        jp_finance = _factors.JP_VALUATION_FINANCE(code,'1995-01-01',end_date)
        # print(jp_finance)
        # exit()
        #merge
        if df_price.empty:
            # print('code {} has no data'.format(code))
            continue
        if not df_finance.empty:
            df = df_price.merge(df_finance, how='left', on ='date', suffixes=('', '_y'))
            drop_y(df)            
        else:
            df = df_price.copy()
        if not jp_finance.empty:
            df = df.merge(jp_finance, how='left', on ='date', suffixes=('', '_y'))
            drop_y(df)
            # print(df[df.date>'2008-01-08'])
        
        t_columns=list(df.columns)
        for it in all_columns:
            if it in t_columns:
                continue
            else:
                df[it]=np.nan
        
        T = __make_period__(period, start_date, end_date)
        df = df.merge(T,how='right', on = 'date', suffixes=('', '_y'))
        df = df.reset_index()
        del df['index']
        PERIOD = int(period[:-1])
        df = df[df.index%PERIOD==0]
        df = df.reset_index()
        df['pe'] = df['eps'].div(df['close'], axis = 0)
        del df['index']
        # del df['open']
        # del df['high']
        # del df['low']
        # del df['volume']
        call_with_name ={
            'rsi': talib.RSI,
            'sma': talib.SMA,
            'ema': talib.EMA,
            'mom': talib.MOM,
            'rocr': talib.ROCR,
            'macd': talib.MACD,
            'tsf':  talib.TSF,
            'trix': talib.TRIX,
            'bbands': talib.BBANDS,
            #########################
            'atr': talib.ATR,
            'mfi': talib.MFI,
            'adx': talib.ADX,
            'cci': talib.CCI,
            'willr': talib.WILLR,
            'obv': talib.OBV
        }
        period_dict = {}
        rangedf = df[df.date>= start_date]  
        ta_indicators = pd.DataFrame()
        ta_indicators['date'] = rangedf['date']
        for ind in indicator_paras:   #exp: {'rsi': [['10d', '1d'], ['10d', '3d']]}
            for cu in indicator_paras[ind]:                
                if type(period_dict.get(cu[-1])) == type(period_dict.get('nothing')):                    
                    period_dict[cu[-1]] = __make_period__(cu[-1], start_date, end_date)
                    period_dict[cu[-1]] = period_dict[cu[-1]].merge(df_price,how='left', on = 'date', suffixes=('', '_y'))
                
                column_name = name_tool([ind] + cu )
                column_name_ex0 = ''
                column_name_ex1 = ''
                ta_normal_list = []
                ta_normal_list1 = []
                ta_normal_list2 = []
                for currentdate in ta_indicators['date']:
                    close_dt = period_dict[cu[-1]][period_dict[cu[-1]].date<=currentdate]['close']
                    # close_dt = df[df.date <= currentdate]['close']
                    volume_dt = period_dict[cu[-1]][period_dict[cu[-1]].date<=currentdate]['volume']
                    # volume_dt = df[df.date <= currentdate]['volume']
                    low_dt = period_dict[cu[-1]][period_dict[cu[-1]].date<=currentdate]['low']
                    # low_dt = df[df.date <= currentdate]['low']
                    high_dt = period_dict[cu[-1]][period_dict[cu[-1]].date<=currentdate]['high']
                    # high_dt = df[df.date <= currentdate]['high']
                    close_list = np.asarray(close_dt.tolist())
                    volume_list = np.asarray(volume_dt.tolist()) 
                    low_list = np.asarray(low_dt.tolist()) 
                    high_list = np.asarray(high_dt.tolist()) 

                    if ind in ['rsi','sma','ema','mom','rocr','tsf','trix']:                        
                        ta_normal_list.append(call_with_name[ind](close_list, int(cu[0]))[-1])
                        if ind =='ema' and currentdate == '2017-07-31':
                            print(period_dict[cu[-1]])
                            print(close_dt)
                            print(close_list)
                            print(ta_normal_list)
                            exit()
                            
                    elif ind in ['atr', 'adx', 'cci', 'willr']:
                        ta_normal_list.append(call_with_name[ind](high_list, low_list, close_list, int(cu[0]))[-1])
                    elif ind =='mfi':
                        ta_normal_list.append(call_with_name[ind](high_list, low_list, close_list, volume_list, int(cu[0]))[-1])
                    elif ind =='obv':
                        ta_normal_list.append(call_with_name[ind](close_list, volume_list))
                    elif ind == 'macd':
                        column_name_ex0 = name_tool(['macdsig']+cu)
                        column_name_ex1 = name_tool(['macdhist']+cu)
                        factors.append(column_name_ex0)
                        factors.append(column_name_ex1)
                        a, b, c = call_with_name[ind](close_list, int(cu[0]), int(cu[1]), int(cu[2]))
                        ta_normal_list.append(a[-1])
                        ta_normal_list1.append(b[-1])
                        ta_normal_list2.append(c[-1])
                    elif ind == 'bbands':
                        column_name = name_tool(['bbandsupper']+cu)
                        bbands_index = factors.index(name_tool(['bbands']+cu))
                        if bbands_index == len(factors) -1:
                            factors = factors[:-1]
                        else:
                            factors = factors[0:bbands_index] + factors[bbands_index+1:]
                        column_name_ex0 = name_tool(['bbandsmiddle']+cu)
                        column_name_ex1 = name_tool(['bbandslower']+cu)
                        factors.append(column_name_ex0)
                        factors.append(column_name_ex1)
                        a,b,c = call_with_name[ind](close_list, int(cu[0]), int(cu[1]), int(cu[2]), int(cu[3]))
                        ta_normal_list.append(a[-1])
                        ta_normal_list1.append(b[-1])
                        ta_normal_list2.append(c[-1])

                ta_indicators[column_name] = ta_normal_list
                if ta_normal_list1:
                    ta_indicators[column_name_ex0] = ta_normal_list1
                if ta_normal_list2:
                    ta_indicators[column_name_ex1] = ta_normal_list2
                # else:
                #     close_list = np.asarray(period_dict[cu[-1]]["close"].tolist()) 
                #     column_name = name_tool([ind] + cu )
                #     if ind is not 'macd' or 'bbands':                        
                #         period_dict[cu[-1]][column_name] = call_with_name[ind](close_list, int(cu[0]))
                #     elif ind == 'macd':
                #         period_dict[cu[-1]][column_name], period_dict[cu[-1]][name_tool(['macdsig']+cu)],period_dict[cu[-1]][name_tool(['macdhist']+cu)] =\
                #             call_with_name[ind](close_list, int(cu[0]), int(cu[1]), int(cu[2]))
                #     elif ind == 'bbands':
                #         period_dict[cu[-1]][name_tool(['bbandsupper']+cu)], period_dict[cu[-1]][name_tool(['bbandsmiddle']+cu)],period_dict[cu[-1]][name_tool(['bbandslower']+cu)] =\
                #             call_with_name[ind](close_list, int(cu[0]), int(cu[1]), int(cu[2]), int(cu[3]))
        
        #pick up data
        if period.endswith('m'):
            start_date = start_date+'-01'
        rangedf = df[df.date>= start_date]  
        rangelen = len(rangedf)  # the total output, list length of outT        
        rangedf = rangedf.merge(ta_indicators, how = 'left', on='date', copy = False, suffixes=('', '_y'))
        drop_y(rangedf)
        for i in range(rangelen): #the nth output
            if rangedf.iloc[i]['close'] <= 0.0004:
                continue
            c_dt = rangedf.iloc[i].to_dict() 
            if len(outT) ==0:
                for jj in range(rangelen):
                    outT.append(pd.DataFrame([],columns=c_dt.keys()))
            outT[i].loc[len(outT[i])] = c_dt
    if len(factors)>=0:
        factors = ['code', 'close', 'date'] + factors
        factors = list(set(factors))
        for i in range(len(outT)):            
            for it in factors:
                co_names = list(outT[i].columns)
                if co_names.count(it) == 0:
                    t = factors.index(it)
                    factors = factors[:t] + factors[t+1:]                  
            outT[i] = outT[i][factors]
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
    re = get_all('test','1m','2010-01', ['open', 'ema_10_1m','rsi_10_1m', 'EBITDA2TA'])[0]
    print(re)
    # print(re[1])
    # print(re[2])    
