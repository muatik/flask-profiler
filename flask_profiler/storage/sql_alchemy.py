import json
import time
from datetime import datetime
from decimal import ROUND_UP, Decimal

from sqlalchemy import Column, Integer, Numeric, Text, create_engine, func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from .base import FilterQuery

Base = declarative_base()


def formatDate(timestamp, dateFormat):
    return datetime.fromtimestamp(timestamp).strftime(dateFormat)


class Measurements(Base):  # type: ignore
    __tablename__ = "flask_profiler_measurements"

    id = Column(Integer, primary_key=True)
    startedAt = Column(Numeric)
    endedAt = Column(Numeric)
    elapsed = Column(Numeric(10, 4))
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
            self.context,
        )


class Sqlalchemy:
    def __init__(self, db_url: str):
        self.db = create_engine(
            db_url,
            pool_pre_ping=True,
        )
        self.create_database()

    def create_database(self):
        Base.metadata.create_all(self.db)

    def insert(self, kwds):
        endedAt = int(kwds.get("endedAt", None))
        startedAt = int(kwds.get("startedAt", None))
        elapsed = Decimal(kwds.get("elapsed", None))
        if elapsed:
            elapsed = elapsed.quantize(Decimal(".0001"), rounding=ROUND_UP)
        args = json.dumps(list(kwds.get("args", ())))  # tuple -> list -> json
        kwargs = json.dumps(kwds.get("kwargs", ()))
        context = json.dumps(kwds.get("context", {}))
        method = kwds.get("method", None)
        name = kwds.get("name", None)

        session = sessionmaker(self.db)()
        session.add(
            Measurements(
                endedAt=endedAt,
                startedAt=startedAt,
                elapsed=elapsed,
                args=args,
                kwargs=kwargs,
                context=context,
                method=method,
                name=name,
            )
        )
        session.commit()

    @staticmethod
    def getFilters(kwargs):
        filters = {}
        filters["sort"] = kwargs.get("sort", "endedAt,desc").split(",")

        # because inserting and filtering may take place at the same moment,
        # a very little increment(0.5) is needed to find inserted
        # record by sql.
        filters["endedAt"] = float(kwargs.get("endedAt", time.time() + 0.5))
        filters["startedAt"] = float(
            kwargs.get("startedAt", time.time() - 3600 * 24 * 7)
        )

        filters["elapsed"] = kwargs.get("elapsed", None)
        filters["method"] = kwargs.get("method", None)
        filters["name"] = kwargs.get("name", None)
        filters["args"] = json.dumps(
            list(kwargs.get("args", ()))
        )  # tuple -> list -> json
        filters["kwargs"] = json.dumps(kwargs.get("kwargs", ()))
        filters["sort"] = kwargs.get("sort", "endedAt,desc").split(",")
        filters["skip"] = int(kwargs.get("skip", 0))
        filters["limit"] = int(kwargs.get("limit", 100))
        return filters

    def filter(self, criteria: FilterQuery):
        session = sessionmaker(self.db)()
        query = session.query(Measurements)
        if criteria.endedAt:
            query = query.filter(Measurements.endedAt <= criteria.endedAt.timestamp())
        if criteria.startedAt:
            query = query.filter(
                Measurements.startedAt >= criteria.startedAt.timestamp()
            )
        if criteria.elapsed:
            query = query.filter(Measurements.elapsed >= criteria.elapsed)
        if criteria.method:
            query = query.filter(Measurements.method == criteria.method)
        if criteria.name:
            query = query.filter(Measurements.name == criteria.name)
        if criteria.sort[1] == "desc":
            query = query.order_by(getattr(Measurements, criteria.sort[0]).desc())
        else:
            query = query.order_by(getattr(Measurements, criteria.sort[0]).asc())
        rows = query.limit(criteria.limit).offset(criteria.skip)
        return (Sqlalchemy.jsonify_row(row) for row in rows)

    @staticmethod
    def jsonify_row(row):
        data = {
            "id": row.id,
            "startedAt": row.startedAt,
            "endedAt": row.endedAt,
            "elapsed": row.elapsed,
            "method": row.method,
            "args": tuple(json.loads(row.args)),  # json -> list -> tuple
            "kwargs": json.loads(row.kwargs),
            "name": row.name,
            "context": json.loads(row.context),
        }
        return data

    def truncate(self):
        session = sessionmaker(self.db)()
        try:
            session.query(Measurements).delete()
            session.commit()
            return True
        except Exception:
            session.rollback()
            return False

    def delete(self, measurementId):
        session = sessionmaker(self.db)()
        try:
            session.query(Measurements).filter_by(id=measurementId).delete()
            session.commit()
            return True
        except Exception:
            session.rollback()
            return False

    def getSummary(self, kwds={}):
        filters = Sqlalchemy.getFilters(kwds)
        session = sessionmaker(self.db)()
        count = func.count(Measurements.id).label("count")
        min_elapsed = func.min(Measurements.elapsed).label("minElapsed")
        max_elapsed = func.max(Measurements.elapsed).label("maxElapsed")
        avg_elapsed = func.avg(Measurements.elapsed).label("avgElapsed")
        query = session.query(
            Measurements.method,
            Measurements.name,
            count,
            min_elapsed,
            max_elapsed,
            avg_elapsed,
        )

        if filters["startedAt"]:
            query = query.filter(Measurements.startedAt >= filters["startedAt"])
        if filters["endedAt"]:
            query = query.filter(Measurements.endedAt <= filters["endedAt"])
        if filters["elapsed"]:
            query = query.filter(Measurements.elapsed >= filters["elapsed"])

        query = query.group_by(Measurements.method, Measurements.name)
        if filters["sort"][1] == "desc":
            if filters["sort"][0] == "count":
                query = query.order_by(count.desc())
            elif filters["sort"][0] == "minElapsed":
                query = query.order_by(min_elapsed.desc())
            elif filters["sort"][0] == "maxElapsed":
                query = query.order_by(max_elapsed.desc())
            elif filters["sort"][0] == "avgElapsed":
                query = query.order_by(avg_elapsed.desc())
            else:
                query = query.order_by(getattr(Measurements, filters["sort"][0]).desc())
        else:
            if filters["sort"][0] == "count":
                query = query.order_by(count.asc())
            elif filters["sort"][0] == "minElapsed":
                query = query.order_by(min_elapsed.asc())
            elif filters["sort"][0] == "maxElapsed":
                query = query.order_by(max_elapsed.asc())
            elif filters["sort"][0] == "avgElapsed":
                query = query.order_by(avg_elapsed.asc())
            else:
                query = query.order_by(getattr(Measurements, filters["sort"][0]).asc())
        rows = query.all()

        result = []
        for r in rows:
            result.append(
                {
                    "method": r[0],
                    "name": r[1],
                    "count": r[2],
                    "minElapsed": r[3],
                    "maxElapsed": r[4],
                    "avgElapsed": r[5],
                }
            )
        return result

    def getTimeseries(self, kwds={}):
        filters = Sqlalchemy.getFilters(kwds)
        session = sessionmaker(self.db)()
        if kwds.get("interval", None) == "daily":
            interval = 3600 * 24  # daily
            dateFormat = "%Y-%m-%d"
        else:
            interval = 3600  # hourly
            dateFormat = "%Y-%m-%d %H"
        endedAt, startedAt = filters["endedAt"], filters["startedAt"]

        rows = (
            session.query(
                Measurements.startedAt,
            )
            .filter(
                Measurements.endedAt <= endedAt, Measurements.startedAt >= startedAt
            )
            .order_by(Measurements.startedAt.asc())
            .all()
        )

        rows = [datetime.utcfromtimestamp(row[0]).strftime(dateFormat) for row in rows]
        temp = set(rows)
        rows = [(time, rows.count(time)) for time in temp]
        series = {}

        for i in range(int(startedAt), int(endedAt) + 1, interval):
            series[formatDate(i, dateFormat)] = 0

        for row in rows:
            series[
                formatDate(
                    datetime.strptime(row[0], dateFormat).timestamp(), dateFormat
                )
            ] = row[1]
        return series

    def getMethodDistribution(self, kwds=None):
        if not kwds:
            kwds = {}
        f = Sqlalchemy.getFilters(kwds)
        session = sessionmaker(self.db)()
        endedAt, startedAt = f["endedAt"], f["startedAt"]

        rows = (
            session.query(Measurements.method, func.count(Measurements.id))
            .filter(
                Measurements.endedAt <= endedAt, Measurements.startedAt >= startedAt
            )
            .group_by(Measurements.method)
            .all()
        )

        results = {}
        for row in rows:
            results[row[0]] = row[1]
        return results

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        return self.db
