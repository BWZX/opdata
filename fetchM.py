import tushare as ts
from mongoconnet import *
import pandas as pd
import config
import json

# HS_DF = pd.DataFrame.from_csv('./hs300.csv')

def fetchAll(slist):    
    """
        获取slist 列表的股票的历史数据，
        不包括成交明细，同时把数据存到数据库。
        这个函数应该只运行一次        
    """
    for sto in slist:
        print(sto)        
        df_D=ts.get_k_data(sto,ktype='M') 
        df_D['name']=config.StocksList[sto]
        records = json.loads(df_D.T.to_json()).values()
        securityM.insert(records)
    
def main():
    fetchAll(config.stolist)
    pass

if __name__ == '__main__':
    main()


