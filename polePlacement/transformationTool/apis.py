
from __future__ import annotations
from dataclasses import dataclass
from typing import Optional, List
import numpy as np

@dataclass
class RunRequest:
    # Inputs
    A: Optional[np.ndarray] = None
    B: Optional[np.ndarray] = None
    C: Optional[np.ndarray] = None
    D: Optional[np.ndarray] = None
    json_in: Optional[str] = None

    # Actions
    to_ccf: bool = False
    to_ocf: bool = False
    to_diag: bool = False
    to_jordan: bool = False

    # Options
    show_tf: bool = False
    check_invariance: bool = False
    pretty: bool = False
    name: str = "transform"

    # Output toggles
    save_json: bool = False
    save_csv: bool = False

@dataclass
class TransformResult:
    name: str
    form: str
    eigvals: List[complex]
    T: Optional[np.ndarray]
    Ahat: np.ndarray
    Bhat: Optional[np.ndarray]
    Chat: Optional[np.ndarray]
    Dhat: Optional[np.ndarray]
    a_coeffs: Optional[List[complex]] = None
    b_coeffs: Optional[List[complex]] = None
    rank_ctrb_before: Optional[int] = None
    rank_ctrb_after: Optional[int] = None
    rank_obsv_before: Optional[int] = None
    rank_obsv_after: Optional[int] = None
