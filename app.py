import streamlit as st
st.set_page_config(page_title='Commodity Dashboard', layout='wide')
st.write('Base app placeholder. Please re-run the full generator if needed.')
from pathlib import Path
DATA_DIR = Path(__file__).parent / 'data'

# === Pro Features: Sentiment, Futures Curve, Options Skew, Alerts UI, Push Alerts ===
import json
import yfinance as yf
import pandas as pd
from sentiment import score_headlines
from notifier import send_email, send_telegram
from pathlib import Path
DATA_DIR = Path(__file__).parent / 'data'

st.markdown('---')
st.header('Pro Analytics')

st.subheader('News Sentiment')
if 'news_items' in globals() and news_items:
    try:
        enriched = score_headlines(news_items)
        avg_sent = sum(i.get('sentiment',0.0) for i in enriched)/len(enriched)
        st.metric('Avg headline sentiment (VADER)', f"{avg_sent:+.3f}")
        with st.expander('Headline scores'):
            for it in enriched:
                st.write(f"{it.get('sentiment',0):+0.3f} — {it.get('title','')}")
    except Exception:
        st.caption('Sentiment scoring unavailable (install vaderSentiment).')
else:
    st.caption('No news parsed yet to score sentiment.')

st.subheader('Futures Curve (Yahoo)')
curve_points = []
try:
    fmap = json.loads((DATA_DIR / 'futures_mapping.json').read_text())
    tickers = fmap.get(commodity, [])
    for tk in tickers:
        try:
            close = yf.download(tk, period='5d', interval='1d')['Close'].dropna()
            if len(close):
                curve_points.append({'ticker': tk, 'price': float(close.iloc[-1])})
        except Exception:
            pass
    if curve_points:
        cdf = pd.DataFrame(curve_points)
        st.bar_chart(cdf.set_index('ticker')['price'], height=240)
    else:
        st.caption('No curve points. Edit data/futures_mapping.json for your market.')
except Exception:
    st.caption('Futures mapping file missing or unreadable.')

st.subheader('Options Skew (ETF proxy)')
try:
    proxy_map = json.loads((DATA_DIR / 'options_proxy.json').read_text())
    proxy = proxy_map.get(commodity)
    if proxy:
        t = yf.Ticker(proxy)
        exps = t.options
        if exps:
            exp = exps[0]
            oc = t.option_chain(exp)
            calls, puts = oc.calls.copy(), oc.puts.copy()
            spot_hist = t.history(period='5d')['Close'].dropna()
            if len(spot_hist):
                spot = float(spot_hist.iloc[-1])
                calls['dist'] = (calls['strike'] - 1.25*spot).abs()
                puts['dist'] = (puts['strike'] - 0.75*spot).abs()
                c_iv = float(calls.nsmallest(1, 'dist')['impliedVolatility'].iloc[0]) if not calls.empty else float('nan')
                p_iv = float(puts.nsmallest(1, 'dist')['impliedVolatility'].iloc[0]) if not puts.empty else float('nan')
                if c_iv == c_iv and p_iv == p_iv:
                    skew = (c_iv - p_iv) * 100
                    st.metric('25Δ Call–Put IV Skew (≈)', f"{skew:+.2f} pp")
                else:
                    st.caption('Missing IV values to compute skew.')
            else:
                st.caption('No recent spot data for proxy symbol.')
        else:
            st.caption('No option expiries available.')
    else:
        st.caption('No proxy mapping for this commodity.')
except Exception:
    st.caption('Options data fetch failed (Yahoo or mapping).')

st.subheader('Alerts — Thresholds & Delivery')
with st.form('alerts_form_pro'):
    deficit_enable = st.checkbox('Alert on Supply Deficit', value=True)
    momentum_thr   = st.slider('30‑day momentum threshold (%)', 0.0, 20.0, 5.0, 0.5)
    email_enable   = st.checkbox('Email (SMTP in .env)')
    tg_enable      = st.checkbox('Telegram (.env)')
    test_btn       = st.form_submit_button('Save / Test Now')
    if test_btn:
        triggered = []
        try:
            latest = sd.sort_values('year').iloc[-1]
            bal = latest['supply_mt'] - latest['demand_mt']
            if deficit_enable and bal < 0:
                triggered.append(f'Deficit watch: {bal:.2f} {latest["unit"]}.')
        except Exception:
            pass
        try:
            if len(price_df) >= 30:
                p30 = price_df.tail(30)
                mom = (p30['Close'].iloc[-1] / p30['Close'].iloc[0] - 1.0) * 100
                if abs(mom) >= momentum_thr:
                    direction = '↑' if mom > 0 else '↓'
                    triggered.append(f'30‑day momentum {direction} {mom:+.1f}% (≥ {momentum_thr:.1f}%).')
        except Exception:
            pass
        if triggered:
            st.success('Alerts triggered:\n' + '\n'.join(triggered))
            msg = f'{commodity} Alerts:\n' + '\n'.join(triggered)
            if email_enable:
                st.write('Email sent:' if send_email(f'{commodity} Alert', msg) else 'Email not sent (check .env).')
            if tg_enable:
                st.write('Telegram sent:' if send_telegram(msg) else 'Telegram not sent (check .env).')
        else:
            st.info('No alerts fired with current settings. You can still test delivery.')
