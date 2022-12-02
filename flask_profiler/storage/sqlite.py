import json
import sqlite3
import threading
from datetime import datetime
from typing import Dict, List, Tuple

from .base import FilterQuery, Measurement, Record, RequestMetadata, Summary


def formatDate(timestamp, dateFormat):
    return datetime.fromtimestamp(timestamp).strftime(dateFormat)


class Sqlite:
    def __init__(self, sqlite_file: str, table_name: str) -> None:
        self.sqlite_file = sqlite_file
        self.table_name = table_name
        self.startedAt_head = "startedAt"  # name of the column
        self.endedAt_head = "endedAt"  # name of the column
        self.elapsed_head = "elapsed"  # name of the column
        self.method_head = "method"
        self.args_head = "args"
        self.kwargs_head = "kwargs"
        self.name_head = "name"
        self.context_head = "context"

        self.connection = sqlite3.connect(self.sqlite_file, check_same_thread=False)
        self.cursor = self.connection.cursor()

        self.lock = threading.Lock()
        try:
            self.create_database()
        except sqlite3.OperationalError as e:
            if "already exists" not in str(e):
                raise e

    def create_database(self) -> None:
        with self.lock:
            sql = """CREATE TABLE {table_name}
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
            """.format(
                table_name=self.table_name,
                startedAt=self.startedAt_head,
                endedAt=self.endedAt_head,
                elapsed=self.elapsed_head,
                args=self.args_head,
                kwargs=self.kwargs_head,
                method=self.method_head,
                context=self.context_head,
                name=self.name_head,
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
                table_name=self.table_name,
            )
            self.cursor.execute(sql)

            self.connection.commit()

    def insert(self, measurement: Measurement) -> None:
        endedAt = measurement.endedAt
        startedAt = measurement.startedAt
        elapsed = measurement.elapsed
        args = json.dumps(list(measurement.args))
        kwargs = json.dumps(measurement.kwargs)
        context = json.dumps(measurement.context.serialize_to_json())
        method = measurement.method
        name = measurement.name

        sql = """INSERT INTO {0} VALUES (
            null, ?, ?, ?, ?,?, ?, ?, ?)""".format(
            self.table_name
        )

        with self.lock:
            self.cursor.execute(
                sql, (startedAt, endedAt, elapsed, args, kwargs, method, context, name)
            )

            self.connection.commit()

    def getTimeseries(
        self, startedAt: float, endedAt: float, interval: str
    ) -> Dict[Tuple[datetime, str], int]:
        if interval == "daily":
            interval_seconds = 3600 * 24  # daily
            dateFormat = "%Y-%m-%d"
        else:
            interval_seconds = 3600  # hourly
            dateFormat = "%Y-%m-%d %H"
        with self.lock:
            sql = """SELECT startedAt, count(id) as count
                FROM "{table_name}"
                WHERE endedAt<=:endedAt AND startedAt>=:startedAt
                group by strftime(:dateFormat, datetime(startedAt, 'unixepoch'))
                order by startedAt asc
                """.format(
                table_name=self.table_name
            )
            self.cursor.execute(
                sql, dict(endedAt=endedAt, startedAt=startedAt, dateFormat=dateFormat)
            )
            rows = self.cursor.fetchall()
        series = {}
        for i in range(int(startedAt), int(endedAt) + 1, interval_seconds):
            series[formatDate(i, dateFormat)] = 0
        for row in rows:
            series[formatDate(row[0], dateFormat)] = row[1]
        return series

    def getMethodDistribution(self, startedAt: float, endedAt: float) -> Dict[str, int]:
        with self.lock:
            sql = """SELECT
                    method, count(id) as count
                FROM "{table_name}"
                where endedAt<=:endedAt AND startedAt>=:startedAt
                group by method
                """.format(
                table_name=self.table_name
            )

            self.cursor.execute(sql, dict(endedAt=endedAt, startedAt=startedAt))
            rows = self.cursor.fetchall()
        results = {}
        for row in rows:
            results[row[0]] = row[1]
        return results

    def filter(self, criteria: FilterQuery) -> List[Record]:
        conditions = "WHERE 1=1"

        if criteria.endedAt:
            conditions = conditions + " AND endedAt <= :endedAt"
        if criteria.startedAt:
            conditions = conditions + " AND startedAt >= :startedAt"
        if criteria.elapsed:
            conditions = conditions + " AND elapsed >= :elapsed"
        if criteria.method:
            conditions = conditions + " AND method = :method"
        if criteria.name:
            conditions = conditions + " AND name = :name"

        with self.lock:
            sql = """SELECT * FROM "{table_name}" {conditions}
            order by {sort_field} {sort_direction}
            limit :limit OFFSET :offset """.format(
                table_name=self.table_name,
                conditions=conditions,
                sort_field=criteria.sort[0],
                sort_direction=criteria.sort[1],
            )

            self.cursor.execute(
                sql,
                dict(
                    endedAt=criteria.endedAt.timestamp() if criteria.endedAt else None,
                    startedAt=criteria.startedAt.timestamp()
                    if criteria.startedAt
                    else None,
                    elapsed=criteria.elapsed,
                    method=criteria.method,
                    name=criteria.name,
                    offset=criteria.skip,
                    limit=criteria.limit,
                ),
            )
            rows = self.cursor.fetchall()
        return [self._row_to_record(row) for row in rows]

    def get(self, measurement_id: int) -> Record:
        with self.lock:
            self.cursor.execute(
                'SELECT * FROM "{table_name}" WHERE ID = :id'.format(
                    table_name=self.table_name,
                ),
                dict(id=measurement_id),
            )
            rows = self.cursor.fetchall()
        record = rows[0]
        return self._row_to_record(record)

    def truncate(self) -> bool:
        with self.lock:
            self.cursor.execute("DELETE FROM {0}".format(self.table_name))
            self.connection.commit()
        # Making the api match with mongo collection, this function must return
        # True or False based on success of this delete operation
        return True if self.cursor.rowcount else False

    def delete(self, measuremt_id: int) -> None:
        with self.lock:
            self.cursor.execute(
                'DELETE FROM "{table_name}" WHERE ID = :id'.format(
                    table_name=self.table_name,
                ),
                dict(id=measuremt_id),
            )
            return self.connection.commit()

    def _row_to_record(self, row) -> Record:
        raw_context = json.loads(row[7])
        context = RequestMetadata(**raw_context)
        return Record(
            id=row[0],
            startedAt=row[1],
            endedAt=row[2],
            elapsed=row[3],
            args=json.loads(row[4]),
            kwargs=json.loads(row[5]),
            method=row[6],
            context=context,
            name=row[8],
        )

    def getSummary(self, criteria: FilterQuery) -> List[Summary]:
        conditions = "WHERE 1=1 and "
        if criteria.startedAt:
            conditions = conditions + "startedAt>={0} AND ".format(
                criteria.startedAt.timestamp()
            )
        if criteria.endedAt:
            conditions = conditions + "endedAt<={0} AND ".format(
                criteria.endedAt.timestamp()
            )
        if criteria.elapsed:
            conditions = conditions + "elapsed>={0} AND".format(criteria.elapsed)
        conditions = conditions.rstrip(" AND")
        with self.lock:
            sql = """SELECT
                    method, name,
                    count(id) as count,
                    min(elapsed) as minElapsed,
                    max(elapsed) as maxElapsed,
                    avg(elapsed) as avgElapsed
                FROM "{table_name}" {conditions}
                group by method, name
                order by {sort_field} {sort_direction}
                """.format(
                table_name=self.table_name,
                conditions=conditions,
                sort_field=criteria.sort[0],
                sort_direction=criteria.sort[1],
            )
            self.cursor.execute(sql)
            return [
                Summary(
                    method=row[0],
                    name=row[1],
                    count=row[2],
                    min_elapsed=row[3],
                    max_elapsed=row[4],
                    avg_elapsed=row[5],
                )
                for row in self.cursor.fetchall()
            ]

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        return self.connection.close()
