import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
from utils import load_data, calculate_fleet_power

# Configuration
st.set_page_config(page_title="Tesla Power Trading Business Opportunity", layout="wide", page_icon="⚡")

# CSS pour la police Tesla et style des tableaux
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@400;500;600;700&display=swap');

html, body, [class*="css"] {
    font-family: 'Montserrat', sans-serif !important;
}

.stDataFrame {
    font-family: 'Montserrat', sans-serif !important;
    text-align: center !important;
}

.stDataFrame th {
    text-align: center !important;
    font-weight: 600 !important;
}

.stDataFrame td {
    text-align: center !important;
}

.estimated {
    color: #888888 !important;
    font-style: italic !important;
}

h1, h2, h3, h4, h5, h6 {
    font-family: 'Montserrat', sans-serif !important;
    font-weight: 600 !important;
    text-align: center !important;
}

.stDataFrame table {
    margin-left: auto;
    margin-right: auto;
}
</style>
""", unsafe_allow_html=True)

# Logo Tesla
col1, col2 = st.columns([1, 8])
with col1:
    try:
        st.image("tesla_fleet_analysis/tesla.png", width=80)
    except:
        try:
            st.image("tesla.png", width=80)
        except:
            pass

with col2:
    st.markdown("<h1 style='margin-top: 0; font-family: Montserrat;'>Tesla Power Trading Business Opportunity</h1>", unsafe_allow_html=True)
    st.markdown("""
    <p style='font-family: Montserrat;'>This dashboard estimates the <strong>Power trading opportunity</strong> for Tesla by optimizing their assets (vehicle fleet, superchargers) and their flexibility.</p>
    """, unsafe_allow_html=True)

# Chargement des données
historical_sales = load_data("data/historical_sales.csv")
battery_capacity = load_data("data/battery_capacity.csv")

# Paramètres
growth_rate = st.sidebar.slider("Annual Sales Growth Rate (%)", -30, 30, 10)
retirement_rate = st.sidebar.slider("Retirement Rate", 0.80, 0.99, 0.95)
years_to_forecast = st.sidebar.slider("Forecast Years", 1, 15, 10)

# Extrapolation des ventes avec croissance annuelle cumulative et cap à 0
last_year = historical_sales["Year"].max()
future_years = range(last_year + 1, last_year + 1 + years_to_forecast)

# Créer DataFrame avec extrapolation correcte
future_sales = historical_sales.copy()
last_values = {model: historical_sales[historical_sales["Year"] == last_year][model].values[0]
               for model in historical_sales.columns[1:]}

for year in future_years:
    new_row = {"Year": year}
    for model in historical_sales.columns[1:]:
        last_values[model] = max(0, last_values[model] * (1 + growth_rate/100))
        new_row[model] = int(last_values[model])
    future_sales = pd.concat([future_sales, pd.DataFrame([new_row])], ignore_index=True)

# Limiter aux années demandées
future_sales = future_sales[future_sales["Year"] <= last_year + years_to_forecast]

# Préparation des données pour la capacité de batterie
latest_battery = battery_capacity.groupby('Model').last().reset_index()

# Fonction pour appliquer le style aux données estimées
def style_estimated_data(df, last_year):
    def apply_style(row):
        if row["Year"] > last_year:
            return ['color: #888888; font-style: italic'] * len(row)
        return [''] * len(row)
    return df.style.apply(apply_style, axis=1)

# Calcul de la fleet capacity avec le bon nombre d'années
fleet_capacity = calculate_fleet_power(future_sales, latest_battery, growth_rate, retirement_rate, years_to_forecast)
fleet_capacity = fleet_capacity[fleet_capacity["Year"] <= last_year + years_to_forecast]

# Calcul du Power Potential avec cumul annuel
def calculate_cumulative_power(fleet_capacity, retirement_rate):
    power_data = fleet_capacity.copy()
    power_data["Power Potential (MW)"] = power_data["Total Capacity (MWh)"]

    # Calcul du cumul simple (sans retirement rate)
    simple_cumulative = []
    current_sum = 0
    for i, row in power_data.iterrows():
        current_sum += row["Power Potential (MW)"]
        simple_cumulative.append(current_sum)

    # Calcul du cumul avec retirement rate
    retirement_cumulative = []
    for i, row in power_data.iterrows():
        if i == 0:
            retirement_cumulative.append(row["Power Potential (MW)"])
        else:
            cumulative = row["Power Potential (MW)"]
            for j in range(1, min(i, 3)+1):
                prev_year = i - j
                if prev_year >= 0:
                    cumulative += power_data.iloc[prev_year]["Power Potential (MW)"] * (retirement_rate ** j)
            retirement_cumulative.append(cumulative)

    power_data["Simple Cumulative (MW)"] = simple_cumulative
    power_data["Retirement Cumulative (MW)"] = retirement_cumulative
    return power_data

power_data = calculate_cumulative_power(fleet_capacity, retirement_rate)
power_data = power_data[power_data["Year"] <= last_year + years_to_forecast]

# Données pour le nouvel onglet Power Supply
power_comparison_data = [
    {"Object": "France — consumption", "Min": -450, "Max": -440, "Unit": "TWh",
     "Comment": "Total annual electricity consumption in France (2023 data)"},
    {"Object": "Nuclear reactor (900–1300 MW)", "Min": 6.5, "Max": 9.7, "Unit": "TWh",
     "Comment": "Annual production of one nuclear reactor"},
    {"Object": "SNCF (group)", "Min": -9, "Max": -7, "Unit": "TWh",
     "Comment": "Total annual electricity consumption of SNCF group"},
    {"Object": "Large steel plant", "Min": -5, "Max": -0.6, "Unit": "TWh",
     "Comment": "Annual electricity consumption of a large integrated steel plant"},
    {"Object": "Tesla Superchargers (FR)", "Min": -0.13, "Max": -0.08, "Unit": "TWh",
     "Comment": "Estimated annual consumption of Tesla superchargers in France"},
    {"Object": "Tesla Fleet (FR consumption)", "Min": -0.42, "Max": -0.25, "Unit": "TWh",
     "Comment": "Estimated annual consumption of Tesla vehicle fleet in France"},
    {"Object": "Onshore wind turbine", "Min": 0.005, "Max": 0.01, "Unit": "TWh",
     "Comment": "Annual production of one average onshore wind turbine (2-3 MW)"},
    {"Object": "High school", "Min": -0.0005, "Max": -0.0002, "Unit": "TWh",
     "Comment": "Annual electricity consumption of an average high school"},
    {"Object": "100m² house with heat pump", "Min": -0.000006, "Max": -0.0000016, "Unit": "TWh",
     "Comment": "Annual electricity consumption of a 100m² house with heat pump"}
]

# Coordonnées des superchargeurs en France
france_superchargeurs = pd.DataFrame({
    'Name': [
        'Paris Centre', 'Lyon Perrache', 'Marseille Vieux-Port', 'Bordeaux Lac',
        'Toulouse Blagnac', 'Nantes Atlantique', 'Strasbourg Zenith', 'Lille Europe',
        'Rennes Alma', 'Montpellier Odyssium', 'Nice Aéroport', 'Dijon Toison d\'Or'
    ],
    'Lat': [
        48.8566, 45.7589, 43.2965, 44.8612, 43.6295, 47.2184,
        48.5839, 50.6292, 48.1173, 43.6119, 43.6585, 47.3220
    ],
    'Lon': [
        2.3522, 4.8414, 5.3698, -0.5632, 1.4442, -1.5536,
        7.7521, 3.0573, -1.6778, 3.8772, 7.2173, 5.0415
    ],
    'Stalls': np.random.choice([4, 6, 8, 10, 12, 16], 12),
    'Power': np.random.choice([150, 250], 12),
    'Status': np.random.choice(['Operational', 'Coming Soon'], 12, p=[0.9, 0.1])
})

# Onglets
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "📊 Vehicle Sales",
    "⚡ Fleet Capacity",
    "🔋 Power Potential",
    "⚡ Superchargeur Network",
    "💰 Power Prices",
    "📊 Power Supply"
])

# --- Onglet 1: Vehicle Sales ---
with tab1:
    st.markdown("<h2>Vehicle Sales</h2>", unsafe_allow_html=True)

    # Graphique avec distinction visuelle
    fig = go.Figure()

    for i, model in enumerate(historical_sales.columns[1:]):
        # Données réelles
        real_data = future_sales[future_sales["Year"] <= last_year]
        fig.add_trace(go.Bar(
            x=real_data["Year"],
            y=real_data[model],
            name=model,
            marker_color=px.colors.qualitative.Set3[i]
        ))

        # Données estimées
        estimated_data = future_sales[future_sales["Year"] > last_year]
        if not estimated_data.empty:
            fig.add_trace(go.Bar(
                x=estimated_data["Year"],
                y=estimated_data[model],
                name=model,
                marker_color=px.colors.qualitative.Set3[i],
                marker=dict(line=dict(color='gray', width=1)),
                opacity=0.6,
                showlegend=False
            ))

    fig.add_vline(x=last_year + 0.5, line_dash="dash", line_color="gray", annotation_text="Forecast Start")
    fig.update_layout(
        barmode='group',
        title="Annual Vehicle Sales by Model",
        xaxis_title="Year",
        yaxis_title="Number of Vehicles",
        height=500,
        font=dict(family="Montserrat")
    )
    st.plotly_chart(fig, use_container_width=True)

    # Tableau avec données centrées
    styled_sales = style_estimated_data(future_sales, last_year).format({
        "Year": "{:.0f}",
        **{col: "{:,.0f}" for col in historical_sales.columns[1:]}
    })
    st.dataframe(styled_sales, hide_index=True, use_container_width=True)

# --- Onglet 2: Fleet Capacity ---
with tab2:
    st.markdown("<h2>Fleet Battery Capacity</h2>", unsafe_allow_html=True)

    # Format avec 2 chiffres après la virgule
    styled_capacity = style_estimated_data(fleet_capacity, last_year).format({
        "Year": "{:.0f}",
        "Total Capacity (MWh)": "{:,.2f}"
    })
    st.dataframe(styled_capacity, hide_index=True, use_container_width=True)

    fig_capacity = px.line(fleet_capacity, x="Year", y="Total Capacity (MWh)",
                          title=f"Total Fleet Battery Capacity (Next {years_to_forecast} Years)")
    fig_capacity.update_layout(font=dict(family="Montserrat"))
    st.plotly_chart(fig_capacity, use_container_width=True)

# --- Onglet 3: Power Potential ---
with tab3:
    st.markdown("<h2>Power Potential</h2>", unsafe_allow_html=True)

    # Sélection des colonnes et formatage
    power_display = power_data[["Year", "Power Potential (MW)",
                               "Simple Cumulative (MW)", "Retirement Cumulative (MW)"]].copy()
    styled_power = style_estimated_data(power_display, last_year).format({
        "Year": "{:.0f}",
        "Power Potential (MW)": "{:,.2f}",
        "Simple Cumulative (MW)": "{:,.2f}",
        "Retirement Cumulative (MW)": "{:,.2f}"
    })
    st.dataframe(styled_power, hide_index=True, use_container_width=True)

    # Graphique du power potential
    fig_power = go.Figure()
    fig_power.add_trace(go.Scatter(
        x=power_data["Year"],
        y=power_data["Power Potential (MW)"],
        name="Annual Power Potential",
        line=dict(color='#1f77b4')
    ))
    fig_power.add_trace(go.Scatter(
        x=power_data["Year"],
        y=power_data["Simple Cumulative (MW)"],
        name="Simple Cumulative",
        line=dict(color='#ff7f0e')
    ))
    fig_power.add_trace(go.Scatter(
        x=power_data["Year"],
        y=power_data["Retirement Cumulative (MW)"],
        name="Retirement Cumulative",
        line=dict(color='#2ca02c')
    ))
    fig_power.update_layout(
        title=f"Power Potential Over Time (Next {years_to_forecast} Years)",
        xaxis_title="Year",
        yaxis_title="Power Potential (MW)",
        font=dict(family="Montserrat")
    )
    st.plotly_chart(fig_power, use_container_width=True)

# --- Onglet 4: Superchargeur Network ---
with tab4:
    st.markdown("<h2>Superchargeur Network in France</h2>", unsafe_allow_html=True)

    fig_map = px.scatter_mapbox(france_superchargeurs,
                                lat="Lat", lon="Lon",
                                color="Power", size="Stalls",
                                hover_name="Name", hover_data=["Status", "Stalls", "Power"],
                                zoom=5, height=600)
    fig_map.update_layout(
        mapbox_style="open-street-map",
        margin={"r":0,"t":0,"l":0,"b":0},
        mapbox=dict(center=dict(lat=46.6034, lon=2.4806), zoom=5)
    )
    st.plotly_chart(fig_map, use_container_width=True)

    france_superchargeurs['Annual Consumption (MWh)'] = (
        france_superchargeurs['Stalls'] * 8 * 365 * 50 / 1000
    )

    st.dataframe(france_superchargeurs.sort_values('Annual Consumption (MWh)', ascending=False).style.format({
        "Lat": "{:.2f}", "Lon": "{:.2f}", "Annual Consumption (MWh)": "{:,.0f}"
    }), hide_index=True, use_container_width=True)

# --- Onglet 5: Power Prices ---
with tab5:
    st.markdown("<h2>Electricity Power Prices</h2>", unsafe_allow_html=True)

    dates = pd.date_range(start="2023-01-01", end="2023-12-31", freq="h")
    power_prices = pd.DataFrame({
        'Date': dates,
        'Price (€/MWh)': np.random.uniform(50, 200, len(dates)) * np.sin(np.linspace(0, 2*np.pi, len(dates))) + 100
    })

    fig_prices = px.line(power_prices, x="Date", y="Price (€/MWh)", title="Electricity Prices Evolution")
    st.plotly_chart(fig_prices, use_container_width=True)

# --- Onglet 6: Power Supply ---
with tab6:
    st.markdown("<h2>Power Supply Comparison in France</h2>", unsafe_allow_html=True)

    # Préparation des données pour le graphique
    df = pd.DataFrame(power_comparison_data)

    # Création du graphique centré sur 0
    fig = go.Figure()

    # Ajout des barres pour chaque objet
    for i, row in df.iterrows():
        fig.add_trace(go.Bar(
            x=[row['Object']],
            y=[row['Min']],
            base=[0] if row['Min'] > 0 else [row['Max']],
            name=row['Object'],
            marker_color='red' if row['Min'] < 0 else 'green',
            width=0.6,
            hovertemplate=f"{row['Object']}<br>Min: {abs(row['Min']):,.1f} {row['Unit']}<br>Max: {abs(row['Max']):,.1f} {row['Unit']}<br>Comment: {row['Comment']}"
        ))

    # Mise en forme
    fig.update_layout(
        title="Energy Production/Consumption Comparison in France (Log Scale)",
        yaxis_type="log",
        yaxis_title="Energy (TWh)",
        xaxis_title="",
        barmode='relative',
        hovermode="x unified",
        height=600
    )

    st.plotly_chart(fig, use_container_width=True)

    # Tableau synthétique avec commentaires
    st.markdown("<h3>Synthetic Table with Comments</h3>", unsafe_allow_html=True)
    st.dataframe(df.assign(
        **{"Min": df.apply(lambda x: f"{abs(x['Min']):,.1f} {x['Unit']}" if x['Min'] < 0 else f"{x['Min']:,.1f} {x['Unit']}", axis=1)},
        **{"Max": df.apply(lambda x: f"{abs(x['Max']):,.1f} {x['Unit']}" if x['Max'] < 0 else f"{x['Max']:,.1f} {x['Unit']}", axis=1)}
    ), hide_index=True, use_container_width=True)