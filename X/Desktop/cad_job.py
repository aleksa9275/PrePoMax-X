"""Background CAD import. Scene publication belongs to the GUI thread."""
from pathlib import Path
from tempfile import TemporaryDirectory
from threading import Event

from PyQt6 import QtCore

from cad_import import CadImportCancelled, NativeCadTool
from cad_scene import read_cad_parts
from cad_document import CadDocument, CadMesh


class CadImportJob(QtCore.QThread):
    def __init__(self, source, tool, decoder, parent=None):
        super().__init__(parent)
        self.source = Path(source).resolve()
        self.tool = tool
        self.decoder = decoder
        self.cancel_requested = Event()
        self.result = None
        self.document = None

    def cancel(self):
        self.cancel_requested.set()

    def run(self):
        try:
            if isinstance(self.tool, NativeCadTool):
                self.document = CadDocument(self.source, self.tool, self.decoder, cancel=self.cancel_requested)
                scene = self.document.scene
            else:
                with TemporaryDirectory(prefix="prepomaxx-cad-") as directory:
                    scene = read_cad_parts(self.source, self.tool, self.decoder, Path(directory) / "import",
                                          cancel=self.cancel_requested)
            if self.cancel_requested.is_set():
                raise CadImportCancelled("CAD import cancelled.")
            self.result = {"success": True, "scene": scene, "document": self.document}
        except CadImportCancelled:
            self.result = {"success": False, "cancelled": True}
        except Exception as error:
            self.result = {"success": False, "error": str(error)}
        if not self.result["success"] and self.document is not None:
            self.document.close()
            self.document = None


class CadMeshJob(QtCore.QThread):
    def __init__(self, document, command, reader, maximum_size, parent=None, *, element_order=1):
        super().__init__(parent)
        self.document, self.command, self.reader, self.maximum_size = document, command, reader, maximum_size
        self.element_order = element_order
        self.cancel_requested = Event()
        self.result = None
        self.mesh = None

    def cancel(self):
        self.cancel_requested.set()

    def run(self):
        try:
            self.mesh = CadMesh(self.document, self.command, self.reader, self.maximum_size, cancel=self.cancel_requested, element_order=self.element_order)
            if self.cancel_requested.is_set():
                raise CadImportCancelled("CAD meshing cancelled.")
            self.result = {"success": True, "mesh": self.mesh}
        except CadImportCancelled:
            self.result = {"success": False, "cancelled": True}
        except Exception as error:
            self.result = {"success": False, "error": str(error)}
        if not self.result["success"] and self.mesh is not None:
            self.mesh.close()
            self.mesh = None
