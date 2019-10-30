@echo off
:loop
timeout /t 7200 /nobreak
call activate mcs
python post.py
call conda deactivate
goto loop
