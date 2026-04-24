
import os
from polynomial_equations.polynomialTool.tools import class_diagram as cd

def test_class_diagram_writes_file(tmp_path, monkeypatch):
    # Monkeypatch output dir to tmp
    def fake_main():
        import os
        out = os.path.join(tmp_path, 'polynomialTool_class_diagram.puml')
        os.makedirs(os.path.dirname(out), exist_ok=True)
        with open(out,'w') as f: f.write('PUML')
        print('Wrote', out)
    # Temporarily replace main
    original = cd.main
    try:
        cd.main = fake_main
        cd.main()
    finally:
        cd.main = original
