#!/usr/bin/env python3
"""Synthetic NRBF/envelope tests. Does not invoke a formatter or private model."""
import importlib.util
import io
import json
import os
from pathlib import Path
import struct
import subprocess
import sys
import tempfile
import unittest
import zlib

HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location("pmx_inspection",HERE/"inspect-pmx.py")
inspector=importlib.util.module_from_spec(spec); spec.loader.exec_module(inspector)
result_spec=importlib.util.spec_from_file_location("result_chunks",HERE/"inspect-result-chunks.py")
result_probe=importlib.util.module_from_spec(result_spec); result_spec.loader.exec_module(result_probe)


def i32(value): return struct.pack("<i",value)
def text(value):
    data=value.encode("utf-8")
    assert len(data)<128
    return bytes([len(data)])+data


HEADER=b"\x00"+struct.pack("<iiii",1,-1,1,0)
STRING=HEADER+b"\x06"+i32(1)+text("fixture")+b"\x0b"
SELF_CLASS=(HEADER+b"\x0c"+i32(2)+text("Absent.Assembly, Version=1.0.0.0, Culture=neutral, PublicKeyToken=null")+
            b"\x05"+i32(1)+text("PrePoMax.Controller")+i32(2)+text("_commands")+text("Count")+
            bytes([2,0,8])+i32(2)+b"\x09"+i32(1)+i32(42)+b"\x0b")


def envelope(graph=STRING,model=b"MODEL",tail=b"TAIL",header="PrePoMax v2.6.0",graph_length=None):
    inflated=struct.pack("<q",len(graph) if graph_length is None else graph_length)+graph+model
    compressor=zlib.compressobj(wbits=-15)
    compressed=compressor.compress(inflated)+compressor.flush()
    return header.encode().ljust(32,b"\0")+i32(len(compressed))+compressed+tail


class InspectionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.work=tempfile.TemporaryDirectory(prefix="prepomaxx-pmx-tests-")
        cls.folder=Path(cls.work.name); cls.commands=[]
        cls.assembly=inspector.build_decoder(cls.folder/"build",cls.commands)
    @classmethod
    def tearDownClass(cls): cls.work.cleanup()
    def test_envelope_exact_ranges(self):
        raw=envelope(); report,graph=inspector.framing(io.BytesIO(raw))
        self.assertEqual(graph,STRING); self.assertEqual(report["mainFrame"]["opaqueModelBytes"],5)
        self.assertEqual(report["opaqueTail"]["bytes"],4); self.assertTrue(report["inputUnchanged"])
    def test_negative_compressed_length(self):
        raw=bytearray(envelope()); raw[32:36]=i32(-1)
        with self.assertRaisesRegex(ValueError,"length outside"): inspector.framing(io.BytesIO(raw))
    def test_oversized_compressed_length(self):
        raw=bytearray(envelope()); raw[32:36]=i32(len(raw))
        with self.assertRaisesRegex(ValueError,"length outside"): inspector.framing(io.BytesIO(raw))
    def test_oversized_graph_length(self):
        with self.assertRaisesRegex(ValueError,"graph length"): inspector.framing(io.BytesIO(envelope(graph_length=2**40)))
    def test_negative_graph_length(self):
        with self.assertRaisesRegex(ValueError,"graph length"): inspector.framing(io.BytesIO(envelope(graph_length=-1)))
    def test_decompression_limit(self):
        with self.assertRaisesRegex(ValueError,"limit exceeded"): inspector.framing(io.BytesIO(envelope(model=b"x"*100000)),max_inflated=1024)
    def test_invalid_deflate(self):
        raw=b"PrePoMax v2.6.0".ljust(32,b"\0")+i32(4)+b"\xff"*4
        with self.assertRaisesRegex(ValueError,"Deflate"): inspector.framing(io.BytesIO(raw))
    def test_truncated_deflate(self):
        raw=envelope(tail=b""); length=struct.unpack("<i",raw[32:36])[0]
        raw=raw[:32]+i32(length-1)+raw[36:-1]
        with self.assertRaisesRegex(ValueError,"Truncated Deflate"): inspector.framing(io.BytesIO(raw))
    def test_deflate_trailing_bytes(self):
        raw=envelope(tail=b""); length=struct.unpack("<i",raw[32:36])[0]
        raw=raw[:32]+i32(length+1)+raw[36:]+b"!"
        with self.assertRaisesRegex(ValueError,"after end"): inspector.framing(io.BytesIO(raw))
    def test_legacy_version_explicitly_unsupported(self):
        with self.assertRaisesRegex(ValueError,"Pre-2.0.6"): inspector.framing(io.BytesIO(envelope(header="PrePoMax v2.0.5")))
    def test_unknown_header(self):
        with self.assertRaisesRegex(ValueError,"unrecognized"): inspector.framing(io.BytesIO(envelope(header="Another format")))
    def test_invalid_nrbf_header(self):
        with self.assertRaisesRegex(ValueError,"NRBF stream header"): inspector.framing(io.BytesIO(envelope(graph=b"x"*31)))
    def test_truncated_file(self):
        with self.assertRaisesRegex(ValueError,"size limits"): inspector.framing(io.BytesIO(b"PrePoMax"))
    def test_string_record_without_value_disclosure(self):
        report=inspector.decode_graph(STRING,self.assembly,self.folder)
        self.assertEqual(report["recordCount"],1); self.assertTrue(report["rootType"].startswith("System.String,"))
        self.assertNotIn("fixture",json.dumps(report)); self.assertFalse(report["unsafeFormatterSwitchEnabled"])
    def test_unknown_application_type_cycle_without_loading(self):
        report=inspector.decode_graph(SELF_CLASS,self.assembly,self.folder)
        self.assertTrue(report["rootType"].startswith("PrePoMax.Controller, Absent.Assembly,"))
        edge=report["referenceEdges"][0]; self.assertEqual(edge["sourceOrdinal"],edge["targetOrdinal"])
        self.assertNotIn("Absent.Assembly",report["loadedAssemblyNames"])
        self.assertNotIn("PrePoMax",report["loadedAssemblyNames"])
        self.assertNotIn("CaeModel",report["loadedAssemblyNames"])
    def test_decoder_rejects_truncated_records(self):
        with self.assertRaisesRegex(ValueError,"decoder rejected"): inspector.decode_graph(STRING[:-1],self.assembly,self.folder)
    def test_decoder_rejects_trailing_records(self):
        with self.assertRaisesRegex(ValueError,"decoder rejected"): inspector.decode_graph(STRING+b"extra",self.assembly,self.folder)
    def test_decoder_cli_contract(self):
        for arguments in [[],["unknown"]]:
            result=subprocess.run(["dotnet",str(self.assembly),*arguments],text=True,capture_output=True,timeout=15)
            self.assertEqual(result.returncode,2); self.assertFalse(json.loads(result.stdout)["success"])
    def test_output_hardlink_is_refused_without_input_mutation(self):
        source=self.folder/"source.pmx"; source.write_bytes(envelope()); output=self.folder/"hardlink.json"
        os.link(source,output)
        result=subprocess.run([sys.executable,str(HERE/"inspect-pmx.py"),str(source),"--output",str(output)],text=True,capture_output=True,timeout=15)
        self.assertEqual(result.returncode,2); self.assertEqual(source.read_bytes(),envelope())
    def test_result_chunk_fingerprints(self):
        def compressed(value):
            c=zlib.compressobj(wbits=-15); data=c.compress(value)+c.flush(); return i32(len(data))+data
        tail=i32(1)+i32(4)+b"name"+i32(1)+compressed(b"mesh")+i32(1)+i32(1)+compressed(b"field")+i32(-1)
        path=self.folder/"results.pmx";path.write_bytes(envelope(tail=tail))
        report=result_probe.inspect(path)
        self.assertEqual(report["fieldFrameCount"],1);self.assertEqual([c["inflatedBytes"] for c in report["chunks"]],[4,5])
        self.assertNotIn("name",json.dumps(report))
    def test_result_chunk_negative_length_rejected(self):
        tail=i32(1)+i32(0)+i32(1)+i32(-1)
        path=self.folder/"bad-results.pmx";path.write_bytes(envelope(tail=tail))
        with self.assertRaisesRegex(ValueError,"chunk length"): result_probe.inspect(path)
    def test_result_multicollection_explicitly_unsupported(self):
        path=self.folder/"multi-results.pmx";path.write_bytes(envelope(tail=i32(2)))
        with self.assertRaisesRegex(ValueError,"single-result"): result_probe.inspect(path)
    def test_versioned_field_metadata_insertion(self):
        original=b"sample component bytes"+bytes(9)
        changed=original[:-9]+i32(2)+original[-9:]
        self.assertTrue(result_probe.datatype_insertion_only(original,changed))
    def test_field_data_mutation_is_not_metadata_only(self):
        original=b"sample component bytes"+bytes(9)
        changed=b"changed component data"+i32(2)+bytes(9)
        self.assertFalse(result_probe.datatype_insertion_only(original,changed))


if __name__=="__main__": unittest.main(verbosity=2)
