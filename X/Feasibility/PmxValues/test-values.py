#!/usr/bin/env python3
"""Synthetic binding/change tests without application serialization."""
import importlib.util
import json
from pathlib import Path
import struct
import tempfile

HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location("values",HERE/"compare-values.py")
values=importlib.util.module_from_spec(spec);spec.loader.exec_module(values)
base_spec=importlib.util.spec_from_file_location("synthetic",HERE.parent/"Pmx/test-inspection.py")
synthetic=importlib.util.module_from_spec(base_spec);base_spec.loader.exec_module(synthetic)


def fixture(left,right):
    i=synthetic.i32;t=synthetic.text
    graph=synthetic.HEADER+b"\x0c"+i(2)+t("Absent.Assembly, Version=1.0.0.0, Culture=neutral, PublicKeyToken=null")+b"\x05"+i(1)+t("CaeModel.Fixture")+i(2)+t("Left")+t("Right")+bytes([0,0,8,8])+i(2)+i(left)+i(right)+b"\x0b"
    return synthetic.envelope(graph=graph)


def main():
    checks=[]
    with tempfile.TemporaryDirectory(prefix="prepomaxx-value-tests-") as temp:
        folder=Path(temp);before=folder/"before.pmx";after=folder/"after.pmx"
        before.write_bytes(fixture(5,9))
        for name,pair,expected in [("same scalar bindings",(5,9),True),("scalar mutation rejected",(6,9),False),("member binding swap rejected",(9,5),False)]:
            after.write_bytes(fixture(*pair));report=values.compare(before,after)
            matched=report["matchingTypes"]==report["comparedTypes"]==1
            assert matched==expected;assert not report["unsafeFormatterSwitchEnabled"]
            assert "Absent.Assembly" not in report["loadedAssemblyNames"]
            checks.append({"name":name,"passed":True})
    print(json.dumps({"success":True,"checks":checks,"privateInputUsed":False}))


if __name__=="__main__":main()
