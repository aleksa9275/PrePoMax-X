#!/usr/bin/env python3
"""Extract the original viewport color control points and color spaces verbatim."""
import argparse,hashlib,json,re
from pathlib import Path
h=Path(__file__).resolve().parent;p=argparse.ArgumentParser();p.add_argument('--check',action='store_true');a=p.parse_args()
import subprocess
# The interim Python renderer keeps the ActiViz-era vtkControl.cs of the 3.0.0 base until the original vtkControl
# runs on vtkNative (M1, D063); upstream moved this code to vtkNative/src/Geometry/vtkNativeColorSpectrum.cpp.
REFERENCE='eb6aff0c:vtkControl/vtkControl.cs'
raw=subprocess.run(['git','-C',str(h.parents[1]),'show',REFERENCE],check=True,capture_output=True).stdout;s=raw.decode('utf-8-sig');body=s[s.index('private vtkColorTransferFunction GetColorTransferFunction()'):];body=body[:body.index('double n = 0;')]
body=re.sub(r'//[^\n]*','',body);maps={}
for match in re.finditer(r'if \(_colorSpectrum.Type == vtkColorSpectrumType\.(\w+)\)\s*\{(.*?)\n            \}',body,re.S):
 name,block=match.groups();space=re.search(r'SetColorSpaceTo(\w+)\(',block).group(1)
 points=[[float(v.strip().replace('b','0')) for v in row.split(',')] for row in re.findall(r'rgbPoints.Add\(new double\[\] \{ (.*?) \}\)',block)]
 maps[name]={'space':space,'points':points}
assert len(maps)==14,len(maps)
text='# Generated from vtkControl/vtkControl.cs GetColorTransferFunction; root LICENSE.\n# Source SHA256 '+hashlib.sha256(s.encode()).hexdigest()+'\nCOLORMAPS = '+repr(maps)+'\n'
out=h/'original_colormaps.py'
if a.check:
 if out.read_text()!=text:raise SystemExit('Original colormaps are stale')
else:out.write_text(text)
