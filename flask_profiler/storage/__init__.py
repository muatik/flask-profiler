# -*- coding: utf8 -*-

import importlib
from .base import BaseStorage


def getCollection(conf):
    engine = conf.get("engine", "")
    if engine.lower() == "mongodb":
        from .mongo import Mongo
        return Mongo(conf)
    elif engine.lower() == "sqlite":
        from .sqlite import Sqlite
        return Sqlite(conf)
    else:
        try:
            engine = engine.split('.')
            if len(engine) < 1: # engine must have at least module name and class
                raise ImportError

            module_name = '.'.join(engine[:-1])
            klass_name = engine[-1]
            module = importlib.import_module(module_name)
            storage = getattr(module, klass_name)
            if not issubclass(storage, BaseStorage):
                raise ImportError

        except ImportError:
            raise ValueError(
                ("flask-profiler requires a valid storage engine but it is"
                    " missing or wrong. provided engine: {}".format(engine)))


        return storage(conf)
