import sqlite3
import json
from .base import BaseStorage
from datetime import datetime
from timeit import default_timer
import time
# from time import perf_counter


def formatDate(timestamp, dateFormat):
    return datetime.fromtimestamp(timestamp).strftime(dateFormat)


class Sqlite(BaseStorage):
    """docstring for Sqlite"""
    def __init__(self, config=None):
        super(Sqlite, self).__init__()
        self.config = config
        self.sqlite_file = self.config.get("FILE", "flask_profiler.sql")
        self.table_name = self.config.get("TABLE", "measurements")

        self.startedAt_head = 'startedAt'  # name of the column
        self.endedAt_head = 'endedAt'  # name of the column
        self.elapsed_head = 'elapsed'  # name of the column
        self.method_head = 'method'
        self.args_head = 'args'
        self.kwargs_head = 'kwargs'
        self.name_head = 'name'
        self.context_head = 'context'

        self.connection = sqlite3.connect(
            self.sqlite_file, check_same_thread=False)
        self.cursor = self.connection.cursor()
        try:
            self.create_database()
        except sqlite3.OperationalError as e:
            if "already exists" not in str(e):
                raise e

    def __enter__(self):
        return self

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

    def create_database(self):
        sql = '''CREATE TABLE {table_name}
            (
            ID Integer PRIMARY KEY AUTOINCREMENT,
            {startedAt} REAL,
            {endedAt} REAL,
            {elapsed} REAL,
            {args} TEXT,
            {kwargs} TEXT,
            {method} TEXT,
            {context} TEXT,
            {name} TEXT
            );
        '''.format(
                table_name=self.table_name,
                startedAt=self.startedAt_head,
                endedAt=self.endedAt_head,
                elapsed=self.elapsed_head,
                args=self.args_head,
                kwargs=self.kwargs_head,
                method=self.method_head,
                context=self.context_head,
                name=self.name_head
            )
        self.cursor.execute(sql)

        sql = """
        CREATE INDEX measurement_index ON {table_name}
            ({startedAt}, {endedAt}, {elapsed}, {name}, {method});
        """.format(
            startedAt=self.startedAt_head,
            endedAt=self.endedAt_head,
            elapsed=self.elapsed_head,
            name=self.name_head,
            method=self.method_head,
            table_name=self.table_name)
        self.cursor.execute(sql)

        self.connection.commit()

    def insert(self, kwds):
        endedAt = float(kwds.get('endedAt', None))
        startedAt = float(kwds.get('startedAt', None))
        elapsed = kwds.get('elapsed', None)
        args = json.dumps(list(kwds.get('args', ())))  # tuple -> list -> json
        kwargs = json.dumps(kwds.get('kwargs', ()))
        context = json.dumps(kwds.get('context', {}))
        method = kwds.get('method', None)
        name = kwds.get('name', None)

        sql = """INSERT INTO {} VALUES (
            null, ?, ?, ?, ?,?, ?, ?, ?)""".format(self.table_name)

        self.cursor.execute(sql, (
                startedAt,
                endedAt,
                elapsed,
                args,
                kwargs,
                method,
                context,
                name))

        self.connection.commit()

    def getTimeseries(self, kwds={}):
        filters = Sqlite.getFilters(kwds)

        if kwds.get('interval', None) == "daily":
            interval = 3600 * 24   # daily
            dateFormat = '%Y-%m-%d'
        else:
            interval = 3600  # hourly
            dateFormat = '%Y-%m-%d %H'

        endedAt, startedAt = filters["endedAt"], filters["startedAt"]

        conditions = "where endedAt<={} AND startedAt>={} ".format(
            endedAt, startedAt)

        sql = '''SELECT
                startedAt, count(id) as count
            FROM "{table_name}" {conditions}
            group by strftime("{dateFormat}", datetime(startedAt, 'unixepoch'))
            order by startedAt asc
            '''.format(
                table_name=self.table_name,
                dateFormat=dateFormat,
                conditions=conditions
                )

        self.cursor.execute(sql)
        rows = self.cursor.fetchall()

        series = {}
        for i in range(int(startedAt), int(endedAt) + 1, interval):
            series[formatDate(i, dateFormat)] = 0

        for row in rows:
            series[formatDate(row[0], dateFormat)] = row[1]
        return series

    def getMethodDistribution(self, kwds=None):
        if not kwds:
            kwds = {}
        f = Sqlite.getFilters(kwds)
        endedAt, startedAt = f["endedAt"], f["startedAt"]
        conditions = "where endedAt<={} AND startedAt>={} ".format(
            endedAt, startedAt)

        sql = '''SELECT
                method, count(id) as count
            FROM "{table_name}" {conditions}
            group by method
            '''.format(
                table_name=self.table_name,
                conditions=conditions
                )

        self.cursor.execute(sql)
        rows = self.cursor.fetchall()

        results = {}
        for row in rows:
            results[row[0]] = row[1]
        return results

    def filter(self, kwds={}):
        # Find Operation
        f = Sqlite.getFilters(kwds)

        conditions = "WHERE 1=1 AND "

        if f["endedAt"]:
            conditions = conditions + 'endedAt<={} AND '.format(f["endedAt"])
        if f["startedAt"]:
            conditions = conditions + 'startedAt>={} AND '.format(
                f["startedAt"])
        if f["elapsed"]:
            conditions = conditions + 'elapsed>={} AND '.format(f["elapsed"])
        if f["method"]:
            conditions = conditions + 'method="{}" AND '.format(f["method"])
        if f["name"]:
            conditions = conditions + 'name="{}" AND '.format(f["name"])

        conditions = conditions.rstrip(" AND")

        sql = '''SELECT * FROM "{table_name}" {conditions}
        order by {sort_field} {sort_direction}
        limit {limit} OFFSET {skip} '''.format(
            table_name=self.table_name,
            conditions=conditions,
            sort_field=f["sort"][0],
            sort_direction=f["sort"][1],
            limit=f['limit'],
            skip=f['skip']
        )

        self.cursor.execute(sql)
        rows = self.cursor.fetchall()
        return (self.jsonify_row(row) for row in rows)

    def get(self, measurementId):
        self.cursor.execute(
            'SELECT * FROM "{table_name}" WHERE ID={measurementId}'.format(
                table_name=self.table_name,
                measurementId=measurementId
                )
        )
        rows = self.cursor.fetchall()
        record = rows[0]
        return self.jsonify_row(record)

    def truncate(self):
        self.cursor.execute("DELETE FROM {}".format(self.table_name))
        self.connection.commit()
        # Making the api match with mongo collection, this function must return
        # True or False based on success of this delete operation
        return True if self.cursor.rowcount else False

    def delete(self, measurementId):
        self.cursor.execute(
            'DELETE FROM "{table_name}" WHERE ID={measurementId}'.format(
                table_name=self.table_name,
                measurementId=measurementId
                )
        )
        return self.connection.commit()

    def jsonify_row(self, row):
        data = {
            "id": row[0],
            "startedAt": row[1],
            "endedAt": row[2],
            "elapsed": row[3],
            "args": tuple(json.loads(row[4])),  # json -> list -> tuple
            "kwargs": json.loads(row[5]),
            "method": row[6],
            "context": json.loads(row[7]),
            "name": row[8]
        }

        return data

    def getSummary(self, kwds={}):
        filters = Sqlite.getFilters(kwds)

        conditions = "WHERE 1=1 and "

        if filters["startedAt"]:
            conditions = conditions + "startedAt>={} AND ".format(
                filters["startedAt"])
        if filters["endedAt"]:
            conditions = conditions + "endedAt<={} AND ".format(
                filters["endedAt"])
        if filters["elapsed"]:
            conditions = conditions + "elapsed>={} AND".format(
                filters["elapsed"])

        conditions = conditions.rstrip(" AND")

        sql = '''SELECT
                method, name,
                count(id) as count,
                min(elapsed) as minElapsed,
                max(elapsed) as maxElapsed,
                avg(elapsed) as avgElapsed
            FROM "{table_name}" {conditions}
            group by method, name
            order by {sort_field} {sort_direction}
            '''.format(
                table_name=self.table_name,
                conditions=conditions,
                sort_field=filters["sort"][0],
                sort_direction=filters["sort"][1]
                )

        self.cursor.execute(sql)
        rows = self.cursor.fetchall()

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
        return self.connection.close()
