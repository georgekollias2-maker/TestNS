"""Analog Pivot (Streamlit): φίλτρα, ομαδοποίηση και συναθροίσεις σε πίνακα NASA.

Τοπική χρήση:  streamlit run pivot_app.py
Προετοιμασία πριν το hackathon, με βοήθεια AI (Claude).
"""
import io

import numpy as np
import pandas as pd
import streamlit as st

st.set_page_config(page_title="Analog Pivot", layout="wide")
st.title("Analog Pivot")

FUNCS = {"μέσος όρος": "mean", "άθροισμα": "sum", "μέγιστο": "max", "ελάχιστο": "min",
         "πλήθος τιμών": "count", "διακριτές τιμές": "nunique"}


def read_power_csv(raw: bytes) -> pd.DataFrame:
    """CSV, με παράλειψη του header του NASA POWER αν υπάρχει."""
    text = raw.decode("utf-8-sig", errors="replace")
    if "-END HEADER-" in text:
        text = text.split("-END HEADER-", 1)[1].split("\n", 1)[1]
    return pd.read_csv(io.StringIO(text), sep=None, engine="python")


up = st.sidebar.file_uploader("Αρχείο CSV", type=["csv", "txt", "tsv"])
if up is None:
    st.info("Ανεβάστε ένα CSV (π.χ. από το NASA POWER).")
    st.stop()

df = read_power_csv(up.getvalue())
if st.sidebar.checkbox("-999 → κενό (fill value του POWER)", value=True):
    df = df.replace(-999, np.nan)
st.sidebar.caption(f"{len(df):,} γραμμές · {df.shape[1]} στήλες")

# --- Φίλτρα ---
st.sidebar.header("Φίλτρα")
d = df
for col in st.sidebar.multiselect("Στήλες για φίλτρο", df.columns):
    s = df[col]
    if pd.api.types.is_numeric_dtype(s) and s.nunique() > 20:
        lo, hi = float(s.min()), float(s.max())
        a, b = st.sidebar.slider(col, lo, hi, (lo, hi))
        d = d[d[col].between(a, b)]
    else:
        opts = sorted(s.dropna().unique().tolist())
        keep = st.sidebar.multiselect(col, opts, default=opts)
        d = d[d[col].isin(keep)]

# --- Ομαδοποίηση και συναθροίσεις ---
c1, c2, c3 = st.columns(3)
group = c1.multiselect("Ομαδοποίηση ανά", df.columns)
num_cols = [c for c in df.columns if pd.api.types.is_numeric_dtype(df[c]) and c not in group]
values = c2.multiselect("Στήλες τιμών", num_cols, default=num_cols[:1])
funcs = c3.multiselect("Πράξεις", list(FUNCS), default=["μέσος όρος", "μέγιστο"])

st.caption(f"{len(df):,} γραμμές → {len(d):,} μετά τα φίλτρα")

if values and funcs:
    spec = {f"{v}_{FUNCS[f]}": (v, FUNCS[f]) for v in values for f in funcs}
    out = (d.groupby(group, dropna=False).agg(**spec).reset_index() if group
           else d.agg({v: [FUNCS[f] for f in funcs] for v in values}))
    st.dataframe(out, use_container_width=True)
    st.download_button("Λήψη CSV", out.to_csv(index=not group).encode("utf-8-sig"), "pivot_result.csv")
else:
    st.warning("Διαλέξτε τουλάχιστον μία στήλη τιμών και μία πράξη.")