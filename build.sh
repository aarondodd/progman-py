#!/bin/bash
pyinstaller --noconfirm --clean --windowed --onefile --name progman --collect-all PyQt6 main.py
