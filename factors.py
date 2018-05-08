# from opdata.mongoconnect import *   
from mongoconnect import *
import opdata
import pandas as pd

def JP_VALUATION_FINACE(code, start_date, end_date):
    cursor = financetable.find({'code':code}).sort('date')
    opcf = pd.DataFrame(list(cursor))

    def setValue(v):
        nonlocal lastvalue
        if pd.isnull(v) or v == 'None' or v == '--':
            return lastvalue
        else:
            lastvalue = v
            return lastvalue
    
    T = opdata.__T
    T.rename(columns={'calendarDate':'date'}, inplace=True)
    T = T[T.date > '2003-01-01']
    T=T.merge(opcf,on='date',how='left')
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
    del T['isOpen']

    price = opdata.get_day(code, start_date, end_date)



