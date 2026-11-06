"""Owned native CAD inputs and immutable mesh/job provenance; no geometry parser."""
import hashlib
import json
from pathlib import Path
from tempfile import TemporaryDirectory

from cad_import import file_sha256, require_output, run_stage
from cad_scene import compose_cad_parts


class CadDocument:
    def __init__(self, source, tool, decoder, *, cancel=None):
        self.storage = TemporaryDirectory(prefix="prepomaxx-cad-document-")
        self.root = Path(self.storage.name)
        self.source = Path(source).resolve()
        self.tool = tool
        self.edits = []
        self.edits_snapshot = '[]'
        self.edit_files = []
        try:
            self.parts = tool.convert_parts(self.source, self.root / "import", cancel=cancel)
            self.snapshot = self.root / "import" / ("source" + self.source.suffix.lower())
            self.scene = compose_cad_parts([(b.stem, decoder(v, cancel=cancel)) for b, v in self.parts], force_parts=True)
            self.scene["cad"]["conversion"] = tool.description
            self.identities = {p: file_sha256(p) for p in [self.snapshot, *[p for pair in self.parts for p in pair]]}
            self.tool_receipt = file_sha256(tool.receipt)
        except BaseException:
            self.close()
            raise

    def verify(self):
        if json.dumps(self.edits,sort_keys=True,allow_nan=False)!=self.edits_snapshot:
            raise ValueError('Native CAD edit history changed after validation.')
        self.tool.verify_runtime()
        if file_sha256(self.tool.receipt) != self.tool_receipt:
            raise ValueError("Native CAD tool identity changed since import.")
        for path, digest in self.identities.items():
            if path.is_symlink() or file_sha256(path) != digest:
                raise ValueError("Retained CAD input changed: " + path.name)

    def close(self):
        self.storage.cleanup()


class CadMesh:
    def __init__(self, document, mesh_command, reader, maximum_size, *, cancel=None, element_order=1):
        if type(element_order) is not int or element_order not in (1,2):raise ValueError("Choose mesh order 1 or 2 (preview only).")
        self.storage = TemporaryDirectory(prefix="prepomaxx-cad-mesh-")
        self.root = Path(self.storage.name)
        self.document = document
        self.element_order = element_order
        self.size = maximum_size
        self.authored_regions = []
        try:
            document.verify()
            self.parameters = self.root / "parameters"
            self.parameter_result = reader([*mesh_command, "netgen-quadratic-parameters" if element_order==2 else "netgen-parameters", str(maximum_size), str(self.parameters)], cancel=cancel)
            self.volumes = []
            for index, (brep, _) in enumerate(document.parts, 1):
                vol = self.root / f"part-{index}.vol"
                run_stage([*document.tool.command, "BREP_MESH", str(brep), str(vol), str(self.parameters)],
                          self.root, f"mesh-{index}.log", cancel=cancel)
                require_output(vol, 16 * 1024 * 1024)
                self.volumes.append(vol)
            self.mesh = self.root / "mesh.inp"
            self.scene = reader([*mesh_command, "from-vol-quadratic-preview" if element_order==2 else "from-vol", str(self.mesh), *map(str, self.volumes)], cancel=cancel)
            self.mesh_bytes = self.mesh.read_bytes()
            self.identities = {p: file_sha256(p) for p in [self.parameters, self.mesh, *self.volumes]}
            if self.identities[self.mesh] != self.scene["SourceSha256"]:
                raise ValueError("Native mesh changed during decoding.")
            document.verify()
        except BaseException:
            self.close()
            raise

    def freeze(self, destination):
        """Copy every authoritative CAD/mesh input into the submitted job."""
        self.document.verify()
        for path, digest in self.identities.items():
            if path.is_symlink() or file_sha256(path) != digest:
                raise ValueError("Retained native mesh input changed: " + path.name)
        destination = Path(destination)
        destination.mkdir()
        inputs = []
        for path, digest in {**self.document.identities, **self.identities}.items():
            # Prefix avoids the source and generated mesh sharing a basename.
            name = ("cad-" if path in self.document.identities else "mesh-") + path.name
            target = destination / name
            with target.open("xb") as stream:
                stream.write(path.read_bytes())
            if file_sha256(target) != digest:
                raise ValueError("CAD job input changed while being frozen.")
            inputs.append({"file": name, "sha256": digest})
        receipt = {"schemaVersion": 1, "sourceName": self.document.source.name,
                   "sourceSha256": self.document.identities[self.document.snapshot],
                   "toolReceiptSha256": self.document.tool_receipt,
                   "maximumSize": self.size, "elementOrder": self.element_order, "analysisEligible": self.element_order==1, "meshingThreads": 1,
                   "authoredRegions": self.authored_regions,
                   "baseMeshSha256": self.identities[self.mesh], "mapping": self.scene["cadMesh"], "files": inputs,
                   "scope": "Frozen native CAD/meshing job provenance; not project persistence"}
        if self.document.edits:
            receipt['geometryEdits'] = self.document.edits
        tool_bytes = self.document.tool.receipt.read_bytes()
        if hashlib.sha256(tool_bytes).hexdigest() != self.document.tool_receipt:
            raise ValueError("CAD tool receipt changed while freezing the job.")
        with (destination / 'tool-build-receipt.json').open('xb') as stream:
            stream.write(tool_bytes)
        (destination / "identity.json").write_text(json.dumps(receipt, indent=2) + "\n")
        return receipt

    def close(self):
        self.storage.cleanup()
