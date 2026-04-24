
import os, json
from polynomial_equations.polynomialTool.io import parse_coeffs, parse_complex_list, save_json, save_csv
from polynomial_equations.polynomialTool.utils import out_path, in_path, ensure_dir_for

def test_parse_helpers_and_save(tmp_path):
    coeffs = parse_coeffs('1, 2; 3')
    cmplx  = parse_complex_list('1+2j, -3j')
    assert coeffs == [1.0,2.0,3.0] and cmplx[0] == complex(1,2)
    js = tmp_path/'a'/'b'/'c.json'; save_json(str(js), {'ok':True})
    assert js.exists()
    csvp = tmp_path/'x.csv'; save_csv(str(csvp), [('A',[1,2])]); assert csvp.exists()

def test_utils_paths_create_dirs(tmp_path):
    p = out_path('nested','file.txt')
    ensure_dir_for(str(tmp_path/'z'/'w'/'k.txt'))
    assert os.path.isdir(os.path.dirname(p))
