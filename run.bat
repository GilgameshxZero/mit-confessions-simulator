@echo off
call activate mcs
:loop
python post.py
timeout /t 7200 /nobreak
goto loop
