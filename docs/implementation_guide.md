# Implementation Guide

This guide walks through the practical steps required to run the automated G10 FX data pipeline locally, whether you prefer a lightweight editor (e.g. Cursor, VS Code) or a full IDE such as PyCharm.

## 1. Clone the repository

```bash
git clone https://github.com/<your-org>/FX-Trading-Analysis-Repository.git
cd FX-Trading-Analysis-Repository
```

> Replace `<your-org>` with the actual GitHub owner if it differs.

## 2. Choose your development environment

You can work in **any** IDE or editor that supports Python. Popular choices include:

- **Cursor / VS Code** – open the folder via *File → Open Folder*. A built-in terminal lets you run the commands below without leaving the editor.
- **PyCharm** – import the project via *File → Open*. Configure a virtual environment when prompted.
- **JupyterLab** – launch with `jupyter lab` and create a notebook in the repository directory if you prefer an interactive workflow.

The key requirement is the ability to run shell commands and Python scripts from the project root.

## 3. Create and activate a virtual environment

```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

Creating an isolated environment avoids conflicts with system Python packages.

## 4. Install dependencies

```bash
pip install -r requirements.txt
```

The requirements file pins the core scientific stack (pandas, NumPy, statsmodels, requests, matplotlib) used by the pipeline.

## 5. Run the data pipeline

```bash
python scripts/fetch_g10_data.py
```

The script automatically downloads the required data, aligns the time series, and saves:

- `data/g10_fx_macro_dataset.csv` – the merged monthly dataset.
- `data/eurusd_regression_summary.txt` – OLS regression diagnostics.
- `plots/eurusd_vs_yield_spread.png` – validation chart of EURUSD vs. yield spread.

These paths are created if they do not already exist, so no manual folder setup is needed.

## 6. (Optional) Inspect outputs in your IDE

- Use your editor’s CSV viewer to open the dataset and verify column names.
- Preview the regression summary to confirm the statistical output.
- Display the chart to validate that the pipeline produced the expected visual.

## 7. Customize the pipeline

The script exposes a `build_dataset(start, end)` function. You can import it from another module or notebook to:

- Change the date range (`start`, `end`).
- Add new FRED or Yahoo Finance symbols.
- Extend the feature engineering steps (e.g. volatility calculations, moving averages).

Example usage inside a notebook or another script:

```python
from datetime import datetime
from scripts.fetch_g10_data import build_dataset

df = build_dataset(start=datetime(2010, 1, 1))
df.head()
```

## 8. Troubleshooting tips

- **SSL or network errors** – ensure you have internet access; FRED and Yahoo Finance endpoints must be reachable.
- **Missing packages** – double-check that you activated the virtual environment before running `pip install`.
- **Non-UTC system clock** – if your machine clock is significantly off, Yahoo Finance may reject requests; synchronize the clock if download errors persist.

Following these steps lets you reproduce the dataset exactly as designed, regardless of the editor or IDE you prefer.
