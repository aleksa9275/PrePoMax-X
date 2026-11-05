@echo off
rem PrePoMax is deployed portable - there is no installer, so the Visual C++ runtime
rem cannot be assumed present on the target machine and has to ship next to the exe.
rem The UCRT (api-ms-win-crt-*.dll) is part of Windows 10/11 and is deliberately not copied.
rem
rem   msvcp140.dll / vcruntime140.dll / vcruntime140_1.dll
rem       imported by NetGenMesher.exe, nglib.dll and the OpenCASCADE modules
rem   vcomp140.dll   OpenMP runtime, imported by FreeImage.dll
rem   msvcr100.dll   Visual C++ 2010 runtime, imported by the prebuilt pthreadVC2.dll
rem
rem The dlls are vendored in redist\ next to this script rather than taken from the build machine's Visual
rem Studio, so the deliverable is pinned and reproducible - the same reason
rem opencascade-8.0.1\bin and the pthreads-win32 prebuilt are vendored in this solution.
setlocal
set "ROOT=%~1"
set "DST=%~2"
if not "%ROOT:~-1%"=="\" set "ROOT=%ROOT%\"
if not exist "%DST%" mkdir "%DST%"
for %%f in (
  msvcp140.dll
  vcruntime140.dll
  vcruntime140_1.dll
  vcomp140.dll
  msvcr100.dll
) do xcopy /D /Y /I "%ROOT%redist\%%f" "%DST%" >nul
endlocal
