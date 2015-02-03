@echo off

REM The windows service recovery adds a command-line switch
REM /fail=%1% to the command, where %1% is the number of failures.
REM This is parsed by the batch file as two separate args, so the
REM number of failures comes in as %2

REM If the number of failures is >= 3, we don't restart.  Just notify
REM a failure.

IF %2 GEQ 3 GOTO failure

:restart
REM ## Restart workers and send notification
net start "MDID Workers"
python d:\mdid\jmutools\workers\notify_workers_restart.py
goto end

:failure
REM ## Don't restart workers, just send failure notification
python d:\mdid\jmutools\workers\notify_workers_failure.py

:end