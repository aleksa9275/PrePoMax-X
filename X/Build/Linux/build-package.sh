#!/usr/bin/env bash
# Builds the PrePoMax-X Linux package from source on this machine's architecture (x86-64 or ARM64), in a container.
#
#   X/Build/Linux/build-package.sh [WORK_DIR]
#
# Needs Podman or Docker, git, about 30 GB of free disk and 16 GB of memory; takes a few hours (VTK and OpenCASCADE
# dominate). WORK_DIR (default ~/prepomax-x-build) keeps the downloads and finished stages, so a run that stopped
# continues where it left off. Result: WORK_DIR/out/PrePoMax-X (run ./PrePoMax-X/PrePoMax-X) and its tar.gz.
# Environment: ENGINE=podman|docker, JOBS=<parallel jobs> (default: the number of CPUs).
set -euo pipefail
root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
case "$(uname -m)" in
  x86_64|amd64) target=linux-x64 ;;
  aarch64|arm64) target=linux-arm64 ;;
  *) echo "Unsupported architecture: $(uname -m) (x86-64 and ARM64 only)" >&2; exit 1 ;;
esac
engine="${ENGINE:-$(command -v podman >/dev/null && echo podman || echo docker)}"
command -v "$engine" >/dev/null || { echo "Podman or Docker is required" >&2; exit 1; }
work="${1:-$HOME/prepomax-x-build}"
mkdir -p "$work/home"
work="$(cd "$work" && pwd)"
jobs="${JOBS:-$(getconf _NPROCESSORS_ONLN 2>/dev/null || echo 4)}"
image=prepomax-x-package-build:1
echo "== Building the build environment ($engine, $image)"
"$engine" build -t "$image" -f "$root/X/Build/Linux/Containerfile.package" "$root/X/Build/Linux"
# Files in the checkout and the work folder stay owned by the calling user
if [ "$engine" = podman ]; then user=(--userns=keep-id); else user=(--user "$(id -u):$(id -g)"); fi
"$engine" run --rm "${user[@]}" -e HOME=/work/home -v "$root:/src" -v "$work:/work" -w /src "$image" \
    bash X/Build/Linux/build-inside.sh "$target" "$jobs"
echo "== Package: $work/out/PrePoMax-X   Archive: $work/out/PrePoMax-X-$target.tar.gz"
