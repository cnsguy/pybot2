#!/bin/sh
black main.py core/* modules/*
mypy main.py && exec python3 main.py config.json
