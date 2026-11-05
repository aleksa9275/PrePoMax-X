@echo off
rem Copies the complete OpenCASCADE DLL closure built for NetGenMesher.
rem The OCCT 8.0.1 bundle is configured from source with only the required toolkits,
rem so all 29 DLLs below belong in the portable deliverable. Optional FreeImage,
rem FFmpeg, FreeType, OpenVR and TBB dependencies are disabled in this build.
setlocal
set "SRC=%~1"
set "DST=%~2"
if not exist "%DST%" mkdir "%DST%"
for %%f in (
  TKBO.dll
  TKBRep.dll
  TKBool.dll
  TKCAF.dll
  TKCDF.dll
  TKDE.dll
  TKDEIGES.dll
  TKDESTEP.dll
  TKDESTL.dll
  TKFillet.dll
  TKG2d.dll
  TKG3d.dll
  TKGeomAlgo.dll
  TKGeomBase.dll
  TKHLR.dll
  TKLCAF.dll
  TKMath.dll
  TKMesh.dll
  TKMeshVS.dll
  TKOffset.dll
  TKPrim.dll
  TKService.dll
  TKShHealing.dll
  TKTopAlgo.dll
  TKV3d.dll
  TKVCAF.dll
  TKXCAF.dll
  TKXSBase.dll
  TKernel.dll
) do xcopy /D /Y /I "%SRC%\%%f" "%DST%" >nul
endlocal
