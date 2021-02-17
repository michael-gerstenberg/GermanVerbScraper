from pymongo import MongoClient
import config

def connect_mongo_db():
    client = MongoClient(config.mongo_db_secret)
    return client

