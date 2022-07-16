#!/bin/bash

BASEDIR="$(dirname "${BASH_SOURCE[0]}")"
BASEDIR="$(realpath "$BASEDIR")"

cd "$BASEDIR/posts"
python3.9 ./generate.py ./*
python3.9 ./newsgen.py
cd "$BASEDIR"
python3.9 ./inject.py
