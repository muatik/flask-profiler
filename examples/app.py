# your app.py
from flask import Flask
import flask_profiler

app = Flask(__name__)
app.config["DEBUG"] = True

# You need to declare necessary configuration to initialize
# flask-profiler as follows:
app.config["flask_profiler"] = {
    "verbose": True,
    "enabled": app.config["DEBUG"],
    "storage": {
        "engine": "sqlite"
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
# app as an argument to flask-provider.
# All the endpoints declared so far will be tracked by flask-provider.
flask_profiler.init_app(app)


# endpoint declarations after flask_profiler.init_app() will be
# hidden to flask_profider.
@app.route('/doSomething', methods=['GET'])
def doSomething():
    return "flask-provider will not measure this."


# But in case you want an endpoint to be measured by flask-provider,
# you can specify this explicitly by using profile() decorator
@app.route('/doSomething', methods=['GET'])
@flask_profiler.profile()
def doSomethingImportant():
    return "flask-provider will measure this request."

if __name__ == '__main__':
    app.run(host="127.0.0.1", port=5000)
