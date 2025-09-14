import pandas as pd
from io import StringIO

def load_data(filepath):
    """Charge les données avec gestion des séparateurs"""
    with open(filepath, 'r') as f:
        content = f.read()

    sep = ';' if ';' in content[:100] else ','
    df = pd.read_csv(StringIO(content), sep=sep, skipinitialspace=True)
    df.columns = df.columns.str.strip()

    for col in df.columns:
        if col not in ["Year", "Model"]:
            df[col] = pd.to_numeric(df[col], errors='coerce')

    return df

def calculate_fleet_power(sales_data, battery_data, growth_rate, retirement_rate, forecast_years):
    """Calcule la capacité de la flotte avec les dernières capacités de batterie"""
    # Fusionner les données de ventes et de capacité de batterie
    merged = sales_data.melt(id_vars="Year", var_name="Model", value_name="Sales")

    # Créer un dictionnaire des dernières capacités par modèle
    battery_dict = battery_data.groupby('Model')['Battery Capacity (kWh)'].last().to_dict()
    merged["Battery Capacity (kWh)"] = merged["Model"].map(battery_dict)

    merged["Capacity (MWh)"] = merged["Sales"] * merged["Battery Capacity (kWh)"] / 1000

    capacity = merged.pivot_table(index="Year", columns="Model", values="Capacity (MWh)", aggfunc="sum").fillna(0)

    last_year = sales_data["Year"].max()
    all_years = range(sales_data["Year"].min(), last_year + forecast_years + 1)
    fleet_capacity = pd.DataFrame(index=all_years, columns=capacity.columns).fillna(0.0)

    for year in all_years:
        if year in capacity.index:
            fleet_capacity.loc[year] = capacity.loc[year]
        else:
            prev_year = year - 1
            fleet_capacity.loc[year] = fleet_capacity.loc[prev_year] * (1 + growth_rate / 100) * (retirement_rate ** (year - sales_data["Year"].min()))
            if year in capacity.index:
                fleet_capacity.loc[year] += capacity.loc[year]

    fleet_capacity["Total Capacity (MWh)"] = fleet_capacity.sum(axis=1)
    fleet_capacity = fleet_capacity.reset_index().rename(columns={"index": "Year"})

    return fleet_capacity