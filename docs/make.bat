@ECHO OFF

pushd %~dp0

REM Command file for Sphinx documentation

if "%SPHINXBUILD%" == "" (
	set SPHINXBUILD=sphinx-build
)
set SOURCEDIR=.
set BUILDDIR=_build
set SPHINXPROJ=Pywikibot
set SPHINXOPTS=-j auto

if "%1" == "" goto help
if "%1" == "help" goto help

if "%2" == "" goto notheme
set SPHINXOPTS=%SPHINXOPTS% -D "html_theme=%2"
:notheme

%SPHINXBUILD% >NUL 2>NUL
if errorlevel 9009 (
	echo.
	echo.The 'sphinx-build' command was not found. Make sure you have Sphinx
	echo.installed, then set the SPHINXBUILD environment variable to point
	echo.to the full path of the 'sphinx-build' executable. Alternatively you
	echo.may add the Sphinx directory to PATH.
	echo.
	echo.If you don't have Sphinx installed, grab it from
	echo.http://sphinx-doc.org/
	exit /b 1
)

set STARTTIME=%TIME:~0,8%
%SPHINXBUILD% -M %1 %SOURCEDIR% %BUILDDIR% %SPHINXOPTS%
set ENDTIME=%TIME:~0,8%

echo Start:   %STARTTIME%
echo End:     %ENDTIME%

rem calculate elapsed time, code modified from
rem https://stackoverflow.com/questions/4487100/how-can-i-use-a-windows-batch-file-to-measure-the-performance-of-console-applica

rem convert STARTTIME and ENDTIME to seconds
set /A STARTTIME=(1%STARTTIME:~0,2%-100)*3600 + (1%STARTTIME:~3,2%-100)*60 + (1%STARTTIME:~6,2%-100)
set /A ENDTIME=(1%ENDTIME:~0,2%-100)*3600 + (1%ENDTIME:~3,2%-100)*60 + (1%ENDTIME:~6,2%-100)

rem calculating the duratyion is easy
set /A DURATION=%ENDTIME%-%STARTTIME%

rem we might have measured the time inbetween days
if %ENDTIME% LSS %STARTTIME% set set /A DURATION=%STARTTIME%-%ENDTIME%

rem now break the seconds down to hors, minutes, seconds
set /A DURATIONH=%DURATION% / 3600
set /A DURATIONM=(%DURATION% - %DURATIONH%*3600) / 60
set /A DURATIONS=(%DURATION% - %DURATIONH%*3600 - %DURATIONM%*60)

rem some formatting
if %DURATIONH% LSS 10 set DURATIONH=0%DURATIONH%
if %DURATIONM% LSS 10 set DURATIONM=0%DURATIONM%
if %DURATIONS% LSS 10 set DURATIONS=0%DURATIONS%

echo Elapsed: %DURATIONH%:%DURATIONM%:%DURATIONS%

goto end

:help
echo.
echo make has the following options:
echo     make ^<target^> [^<theme^>]
echo     make html basic
echo.
%SPHINXBUILD% -M help %SOURCEDIR% %BUILDDIR%

:end
popd
