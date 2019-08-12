@echo off
:loop
call activate mcs
python post.py
call conda deactivate
timeout /t 7200 /nobreak
goto loop
