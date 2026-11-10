#!/usr/bin/env python3
"""Extract the original UserControls/ModelTree layout: the three tabs, each tree's
static nodes (name, text, image), the step sub-nodes added by AddStep, the node
names of the ModelTree fields, the tree context menu (order, text, image,
shortcut) and the ImageList icon keys with their icon files. Icons that exist only inside the
ilIcons ImageStream (BasePart.ico) are decoded to X/UI/ImageList/*.png.

Output: X/UI/original_model_tree.json, consumed by model_tree.py. `--check` fails
when the checked-in file no longer matches the original sources.
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import json
import re
import struct
import sys
import zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DESIGNER = ROOT / "UserControls/ModelTree.Designer.cs"
SOURCE = ROOT / "UserControls/ModelTree.cs"
RESOURCES = ROOT / "UserControls/Properties/Resources.resx"
OUT = Path(__file__).with_name("original_model_tree.json")
ICON_FOLDERS = [ROOT / "UserControls/Resources", ROOT / "PrePoMax/Icons"]
RESX = ROOT / "UserControls/ModelTree.resx"
# Icons that exist only inside the ilIcons ImageListStreamer of ModelTree.resx.
IMAGE_LIST_DIR = Path(__file__).with_name("ImageList")


def image_list_png(index: int) -> bytes:
    """Decode image `index` of the ilIcons ImageStream: the BinaryFormatter byte array holds an
    'MSFt' run-length stream of an ImageList_Write image (ILHEAD + 32-bit BMP, 4 images per row)."""
    text = RESX.read_text(encoding="utf-8-sig")
    value = re.search(r'<data name="ilIcons\.ImageStream"[^>]*>\s*<value>(.*?)</value>', text, re.S)[1]
    blob = base64.b64decode("".join(value.split()))
    start = blob.find(b"MSFt")
    length = struct.unpack("<i", blob[start - 5:start - 1])[0]
    runs = blob[start + 4:start + length]
    stream = bytearray()
    for k in range(0, len(runs) - 1, 2):
        stream += bytes([runs[k + 1]]) * runs[k]
    magic, _, count, _, _, cx, cy = struct.unpack("<2sHhhhhh", stream[:14])
    bmp = stream[28:]
    width, height = struct.unpack("<ii", bmp[18:26])
    bits, offset = struct.unpack("<H", bmp[28:30])[0], struct.unpack("<I", bmp[10:14])[0]
    if magic != b"IL" or bits != 32 or index >= count:
        raise ValueError("unsupported ImageList stream")
    per_row = width // cx
    x0, y0 = (index % per_row) * cx, (index // per_row) * cy
    rows = []
    for y in range(cy):
        row = bytearray(b"\x00")
        for x in range(cx):
            o = offset + ((height - 1 - (y0 + y)) * width + x0 + x) * 4
            b, g, r, a = bmp[o:o + 4]
            row += bytes([r, g, b, a])
        rows.append(bytes(row))

    def chunk(kind: bytes, data: bytes) -> bytes:
        return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind + data))
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", cx, cy, 8, 6, 0, 0, 0)) +
            chunk(b"IDAT", zlib.compress(b"".join(rows), 9)) + chunk(b"IEND", b""))


def icon_file(key: str) -> str | None:
    for folder in ICON_FOLDERS:
        found = sorted(folder.rglob(key))
        if found:
            return found[0].relative_to(ROOT).as_posix()
    return None


def resource_icons() -> dict[str, str]:
    text = RESOURCES.read_text(encoding="utf-8-sig")
    icons = {}
    for name, value in re.findall(r'<data name="(\w+)" type="System\.Resources\.ResXFileRef[^"]*">\s*<value>([^;<]+);', text):
        path = (RESOURCES.parent / value.replace("\\", "/")).resolve()
        if path.exists():
            icons[name] = path.relative_to(ROOT).as_posix()
    return icons


def extract() -> dict:
    designer = DESIGNER.read_text(encoding="utf-8-sig")
    source = SOURCE.read_text(encoding="utf-8-sig")
    # Static tree nodes: TreeNode("Text", new TreeNode[] { children })
    children = {}
    for name, body in re.findall(r"TreeNode (treeNode\d+) = new System\.Windows\.Forms\.TreeNode\(\"[^\"]*\"(?:, new System\.Windows\.Forms\.TreeNode\[\] \{(.*?)\})?\);", designer, re.S):
        children[name] = re.findall(r"treeNode\d+", body or "")
    props = {}
    for node, prop, value in re.findall(r"(treeNode\d+)\.(Name|Text|ImageKey) = \"([^\"]*)\";", designer):
        props.setdefault(node, {})[prop] = value

    def node(name: str) -> dict | None:
        p = props.get(name, {})
        # Designer sample parts (Name "Node<i>") are removed by ModelTree.Clear().
        if re.fullmatch(r"Node\d+", p.get("Name", "")):
            return None
        item = {"name": p.get("Name", ""), "text": p.get("Text", ""), "image": p.get("ImageKey")}
        kids = [k for k in (node(c) for c in children.get(name, [])) if k]
        if kids:
            item["children"] = kids
        return item

    trees = {}
    for tree, body in re.findall(r"this\.(cltv\w+)\.Nodes\.AddRange\(new System\.Windows\.Forms\.TreeNode\[\] \{(.*?)\}\);", designer, re.S):
        trees[tree] = [n for n in (node(c) for c in re.findall(r"treeNode\d+", body)) if n]
    tabs = []
    for tab in re.findall(r"this\.tcGeometryModelResults\.Controls\.Add\(this\.(\w+)\);", designer):
        text = re.search(r"this\." + tab + r"\.Text = \"([^\"]*)\";", designer)[1]
        tree = re.search(r"this\." + tab + r"\.Controls\.Add\(this\.(cltv\w+)\);", designer)[1]
        tabs.append({"id": tab, "text": text, "tree": tree})
    names = dict(re.findall(r"private string _(\w+Name) = \"([^\"]*)\";", source))
    add_step = re.search(r"private TreeNode AddStep\(Step step\)(.*?)\n        \}", source, re.S)[1]
    step_nodes = [{"name": names[n], "image": image} for n, image in
                  re.findall(r"tmp = stepNode\.Nodes\.Add\(_(\w+)\);.*?SetNodeImage\(tmp, \"([^\"]+)\"\);", add_step, re.S)]
    # Context menu: cmsTree items, text, image, shortcut
    # AssembleTreeContextMenu appends the cmsTreeSecondary items to cmsTree.
    order = [i for strip in ("cmsTree", "cmsTreeSecondary") for i in re.findall(r"this\.(\w+)", re.search(
        r"this\." + strip + r"\.Items\.AddRange\(new System\.Windows\.Forms\.ToolStripItem\[\] \{(.*?)\}\);", designer, re.S)[1])]
    kind = dict(re.findall(r"this\.(\w+) = new System\.Windows\.Forms\.(\w+)\(\);", designer))
    text = dict(re.findall(r"this\.(tsmi\w+)\.Text = \"([^\"]*)\";", designer))
    icons = resource_icons()
    images = {k: icons.get(v) for k, v in re.findall(r"this\.(tsmi\w+)\.Image = global::UserControls\.Properties\.Resources\.(\w+);", designer)}
    keys = {k: "+".join({"Control": "Ctrl"}.get(p, p) for p in re.findall(r"Keys\.(\w+)", v))
            for k, v in re.findall(r"this\.(tsmi\w+)\.ShortcutKeys = \(\((.*?)\)\);", designer, re.S)}
    menu = []
    for item in order:
        if kind.get(item) == "ToolStripSeparator":
            menu.append({"id": item, "separator": True})
            continue
        entry = {"id": item, "text": text.get(item, "")}
        if images.get(item):
            entry["image"] = images[item]
        if item in keys:
            entry["shortcut"] = keys[item]
        menu.append(entry)
    image_keys = re.findall(r"this\.ilIcons\.Images\.SetKeyName\(\d+, \"([^\"]+)\"\);", designer)
    icons_by_key = {k: icon_file(k) for k in image_keys}
    extracted = {}
    for index, key in enumerate(image_keys):
        if icons_by_key[key] is None:
            target = IMAGE_LIST_DIR / (Path(key).stem + ".png")
            extracted[target] = image_list_png(index)
            icons_by_key[key] = target.relative_to(ROOT).as_posix()
    return {
        "source": {p.relative_to(ROOT).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in (DESIGNER, SOURCE, RESOURCES, RESX)},
        "tabs": tabs,
        "trees": trees,
        "names": names,
        "stepNodes": step_nodes,
        "contextMenu": menu,
        "icons": icons_by_key,
    }, extracted


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    data, extracted = extract()
    content = json.dumps(data, indent=1, ensure_ascii=False) + "\n"
    if args.check:
        stale = not OUT.exists() or OUT.read_text(encoding="utf-8") != content
        stale |= any(not path.exists() or path.read_bytes() != png for path, png in extracted.items())
        if stale:
            print("original_model_tree.json is stale; run X/UI/generate-model-tree.py", file=sys.stderr)
            return 1
        return 0
    OUT.write_text(content, encoding="utf-8")
    for path, png in extracted.items():
        path.parent.mkdir(exist_ok=True)
        path.write_bytes(png)
    return 0


if __name__ == "__main__":
    sys.exit(main())
