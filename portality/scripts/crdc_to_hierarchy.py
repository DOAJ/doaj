#!/usr/bin/env python3
"""
Read multiple classification CSVs and produce a hierarchical JSON array:
[
  { "name": "<Class title>", "code": "<Code>", "children": [ ... ] },
  ...
]
Top-level entries are rows with Level == 1. Children are attached by:
 - explicit Parent column (if present), or
 - prefix-matching of normalised codes (longest prefix wins).
Usage:
  csv_to_hierarchy_json.py file1.csv file2.csv file3.csv [-o out.json]
"""
import sys
import csv
import json
import argparse
import re
from collections import defaultdict

def normalize_code(code):
    if code is None:
        return ""
    return re.sub(r'\W+', '', code.strip()).upper()

def read_rows_from_csv(path):
    rows = []
    # use utf-8-sig so any BOM is removed from the start of the file/first header
    with open(path, newline='', encoding='utf-8-sig') as fh:
        rdr = csv.DictReader(fh)
        orig_fieldnames = rdr.fieldnames or []
        # clean field names (strip whitespace and remove BOM char if present)
        cleaned_fieldnames = [fn.replace('\ufeff', '').strip() for fn in orig_fieldnames]

        for r in rdr:
            # build a row dict keyed by cleaned header names
            newrow = {}
            for orig, clean in zip(orig_fieldnames, cleaned_fieldnames):
                newrow[clean] = r.get(orig)
            rows.append(newrow)
    return rows

def build_nodes(rows):
    nodes = {}             # code -> node dict (includes metadata)
    by_level = defaultdict(list)
    for r in rows:
        # some CSVs may name the title column as "Class title"
        title = r.get("Class title") or r.get("Hierarchical structure") or r.get("Class title ")
        code_raw = r.get("Code") or ""
        level_raw = r.get("Level") or ""
        try:
            level = int(level_raw.strip())
        except Exception:
            # fallback: non-numeric or empty -> treat as 1
            level = 1
        code = code_raw.strip()
        norm = normalize_code(code)
        node = {
            "name": title.strip() if isinstance(title, str) else (title or ""),
            "code": code,
            "children": [],
            "_level": level,
            "_norm": norm,
            "_parent_field": (r.get("Parent") or "").strip() if "Parent" in r else "",
        }
        nodes[code] = node
        by_level[level].append(node)
    return nodes, by_level

def find_node_by_code(nodes, code):
    # direct match first
    if code in nodes:
        return nodes[code]
    # try to match by normalised code equality (handles small formatting differences)
    target_norm = normalize_code(code)
    for n in nodes.values():
        if n["_norm"] == target_norm:
            return n
    return None

def attach_children(nodes, by_level):
    # attach nodes with explicit Parent first (if any)
    for node in list(nodes.values()):
        parent_code = node.get("_parent_field") or ""
        if parent_code:
            parent = find_node_by_code(nodes, parent_code)
            if parent:
                parent["children"].append(node)
                node["_attached"] = True

    # attach remaining nodes by prefix matching, from highest level down to level 2
    all_nodes = list(nodes.values())
    levels = sorted(by_level.keys(), reverse=True)  # attach deeper levels first
    for lvl in levels:
        if lvl <= 1:
            continue
        for node in by_level.get(lvl, []):
            if node.get("_attached"):
                continue
            # among possible parents (levels < lvl), pick the one whose normalised code
            # is a prefix of this node's normalised code and has the longest length
            candidates = []
            for p in all_nodes:
                if p["_level"] < node["_level"]:
                    if node["_norm"].startswith(p["_norm"]) and p["_norm"]:
                        candidates.append(p)
            if candidates:
                parent = max(candidates, key=lambda x: len(x["_norm"]))
                parent["children"].append(node)
                node["_attached"] = True
            else:
                # no prefix match found; leave unattached (will become top-level if level==1)
                node["_attached"] = False

def collect_roots(nodes):
    # Primary roots: explicit Level == 1 rows
    roots = [n for n in nodes.values() if n.get("_level") == 1]

    # If none found, prefer unattached nodes that claim Level == 1 (defensive)
    if not roots:
        roots = [n for n in nodes.values() if not n.get("_attached") and n.get("_level") == 1]

    # Final fallback (very rare): any unattached nodes (but try to avoid promoting deeper levels)
    if not roots:
        roots = [n for n in nodes.values() if not n.get("_attached")]

    # sort roots by code for deterministic output
    roots.sort(key=lambda x: (x.get("code") or ""))
    return roots

def strip_meta(node):
    # recursively remove internal metadata keys before JSON dump
    res = {
        "name": node.get("name", ""),
        "code": node.get("code", "")
    }
    # build children list (recursively) and only include if non-empty
    children_nodes = node.get("children") or []
    children = [strip_meta(c) for c in children_nodes]
    if children:
        res["children"] = children
    return res

def main():
    p = argparse.ArgumentParser(description="Convert classification CSVs to hierarchical JSON.")
    p.add_argument("csv_files", nargs="+", help="CSV files to process (order doesn't matter).")
    p.add_argument("-o", "--output", help="Output JSON file (default stdout).")
    args = p.parse_args()

    all_rows = []
    for fp in args.csv_files:
        try:
            all_rows.extend(read_rows_from_csv(fp))
        except Exception as e:
            sys.exit("Failed to read {}: {}".format(fp, e))

    nodes, by_level = build_nodes(all_rows)
    attach_children(nodes, by_level)
    roots = collect_roots(nodes)
    out = [strip_meta(r) for r in roots]

    if args.output:
        with open(args.output, "w", encoding="utf-8") as fh:
            json.dump(out, fh, indent=2, ensure_ascii=False)
    else:
        json.dump(out, sys.stdout, indent=2, ensure_ascii=False)
        sys.stdout.write("\n")

if __name__ == "__main__":
    main()
