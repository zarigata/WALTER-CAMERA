@echo off
setlocal ENABLEDELAYEDEXPANSION
pushd %~dp0

set FAILED=0
python -m interactive_video_booth.main --stage 0
if NOT %ERRORLEVEL%==0 set FAILED=1
python -m interactive_video_booth.main --stage 1
if NOT %ERRORLEVEL%==0 set FAILED=1

if %FAILED%==0 (
  echo SMOKE TESTS: STAGE0 OK, STAGE1 OK -> PASS
  set EXITCODE=0
) else (
  echo SMOKE TESTS: FAIL
  set EXITCODE=1
)

popd
exit /b %EXITCODE%
