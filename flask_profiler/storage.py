# -*- coding: utf8 -*-


def getCollection(conf):
    if conf.get("engine", "mongodb").lower() == "mongodb":
        return getMongoCollection(conf)


def getMongoCollection(conf):
    from pymongo import MongoClient
    db = MongoClient()[conf.get("database", "flask_profiler")]
    collection = db[conf.get("collection", "measurements")]
    return collection
