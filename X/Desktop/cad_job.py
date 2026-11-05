"""Background CAD import. Scene publication belongs to the GUI thread."""
from pathlib import Path
from tempfile import TemporaryDirectory
from threading import Event

from PyQt6 import QtCore

from cad_import import CadImportCancelled
from cad_scene import read_cad_parts


class CadImportJob(QtCore.QThread):
    def __init__(self, source, tool, decoder, parent=None):
        super().__init__(parent)
        self.source = Path(source).resolve()
        self.tool = tool
        self.decoder = decoder
        self.cancel_requested = Event()
        self.result = None

    def cancel(self):
        self.cancel_requested.set()

    def run(self):
        try:
            with TemporaryDirectory(prefix="prepomaxx-cad-") as directory:
                scene = read_cad_parts(self.source, self.tool, self.decoder, Path(directory) / "import",
                                       cancel=self.cancel_requested)
            if self.cancel_requested.is_set():
                raise CadImportCancelled("CAD import cancelled.")
            scene["cad"]["conversion"] = "Original 3.0.0 via CrossOver"
            self.result = {"success": True, "scene": scene}
        except CadImportCancelled:
            self.result = {"success": False, "cancelled": True}
        except Exception as error:
            self.result = {"success": False, "error": str(error)}
