#!/usr/bin/env python3
"""Extract the original FrmMain main menu (order, text, shortcuts, checkability,
click handlers) and each handler's original entity-selection logic.

Output: X/UI/original_main_menu.json, consumed by main_menu.py. `--check` fails
when the checked-in file no longer matches the original sources.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DESIGNER = ROOT / "PrePoMax/Forms/FrmMain.Designer.cs"
FORM = ROOT / "PrePoMax/Forms/FrmMain.cs"
OUT = Path(__file__).with_name("original_main_menu.json")
SELECT = re.compile(r'(SelectOneEntity|SelectMultipleEntities|SelectOneEntityInStep|SelectMultipleEntitiesInStep)\(\s*"([^"]+)"\s*,\s*'
                    r'_controller\.(\w+(?:<\w+>)?)\(([^)]*)\)\s*,\s*(?:stepName\s*,\s*)?(?:_controller\.)?(\w+)(?:\s*,\s*(\d+))?(?:\s*,\s*(\d+))?')


def method_body(source: str, name: str) -> str | None:
    match = re.search(r"\n        [\w <>,\[\]]*?\b" + re.escape(name) + r"\(", source)
    if not match:
        return None
    start = source.index("{", match.end())
    depth = 0
    for i in range(start, len(source)):
        depth += {"{": 1, "}": -1}.get(source[i], 0)
        if depth == 0:
            return source[start:i + 1]
    return None


def selection(source: str, handler: str | None) -> dict | None:
    body = method_body(source, handler) if handler else None
    if not body:
        return None
    match = SELECT.search(body)
    if not match:
        return None
    kind, title, getter, arguments, target, minimum, maximum = match.groups()
    result = {"mode": "many" if "Multiple" in kind else "one", "title": title, "getter": getter,
              "target": target, "minimum": int(minimum or 1)}
    if maximum:
        result["maximum"] = int(maximum)
    if arguments.strip():
        result["arguments"] = [a.strip() for a in arguments.split(",")]
    if getter == "GetAllSteps":
        inner = selection(source, target)
        if inner:
            result["inStep"] = inner
    action = helper(source, target)
    if action:
        result["action"] = action
    return result


def helper(source: str, name: str) -> dict | None:
    """Summarise what an original FrmMain helper does after selection."""
    body = method_body(source, name)
    if not body:
        return None
    action = {}
    confirm = re.search(r'ShowWarningQuestionOKCancel\(\s*"((?:[^"\\]|\\.)*)"', body)
    if confirm:
        action["confirm"] = confirm[1]
    calls = re.findall(r"_controller\.(\w+)\(", body)
    if calls:
        action["calls"] = list(dict.fromkeys(calls))
    forms = re.findall(r"ShowForm\(_frm(\w+)\s*,\s*\"([^\"]*)\"", body)
    if forms:
        action["form"] = {"form": forms[0][0], "title": forms[0][1]}
    return action or None


def extract() -> dict:
    designer = DESIGNER.read_text(encoding="utf-8-sig")
    form = FORM.read_text(encoding="utf-8-sig")
    children = {m[1]: re.findall(r"this\.(\w+)", m[2]) for m in re.finditer(
        r"this\.(\w+)\.DropDownItems\.AddRange\(new System\.Windows\.Forms\.ToolStripItem\[\] \{(.*?)\}\);", designer, re.S)}
    text = dict(re.findall(r'this\.(\w+)\.Text = "((?:[^"\\]|\\.)*)";', designer))
    click = dict(re.findall(r"this\.(\w+)\.Click \+= new System\.EventHandler\(this\.(\w+)\);", designer))
    kind = dict(re.findall(r"this\.(\w+) = new System\.Windows\.Forms\.(\w+)\(\);", designer))
    visible = {k: v == "true" for k, v in re.findall(r"this\.(\w+)\.Visible = (true|false);", designer)}
    # Release builds hide the items listed under `#if !DEBUG` in the FrmMain constructor.
    release = re.search(r"#if !DEBUG(.*?)#endif", form, re.S)
    if release:
        visible.update({k: False for k in re.findall(r"(\w+)\.Visible = false;", release[1])})
    checkable = {k for k, v in re.findall(r"this\.(\w+)\.CheckOnClick = (true|false);", designer) if v == "true"}
    keys = {}
    for name, value in re.findall(r"this\.(\w+)\.ShortcutKeys = \(\((.*?)\)\);", designer, re.S):
        parts = re.findall(r"Keys\.(\w+)", value)
        keys[name] = "+".join({"Control": "Ctrl"}.get(p, p) for p in parts)
    top = re.findall(r"this\.(\w+)", re.search(r"this\.menuStripMain\.Items\.AddRange\(.*?\{(.*?)\}\);", designer, re.S)[1])

    def node(name: str) -> dict:
        item = {"id": name, "text": text.get(name, "").replace("&&", "&").strip()}
        if kind.get(name) == "ToolStripSeparator":
            return {"id": name, "separator": True}
        if name in click:
            item["handler"] = click[name]
            chosen = selection(form, click[name])
            if chosen:
                item["select"] = chosen
        if name in keys:
            item["shortcut"] = keys[name]
        if name in checkable:
            item["checkable"] = True
        if visible.get(name) is False:
            item["visible"] = False
        if name in children:
            item["children"] = [node(c) for c in children[name]]
        return item

    return {
        "source": {p.relative_to(ROOT).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in (DESIGNER, FORM)},
        "menus": [node(t) for t in top],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    content = json.dumps(extract(), indent=1, ensure_ascii=False) + "\n"
    if args.check:
        if not OUT.exists() or OUT.read_text(encoding="utf-8") != content:
            print("original_main_menu.json is stale; run X/UI/generate-main-menu.py", file=sys.stderr)
            return 1
        return 0
    OUT.write_text(content, encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
