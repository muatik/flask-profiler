{ buildPythonPackage, simplejson, flask-httpauth, flask
, sqlalchemy, flask-testing, pytestCheckHook }:
buildPythonPackage rec {
  pname = "flask_profiler";
  version = "master";
  src = ../.;
  propagatedBuildInputs = [ simplejson flask-httpauth flask ];
  checkInputs = [ sqlalchemy flask-testing pytestCheckHook ];
}
