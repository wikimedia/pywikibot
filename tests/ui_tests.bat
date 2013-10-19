@echo off
set PYTHONPATH=%~dp0..;%~dp0../externals
set PYWIKIBOT2_DIR=%~dp0..
"%~dp0ui_tests.py"
