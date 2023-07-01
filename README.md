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

## Screenshots

![Select and execute the extension in EGS](img/EGS_extension_manager.png)
<p align = "center">
<i>Select and execute the extension in EGS</i>
</p>

![Running the extension](img/opf_with_EGS.png)
<p align = "center">
<i>Running the extension</i>
</p>

![Tab 1: Cost coefficients](img/tab1.png)
<p align = "center">
<i>Tab 1: Cost coefficients</i>
</p>

![Tab 2: Model and basic solver settings](img/tab2.png)
<p align = "center">
<i>Tab 2: Model and basic solver settings</i>
</p>

![Tab 3: Advanced solver parameters](img/tab3.png)
<p align = "center">
<i>Tab 3: Advanced solver parameters</i>
</p>

![Results](img/results.png)
<p align = "center">
<i>Results</i>
</p>
