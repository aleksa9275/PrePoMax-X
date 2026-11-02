"""Ad-hoc Mac app packaging adapter; shared C# publication stays in build.py."""
import sys

def package(build, root):
    output = build.output
    build.run([sys.executable, "-m", "PyInstaller", "--noconfirm", "--windowed", "--onedir",
        "--name", "PrePoMax-X-Viewport", "--target-architecture", "arm64", "--collect-all", "vtkmodules",
        "--add-data", f"{output / 'hosts'}:hosts", "--add-data", f"{output / 'source-identity.json'}:.",
        "--add-data", f"{root / 'X/Build/targets.json'}:.", "--distpath", output / "dist",
        "--workpath", output / "build", "--specpath", output, root / "X/Desktop/viewport.py"])
    app = output / "dist/PrePoMax-X-Viewport.app"
    if not app.is_dir():
        raise ValueError("Mac package directory not created")
    build.run(["codesign", "--verify", "--deep", "--strict", app])
    return app
