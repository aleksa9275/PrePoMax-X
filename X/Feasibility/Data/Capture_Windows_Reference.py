# PrePoMax Python Script
# Run only inside the original pinned Windows PrePoMax host, in a new session.
# Original APIs are verified in APIs/Python/PrePoMaxAPI.cs; live execution is pending.
import os

directory = pmx.work_directory
fixture = os.path.join(directory, "cube.inp")
project = os.path.join(directory, "cube-mesh.pmx")
deck = os.path.join(directory, "cube-export.inp")
if not os.path.isfile(fixture):
    raise Exception("Copy the repository cube.inp fixture into the disposable capture work directory first.")
if os.path.exists(project) or os.path.exists(deck):
    raise Exception("Use a new capture directory; reference outputs already exist.")

pmx.new_model("ThreeD", "MM_TON_S_C")
pmx.import_file(fixture)
pmx.save(project)
pmx.export_to_calculix(deck)
print("Reference capture saved cube-mesh.pmx and cube-export.inp. Record binary/source hashes and reopen the project in the original Windows host.")
