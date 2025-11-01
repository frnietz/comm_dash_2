import os
import requests
import pandas as pd
from dotenv import load_dotenv
load_dotenv()

EIA_API_KEY = os.getenv('EIA_API_KEY', '')

def _safe_get(url, params=None, timeout=20):
    try:
        r = requests.get(url, params=params, timeout=timeout)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        return {'error': str(e), 'url': url, 'params': params}

# World Bank Indicators API v2
def worldbank_indicator(indicator: str, country: str = 'WLD', date: str = '2000:2025') -> pd.DataFrame:
    base = f'https://api.worldbank.org/v2/country/{country}/indicator/{indicator}'
    params = {'format': 'json', 'date': date, 'per_page': 20000}
    data = _safe_get(base, params=params)
    if isinstance(data, dict) and 'error' in data:
        return pd.DataFrame()
    rows = data[1] if isinstance(data, list) and len(data) > 1 else []
    df = pd.DataFrame(rows)
    if df.empty:
        return df
    df = df[['date','value']].dropna()
    df['date'] = pd.to_datetime(df['date'].astype(str) + '-12-31')
    df = df.sort_values('date').reset_index(drop=True)
    return df

# FAOSTAT QCL domain (demo mapping)
FAOSTAT_BASE = 'https://fenixservices.fao.org/faostat/api/v1/en/QCL'
FAOSTAT_ITEMS = {'Wheat': 15, 'Maize': 56, 'Soybeans': 236, 'Barley': 44}

def faostat_production_world(item_name: str, element: str = 'Production', area: str = 'World', year_start: int = 2000, year_end: int = 2024) -> pd.DataFrame:
    code = FAOSTAT_ITEMS.get(item_name)
    if code is None:
        return pd.DataFrame()
    params = {'item_code': code, 'element': element, 'area': area, 'year': f'{year_start}:{year_end}'}
    try:
        r = requests.get(FAOSTAT_BASE, params=params, timeout=30)
        r.raise_for_status()
        j = r.json()
        df = pd.DataFrame(j.get('data', []))
        if df.empty:
            return df
        if 'year' not in df.columns and 'Year' in df.columns:
            df['year'] = df['Year']
        if 'value' not in df.columns and 'Value' in df.columns:
            df['value'] = df['Value']
        return df[['year','value']].sort_values('year')
    except Exception:
        return pd.DataFrame()

# EIA Open Data
def eia_series(series_id: str) -> pd.DataFrame:
    if not EIA_API_KEY:
        return pd.DataFrame()
    url_v1 = 'https://api.eia.gov/series/'
    params = {'api_key': EIA_API_KEY, 'series_id': series_id}
    try:
        r = requests.get(url_v1, params=params, timeout=30)
        r.raise_for_status()
        j = r.json()
        series = j.get('series', [{}])[0]
        data = series.get('data', [])
        df = pd.DataFrame(data, columns=['date_str','Close'])
        df['date'] = pd.to_datetime(df['date_str'], errors='coerce')
        df = df.dropna(subset=['date']).sort_values('date')
        return df[['date','Close']]
    except Exception:
        return pd.DataFrame()

# Google News RSS via feedparser
def google_news_rss(query: str, hl: str='en-US', gl: str='US', ceid: str='US:en', max_items: int=10):
    import feedparser, urllib.parse
    url = f'https://news.google.com/rss/search?q={urllib.parse.quote(query)}&hl={hl}&gl={gl}&ceid={ceid}'
    feed = feedparser.parse(url)
    out = []
    for e in feed.entries[:max_items]:
        src = ''
        try:
            src = getattr(e, 'source', {}).get('title','') if hasattr(e, 'source') else ''
        except Exception:
            src = ''
        out.append({'title': e.get('title'), 'link': e.get('link'), 'published': e.get('published',''), 'source': src})
    return out
