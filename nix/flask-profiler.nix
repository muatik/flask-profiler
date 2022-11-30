{ buildPythonPackage, simplejson, flask-httpauth, flask, sqlalchemy
, flask-testing, pytestCheckHook, setuptools, pymongo }:
buildPythonPackage rec {
  pname = "flask_profiler";
  version = "master";
  src = ../.;
  buildInputs = [ setuptools ];
  propagatedBuildInputs = [ simplejson flask-httpauth flask ];
  checkInputs = [ sqlalchemy flask-testing pytestCheckHook ];
  format = "pyproject";
  passthru.optional-dependencies = {
    mongodb = [ pymongo ];
    sqlalchemy = [ sqlalchemy ];
  };
}
