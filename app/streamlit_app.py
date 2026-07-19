from pathlib import Path

import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

st.set_page_config(page_title="Getaround — Analyse des Retards", page_icon="🚗", layout="wide")

# Chemin robuste vers le fichier de donnees, independant du dossier de travail
# (Streamlit Cloud lance l'app depuis la racine du repo, mais on veut que ca marche
# aussi en local depuis le dossier app/)
DATA_PATH = Path(__file__).resolve().parent.parent / "data" / "get_around_delay_analysis.xlsx"


@st.cache_data
def load_data():
    return pd.read_excel(DATA_PATH)


@st.cache_data
def build_consec(df):
    df_consec = df.dropna(
        subset=["previous_ended_rental_id", "time_delta_with_previous_rental_in_minutes"]
    ).copy()

    prev_delay = df[["rental_id", "delay_at_checkout_in_minutes"]].rename(
        columns={
            "rental_id": "previous_ended_rental_id",
            "delay_at_checkout_in_minutes": "prev_delay_minutes",
        }
    )
    df_consec = df_consec.merge(prev_delay, on="previous_ended_rental_id", how="left")
    df_consec["is_impacted"] = (
        df_consec["prev_delay_minutes"] > df_consec["time_delta_with_previous_rental_in_minutes"]
    ).fillna(False)
    return df_consec


df = load_data()
df_consec = build_consec(df)
total_rentals = len(df)

st.sidebar.header("Parametres de la politique")
scope_label = st.sidebar.radio(
    "Portee", options=["Toutes les voitures", "Voitures Connect uniquement"], index=0
)
scope = "all" if scope_label == "Toutes les voitures" else "connect"

threshold = st.sidebar.slider(
    "Seuil minimum entre deux locations (minutes)", min_value=0, max_value=720, value=60, step=15
)
st.sidebar.caption(
    "Ajuste le seuil et la portee pour voir l'impact estime sur les revenus "
    "et le nombre de cas de retard resolus."
)

df_scope = df if scope == "all" else df[df["checkin_type"] == "connect"]
consec_scope = df_consec if scope == "all" else df_consec[df_consec["checkin_type"] == "connect"]

blocked = (df_scope["time_delta_with_previous_rental_in_minutes"] < threshold).sum()
pct_revenue_affected = blocked / total_rentals * 100 if total_rentals else 0

total_problematic = consec_scope["is_impacted"].sum()
solved = consec_scope[
    (consec_scope["is_impacted"]) & (consec_scope["time_delta_with_previous_rental_in_minutes"] < threshold)
]
pct_solved = len(solved) / total_problematic * 100 if total_problematic > 0 else 0

st.title("Getaround — Analyse des Retards et Optimisation du Delai Minimum")
st.markdown(
    "Ce tableau de bord aide l'equipe produit a choisir le seuil et la portee "
    "du futur delai minimum entre deux locations, en simulant son impact."
)

col1, col2, col3, col4 = st.columns(4)
col1.metric("Locations totales", f"{total_rentals:,}")
col2.metric("Locations bloquees", f"{blocked:,}")
col3.metric("% revenus potentiellement affectes", f"{pct_revenue_affected:.1f} %")
col4.metric("Cas problematiques resolus", f"{pct_solved:.0f} %")

st.divider()

tab1, tab2, tab3 = st.tabs(
    ["Vue d'ensemble des retards", "Simulation seuil / portee", "Impact location suivante"]
)

