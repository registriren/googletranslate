#!/bin/sh
./stop.sh
python3 googletranslate.py >> log.txt 2>&1 & echo $! >> log.pid
