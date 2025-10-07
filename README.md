# FX Trading Analysis Repository

This repository contains Python tooling to source and analyse macro drivers behind G10 FX crosses. The first milestone implements a reproducible pipeline that downloads five or more years of monthly data for exchange rates, short-term yield differentials, commodity prices, and risk appetite metrics.

## Getting started

If you are new to running Python projects, follow the step-by-step walkthrough in [`docs/implementation_guide.md`](docs/implementation_guide.md). It explains how to open the repository in IDEs such as Cursor or PyCharm, configure a virtual environment, and execute the pipeline. The abbreviated instructions are:

1. Create a virtual environment and install the scientific Python stack:
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```
2. Run the data build script:
   ```bash
   python scripts/fetch_g10_data.py
   ```

The script saves the consolidated dataset to `data/g10_fx_macro_dataset.csv`, exports an OLS regression summary (`data/eurusd_regression_summary.txt`), and writes a diagnostic chart to `plots/eurusd_vs_yield_spread.png`.

> 💡 You do **not** need to execute multiple files—`scripts/fetch_g10_data.py` calls every step of the pipeline. The other
> tracked files are documentation or generated outputs.

## Repository contents

- `scripts/fetch_g10_data.py` – pulls historical FX and macro series, engineers features (log returns, yield spreads), and runs an illustrative statsmodels regression.
- `data/` – output folder for the aligned dataset and regression diagnostics.
- `plots/` – generated figures, including EURUSD vs. its yield differential.
- `docs/data_dictionary.md` – documentation of each field plus economic intuition.

## Next steps

- Extend the feature set with additional commodity or equity market factors.
- Explore predictive models (rolling regressions, machine learning) using the prepared dataset.
- Package the workflow as a notebook with more exploratory charts for presentation.
