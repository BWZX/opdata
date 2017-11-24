import pymongo
from pymongo import MongoClient
__client = MongoClient('mongodb://admin:%2B@node0:27017')
security =__client.quantDay.security