with tab1:
    st.subheader("Distribution des retards au checkout")
    df_delay = df[df["state"] == "ended"].dropna(subset=["delay_at_checkout_in_minutes"]).copy()
    df_delay_clipped = df_delay[df_delay["delay_at_checkout_in_minutes"].between(-120, 300)]

    fig_hist = px.histogram(
        df_delay_clipped,
        x="delay_at_checkout_in_minutes",
        color="checkin_type",
        nbins=60,
        barmode="overlay",
        opacity=0.7,
        labels={
            "delay_at_checkout_in_minutes": "Retard au checkout (minutes)",
            "checkin_type": "Type de check-in",
        },
        title="Distribution des retards - Mobile vs Connect (recadre entre -120 et +300 min)",
    )
    fig_hist.add_vline(x=0, line_dash="dash", line_color="gray")
    st.plotly_chart(fig_hist, use_container_width=True)

    n_late = (df_delay["delay_at_checkout_in_minutes"] > 0).sum()
    pct_late = n_late / len(df_delay) * 100 if len(df_delay) else 0
    late_by_type = (
        df_delay.assign(is_late=df_delay["delay_at_checkout_in_minutes"] > 0)
        .groupby("checkin_type")["is_late"]
        .mean()
        .mul(100)
        .round(1)
    )

    c1, c2 = st.columns(2)
    c1.metric("Taux de retard global", f"{pct_late:.1f} %")
    c2.write("Taux de retard par type de check-in :")
    c2.dataframe(late_by_type.rename("% en retard"))

with tab2:
    st.subheader(f"Impact simule - Portee : {scope_label}, Seuil : {threshold} min")

    thresholds = [30, 60, 90, 120, 150, 180, 210, 240, 300, 360, 480, 720]
    rows = []
    for t in thresholds:
        b = (df_scope["time_delta_with_previous_rental_in_minutes"] < t).sum()
        s = consec_scope[
            (consec_scope["is_impacted"])
            & (consec_scope["time_delta_with_previous_rental_in_minutes"] < t)
        ]
        rows.append(
            {
                "Seuil (min)": t,
                "% revenus affectes": b / total_rentals * 100 if total_rentals else 0,
                "% cas resolus": len(s) / total_problematic * 100 if total_problematic > 0 else 0,
            }
        )
    sim_df = pd.DataFrame(rows)

    fig_sim = go.Figure()
    fig_sim.add_trace(
        go.Scatter(x=sim_df["Seuil (min)"], y=sim_df["% revenus affectes"],
                   name="% revenus affectes", mode="lines+markers")
    )
    fig_sim.add_trace(
        go.Scatter(x=sim_df["Seuil (min)"], y=sim_df["% cas resolus"],
                   name="% cas resolus", mode="lines+markers")
    )
    fig_sim.add_vline(x=threshold, line_dash="dash", line_color="red",
                       annotation_text="Seuil selectionne")
    fig_sim.update_layout(xaxis_title="Seuil (minutes)", yaxis_title="%",
                          title="Compromis revenus vs resolution des cas problematiques")
    st.plotly_chart(fig_sim, use_container_width=True)

    st.dataframe(sim_df.round(1), use_container_width=True, hide_index=True)

with tab3:
    st.subheader("Retards precedents impactant la location suivante")

    n_consec = len(consec_scope)
    n_impacted = int(consec_scope["is_impacted"].sum())
    pct_impacted = n_impacted / n_consec * 100 if n_consec else 0

    c1, c2 = st.columns(2)
    c1.metric("Locations avec une precedente identifiee", f"{n_consec:,}")
    c2.metric("Impactees par le retard precedent", f"{n_impacted:,} ({pct_impacted:.1f} %)")

    fig_delta = px.histogram(
        consec_scope,
        x="time_delta_with_previous_rental_in_minutes",
        color="is_impacted",
        nbins=50,
        labels={
            "time_delta_with_previous_rental_in_minutes": "Delai avec la location precedente (minutes)",
            "is_impacted": "Cas impacte",
        },
        title="Delai entre deux locations, selon qu'il y a eu impact ou non",
    )
    fig_delta.add_vline(x=threshold, line_dash="dash", line_color="red",
                         annotation_text="Seuil selectionne")
    st.plotly_chart(fig_delta, use_container_width=True)

st.divider()
st.caption("Source : get_around_delay_analysis.xlsx - voir notebooks/01_eda_delays.ipynb pour l'analyse complete.")
