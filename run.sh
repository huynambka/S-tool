#!/bin/bash
venv/bin/python3.11 src/main.py --url 'http://127.0.0.1:1337/addContact' --params '{"firstName":"Shiba","lastName":"Jutsu","description":"Some","country":"Vietnam"}' --method POST

