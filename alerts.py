import pandas as pd
from dataclasses import dataclass

@dataclass
class AlertRules:
    deficit: bool = True
    momentum_30d_pct: float = 5.0
    slope_trend_enable: bool = True

def evaluate_alerts(sd_df: pd.DataFrame, price_df: pd.DataFrame, unit: str) -> list:
    msgs = []
    if not sd_df.empty:
        latest = sd_df.sort_values('year').iloc[-1]
        bal = latest['supply_mt'] - latest['demand_mt']
        if bal < 0:
            msgs.append(f'Deficit watch: {bal:.2f} {latest["unit"]} (demand exceeds supply).')
    if len(price_df) >= 30:
        p30 = price_df.tail(30)
        mom = (p30['Close'].iloc[-1] / p30['Close'].iloc[0] - 1.0) * 100
        if abs(mom) >= 5.0:
            direction = '↑' if mom > 0 else '↓'
            msgs.append(f'30‑day momentum {direction} {mom:+.1f}%')
        import numpy as np
        slope = np.polyfit(range(len(p30)), p30['Close'].values, 1)[0]
        if slope > 0:
            msgs.append('Trend: Uptrend (positive slope)')
        elif slope < 0:
            msgs.append('Trend: Downtrend (negative slope)')
    return msgs
