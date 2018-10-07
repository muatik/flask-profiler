import json
from decimal import Decimal, ROUND_UP
from .base import BaseStorage
from datetime import datetime
import time
from sqlalchemy import create_engine, Text
from sqlalchemy import Column, Integer, Numeric
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

base = declarative_base()


def formatDate(timestamp, dateFormat):
    return datetime.fromtimestamp(timestamp).strftime(dateFormat)


class Measurements(base):
    __tablename__ = 'flask_profiler_measurements'

    id = Column(Integer, primary_key=True)
    startedAt = Column(Numeric)
    endedAt = Column(Numeric)
    elapsed = Column(Numeric(6, 4))
    method = Column(Text)
    args = Column(Text)
    kwargs = Column(Text)
    name = Column(Text)
    context = Column(Text)

    def __repr__(self):
        return "<Measurements {}, {}, {}, {}, {}, {}, {}, {}, {}>".format(
            self.id,
            self.startedAt,
            self.endedAt,
            self.elapsed,
            self.method,
            self.args,
            self.kwargs,
            self.name,
            self.context
        )


class Sqlalchemy(BaseStorage):

    def __init__(self, config=None):
        super(Sqlalchemy, self).__init__()
        self.config = config
        self.db = create_engine(
            self.config.get("db_url", "sqlite:///flask_profiler.sql")
        )
        self.create_database()

    def __enter__(self):
        return self

    def create_database(self):
        base.metadata.create_all(self.db)

    def insert(self, kwds):
        endedAt = int(kwds.get('endedAt', None))
        startedAt = int(kwds.get('startedAt', None))
        elapsed = Decimal(kwds.get('elapsed', None))
        if elapsed:
            elapsed = elapsed.quantize(Decimal('.0001'), rounding=ROUND_UP)
        args = json.dumps(list(kwds.get('args', ())))  # tuple -> list -> json
        kwargs = json.dumps(kwds.get('kwargs', ()))
        context = json.dumps(kwds.get('context', {}))
        method = kwds.get('method', None)
        name = kwds.get('name', None)

        session = sessionmaker(self.db)()
        session.add(Measurements(
            endedAt=endedAt,
            startedAt=startedAt,
            elapsed=elapsed,
            args=args,
            kwargs=kwargs,
            context=context,
            method=method,
            name=name,
        ))
        session.commit()

    @staticmethod
    def getFilters(kwargs):
        filters = {}
        filters["sort"] = kwargs.get('sort', "endedAt,desc").split(",")

        # because inserting and filtering may take place at the same moment,
        # a very little increment(0.5) is needed to find inserted
        # record by sql.
        filters["endedAt"] = float(
            kwargs.get('endedAt', time.time() + 0.5))
        filters["startedAt"] = float(
            kwargs.get('startedAt', time.time() - 3600 * 24 * 7))

        filters["elapsed"] = kwargs.get('elapsed', None)
        filters["method"] = kwargs.get('method', None)
        filters["name"] = kwargs.get('name', None)
        filters["args"] = json.dumps(
            list(kwargs.get('args', ())))  # tuple -> list -> json
        filters["kwargs"] = json.dumps(kwargs.get('kwargs', ()))
        filters["sort"] = kwargs.get('sort', "endedAt,desc").split(",")
        filters["skip"] = int(kwargs.get('skip', 0))
        filters["limit"] = int(kwargs.get('limit', 100))
        return filters

    def filter(self, kwds={}):
        # Find Operation
        f = Sqlalchemy.getFilters(kwds)

        conditions = "WHERE 1=1 AND "

        if f["endedAt"]:
            conditions = conditions + 'endedAt<={0} AND '.format(f["endedAt"])
        if f["startedAt"]:
            conditions = conditions + 'startedAt>={0} AND '.format(
                f["startedAt"])
        if f["elapsed"]:
            conditions = conditions + 'elapsed>={0} AND '.format(f["elapsed"])
        if f["method"]:
            conditions = conditions + 'method="{0}" AND '.format(f["method"])
        if f["name"]:
            conditions = conditions + 'name="{0}" AND '.format(f["name"])

        conditions = conditions.rstrip(" AND")

        sql = '''SELECT * FROM flask_profiler_measurements {conditions}
        order by {sort_field} {sort_direction}
        limit {limit} OFFSET {skip} '''.format(
            conditions=conditions,
            sort_field=f["sort"][0],
            sort_direction=f["sort"][1],
            limit=f['limit'],
            skip=f['skip']
        )
        session = sessionmaker(self.db)()
        rows = session.execute(sql)
        return (Sqlalchemy.jsonify_row(row) for row in rows)

    @staticmethod
    def jsonify_row(row):
        data = {
            "id": row[0],
            "startedAt": row[1],
            "endedAt": row[2],
            "elapsed": row[3],
            "method": row[4],
            "args": tuple(json.loads(row[5])),  # json -> list -> tuple
            "kwargs": json.loads(row[6]),
            "name": row[7],
            "context": json.loads(row[8]),
        }
        return data

    def truncate(self):
        session = sessionmaker(self.db)()
        try:
            session.query(Measurements).delete()
            session.commit()
            return True
        except:
            session.rollback()
            return False

    def delete(self, measurementId):
        session = sessionmaker(self.db)()
        try:
            session.query(Measurements).filter_by(id=measurementId).delete()
            session.commit()
            return True
        except:
            session.rollback()
            return False

    def getSummary(self, kwds={}):
        filters = Sqlalchemy.getFilters(kwds)

        conditions = "WHERE 1=1 and "

        if filters["startedAt"]:
            conditions = conditions + "startedAt>={0} AND ".format(
                filters["startedAt"])
        if filters["endedAt"]:
            conditions = conditions + "endedAt<={0} AND ".format(
                filters["endedAt"])
        if filters["elapsed"]:
            conditions = conditions + "elapsed>={0} AND".format(
                filters["elapsed"])

        conditions = conditions.rstrip(" AND")

        sql = '''SELECT
                method, name,
                count(id) as count,
                min(elapsed) as minElapsed,
                max(elapsed) as maxElapsed,
                avg(elapsed) as avgElapsed
            FROM flask_profiler_measurements {conditions}
            group by method, name
            order by {sort_field} {sort_direction}
            '''.format(
                conditions=conditions,
                sort_field=filters["sort"][0],
                sort_direction=filters["sort"][1]
                )
        session = sessionmaker(self.db)()
        rows = session.execute(sql)

        result = []
        for r in rows:
            result.append({
                "method": r[0],
                "name": r[1],
                "count": r[2],
                "minElapsed": r[3],
                "maxElapsed": r[4],
                "avgElapsed": r[5]
            })
        return result

    def getTimeseries(self, kwds={}):
        filters = Sqlalchemy.getFilters(kwds)

        if kwds.get('interval', None) == "daily":
            interval = 3600 * 24   # daily
            dateFormat = "%Y-%m-%d"
        else:
            interval = 3600  # hourly
            dateFormat = "%Y-%m-%d %H"

        endedAt, startedAt = filters["endedAt"], filters["startedAt"]

        conditions = "where endedAt<={0} AND startedAt>={1} ".format(
            endedAt, startedAt)

        sql = '''SELECT
                startedAt, count(id) as count
            FROM flask_profiler_measurements {conditions}
            group by DATE_FORMAT(from_unixtime(startedAt), "{dateFormat}")
            order by startedAt asc
            '''.format(
                dateFormat=dateFormat,
                conditions=conditions
                )
        session = sessionmaker(self.db)()
        rows = session.execute(sql)

        series = {}
        for i in range(int(startedAt), int(endedAt) + 1, interval):
            series[formatDate(i, dateFormat)] = 0

        for row in rows:
            series[formatDate(row[0], dateFormat)] = row[1]
        return series

    def getMethodDistribution(self, kwds=None):
        if not kwds:
            kwds = {}
        f = Sqlalchemy.getFilters(kwds)
        endedAt, startedAt = f["endedAt"], f["startedAt"]
        conditions = "where endedAt<={0} AND startedAt>={1} ".format(
            endedAt, startedAt)

        sql = '''SELECT
                method, count(id) as count
            FROM flask_profiler_measurements {conditions}
            group by method
            '''.format(
                conditions=conditions
                )
        session = sessionmaker(self.db)()
        rows = session.execute(sql)


        results = {}
        for row in rows:
            results[row[0]] = row[1]
        return results

    def __exit__(self, exc_type, exc_value, traceback):
        return self.db
