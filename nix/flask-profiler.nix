{ buildPythonPackage, simplejson, flask-httpauth, flask, sqlalchemy
, flask-testing, pytestCheckHook, setuptools, pymongo }:
buildPythonPackage rec {
  pname = "flask_profiler";
  version = "master";
  src = ../.;
  buildInputs = [ setuptools ];
  propagatedBuildInputs = [ flask-httpauth flask ];
  checkInputs = [ flask-testing pytestCheckHook ];
  format = "pyproject";
}
