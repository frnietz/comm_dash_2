# Commodity Dashboard

A ready-to-run Streamlit app that shows:
- Price & Market Cap/Size
- Price history
- Supply–Demand balance
- Top production locations (map + table)
- Market breakdown by sector
- Auto-generated insights

## Quickstart

```bash
pip install -r requirements.txt
streamlit run app.py
```

### Commodity → Yahoo Finance Ticker Mapping
Edit `data/commodity_meta.json` to set the correct ticker. Defaults:
- Platinum: `PL=F`
- Copper: `HG=F`
- Crude Oil (WTI): `CL=F`
- Wheat: `ZW=F`

If no internet or ticker fails, the app will fall back to synthetic sample data.

## Data you can replace
- `data/supply_demand.csv` — history + simple 2-year forecast
- `data/production_locations.csv` — ISO3 codes required for map (exclude row with iso3=OTH)
- `data/sector_breakdown.csv` — end-use shares
- `data/commodity_meta.json` — units, ticker, and indicative market size
- `data/insights_playbook.md` — logic description for insights

## Notes
- 'Market Cap / Size' is an indicative physical market size, not an equity market cap.
- Consider connecting real sources (FAOSTAT, IEA/EIA, USGS, World Bank) in a data pipeline for production.


## Live Data Connectors
- FAOSTAT (no key): `faostat_production_world()` from QCL domain. Expand `FAOSTAT_ITEMS` in `data_sources.py`.
- World Bank (no key): `worldbank_indicator(indicator, country='WLD')`.
- EIA (API key): create `.env` from `.env.example` and set `EIA_API_KEY`.
- News Panel: Google News RSS via `feedparser`.

## Alerts
- Deficit watch (demand > supply).
- 30‑day momentum threshold (default 5%).
- Trend slope check.
