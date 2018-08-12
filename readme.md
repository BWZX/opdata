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
*    count {int} --a number presents the length of return list, default 10. --no more support.
*    index {bool} -- default to be True, whether contain index in pool or not.
*    args {dict}  -- dict of keyword, support rsi1, rsi2 etc ————no more support.

Returns:<br>
*    list of dataframe,  end date, count

## 所有可用的pool
1. 'test' , 'allstocks', 'hs300'
2. '电子器件', '玻璃行业', '商业百货', '传媒娱乐', '造纸行业', '生物制药', '陶瓷行业', '印刷包装', '建筑建材', '石油行业', '纺织机械', '环保行业', '飞机制造', '其它行业', '船舶制造', '物资外贸', '摩托车', '机械行业', '医疗器械', '家具行业', '公路桥梁', '钢铁行业', '水泥行业', '交通运输', '食品行业', '发电设备', '化工行业', '塑料制品', '仪器仪表', '有色金属', '金融行业', '供水供气', '煤炭行业', '农林牧渔', '酿酒行业', '房地产', '电器行业', '综合行业', '次新股', '汽车制造', '农药化肥', '酒店旅游', '家电行业', '电子信息', '化纤行业', '开发区', '电力行业', '纺织行业', '服装鞋类'

## 所有可用factor 
参数 | 解释
-----|-----
cashratio | 现金比率
name | --
currentasset_days | 流动资产周转天数
adratio | 股东权益增长率
roe | 净资产收益率
net_profits | 净利润
icratio | 利息支付倍速
open | --
close | --
volume | --
currentasset_turnover | 流动资产周转率
nav | 净资产增长率
gross_profit_rate | 毛利率
BVY | --
epsg | 每股收益增长率
date | --
CF2TA | --
SY | --
currentratio | 流动比率
sheqratio | 股东权益比率
bvps | 每股净资产
high | --
cashflowratio | 现金流量比率
inventory_turnover | 存货周转率
rateofreturn | 经营现金流回报率
seg | 股东权益增长率
cf_liabilities | 经营现金流/负债
cf_nm | 经营现金流/净利润
arturndays | 应收账款周转天数
epcf | 每股现金流量
code | --
mbrg | 主营业务收入增长率
nprg | 净利润增长率
business_income | 营业收入
EBT2TA | 经营现金流入/总资产
cf_sales | 经营现金流/销售收入
eps | 每股收益率
arturnover | 应收账款周转率
net_profit_ratio | 净利率
EBITDA2TA | --
quickratio | 速动比率
bips | 每股主营收入
low | --
EBITDA | --
EBIT | --
general_equity | --
flow_equity | --
EBITDA2 | 经营性现金流入
pe | --
rsi |  talib.RSI,
sma |  talib.SMA,
ema |  talib.EMA,
mom |  talib.MOM,
rocr | talib.ROCR,
macd | talib.MACD,
tsf |  talib.TSF,
trix | talib.TRIX,
bbands | talib.BBANDS
atr  | --
mfi  | --
adx  | --
cci  | --
willr | --
obv  | --

## 技术指标说明
{因子代码} _ {指标参数} _ {该指标计算针对的数据周期} <br>
例如： `rsi_10_3d` 表示在以3天为周期的蜡烛图数据上计算rsi指标，其中rsi这个函数本身的参数是10，其余类似。<br>

成交量的说明： 成交量也按照指标的格式，例如： vol_1_3w,  vol_1_2m,  vol_-1_1d, 当且仅当以 1d 结尾时，中间的参数有用， -1 表示数据时间周期的倒数第一个成交量。例如这样调用：`get_all('test','1m','2010-01', ['open', 'vol_-1_1d','rsi_10_1m', 'EBITDA2TA'])` 将会得到每月的最后一个成交量。
