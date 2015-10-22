# -*- coding: utf8 -*-


def getCollection(conf):
    engine = conf.get("engine", "").lower()
    if engine == "mongodb":
        from .mongo import Mongo
        return Mongo(conf)
    elif engine == "sqlite":
        from .sqlite import Sqlite
        return Sqlite(conf)
    else:
        raise ValueError(
            ("flask-profiler requires a valid storage engine but it is missing"
                " or wrong. provided engine: {}".format(engine)))
