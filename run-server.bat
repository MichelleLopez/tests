@echo off
rem Batchfile for running Django server in Windows


rem Check help parameter
IF [%1]==[/?] GOTO :help

rem Check parameters
set arg1=%1
set arg2=%2

IF [%1]==[] (
    set arg1=127.0.0.1
)

IF [%2]==[] (
    set arg2=8000
)

rem Initiate django server
python manage.py runserver %arg1%:%arg2%
GOTO end

:help
ECHO usage: run.bat [IPADDR] [PORT]
ECHO.

:end