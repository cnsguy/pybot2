#!/bin/sh
. venv/bin/activate
black main.py core/* modules/*
mypy --explicit-package-bases --python-executable venv/bin/python . && exec python3 main.py "$@"
