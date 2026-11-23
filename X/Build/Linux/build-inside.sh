#!/usr/bin/env bash
# Runs inside the Containerfile.package container (X/Build/Linux/build-package.sh): repository at /src, work at /work.
set -euo pipefail
target="$1"; jobs="$2"
git config --global --add safe.directory /src
cd /src
echo "== PrePoMax-X $(git rev-parse --short HEAD) for $target, $jobs jobs; $(dotnet --version 2>/dev/null | sed 's/^/.NET SDK /')"
# Every native component from its pinned recipe (resumable: a finished stage is reused)
python3 X/Build/build_ui.py --target "$target" --workspace /work/ws --jobs "$jobs" --format tar.gz
# The release data files of PrePoMax 3.0.1 (material library, example models), checked against their hash
lock=X/Build/Linux/release-301-lock.json
read -r url archive digest folder < <(python3 -c "import json;d=json.load(open('$lock'));print(d['url'],d['archive'].replace(' ','%20'),d['sha256'],d['folder'].replace(' ','%20'))")
archive="${archive//%20/ }"; folder="${folder//%20/ }"
mkdir -p /work/downloads
[ -f "/work/downloads/$archive" ] || curl -fsSL -o "/work/downloads/$archive" "$url"
echo "$digest  /work/downloads/$archive" | sha256sum -c -
rm -rf /work/release && mkdir -p /work/release && unzip -q "/work/downloads/$archive" -d /work/release
# The application, packaged with those components
python3 X/App/package_linux.py --target "$target" --p1 "/work/ws/package/PrePoMax-X-$target.tar.gz" \
    --original "/work/release/$folder" --vtk-native /work/ws/vtk/vtkNative/runtime \
    --highs "$(ls /work/ws/highs/runtime/highs.dll.so)" --netgen /work/ws/netgen/runtime \
    --quadwild /work/ws/quadwild/runtime --output /work/out --archive
echo "== Done: /work/out/PrePoMax-X (folder) and /work/out/PrePoMax-X-$target.tar.gz"
