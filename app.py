
import streamlit as st
import pandas as pd
import numpy as np
import json
import plotly.express as px
import plotly.graph_objects as go
import yfinance as yf
from pathlib import Path
from datetime import datetime, timedelta

st.set_page_config(page_title="Commodity Dashboard", layout="wide")

DATA_DIR = Path(__file__).parent / "data"

@st.cache_data
def load_meta():
    with open(DATA_DIR / "commodity_meta.json", "r") as f:
        return json.load(f)

@st.cache_data
def load_csv(name):
    return pd.read_csv(DATA_DIR / name)

meta = load_meta()
supply_demand = load_csv("supply_demand.csv")
sectors = load_csv("sector_breakdown.csv")
production = load_csv("production_locations.csv")

# ---------- Sidebar ----------
st.sidebar.title("🔎 Explorer")
commodities = list(meta.keys())
default_selection = "Platinum" if "Platinum" in commodities else commodities[0]
commodity = st.sidebar.selectbox("Select commodity", commodities, index=commodities.index(default_selection))

period = st.sidebar.selectbox("Price history", ["1y", "3y", "5y", "max"], index=2)
st.sidebar.caption("Data via Yahoo Finance where available; falls back to local samples.")

# ---------- Header KPIs ----------
m = meta[commodity]
left, mid, right, right2 = st.columns([2,1,1,1])
left.markdown(f"## {m['display_name']} Dashboard")
left.write(m.get("notes",""))

# Try to fetch latest price
price_val = None
ticker = m.get("yfinance_ticker")
if ticker:
    try:
        ticker_obj = yf.Ticker(ticker)
        recent = ticker_obj.history(period="5d")["Close"].dropna()
        if len(recent):
            price_val = float(recent.iloc[-1])
    except Exception as e:
        price_val = None

if price_val is None:
    # Fallback simulated
    price_val = 100.0

