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
            overlays = [ self.overlays.default ];
          };
        in {
          packages = { default = pkgs.python3.pkgs.flask-profiler; };
          devShells.default = pkgs.mkShell {
            packages = with pkgs.python3.pkgs;
              [ black coverage flake8 isort mypy twine virtualenv ]
              ++ flask-profiler.optional-dependencies.mongodb
              ++ flask-profiler.optional-dependencies.sqlalchemy;
            inputsFrom = [ pkgs.python3.pkgs.flask-profiler ];
          };
          checks = {
            black-check = pkgs.runCommand "black-check" { } ''
              cd ${self}
              ${pkgs.python3.pkgs.black}/bin/black --check .
              mkdir $out
            '';
            isort-check = pkgs.runCommand "isort-check" { } ''
              cd ${self}
              ${pkgs.python3.pkgs.isort}/bin/isort --check .
              mkdir $out
            '';
            flake8-check = pkgs.runCommand "flake8-check" { } ''
              cd ${self}
              ${pkgs.python3.pkgs.flake8}/bin/flake8
              mkdir $out
            '';
          };
        });
      supportedSystems = flake-utils.lib.defaultSystems;
      systemIndependent = {
        overlays.default = final: prev: {
          pythonPackagesExtensions = prev.pythonPackagesExtensions
            ++ [ (import nix/pythonPackages.nix) ];
        };
      };
    in systemDependent // systemIndependent;
}
