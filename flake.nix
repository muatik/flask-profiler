{
  description = "flask-profiler";

  inputs = {
    flake-utils.url = "github:numtide/flake-utils";
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
  };

  outputs = { self, nixpkgs, flake-utils, ... }:
    let
      systemDependent = flake-utils.lib.eachSystem supportedSystems (system:
        let
          pkgs = import nixpkgs {
            inherit system;
          };
        in {
          devShells.default = pkgs.mkShell {
            packages = with pkgs.python3.pkgs; [
                black
                coverage
                flake8
                flask
                flask-httpauth
                flask-testing
                isort
                mypy
                pytest
                simplejson
                sqlalchemy
                twine
                virtualenv
              ];
          };
        });
      supportedSystems = flake-utils.lib.defaultSystems;
    in systemDependent;
}
