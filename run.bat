@echo off
:loop
timeout /t 7200 /nobreak
call activate mit-confessions-simulator
python post.py
call conda deactivate
goto loop
