@echo off
call activate mcs
:loop
python post.py
timeout 3600
goto loop
