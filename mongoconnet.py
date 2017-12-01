import pymongo
from pymongo import MongoClient
__client = MongoClient('mongodb://admin:%2Bbeijing2017@124.205.43.244:27017')
security =__client.quantDay.security
finance = __client.quantDay.finance