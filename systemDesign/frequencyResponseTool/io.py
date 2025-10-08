# -*- coding: utf-8 -*-
from __future__ import annotations

import json
import os
from typing import List

def _parse_list_csv(s: str) -> List[float]:
    return [float(t) for t in s.replace(" ", "").split(",") if t != ""]

def parse_desc_list(s: str | list[float]) -> List[float]:
    if isinstance(s, str):
        return _parse_list_csv(s)
    return [float(x) for x in s]

def write_manifest(out_dir: str, manifest: dict) -> str:
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, "manifest.json")
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(manifest, fh, indent=2)
    return path
