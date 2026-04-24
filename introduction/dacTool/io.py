from __future__ import annotations
import csv, json, os
from typing import Iterable, Dict, Any, List
from .utils import resolve_input_path

def bits_from_int(code: int, nbits: int) -> List[int]:
    return [(code >> i) & 1 for i in range(nbits)]  # LSB..MSB

def int_from_bits(bits_lsb_first: List[int]) -> int:
    out = 0
    for i, b in enumerate(bits_lsb_first):
        out |= (int(b) & 1) << i
    return out

def load_vectors_from_csv(path: str, nbits: int) -> Iterable[Dict[str, Any]]:
    with open(path, newline='') as f:
        rdr = csv.DictReader(f)
        fields = [c.strip() for c in (rdr.fieldnames or [])]
        have_code = 'code' in fields
        have_bits = all((f"b{i}" in fields) for i in range(nbits))
        if not have_code and not have_bits:
            raise ValueError("CSV must have 'code' or per-bit b0..b{n-1}")
        for row in rdr:
            if have_code:
                code = int(row['code'])
                bits = bits_from_int(code, nbits)
            else:
                bits = [int(row[f"b{i}"]) for i in range(nbits)]
                code = int_from_bits(bits)
            yield {'code': code, 'bits': bits}

def load_vectors_from_json(path_or_inline: str, nbits: int) -> Iterable[Dict[str, Any]]:
    if os.path.exists(path_or_inline):
        with open(path_or_inline) as f:
            data = json.load(f)
    else:
        data = json.loads(path_or_inline)

    if isinstance(data, list):
        for item in data:
            if isinstance(item, dict):
                if 'code' in item:
                    code = int(item['code'])
                    bits = bits_from_int(code, nbits)
                else:
                    bits = [int(item.get(f"b{i}", 0)) for i in range(nbits)]
                    code = int_from_bits(bits)
            else:
                code = int(item)
                bits = bits_from_int(code, nbits)
            yield {'code': code, 'bits': bits}
    else:
        raise ValueError("JSON must be a list (codes or per-bit dicts)")
