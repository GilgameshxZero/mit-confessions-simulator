@echo off
call activate mcs
:loop
python post.py
timeout /t 3600 /nobreak
goto loop
