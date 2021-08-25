@echo off

:: Check for Python Installation
echo verifying if python 3 is installed
python --version 3>NUL
if errorlevel 1 goto errorNoPython

:: Reaching here means Python is installed.
:: Execute stuff...
echo installing python dependencies
py -3 --version
py -3 -m pip install --upgrade pip
py -3 -m pip install pyyaml
py -3 -m pip install numpy
echo done
pause

:: Once done, exit the batch file -- skips executing the errorNoPython section
goto:eof

:errorNoPython
echo.
echo error^: Python 3 not installed
"C:\Program Files\used\systems\innoventiq\accumanager\required\excutables\python-3.7.3-amd64.exe"
pause