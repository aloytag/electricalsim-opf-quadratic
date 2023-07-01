# electricalsim-opf-quadratic

Extension for solving the Optimal Power Flow calculation (OPF) with quadratic costs for the [Electrical Grid Simulator (EGS)](https://github.com/aloytag/electrical-grid-simulator).

This extension uses the `pandapower` capabilities for OPF through the `PYPOWER` solver, according to the `runopp()` and `rundcopp()` functions (AC OPF and DC OPF). For more details, see the `pandapower` documentation [here](https://pandapower.readthedocs.io/en/latest/opf.html).

## Intallation & updates

Using `pip`:

```bash
pip install electricalsim-opf-quadratic -U
```

On MS Windows you may prefer:
```bash
python -m pip install electricalsim-opf-quadratic -U
```
