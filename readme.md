# opdata.get_all 说明
## 定义
`def get_all(pool, period, start_date, factors=[], count=0, index=True, **args):`

Get all factors within a stocks pool    
Arguments:<br>
*   pool {string} -- pool name, such as 'hs300'        
*    period {string} -- a string indicates data period, could be one of them: nd, nw, nm
*    start_date {string} -- a string presents start time, for example: daily: '2012-01-01',
        weekly: '2012-12-01', monthly: '2012-12'
*    factors {list} -- a list contain factors you want to get, default to get all.
*    count {int} --a number presents the length of return list, default 10. 
*    index {bool} -- default to be True, whether contain index in pool or not.
*    args {dict}  -- dict of keyword, support rsi1, rsi2 etc

Returns:<br>
*    list of dataframe,  end date, count

## 所以可用的pool
1. 'test' , 'allstocks', 'hs300'
2. '电子器件', '玻璃行业', '商业百货', '传媒娱乐', '造纸行业', '生物制药', '陶瓷行业', '印刷包装', '建筑建材', '石油行业', '纺织机械', '环保行业', '飞机制造', '其它行业', '船舶制造', '物资外贸', '摩托车', '机械行业', '医疗器械', '家具行业', '公路桥梁', '钢铁行业', '水泥行业', '交通运输', '食品行业', '发电设备', '化工行业', '塑料制品', '仪器仪表', '有色金属', '金融行业', '供水供气', '煤炭行业', '农林牧渔', '酿酒行业', '房地产', '电器行业', '综合行业', '次新股', '汽车制造', '农药化肥', '酒店旅游', '家电行业', '电子信息', '化纤行业', '开发区', '电力行业', '纺织行业', '服装鞋类'

## 所有可用factor 
参数 | 解释
-----|-----
cashratio | --
name | --
currentasset_days | --
adratio | --
roe | --
net_profits | --
icratio | --
open | --
close | --
volume | --
currentasset_turnover | --
nav | --
gross_profit_rate | --
BVY | --
epsg | --
date | --
CF2TA | --
SY | --
currentratio | --
sheqratio | --
bvps | --
high | --
cashflowratio | --
inventory_turnover | --
rateofreturn | --
seg | --
cf_liabilities | --
cf_nm | --
arturndays | --
epcf | --
code | --
mbrg | --
nprg | --
business_income | --
EBT2TA | 经营现金流入/总资产
cf_sales | --
eps | --
arturnover | --
net_profit_ratio | --
EBITDA2TA | --
quickratio | --
bips | --
low | --
EBITDA | --
EBIT | --
general_equity | --
flow_equity | --
EBITDA2 | 经营性现金流入
pe | --

