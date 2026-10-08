#!/bin/sh
black main.py core/* modules/*
source venv/bin/activate
mypy --explicit-package-bases --python-executable venv/bin/python . && exec python3 main.py "$@"
