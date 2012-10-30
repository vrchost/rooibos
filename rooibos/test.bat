@setlocal
@set ROOIBOS_ADDITIONAL_SETTINGS=settings_test
@set apps=%*
@if "%apps%" == "" set apps=access converters data federatedsearch artstor presentation statistics storage userprofile util viewers workers
manage.py test %apps%
@endlocal
