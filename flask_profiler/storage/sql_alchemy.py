import sqlite3
import json
from .base import BaseStorage
from datetime import datetime
from timeit import default_timer
import time
from sqlalchemy import create_engine
from sqlalchemy import Column, String, Integer, Numeric
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy import func

base = declarative_base()


def formatDate(timestamp, dateFormat):
    return datetime.fromtimestamp(timestamp).strftime(dateFormat)


class Measurements(base):
    __tablename__ = 'flask_profiler_measurements'

    id = Column(Integer, primary_key=True)
    startedAt = Column(Numeric)
    endedAt = Column(Numeric)
    elapsed = Column(Numeric)
    method = Column(String)
    args = Column(String)
    kwargs = Column(String)
    name = Column(String)
    context = Column(String)

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


class Sqlachemy(BaseStorage):
    """docstring for Sqlite"""
    def __init__(self, config=None):
        super(Sqlachemy, self).__init__()
        self.config = config

        self.db = create_engine(self.config.get("db_url", "sqlite:///flask_profiler.sql"))

        self.create_database()

    def __enter__(self):
        return self

    def create_database(self):
        base.metadata.create_all(self.db)

    def insert(self, kwds):
        endedAt = float(kwds.get('endedAt', None))
        startedAt = float(kwds.get('startedAt', None))
        elapsed = kwds.get('elapsed', None)
        args = json.dumps(list(kwds.get('args', ())))  # tuple -> list -> json
        kwargs = json.dumps(kwds.get('kwargs', ()))
        context = json.dumps(kwds.get('context', {}))
        method = kwds.get('method', None)
        name = kwds.get('name', None)

        session = sessionmaker(self.db)()
        doctor_strange = Measurements(
            endedAt=endedAt,
            startedAt=startedAt,
            elapsed=elapsed,
            args=args,
            kwargs=kwargs,
            context=context,
            method=method,
            name=name,
        )
        session.add(doctor_strange)
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
        f = Sqlachemy.getFilters(kwds)
        session = sessionmaker(self.db)()
        query = session.query(Measurements)

        if "endedAt" in f and f["endedAt"]:
            query = query.filter(Measurements.endedAt <= f["endedAt"])
        if "startedAt" in f and f["startedAt"]:
            query = query.filter(Measurements.startedAt >= f["startedAt"])
        if "elapsed" in f and f["elapsed"]:
            query = query.filter(Measurements.elapsed >= f["elapsed"])
        if "method" in f and f["method"]:
            query = query.filter_by(method=f["method"])
        if "name" in f and f["name"]:
            query = query.filter_by(name=f["name"])

        query = query.order_by(getattr(getattr(Measurements, f["sort"][0]), f["sort"][1])())
        query = query.limit(f['limit']).offset(f['skip'])
        rows = query.all()
        return (Sqlachemy.jsonify_row(row) for row in rows)

    @staticmethod
    def jsonify_row(row):
        data = {
            "id": row.id,
            "startedAt": row.startedAt,
            "endedAt": row.endedAt,
            "elapsed": row.elapsed,
            "args": tuple(json.loads(row.args)),  # json -> list -> tuple
            "kwargs": json.loads(row.kwargs),
            "method": row.method,
            "context": json.loads(row.context),
            "name": row.name
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
        f = Sqlachemy.getFilters(kwds)
        session = sessionmaker(self.db)()
        query = session.query(
                    Measurements.method,
                    Measurements.name,
                    func.count(Measurements.id),
                    func.min(Measurements.elapsed),
                    func.max(Measurements.elapsed),
                    func.avg(Measurements.elapsed),
                )

        if "endedAt" in f and f["endedAt"]:
            query = query.filter(Measurements.endedAt <= f["endedAt"])
        if "startedAt" in f and f["startedAt"]:
            query = query.filter(Measurements.startedAt >= f["startedAt"])
        if "elapsed" in f and f["elapsed"]:
            query = query.filter(Measurements.elapsed >= f["elapsed"])
        if "method" in f and f["method"]:
            query = query.filter_by(method=f["method"])
        if "name" in f and f["name"]:
            query = query.filter_by(name=f["name"])

        query = query.group_by(Measurements.method, Measurements.name)
        rows = query.all()

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

    def __exit__(self, exc_type, exc_value, traceback):
        return self.db
