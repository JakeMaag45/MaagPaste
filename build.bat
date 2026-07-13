@echo off
echo Building MaagPaste...

echo Step 1: Installing dependencies...
pip install -r requirements.txt
pip install pyinstaller

echo Step 2: Cleaning previous builds...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
if exist *.spec del *.spec

echo Step 3: Building executable...
pyinstaller --onefile --windowed --name MaagPaste --add-data "icon.ico;." --icon icon.ico --hidden-import customtkinter --hidden-import pyperclip --hidden-import pystray --hidden-import keyboard --hidden-import PIL --hidden-import PIL.Image --hidden-import PIL.ImageDraw --hidden-import PIL.ImageGrab --hidden-import requests --collect-all customtkinter maagpaste.py

echo.
echo Build complete! Check the 'dist' folder for MaagPaste.exe
echo.
echo If the app doesn't work, try running debug_launch.bat to see errors
pause
