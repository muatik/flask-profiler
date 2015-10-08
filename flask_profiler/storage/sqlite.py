import sqlite3
import json
from base import BaseStorage

class Sqlite(BaseStorage):
    """docstring for Sqlite"""
    def __init__(self, config=None):
        super(Sqlite, self).__init__()
        self.config = config
        self.sqlite_file = "flask_profiler.sqlite"
        self.table_name = 'PROFILER'  # name of the table to be created

        if hasattr(self.config, "SQLITE_FILE"):
            self.sqlite_file = self.config.SQLITE_FILE
        if hasattr(self.config, "TABLE_NAME"):
            self.table_name = self.config.TABLE_NAME

        self.startedAt_head = 'startedAt' # name of the column
        self.endedAt_head = 'endedAt' # name of the column
        self.elapsed_head = 'elapsed' # name of the column
        self.method_head = 'method'
        self.url_head = 'url' # name of the column
        self.args_head = 'args'
        self.form_head = 'form'
        self.body_head = 'body'
        self.headers_head = 'headers'
        self.name_head = 'name'

        self.connection = sqlite3.connect(self.sqlite_file)
        self.cursor = self.connection.cursor()
        try:
            self.create_database()
        except Exception, e:
            print e.message

    def __enter__(self):
        return self

    def create_database(self):
        self.cursor.execute(
        '''CREATE TABLE {table_name}
        (
        ID Integer PRIMARY KEY AUTOINCREMENT,
        {startedAt} TEXT,
        {endedAt} TEXT,
        {elapsed} REAL,
        {method} TEXT,
        {url} TEXT,
        {form} TEXT,
        {body} TEXT,
        {headers} TEXT,
        {name} TEXT
        )
        '''.format(
            table_name= self.table_name,
            startedAt= self.startedAt_head,
            endedAt= self.endedAt_head,
            elapsed= self.elapsed_head,
            method= self.method_head,
            url= self.url_head,
            form=self.form_head,
            body=self.body_head,
            headers=self.headers_head,
            name=self.name_head
            )
        )
        self.connection.commit()

    def insert(self, kwargs):
        endedAt = kwargs.get('endedAt', None)
        startedAt = kwargs.get('startedAt', None)
        elapsed = kwargs.get('elapsed', None)
        context = kwargs.get('context', {})
        method = kwargs.get('method', None)
        name = kwargs.get('name', None)
        url = context.get('url', None)
        form = context.get('form', None)
        body = context.get('body', None)
        headers = context.get('headers', None)


        f_startedAt = startedAt.strftime("%Y-%m-%d %H:%M:%S")
        f_endedAt = endedAt.strftime("%Y-%m-%d %H:%M:%S")
        f_context  = json.dumps(context)
        self.cursor.execute(
        '''INSERT INTO "{table_name}" VALUES
        ( {id}, "{startedAt}", "{endedAt}", {elapsed}, "{method}",
         "{url}", "{form}", "{body}", "{headers}", "{name}")'''.format(
            id="null",
            table_name= self.table_name,
            startedAt= f_startedAt,
            endedAt= f_endedAt,
            elapsed= elapsed,
            method= method,
            url= url,
            form=form,
            body=body,
            headers=headers,
            name=name))
        self.connection.commit()


    def filter(self, kwargs={}):
        # Find Operation
        endedAt = kwargs.get('endedAt', None)
        startedAt = kwargs.get('startedAt', None)
        elapsed = kwargs.get('elapsed', None)
        method = kwargs.get('method', None)
        name = kwargs.get('name', None)
        conditions = ""
        if any(kwargs[k] for k in kwargs):
            conditions = "WHERE "

        if endedAt:
            f_endedAt = endedAt.strftime("%Y-%m-%d %H:%M:%S")
            conditions = conditions + "`endedAt` <={} ".format(f_endedAt)
        if startedAt:
            f_startedAt = startedAt.strftime("%Y-%m-%d %H:%M:%S")
            conditions = conditions + "`startedAt` >={} ".format(f_startedAt)
        if elapsed:
            conditions = conditions + "`elapsed` >={} ".format(elapsed)
        if method:
            conditions = conditions + "`method` ={} ".format(method)
        if name:
            conditions = conditions + "`name` ={} ".format(name)

        self.cursor.execute(
            'SELECT * FROM "{table_name}" {conditions}'.format(
                table_name=self.table_name,
                conditions=conditions
                )
        )
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
            "method": row[4],
            "context": {
                "url": row[5],
                "form": row[6],
                "body": row[7],
                "headers": row[8]
            },
            "name": row[9]
        }
        return data

    def getSummary(self, kwargs={}):
        endedAt = kwargs.get('endedAt', None)
        startedAt = kwargs.get('startedAt', None)
        elapsed = kwargs.get('elapsed', None)

        conditions = ""
        if any(kwargs[k] for k in kwargs):
            conditions = "WHERE "

        if endedAt:
            f_endedAt = endedAt.strftime("%Y-%m-%d %H:%M:%S")
            conditions = conditions + "endedAt<={} ".format(f_endedAt)
        if startedAt:
            f_startedAt = startedAt.strftime("%Y-%m-%d %H:%M:%S")
            conditions = conditions + "startedAt>={} ".format(f_startedAt)
        if elapsed:
            conditions = conditions + "elapsed>={}".format(elapsed)

        self.cursor.execute(
            'SELECT * FROM "{table_name}" {conditions}'.format(
                table_name=self.table_name,
                conditions=conditions
                )
        )
        rows = self.cursor.fetchall()
        return self.group_by(rows)

    def group_by(self, rows):
        result = {}
        for row in rows:
            data = self.jsonify_row(row)
            key = data['name'] + data['method']
            if not key in result:
                result[key] = [data]
            else:
                result[key].append(data)
        for r in result:
            space = result[r]
            count = len(space)
            elapsed_data = [i['elapsed'] for i in space]
            method = space[0]['method']
            name = space[0]['name']
            if not elapsed_data:
                continue
            min_v = min(elapsed_data)
            max_v = max(elapsed_data)
            average = sum(elapsed_data) / len(elapsed_data)
            result[r] = {
                "count": count,
                "min": min_v,
                "max": max_v,
                "avg": average,
                "method": method,
                "name": name
            }
        return result.values()

    def __exit__(self, exc_type, exc_value, traceback):
        return self.connection.close()