mid.metric(label=f"Price ({m['unit_price']})", value=f\"{price_val:,.2f}\")
right.metric(label="Market Cap / Size (USD bn)", value=f\"{m['market_cap_or_size_usd_bil']:,.1f}\")

# Supply-demand latest
sd = supply_demand[supply_demand['commodity']==commodity].sort_values("year")
latest_row = sd.iloc[-1]
balance = latest_row['supply_mt'] - latest_row['demand_mt']
badge = "🟥 Deficit" if balance < 0 else ("🟩 Surplus" if balance > 0 else "🟨 Balanced")
right2.metric(label="Balance (latest)", value=badge, delta=f\"{balance:,.2f} {latest_row['unit']}\")

st.markdown("---")

# ---------- Price History ----------
st.subheader("📈 Price History")
period_map = {"1y":"1y","3y":"3y","5y":"5y","max":"max"}
yf_period = period_map[period]

price_df = pd.DataFrame()
if ticker:
    try:
        hist = yf.download(ticker, period=yf_period, interval="1d")['Close'].dropna().to_frame(name="Close")
        price_df = hist.reset_index().rename(columns={"Date":"date"})
    except Exception as e:
        price_df = pd.DataFrame()

if price_df.empty:
    # fallback synthetic series
    rng = pd.date_range(end=datetime.today(), periods=365 if period=='1y' else 1825)
    vals = np.cumsum(np.random.normal(0, 0.5, size=len(rng))) + price_val
    price_df = pd.DataFrame({"date": rng, "Close": vals})

fig_price = px.line(price_df, x="date", y="Close", title=f"{m['display_name']} price")
fig_price.update_layout(margin=dict(l=0,r=0,t=40,b=0), height=360)
st.plotly_chart(fig_price, use_container_width=True)

# Simple trend insight
if len(price_df) > 30:
    last_180 = price_df.tail(180)
    x = np.arange(len(last_180))
    y = last_180["Close"].values
    slope = np.polyfit(x,y,1)[0]
    st.caption(f"Trend (last ~180 sessions): {'⬆️ Uptrend' if slope>0 else '⬇️ Downtrend' if slope<0 else '➡️ Flat'} (slope={slope:.3f})")

# ---------- Supply & Demand ----------
st.subheader("⚖️ Supply vs Demand")
sd_plot = sd.copy()
fig_sd = go.Figure()
fig_sd.add_trace(go.Bar(x=sd_plot["year"], y=sd_plot["supply_mt"], name="Supply"))
fig_sd.add_trace(go.Bar(x=sd_plot["year"], y=sd_plot["demand_mt"], name="Demand"))
fig_sd.update_layout(barmode="group", xaxis_title="Year", yaxis_title=f"Volume ({latest_row['unit']})", height=380, margin=dict(l=0,r=0,t=40,b=0))
st.plotly_chart(fig_sd, use_container_width=True)

# ---------- Production Map ----------
st.subheader("🌍 Top Production Locations")
prod = production[production['commodity']==commodity].copy()
# Separate "OTH" to avoid map issues
prod_map = prod[prod['iso3']!="OTH"]
fig_map = px.choropleth(prod_map, locations="iso3", color="share_pct", hover_name="country",
                         color_continuous_scale="Blues", title="Share of global production (%)")
fig_map.update_layout(height=420, margin=dict(l=0,r=0,t=40,b=0))
st.plotly_chart(fig_map, use_container_width=True)

# Top producers table
st.dataframe(prod.sort_values("share_pct", ascending=False).reset_index(drop=True))

# ---------- Market Breakdown by Sector ----------
st.subheader("🏭 Market Breakdown by Sector")
sec = sectors[sectors['commodity']==commodity].sort_values("share_pct", ascending=False)
fig_sec = px.pie(sec, names="sector", values="share_pct", title="End-use sectors (%)")
fig_sec.update_layout(height=380, margin=dict(l=0,r=0,t=40,b=0))
st.plotly_chart(fig_sec, use_container_width=True)

# ---------- Insights ----------
st.subheader("🧠 Insights")
# Balance insight
latest_year = int(sd['year'].max())
prev_year = int(sd['year'].nlargest(2).iloc[-1]) if len(sd)>=2 else latest_year
latest_bal = sd[sd['year']==latest_year].iloc[0]
prev_bal = sd[sd['year']==prev_year].iloc[0] if latest_year!=prev_year else latest_bal

def balance_label(row):
    diff = row['supply_mt'] - row['demand_mt']
    if diff < 0: return f"Deficit ({diff:.2f} {row['unit']})"
    if diff > 0: return f"Surplus (+{diff:.2f} {row['unit']})"
    return "Balanced"

points = []
points.append(f"**Balance**: {balance_label(latest_bal)} for {latest_year}; {balance_label(prev_bal)} in {prev_year}.")

# Concentration
top_share = prod[prod['country']!="Other"]["share_pct"].max() if len(prod)>0 else 0
if top_share >= 50:
    points.append(f"**Concentration risk**: Top producer holds {top_share:.0f}% share.")

# Sector exposure
top_two = sec.head(2)['sector'].tolist()
if top_two:
    points.append(f"**Demand drivers**: Key end-use sectors are {', '.join(top_two)}.")

# Price momentum (last 30 days)
if len(price_df)>=30:
    p30 = price_df.tail(30)
    mom = (p30['Close'].iloc[-1] / p30['Close'].iloc[0] - 1.0) * 100
    points.append(f"**Momentum (30d)**: {mom:+.1f}%")

for p in points:
    st.markdown(f"- {p}")


# ---------- Live Sources & News ----------
from data_sources import worldbank_indicator, faostat_production_world, eia_series, google_news_rss
from alerts import evaluate_alerts
from dotenv import load_dotenv; load_dotenv()

st.markdown('### 🔌 Live Data (optional)')
with st.expander('Configure live sources (optional)', expanded=False):
    st.write('World Bank and FAOSTAT: no key. EIA requires EIA_API_KEY in a .env file.')
    if st.checkbox('Fetch FAOSTAT (demo crops only)', value=False, key='faostat_toggle'):
        if commodity in ['Wheat','Maize','Barley','Soybeans']:
            fao = faostat_production_world(commodity)
            if not fao.empty:
                st.line_chart(fao.set_index('year')['value'], height=200)
            else:
                st.info('FAOSTAT: No data returned (adjust mapping in data_sources.py).')
        else:
            st.caption('FAOSTAT demo mapping included for a few crops. Edit FAOSTAT_ITEMS to expand.')

    colA, colB = st.columns(2)
    with colA:
        ind = st.text_input('World Bank indicator code (e.g., EG.USE.PCAP.KG.OE)', value='')
        if st.button('Fetch WDI', type='secondary'):
            if ind.strip():
                wdi = worldbank_indicator(ind, 'WLD', '2000:2025')
                if not wdi.empty:
                    st.line_chart(wdi.set_index('date')['value'], height=220)
                else:
                    st.warning('World Bank: No rows or invalid code.')
    with colB:
        series_id = st.text_input('EIA series_id (e.g., PET.RWTC.D)', value='')
        if st.button('Fetch EIA', type='secondary'):
            e = eia_series(series_id)
            if not e.empty:
                st.line_chart(e.set_index('date')['Close'], height=220)
            else:
                st.warning('EIA: No data (check key and series id).')

st.subheader('📰 Latest News')
news_query = f"{m['display_name']} price OR supply OR demand OR forecast"
news_items = google_news_rss(news_query, hl='en-US', gl='US', ceid='US:en', max_items=6)
if news_items:
    for n in news_items:
        st.markdown(f"- [{n['title']}]({n['link']}) • {n.get('published','')}")
else:
    st.caption('No news items parsed.')

st.subheader('🚨 Alerts')
alert_msgs = evaluate_alerts(sd, price_df, latest_row['unit'])
if alert_msgs:
    for a in alert_msgs:
        st.markdown(f"- **{a}**")
else:
    st.caption('No alerts triggered based on current rules.')


st.markdown("---")
st.caption("Note: 'Market Cap / Size' is an indicative market value for the physical commodity, where applicable, not an equity market cap. Data sources to integrate: FAOSTAT (agri), IEA/EIA (energy), USGS (metals), World Bank, LME/COMEX, OPEC, industry councils.")

