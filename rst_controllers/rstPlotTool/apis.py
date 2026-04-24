from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Optional, Tuple

@dataclass
class OverlayFilters:
    include: Optional[str] = None
    exclude: Optional[str] = None

@dataclass
class YLimits:
    ylimY: Optional[Tuple[float, float]] = None
    ylimU: Optional[Tuple[float, float]] = None
    ylimE: Optional[Tuple[float, float]] = None

@dataclass
class RunRequest:
    files: List[str]
    overlay: Optional[bool] = None
    backend: str = "both"         # "both" | "mpl" | "plotly"
    style: str = "matlab"         # "matlab" | "light" | "dark"
    dpi: int = 150
    kmin: Optional[float] = None
    kmax: Optional[float] = None
    robust: float = 0.995
    ylimits: YLimits = field(default_factory=YLimits)
    clip: bool = False
    legend: str = "compact"       # "compact" | "full" | "none"
    filters: OverlayFilters = field(default_factory=OverlayFilters)
    annotate: Optional[str] = None
    title: Optional[str] = None
