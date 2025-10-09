from __future__ import annotations
from dataclasses import dataclass
from typing import List, Literal, Optional

# Public mode literal for clarity in other modules
Mode = Literal["solve", "polydesign", "rst", "modelmatch"]

@dataclass
class RunRequest:
    """
    Container for all inputs to PolynomialApp.run(). Mirrors CLI flags.

    Modes:
      - solve        : compute alpha/beta (optionally pretty-print, show_E)
      - polydesign   : design & preview closed-loop (config-driven)
      - rst          : RST design (rst_config)
      - modelmatch   : model matching with target Gmodel and prefilter H1

    Notes:
      * Paths passed in export_json/export_csv/save are resolved by the I/O layer
        (e.g., utils.resolve_out) so that 'out/...' anchors to the package's out/.
    """
    # Which subcommand
    mode: Mode

    # Base plant
    A: List[float]
    B: List[float]

    # Optional signals/filters depending on mode
    D: Optional[List[float]] = None  # used by solve/polydesign (direct D)
    H: Optional[List[float]] = None  # closed-loop numerator (polydesign/rst)
    F: Optional[List[float]] = None  # feedforward (polydesign/rst/modelmatch)

    # Layout and degree/meta options
    layout: Literal["ogata", "desc"] = "ogata"
    d: int = 0
    degS: Optional[int] = None
    degR: Optional[int] = None

    # Presentation
    pretty: bool = False
    show_E: bool = False

    # Exports (JSON/CSV of results)
    export_json: Optional[str] = None
    export_csv: Optional[str] = None

    # Plot/preview
    backend: Literal["mpl", "plotly", "none"] = "none"
    save: Optional[str] = None
    T: float = 1.0
    kmax: int = 40

    # Ogata parity (shift) handling flag
    ogata_parity: bool = False

    # polydesign-specific: configuration selector
    config: Optional[int] = None

    # rst-specific: configuration selector (default 2 to match examples/tests)
    rst_config: int = 2

    # modelmatch-specific fields
    Gmodel_num: Optional[List[float]] = None
    Gmodel_den: Optional[List[float]] = None
    H1: Optional[List[float]] = None
