# -*- coding: utf8 -*-


def getCollection(conf):
    if conf.get("engine", "mongodb").lower() == "mongodb":
        return getMongoCollection(conf)


def getMongoCollection(conf):
    from storage.mongo import Mongo
    return Mongo(conf)
