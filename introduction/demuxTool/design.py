from __future__ import annotations
"""Design-time helpers and (optional) class diagram generation."""
from typing import List
try:
    import graphviz  # optional
except Exception:  # pragma: no cover
    graphviz = None

def class_diagram_dot() -> str:
    return r"""
    digraph DemuxTool {
        rankdir=LR;
        node [shape=record, fontsize=11];
        App    [label="{DemuxApp|+ run(req): RunResult}"];
        Circuit[label="{DemuxCircuit|+ build(): ports\l+ simulate(vectors): rows}"];
        IO     [label="{io.py|+ load_rows_from_*\l+ write_results_csv\l+ write_vcd}"];
        Utils  [label="{utils.py|+ resolve_*\l+ mask}"];
        App -> Circuit [label="uses"];
        App -> IO [label="reads/writes"];
        App -> Utils [label="paths"];
    }
    """

def render_class_diagram(out_path: str) -> str:
    """Render DOT to a PNG if graphviz is installed; else write DOT."""
    dot = class_diagram_dot()
    if graphviz is None:
        with open(out_path, "w") as f:
            f.write(dot)
        return out_path
    g = graphviz.Source(dot)
    out = g.render(out_path, format="png", cleanup=True)
    return out
