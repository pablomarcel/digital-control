
# rstControllers/rstTool — RST Controller (OOP)

Run from repo root:
```bash
python -m rst_controllers.rstTool.cli --help
# or
python rst_controllers/rstTool/cli.py --help
```

## Quick runs (outputs in `rstControllers/rstTool/out/`)
Unity step:
```bash
python -m rst_controllers.rstTool.cli --A "1 -0.8" --B "0.5" --d 1 --poles "0.6 0.6" --Tmode unity_dc --pretty --step 120 --save_csv --export_json
```
Ac-shaped prefilter:
```bash
python -m rst_controllers.rstTool.cli --A "1 -0.8" --B "0.5" --d 1 --Ac "1 -1.2 0.36" --Ao "1" --Tmode ac --pretty --export_json ac_design.json
```
Integrator + extra pole:
```bash
python -m rst_controllers.rstTool.cli --A "1 -0.8" --B "0.5" --d 1 --poles "0.6 0.6 0.3" --integrator --Tmode unity_dc --pretty --step 200 --save_csv rst_int.csv
```
s-plane poles, derive Ac:
```bash
python -m rst_controllers.rstTool.cli --A "1 -0.8" --B "0.5" --d 1 --Ts 0.1 --spoles "-3+4j -3-4j" --Ao "1 -0.4" --Tmode ac --pretty --export_json s_map.json
```
Direct Acl:
```bash
python -m rst_controllers.rstTool.cli --A "1 -0.8" --B "0.5" --d 1 --Acl "1 -1.2 0.36" --pretty --export_json acl_direct.json
```
Degree override:
```bash
python -m rst_controllers.rstTool.cli --A "1 -0.8" --B "0.5" --d 1 --poles "0.6 0.6" --degS 1 --degR 0 --pretty
```
Class diagram:
```bash
python rst_controllers/rstTool/tools/class_diagram.py
```
