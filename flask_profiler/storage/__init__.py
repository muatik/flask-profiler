# -*- coding: utf8 -*-


def getCollection(conf):
    engine = conf.get("engine", "").lower()
    if engine == "mongodb":
        from mongo import Mongo
        return Mongo(conf)
    elif engine == "sqlite":
        from sqlite import Sqlite
        return Mongo(conf)
