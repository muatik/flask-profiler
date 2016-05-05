# Flask-profiler

[![Build Status](https://travis-ci.org/muatik/flask-profiler.svg?branch=master)](https://travis-ci.org/muatik/flask-profiler)

##### Flask-profiler measures endpoints defined in your flask application; and provides you fine-grained report through a web interface.

It gives answer to these questions:
* Where are the bottlenecks in my application?
* Which endpoints are the slowest in my application?
* Which are the most frequently called endpoints?
* What causes my slow endpoints? In which context, with what args and kwargs are they slow?
* How much time did a specific request take?

In short, if you are curious about what your endpoints are doing and what requests they are receiving, give a try to flask-profiler.

With flask-profiler's web interface, you can monitor all your endpoints' performance and investigate endpoints and received requests by drilling down through filters.

## Screenshots
Dashboard view displays a summary.
![Alt text](/resources/dashboard_screen.png?raw=true "Dashboard view")

You can create filters to investigate certain type requests.
![Alt text](/resources/filtering_all_screen .png?raw=true "Filtering by endpoint")

![Alt text](/resources/filtering_method_screen.png?raw=true "Filtering by method")

You can see all the details of a request.
![Alt text](/resources/filtering_detail_screen.png?raw=true "Request detail")

## Quick Start
It is easy to understand flask-profiler going through an example. Let's dive in.

Install flask-profiler by pip.
```sh
pip install flask_profiler
```


Edit your code where you are creating Flask app.
```python
# your app.py
from flask import Flask
import flask_profiler

app = Flask(__name__)
app.config["DEBUG"] = True

# You need to declare necessary configuration to initialize
# flask-profiler as follows:
app.config["flask_profiler"] = {
    "enabled": app.config["DEBUG"],
    "storage": {
        "engine": "sqlite"
    },
    "basicAuth":{
        "enabled": True,
        "username": "admin",
        "password": "admin"
    }
}


@app.route('/product/<id>', methods=['GET'])
def getProduct(id):
    return "product id is " + str(id)


@app.route('/product/<id>', methods=['PUT'])
def updateProduct(id):
    return "product {} is being updated".format(id)


@app.route('/products', methods=['GET'])
def listProducts():
    return "suppose I send you product list..."

# In order to active flask-profiler, you have to pass flask
# app as an argument to flask-profiler.
# All the endpoints declared so far will be tracked by flask-profiler.
flask_profiler.init_app(app)


# endpoint declarations after flask_profiler.init_app() will be
# hidden to flask_profiler.
@app.route('/doSomething', methods=['GET'])
def doSomething():
    return "flask-profiler will not measure this."


# But in case you want an endpoint to be measured by flask-profiler,
# you can specify this explicitly by using profile() decorator
@app.route('/doSomething', methods=['GET'])
@flask_profiler.profile()
def doSomethingImportant():
    return "flask-profiler will measure this request."

if __name__ == '__main__':
    app.run(host="127.0.0.1", port=5000)


```

Now run your `app.py`
```
python app.py
```

And make some requests like:
```sh
curl http://127.0.0.1:5000/products
curl http://127.0.0.1:5000/product/123
curl -X PUT -d arg1=val1 http://127.0.0.1:5000/product/123
```

If everything is okay, Flask-profiler will measure these requests. You can see the result heading to http://127.0.0.1:5000/flask-profiler/ or get results as json http://127.0.0.1:5000/flask-profiler/api/measurements?sort=elapsed,desc

## Using with different database system
Currently **Sqlite** and **Mongodb** database systems are supported. However, it is easy to support other database systems. If you would like to have others, please go to contribution documentation. (It is really easy.)

### Sqlite
In order to use Sqlite, just specify it as the value of `storage.engine` directive as follows.

```json
app.config["flask_profiler"] = {
    "storage": {
        "engine": "sqlite",
    }
}
```

Below the other options are listed.

| Filter key   |      Description      |  Default |
|----------|-------------|------|
| storage.FILE | sqlite database file name | flask_profiler.sql|
| storage.TABLE | table name in which profiling data will reside | measurements |

### Mongodb
In order to use Mongodb, just specify it as the value of `storage.engine` directive as follows.

```json
app.config["flask_profiler"] = {
    "storage": {
        "engine": "mongodb",
    }
}
```

### Custom database engine
Specify engine as string module and class path.

```json
app.config["flask_profiler"] = {
    "storage": {
        "engine": "custom.project.flask_profiler.mysql.MysqlStorage",
        "MYSQL": "mysql://user:password@localhost/flask_profiler"
    }
}
```

The other options are listed below.

| Filter key   |      Description      |  Default
|----------|-------------|------
| storage.MONGO_URL | mongodb connection string | mongodb://localhost
| storage.DATABASE | database name | flask_profiler
| storage.COLLECTION | collection name | measurements


## Contributing

Contributions are welcome!

Review the [Contributing Guidelines](https://github.com/muatik/flask-profiler/wiki/Development) for details on how to:

* Submit issues
* Add solutions to existing challenges
* Add new challenges

## Authors
* [Musafa Atik](https://www.linkedin.com/in/muatik)
* Fatih Sucu
* [Safa Yasin Yildirim](https://www.linkedin.com/in/safayasinyildirim)

## License
MIT
