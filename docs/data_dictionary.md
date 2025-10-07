# G10 FX Macro Dataset Dictionary

The dataset produced by `scripts/fetch_g10_data.py` aligns monthly observations for major G10 FX crosses and key macro drivers. Values are aggregated to calendar month end. Unless noted otherwise, numeric units are percentages or price levels in their native currency.

| Column | Description | Economic intuition |
| --- | --- | --- |
| `eurusd`, `gbpusd`, `audusd`, `nzdusd` | Monthly closing USD price for EUR, GBP, AUD, NZD (USD per 1 unit of foreign currency) from Yahoo Finance. | Captures spot FX levels; appreciation/depreciation reflects capital flows, policy expectations, and macro shocks. |
| `usdjpy`, `usdchf`, `usdcad`, `usdsek`, `usdnok` | Monthly closing quote for USD vs. JPY/CHF/CAD/SEK/NOK (foreign currency units per USD) from Yahoo Finance. | Represents USD strength against safe-haven (JPY, CHF) and pro-cyclical (CAD, SEK, NOK) currencies. |
| `us_2y_yield` | US 2-year Treasury constant maturity yield (percent) from FRED series `DGS2`. | Baseline US short-term interest rate; higher yields typically support USD. |
| `ea_2y_yield`, `jp_2y_yield`, `uk_2y_yield`, `au_2y_yield`, `nz_2y_yield`, `ca_2y_yield`, `ch_2y_yield`, `se_2y_yield`, `no_2y_yield` | Local 2-year sovereign yields for Euro Area, Japan, UK, Australia, New Zealand, Canada, Switzerland, Sweden, and Norway (FRED `IRLTLT02*`). | Reflect market expectations for local monetary policy. Yield gaps vs. US drive carry/forward premium and influence FX via interest rate parity. |
| `dxy` | Trade-weighted broad US Dollar Index from FRED `DTWEXBGS`. | Gauge of overall USD performance vs. major partners; useful control variable. |
| `wti_crude` | WTI crude oil spot price (USD/barrel) from FRED `DCOILWTICO`. | Key driver for commodity currencies (CAD, NOK) via terms of trade and export revenues. |
| `london_gold_fix` | London Bullion Market gold fixing price (USD/troy ounce) from FRED `GOLDAMGBD228NLBM`. | Supports AUD/NZD as commodity-linked currencies; gold is a major Australian export. |
| `vix` | CBOE Volatility Index (VIX) from FRED `VIXCLS`. | Proxy for global risk sentiment; spikes usually coincide with USD strength and weakness in risk-sensitive currencies. |
| `*_log_return` | Log return of corresponding FX rate (`ln(price_t) - ln(price_{t-1})`). | Normalises FX moves for regression analysis and captures monthly percentage change. |
| `*_2y_differential` | Interest rate differential: `US 2Y yield - foreign 2Y yield` for each FX pair. | Implements uncovered interest parity intuition: wider spreads tend to attract capital to higher-yielding currency (supporting USD when positive). |

Running the script also saves `data/eurusd_regression_summary.txt`, which contains an OLS regression of `eurusd_log_return` on the 2-year yield spread and VIX changes to illustrate linking FX moves to macro factors.
