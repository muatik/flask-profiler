import time
import pymongo
from .base import BaseStorage
import datetime
from bson.objectid import ObjectId


class Mongo(BaseStorage):
    """
    To use this class, you have to provide a config dictionary which contains
    "MONGO_URL", "DATABASE" and "COLLECTION".
    """

    def __init__(self, config=None):
        super(Mongo, self).__init__(),
        self.config = config
        self.mongo_url = self.config.get("MONGO_URL", "mongodb://localhost")
        self.database_name = self.config.get("DATABASE", "flask_profiler")
        self.collection_name = self.config.get("COLLECTION", "measurements")

        def createIndex():
            self.collection.ensure_index(
                [
                    ('startedAt', 1),
                    ('endedAt', 1),
                    ('elapsed', 1),
                    ('name', 1),
                    ('method', 1)]
                )

        self.client = pymongo.MongoClient(self.mongo_url)
        self.db = self.client[self.database_name]
        self.collection = self.db[self.collection_name]
        createIndex()

    def filter(self, filtering={}):
        query = {}
        limit = filtering.get('limit', 100000)
        skip = filtering.get('skip', 0)
        sort = filtering.get('sort', "endedAt,desc").split(",")

        startedAt = float(
            filtering.get('startedAt', time.time() - 3600 * 24 * 7))
        endedAt = float(filtering.get('endedAt', time.time()))
        elapsed = float(filtering.get('elapsed', 0))
        name = filtering.get('name', None)
        method = filtering.get('method', None)
        args = filtering.get('args', None)
        kwargs = filtering.get('kwargs', None)

        if sort[1] == "desc":
            sort_dir = pymongo.DESCENDING
        else:
            sort_dir = pymongo.ASCENDING

        if name:
            query['name'] = name
        if method:
            query['method'] = method
        if endedAt:
            query['endedAt'] = {"$lte": endedAt}
        if startedAt:
            query['startedAt'] = {"$gt": startedAt}
        if elapsed:
            query['elapsed'] = {"$gte": elapsed}
        if args:
            query['args'] = args
        if kwargs:
            query['kwargs'] = kwargs

        if limit:
            cursor = self.collection.find(
                query
                ).sort(sort[0], sort_dir).skip(skip)
        else:
            cursor = self.collection.find(
                query
                ).sort(sort[0], sort_dir).skip(skip).limit(limit)
        return (self.clearify(record) for record in cursor)

    def insert(self, recordDictionary):
        result = self.collection.insert(recordDictionary)
        if result:
            return True
        return False

    def truncate(self):
        self.collection.remove()

    def delete(self, measurementId):
        result = self.collection.remove({"_id": ObjectId(measurementId)})
        if result:
            return True
        return False

    def getSummary(self,  filtering={}):
        match_condition = {}
        endedAt = filtering.get('endedAt', None)
        startedAt = filtering.get('startedAt', None)
        elapsed = filtering.get('elapsed', None)
        name = filtering.get('name', None)
        method = filtering.get('method', None)
        sort = filtering.get('sort', "count,desc").split(",")

        if name:
            match_condition['name'] = name
        if method:
            match_condition['method'] = method
        if endedAt:
            match_condition['endedAt'] = {"$lte": endedAt}
        if startedAt:
            match_condition['startedAt'] = {"$gt": startedAt}
        if elapsed:
            match_condition['elapsed'] = {"$gte": elapsed}

        if sort[1] == "desc":
            sort_dir = -1
        else:
            sort_dir = 1

        result = self.collection.aggregate([
            {"$match": match_condition},
            {
                "$group": {
                    "_id": {
                        "method": "$method",
                        "name": "$name"
                       },
                    "count": {"$sum": 1},
                    "min": {"$min": "$elapsed"},
                    "max": {"$max": "$elapsed"},
                    "avg": {"$avg": "$elapsed"}
                }
            },
            {
                "$sort": {sort[0]: sort_dir}
            }
            ])
        return result

    def clearify(self, obj):
        available_types = [int, dict, str, list]
        for k, v in obj.items():
            if any([isinstance(v, av_type) for av_type in available_types]):
                continue
            if k == "_id":
                k = "id"
                obj.pop("_id")
            obj[k] = str(v)
        return obj

    def get(self, measurementId):
        record = self.collection.find_one({'_id': ObjectId(measurementId)})
        return self.clearify(record)
