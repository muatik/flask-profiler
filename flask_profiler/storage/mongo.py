import pymongo
from base import BaseStorage
import datetime
from bson.objectid import ObjectId


class Mongo(BaseStorage):
    """docstring for Mongo"""

    def __init__(self):
        super(Mongo, self).__init__(),
        #self.config = config
        self.client = pymongo.MongoClient()
        self.db = self.client['profiler_db']
        self.collection = self.db['profiler_backend']

    def filter(self, kwargs):
        query = {}

        endedAt = kwargs.get('endedAt', None)
        startedAt = kwargs.get('startedAt', None)
        elapsed = kwargs.get('elapsed', None)

        if endedAt:
            query['endedAt'] = { "$lte": endedAt }
        if startedAt:
            query['startedAt'] = { "$gt": startedAt }
        if elapsed:
            query['elapsed'] = { "$gte": elapsed }

        if limit:
            return self.collection.find(
                query
                ).sort(sort_key, sort_dir).skip(skip)
        else:
            return self.collection.find(
                query
                ).sort(sort_key, sort_dir).skip(skip).limit(limit)

    def insert(self, recordDictionary):
        return self.collection.insert(recordDictionary)

    def delete(self, criteria):
        return self.collection.remove(criteria)

    def getSummary(self,  kwargs):
        match_condition = {}
        endDate = kwargs.get('endedAt', None)
        startedAt = kwargs.get('startedAt', None)
        elapsed = kwargs.get('elapsed', None)

        if endDate:
            match_condition['endedAt'] = { "$lte": endDate }
        if startDate:
            match_condition['startedAt'] = { "$gt": startDate }
        if elapsed:
            match_condition['elapsed'] = { "$gte": elapsed }

        result = self.collection.aggregate([
                    {"$match": match_condition },
                    {"$group": {
                        "_id": {
                            "method": "$request.method",
                            "url": "$request.url",
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


    def get(self, measurementId):
        return self.collection.find_one({'_id': ObjectId(measurementId)})
