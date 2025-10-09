from __future__ import annotations
from dataclasses import dataclass
from typing import List, Literal, Optional

Mode = Literal["solve","polydesign","rst","modelmatch"]

@dataclass
class RunRequest:
    mode: Mode
    A: List[float]; B: List[float]
    layout: Literal["ogata","desc"] = "ogata"
    d: int = 0
    degS: Optional[int] = None; degR: Optional[int] = None
    pretty: bool = False; show_E: bool = False
    export_json: Optional[str] = None; export_csv: Optional[str] = None
    backend: Literal["mpl","plotly","none"] = "none"
    save: Optional[str] = None; T: float = 1.0; kmax: int = 40
    D: Optional[List[float]] = None; H: Optional[List[float]] = None; F: Optional[List[float]] = None
    config: Optional[int] = None; ogata_parity: bool = False
    Gmodel_num: Optional[List[float]] = None; Gmodel_den: Optional[List[float]] = None
    H1: Optional[List[float]] = None
    rst_config: int = 2
