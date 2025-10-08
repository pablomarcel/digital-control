# -*- coding: utf-8 -*-
"""
I/O helpers for z/pole-zero overlays and parsing.
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import List, Optional, Iterable, Tuple
from pathlib import Path
import json, csv, re
from .utils import ensure_in_path

@dataclass
class PZ:
    z: complex
    kind: str  # 'pole' or 'zero'
    label: Optional[str] = None

def to_complex(s: str) -> complex:
    s = s.strip().lower().replace("i", "j")
    return complex(s)

def parse_num_list(xs: Iterable[str]) -> List[float]:
    joined = " ".join(xs)
    parts = re.split(r"[,\s]+", joined.strip())
    return [float(p) for p in parts if p != ""]

def pretty_list(xs: Iterable[float]) -> str:
    return "[" + ", ".join(f"{x:g}" for x in xs) + "]"

def read_pz_any(path: Path) -> List[PZ]:
    if path.suffix.lower() == ".json":
        return read_pz_json(path)
    if path.suffix.lower() == ".csv":
        return read_pz_csv(path)
    raise ValueError(f"Unsupported file type: {path}")

def read_pz_json(path: Path) -> List[PZ]:
    data = json.loads(path.read_text())
    pzs: List[PZ] = []
    def grab(key, kind):
        if key in data and data[key] is not None:
            for item in data[key]:
                if isinstance(item, str):
                    z = to_complex(item)
                    pzs.append(PZ(z=z, kind=kind))
                elif isinstance(item, (list, tuple)) and len(item) >= 2:
                    z = complex(float(item[0]), float(item[1]))
                    pzs.append(PZ(z=z, kind=kind))
                elif isinstance(item, dict) and "re" in item and "im" in item:
                    z = complex(float(item["re"]), float(item["im"]))
                    pzs.append(PZ(z=z, kind=kind, label=item.get("label")))
    grab("poles", "pole"); grab("zeros", "zero")
    return pzs

def read_pz_csv(path: Path) -> List[PZ]:
    pzs: List[PZ] = []
    with path.open(newline="") as f:
        rdr = csv.DictReader(f)
        headers = [h.lower() for h in (rdr.fieldnames or [])]
        for row in rdr:
            row = {k.lower(): v for k, v in row.items()}
            label = row.get("label") or row.get("name")
            kind = (row.get("kind") or row.get("type") or "pole").strip().lower()
            if "z" in headers and row.get("z"):
                z = to_complex(row["z"])
            elif {"re","im"}.issubset(headers):
                z = complex(float(row["re"]), float(row["im"]))
            else:
                keys = list(row.keys())
                z = complex(float(row[keys[0]]), float(row[keys[1]]))
            if kind not in ("pole","zero"): kind = "pole"
            pzs.append(PZ(z=z, kind=kind, label=label))
    return pzs

def resolve_overlay_paths(names: Iterable[str]) -> List[Path]:
    paths = []
    for n in names:
        p = ensure_in_path(n)
        paths.append(p)
    return paths
