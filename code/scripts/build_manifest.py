#!/usr/bin/env python3
"""Refresh the static release manifest after an intentional artifact change.

This is a maintainer operation. It does not alter scientific inputs or run outputs.
Users checking an untouched artifact should run check_manifest.py instead.
"""
from pathlib import Path
import hashlib,json
ROOT=Path(__file__).resolve().parents[2]
def distributed(p):
    rel=p.relative_to(ROOT)
    if not p.is_file() or ".git" in rel.parts or "__pycache__" in rel.parts:return False
    if p.suffix in [".pyc",".pyo"]:return False
    if rel.parts[:3]==("code","results","generated"):
        return rel.as_posix()=="code/results/generated/README.md"
    return rel.as_posix()!="MANIFEST.sha256.json"
def main():
    files=sorted((p for p in ROOT.rglob("*") if distributed(p)),key=lambda p:p.relative_to(ROOT).as_posix())
    records=[{"path":p.relative_to(ROOT).as_posix(),"bytes":p.stat().st_size,
              "sha256":hashlib.sha256(p.read_bytes()).hexdigest()} for p in files]
    manifest={"schema_version":1,"artifact":"EvidencePath","release_version":"1.0","algorithm":"sha256",
              "scope":"Static distributed research tree; excludes this manifest itself, .git, caches and generated run outputs except their README.",
              "excluded":[".git/**","**/__pycache__/**","**/*.pyc","code/results/generated/** except README.md"],
              "files":records}
    (ROOT/"MANIFEST.sha256.json").write_text(json.dumps(manifest,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"status":"written","files_excluding_manifest":len(records)}))
if __name__=="__main__":main()
