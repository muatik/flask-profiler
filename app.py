# -*- coding: utf8 -*-
from flask import Flask, render_template
from flask_profiler import flask_profiler

app = Flask(__name__)
app.config["DEBUG"] = True
app.config["flask_profiler"] = {}
# app.config.from_object(config)


@app.route('/peope/john', methods=['GET'])
def sayHello():
    return "Hi, I am John"


@app.route('/peope/john', methods=['PUT'])
def updatePerson():
    return "PUT into John? What?"


@app.route('/boss/john', methods=['GET'])
def bossSaysHello():
    return "I am john, the boss one."


@app.route('/boss/john', methods=['PUT'])
def putBoss():
    return "You are allowed to put smth into the boss."


@app.route('/raise/exception', methods=['GET'])
def raiseException():
    raise Exception("this is an exception")

flask_profiler.init_app(app)
if __name__ == '__main__':
    app.run(host="192.168.34.15")
