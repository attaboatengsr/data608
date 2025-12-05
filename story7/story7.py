from shiny import App, ui
from shinywidgets import output_widget, render_widget

import numpy as np
import pandas as pd
import plotly.express as px

# --- Data prep ---
df1 = pd.read_excel("P3.xlsx", skiprows=2)

# Drop columns that start with "Unnamed"
df1 = df1.loc[:, ~df1.columns.str.contains("Unnamed")]

# Rename the remaining columns
df1.columns = [
    "State",
    "Total_Production_TBtu",
    "Total_Consumption_TBtu",
    "Consumption_Less_Production_TBtu",
]
df1 = df1.dropna()

# Read EIA data
df2 = pd.read_html(
    "https://www.eia.gov/state/seds/data.php?incfile=/state/seds/sep_sum/html/sum_btu_totcb.html&sid=US"
)[1]
df2 = df2.iloc[2:].reset_index(drop=True).dropna()

df2.rename(
    columns={
        df2.columns[0]: "State",
        df2.columns[1]: "Coal",
        df2.columns[2]: "Natural Gas",
        df2.columns[3]: "Fuel Oil",
        df2.columns[4]: "HGL",
        df2.columns[5]: "Jet Fuel",
        df2.columns[6]: "Motor Gasoline",
        df2.columns[7]: "Residual Oil",
        df2.columns[8]: "Other",
    },
    inplace=True,
)

# Merge
df = pd.merge(df1, df2, on="State", how="inner")

# Replace placeholders and convert numeric
df = df.replace("(s)", 0).replace("NA", 0)
numeric_cols = [
    "Coal",
    "Natural Gas",
    "Fuel Oil",
    "Motor Gasoline",
    "Total_Production_TBtu",
    "Total_Consumption_TBtu",
]
df[numeric_cols] = df[numeric_cols].apply(pd.to_numeric, errors="coerce")

# Safe calculations
df["Dependency_pct"] = np.where(
    df["Total_Consumption_TBtu"] > 0,
    ((df["Total_Consumption_TBtu"] - df["Total_Production_TBtu"]) / df["Total_Consumption_TBtu"]) * 100,
    0,
)
df["Coal_pct"] = np.where(
    df["Total_Production_TBtu"] > 0, (df["Coal"] / df["Total_Production_TBtu"]) * 100, 0
)
df["NaturalGas_pct"] = np.where(
    df["Total_Production_TBtu"] > 0, (df["Natural Gas"] / df["Total_Production_TBtu"]) * 100, 0
)

# Status column
df["Status"] = df["Consumption_Less_Production_TBtu"].apply(lambda x: "Net Importer" if x > 0 else "Net Exporter")

# Final numeric cleanup (remove inf)
df = df.replace([np.inf, -np.inf], np.nan)

# State abbreviations
state_abbrev = {
    "Alabama": "AL",
    "Alaska": "AK",
    "Arizona": "AZ",
    "Arkansas": "AR",
    "California": "CA",
    "Colorado": "CO",
    "Connecticut": "CT",
    "Delaware": "DE",
    "Florida": "FL",
    "Georgia": "GA",
    "Hawaii": "HI",
    "Idaho": "ID",
    "Illinois": "IL",
    "Indiana": "IN",
    "Iowa": "IA",
    "Kansas": "KS",
    "Kentucky": "KY",
    "Louisiana": "LA",
    "Maine": "ME",
    "Maryland": "MD",
    "Massachusetts": "MA",
    "Michigan": "MI",
    "Minnesota": "MN",
    "Mississippi": "MS",
    "Missouri": "MO",
    "Montana": "MT",
    "Nebraska": "NE",
    "Nevada": "NV",
    "New Hampshire": "NH",
    "New Jersey": "NJ",
    "New Mexico": "NM",
    "New York": "NY",
    "North Carolina": "NC",
    "North Dakota": "ND",
    "Ohio": "OH",
    "Oklahoma": "OK",
    "Oregon": "OR",
    "Pennsylvania": "PA",
    "Rhode Island": "RI",
    "South Carolina": "SC",
    "South Dakota": "SD",
    "Tennessee": "TN",
    "Texas": "TX",
    "Utah": "UT",
    "Vermont": "VT",
    "Virginia": "VA",
    "Washington": "WA",
    "West Virginia": "WV",
    "Wisconsin": "WI",
    "Wyoming": "WY",
}
df["State_Abbrev"] = df["State"].map(state_abbrev)

# Drop rows missing essential fields (avoids NaN in Plotly/Shiny JSON)
required_cols = ["State_Abbrev", "Dependency_pct", "Coal_pct", "NaturalGas_pct", "Total_Production_TBtu", "Total_Consumption_TBtu"]
df = df.dropna(subset=required_cols)

# Convert any remaining NaN to JSON-safe None
df = df.where(pd.notnull(df), None)

# --- UI ---
app_ui = ui.page_fluid(ui.h2("U.S. State Energy Dependency & Production Mix (2023)"), output_widget("showplot"))

# --- Server ---
def server(input, output, session):
    @render_widget
    def showplot():
        fig = px.choropleth(
            df,
            locations="State_Abbrev",
            locationmode="USA-states",
            color="Dependency_pct",
            color_continuous_scale="RdYlGn_r",
            scope="usa",
            labels={
                "Dependency_pct": "Dependency (%)",
                "Coal_pct": "% Coal",
                "NaturalGas_pct": "% Natural Gas",
                "Status": "Import/Export Status",
            },
            hover_name="State",
            hover_data={
                "Total_Production_TBtu": True,
                "Total_Consumption_TBtu": True,
                "Coal_pct": True,
                "NaturalGas_pct": True,
                "Status": True,
                "Dependency_pct": True,
            },
        )
        fig.update_layout(
            title_text="U.S. State Energy Dependency & Production Mix (2023)",
            geo=dict(bgcolor="rgba(0,0,0,0)"),
        )
        return fig

# --- App ---
app = App(app_ui, server)
