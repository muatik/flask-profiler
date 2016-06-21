import time
import datetime
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
        limit = int(filtering.get('limit', 100000))
        skip = int(filtering.get('skip', 0))
        sort = filtering.get('sort', "endedAt,desc").split(",")

        startedAt = datetime.datetime.fromtimestamp(float(
            filtering.get('startedAt', time.time() - 3600 * 24 * 7)))
        endedAt = datetime.datetime.fromtimestamp(
            float(filtering.get('endedAt', time.time())))
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

    def insert(self, measurement):
        measurement["startedAt"] = datetime.datetime.fromtimestamp(
            measurement["startedAt"])
        measurement["endedAt"] = datetime.datetime.fromtimestamp(
            measurement["endedAt"])

        result = self.collection.insert(measurement)
        if result:
            return True
        return False

    def truncate(self):
        result = self.collection.remove()
        if result:
            return True
        return False

    def delete(self, measurementId):
        result = self.collection.remove({"_id": ObjectId(measurementId)})
        if result:
            return True
        return False

    def getSummary(self,  filtering={}):
        match_condition = {}
        endedAt = datetime.datetime.fromtimestamp(
            float(filtering.get('endedAt', time.time())))
        startedAt = datetime.datetime.fromtimestamp(
            float(filtering.get('startedAt', time.time() - 3600 * 24 * 7)))
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

        return self.aggregate([
            {"$match": match_condition},
            {
                "$group": {
                    "_id": {
                        "method": "$method",
                        "name": "$name"
                       },
                    "count": {"$sum": 1},
                    "minElapsed": {"$min": "$elapsed"},
                    "maxElapsed": {"$max": "$elapsed"},
                    "avgElapsed": {"$avg": "$elapsed"}
                }
            },
            {
                "$project": {
                    "_id": 0,
                    "method": "$_id.method",
                    "name": "$_id.name",
                    "count": 1,
                    "minElapsed": 1,
                    "maxElapsed": 1,
                    "avgElapsed": 1
                }
            },
            {
                "$sort": {sort[0]: sort_dir}
            }
        ])

    def getMethodDistribution(self, filtering=None):
        if not filtering:
            filtering = {}

        startedAt = datetime.datetime.fromtimestamp(float(
            filtering.get('startedAt', time.time() - 3600 * 24 * 7)))
        endedAt = datetime.datetime.fromtimestamp(
            float(filtering.get('endedAt', time.time())))

        match_condition = {
            "startedAt": {"$gte": startedAt},
            "endedAt": {"$lte": endedAt}
        }

        result = self.aggregate([
            {"$match": match_condition},
            {
                "$group": {
                    "_id": {
                        "method": "$method"
                       },
                    "count": {"$sum": 1}
                }
            },
            {
                "$project": {
                    "_id": 0,
                    "method": "$_id.method",
                    "count": 1
                }
            }
        ])

        distribution = dict((i["method"], i["count"]) for i in result)
        return distribution

    def getTimeseries(self, filtering=None):
        if not filtering:
            filtering = {}
        if filtering.get('interval', None) == "daily":
            dateFormat = '%Y-%m-%d'
            interval = 3600 * 24   # daily
            groupId = {
                "month": {"$month": "$startedAt"},
                "day": {"$dayOfMonth": "$startedAt"},
                "year": {"$year": "$startedAt"}}

        else:
            dateFormat = '%Y-%m-%d %H'
            interval = 3600  # hourly
            groupId = {
                "hour": {"$hour": "$startedAt"},
                "day": {"$dayOfMonth": "$startedAt"},
                "month": {"$month": "$startedAt"},
                "year": {"$year": "$startedAt"}}

        startedAt = float(
            filtering.get('startedAt', time.time() - 3600 * 24 * 7))
        startedAtF = datetime.datetime.fromtimestamp(startedAt)
        endedAt = float(filtering.get('endedAt', time.time()))
        endedAtF = datetime.datetime.fromtimestamp(endedAt)

        match_condition = {
            "startedAt": {"$gte": startedAtF},
            "endedAt": {"$lte": endedAtF}
        }
        result = self.aggregate([
            {"$match": match_condition},
            {
                "$group": {
                    "_id": groupId,
                    "startedAt": {"$first": "$startedAt"},
                    "count": {"$sum": 1},
                }
            }
        ])
        series = {}
        for i in range(int(startedAt), int(endedAt) + 1, interval):
            series[datetime.datetime.fromtimestamp(i).strftime(dateFormat)] = 0

        for i in result:
            series[i["startedAt"].strftime(dateFormat)] = i["count"]
        return series

    def clearify(self, obj):
        available_types = [int, dict, str, list]
        obj["startedAt"] = obj["startedAt"].strftime("%s")
        obj["endedAt"] = obj["endedAt"].strftime("%s")
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

    def aggregate(self, pipeline, **kwargs):
        """Perform an aggregation and make sure that result will be everytime
        CommandCursor. Will take care for pymongo version differencies
        :param pipeline: {list} of aggregation pipeline stages
        :return: {pymongo.command_cursor.CommandCursor}
        """
        result = self.collection.aggregate(pipeline, **kwargs)
        if pymongo.version_tuple < (3, 0, 0):
            result = result['result']

        return result
