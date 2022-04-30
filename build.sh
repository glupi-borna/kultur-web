#!/bin/bash

BASEDIR="$(dirname "${BASH_SOURCE[0]}")"
BASEDIR="$(realpath "$BASEDIR")"

cd "$BASEDIR/posts"
python3.9 ./generate.py ./*
cd "$BASEDIR"
python3.9 ./inject.py
