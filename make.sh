#!/bin/bash

pyinstaller --noconsole --icon "app.ico" --add-data "app.ico;." --onefile vtracer-gui.py
