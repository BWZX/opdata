#!/usr/bin/python
# -*- coding: utf-8 -*-
import json
import tushare as ts

try:
    with open('stocklist.json','r') as f:
        __flist=json.loads(f.read())
except Exception:
    __flist={}
    pass
# print(__flist)
__nlist={}
#  __netlist=ts.get_today_all()
# for i in range(len(__netlist)):
#     tem=__netlist.iloc[i]
#    __nlist[tem['code']] = tem['name']
__nlist=__flist
refill_list=[it for it in __nlist.keys() if it not in __flist.keys()]
print('lalalal')
StocksList=__nlist
stolist=list(StocksList.keys())
stolist.sort()
# print(stolist)
try:
    with open('stocklist.json','w') as f:
        f.write(json.dumps(StocksList))
    pass
except Exception:
    pass


AppConfig={
    'data_update_interval':300, #300 秒更新一次所有的数据
    'all_update_time':18  #每天获取当日全部明细以及当日成交数据的时间   
}

#largest concurency requests amout
REQ_AMOUNTS = 1002

#############- your config items -########################

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/49.0.2623.75 Safari/537.36"

}

if __name__ == '__main__':
    # stolist=list(StocksList.keys())
    # stolist.sort()
    # with open('stolist.py','w') as f:
    #     f.write(str(stolist))
    print(stolist)
