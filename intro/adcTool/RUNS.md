# intro.adcTool — Counter & SAR ADC simulators

Run **from inside the package**:

```bash
cd digitalControl/intro/adcTool
```
```bash
python cli.py --help
```

## Counter-type examples

```bash
python cli.py --type counter --csv vins.csv --nbits 10 --vref 3.3 --tclk 1e-6 --out counter_results.csv --trace counter.vcd
```

```bash
python cli.py --type counter --json vins.json --nbits 12 --vref 5.0 --tclk 2e-6 --trace-all counter_all.vcd
```

## SAR examples

```bash
python cli.py --type sar --csv vins.csv --nbits 12 --vref 3.3 --tbit 1e-6 --out sar_results.csv --trace sar.vcd --radix all
```

```bash
python cli.py --type sar --json vins.json --nbits 10 --vref 3.3 --tbit 5e-7 --trace-all sar_all.vcd
```

## Class Diagram

```bash
python tools/class_diagram.py --out out
```
# => out/adcTool_class_diagram.puml
