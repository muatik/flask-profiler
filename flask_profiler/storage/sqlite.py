import sqlite3
import datetime
import json

class Sqlite(BaseStorage):
    """docstring for Sqlite"""
    def __init__(self):
        super(Sqlite, self).__init__()
        sqlite_file = 'flask_profiler.sqlite'    # name of the sqlite database file
        self.table_name = 'PORFILER'  # name of the table to be created
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
        self.conn = sqlite3.connect(sqlite_file)
        self.c = self.conn.cursor()
        try:
            create_database()
        except:
            pass



    def create_database(self):
        c.execute(
        '''CREATE TABLE {table_name}
        (
        {startedAt} TEXT,
        {endedAt} TEXT,
        {elapsed} REAL,
        {method} TEXT,
        {context} TEXT,
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
            context= self.context_head,
            url= self.url_head,
            form=self.form_head,
            body=self.body_head,
            headers=self.headers_head,
            name=self.name_head
            )
        )
        conn.commit()

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
        self.c.execute(
        '''INSERT INTO "{table_name}" VALUES
        ("{startedAt}", "{endedAt}", {elapsed}, "{method}" "{context}",
         "{url}", "{form}", "{body}", "{headers}", "{name}")'''.format(
            table_name= table_name,
            startedAt= f_startedAt,
            endedAt= f_endedAt,
            elapsed= self.elapsed_head,
            method= self.method_head,
            context= self.context_head,
            url= self.url_head,
            form=self.form_head,
            body=self.body_head,
            headers=self.headers_head,
            name=self.name_head))
        self.conn.commit()


    def filter(self, kwargs):
        # Find Operation
        endedAt = kwargs.get('endedAt', None)
        startedAt = kwargs.get('startedAt', None)
        elapsed = kwargs.get('elapsed', None)
        method = kwargs.get('method', None)
        name = kwargs.get('name', None)

        f_startedAt = startedAt.strftime("%Y-%m-%d %H:%M:%S")
        f_endedAt = endedAt.strftime("%Y-%m-%d %H:%M:%S")

        conditions = ""
        if f_endedAt:
            conditions = conditions + "endedAt<={} ".format(f_endedAt)
        if f_startedAt:
            conditions = conditions + "startedAt>={} ".format(f_startedAt)
        if elapsed:
            conditions = conditions + "elapsed>={} ".format(elapsed)
        if method:
            conditions = conditions + "method={} ".format(method)
        if name:
            conditions = conditions + "name={} ".format(name)

        self.c.execute(
            'SELECT * FROM "{table_name}" WHERE {conditions}'.format(
                table_name=table_name,
                conditions=conditions
                )
        )
        rows = self.c.fetchall()
        for row in rows:
            print row

    def get(self, measurementId):
        self.c.execute(
            'SELECT * FROM "{table_name}" WHERE ID={measurementId}'.format(
                table_name=table_name,
                measurementId=measurementId
                )
        )
        rows = self.c.fetchall()
        for row in rows:
            print row

    def getSummary(self, kwargs):
        endedAt = kwargs.get('endedAt', None)
        startedAt = kwargs.get('startedAt', None)
        elapsed = kwargs.get('elapsed', None)

        f_startedAt = startedAt.strftime("%Y-%m-%d %H:%M:%S")
        f_endedAt = endedAt.strftime("%Y-%m-%d %H:%M:%S")

        conditions = ""
        if f_endedAt:
            conditions = conditions + "endedAt<={} ".format(f_endedAt)
        if f_startedAt:
            conditions = conditions + "startedAt>={} ".format(f_startedAt)
        if elapsed:
            conditions = conditions + "elapsed>={}".format(elapsed)

        c.execute(
            'SELECT * FROM "{table_name}" WHERE {conditions}'.format(
                table_name=table_name,
                conditions=conditions
                )
        )
        rows = self.c.fetchall()
        self.group_by(rows)

    def group_by(self, rows):
        result = {}
        for row in rows:
            print row[3], row[5]





c.close()