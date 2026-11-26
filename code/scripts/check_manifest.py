#!/usr/bin/env python3
"""Verify every file in the static release manifest, without changing files."""
from pathlib import Path
import hashlib,json,sys
ROOT=Path(__file__).resolve().parents[2]
def main():
    manifest=json.loads((ROOT/"MANIFEST.sha256.json").read_text(encoding="utf-8"))
    mismatches=[]
    for item in manifest["files"]:
        p=ROOT/item["path"]
        if not p.is_file():
            mismatches.append({"path":item["path"],"reason":"missing"})
        elif p.stat().st_size!=item["bytes"] or hashlib.sha256(p.read_bytes()).hexdigest()!=item["sha256"]:
            mismatches.append({"path":item["path"],"reason":"size or SHA-256 differs"})
    report={"status":"passed" if not mismatches else "failed",
            "checked_files":len(manifest["files"]),"mismatches":mismatches,
            "note":"Generated results and caches are intentionally outside the static manifest."}
    print(json.dumps(report,indent=2))
    return bool(mismatches)
if __name__=="__main__":sys.exit(main())
