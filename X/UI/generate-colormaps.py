#!/usr/bin/env python3
"""Extract the original viewport color control points and color spaces verbatim."""
import argparse,hashlib,json,re
from pathlib import Path
h=Path(__file__).resolve().parent;p=argparse.ArgumentParser();p.add_argument('--check',action='store_true');a=p.parse_args()
s=(h.parents[1]/'vtkControl/vtkControl.cs').read_text(encoding='utf-8-sig');body=s[s.index('private vtkColorTransferFunction GetColorTransferFunction()'):];body=body[:body.index('double n = 0;')]
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
