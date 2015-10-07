import pymongo
from base import BaseStorage
import datetime
from bson.objectid import ObjectId

class Mongo(BaseStorage):
    """docstring for Mongo"""

    def __init__(self, config=None):
        super(Mongo, self).__init__(),
        self.host = "localhost"
        self.database_name = "profiler"
        self.collection_name = 'instances'
        self.config = config

        if hasattr(self.config, "MONGO_HOST"):
            self.host = self.config.MONGO_HOST
        if hasattr(self.config, "DATABASE"):
            self.database_name = self.config.DATABASE
        if hasattr(self.config, "COLLECTION"):
            self.collection_name = self.config.COLLECTION

        self.client = pymongo.MongoClient(self.host)
        self.db = self.client[self.database_name]
        self.collection = self.db[self.collection_name]

    def filter(self, kwargs):
        query = {}
        limit = kwargs.get('limit', 100000)
        skip = kwargs.get('skip', 0)
        sort_dir = kwargs.get('sort', "asc")
        sort_key = kwargs.get('sort_by', "_id")
        endedAt = kwargs.get('endedAt', None)
        startedAt = kwargs.get('startedAt', None)
        elapsed = kwargs.get('elapsed', None)
        name = kwargs.get('name', None)
        method = kwargs.get('method', None)

        if sort_dir == "desc":
            sort_dir = pymongo.DESCENDING
        else:
            sort_dir = pymongo.ASCENDING

        if name:
            query['name'] = name
        if method:
            query['method'] = method
        if endedAt:
            query['endedAt'] = { "$lte": endedAt }
        if startedAt:
            query['startedAt'] = { "$gt": startedAt }
        if elapsed:
            query['elapsed'] = { "$gte": elapsed }

        if limit:
            cursor = self.collection.find(
                query
                ).sort(sort_key, sort_dir).skip(skip)
        else:
            cursor = self.collection.find(
                query
                ).sort(sort_key, sort_dir).skip(skip).limit(limit)
        return (self.clearify(record) for record in cursor)

    def insert(self, recordDictionary):
        result = self.collection.insert(recordDictionary)
        if result:
            return True
        return False

    def delete(self, measurementId):
        result = self.collection.remove({"_id": ObjectId(measurementId)})
        if result:
            return True
        return False

    def getSummary(self,  kwargs):
        match_condition = {}
        endedAt = kwargs.get('endedAt', None)
        startedAt = kwargs.get('startedAt', None)
        elapsed = kwargs.get('elapsed', None)
        name = kwargs.get('name', None)
        method = kwargs.get('method', None)

        if name:
            match_condition['name'] = name
        if method:
            match_condition['method'] = method
        if endedAt:
            match_condition['endedAt'] = { "$lte": endedAt }
        if startedAt:
            match_condition['startedAt'] = { "$gt": startedAt }
        if elapsed:
            match_condition['elapsed'] = { "$gte": elapsed }

        result = self.collection.aggregate([
                    {"$match": match_condition },
                    {"$group": {
                        "_id": {
                            "method": "$method",
                            "name": "$name"
                            },
                        "count": { "$sum": 1},
                        "min": {"$min": "$elapsed" },
                        "max": {"$max": "$elapsed" },
                        "avg": {"$avg": "$elapsed" }
                        }
                    }]
                )
        return result

    def clearify(self, obj):
        available_types = [int, dict, str]
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
