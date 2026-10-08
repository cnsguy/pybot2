#!/bin/sh
black main.py core/* modules/*
source venv/bin/activate
mypy main.py && exec python3 main.py "$@"
