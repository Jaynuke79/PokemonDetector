@echo off
REM Wrapper script to run poke.exe with arguments
REM Place this in the same directory as poke.exe for easy use

"%~dp0poke.exe" %*
