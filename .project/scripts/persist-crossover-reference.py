#!/usr/bin/env python3
"""Preserve this explicitly requested research installation in its own bottle."""
import hashlib
import json
from pathlib import Path
import shutil

SOURCE=Path("/tmp/prepomaxx-crossover-app/PrePoMax v2.6.0")
WORK=Path("/tmp/prepomaxx-crossover-work")
BOTTLE=Path.home()/"Library/Application Support/CrossOver/Bottles/PrePoMax-X-reference-2.6"
DESTINATION=BOTTLE/"drive_c/PrePoMax-X-reference"


def sha(path):
    with path.open("rb") as stream: return hashlib.file_digest(stream,"sha256").hexdigest()


def main():
    if not (BOTTLE/"cxbottle.conf").exists(): raise RuntimeError("Expected research bottle missing")
    if DESTINATION.exists(): raise RuntimeError("Research installation already exists; refusing overwrite")
    if not (SOURCE/"PrePoMax.exe").exists() or not (WORK/"roundtrip-2.6.0.pmx").exists(): raise RuntimeError("Verified application/reference output missing")
    if sha(Path("/tmp/prepomaxx-PrePoMax-v2.6.0.zip"))!="7a08995fb776d3e962f859ee576078bf34d13f2b59d81c8012cddf8e69b1c384": raise RuntimeError("Official bundle identity changed")
    DESTINATION.mkdir()
    shutil.copytree(SOURCE,DESTINATION/"App")
    (DESTINATION/"Work").mkdir()
    for name in ["reference.pmx","roundtrip-2.6.0.pmx"]:
        target=DESTINATION/"Work"/name;shutil.copyfile(WORK/name,target)
        if sha(target)!=sha(WORK/name): raise RuntimeError("Reference copy mismatch")
    files=[p for p in SOURCE.rglob("*") if p.is_file()]
    if not all(sha(p)==sha(DESTINATION/"App"/p.relative_to(SOURCE)) for p in files): raise RuntimeError("Application copy verification failed")
    print(json.dumps({"bottle":"PrePoMax-X-reference-2.6","application":str(DESTINATION/"App/PrePoMax.exe"),
                      "workDirectory":str(DESTINATION/"Work"),"applicationFilesVerified":len(files),"referenceCopiesVerified":2}))


if __name__=="__main__": main()
