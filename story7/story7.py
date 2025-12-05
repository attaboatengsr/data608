from shiny import App, ui, render
from shinywidgets import output_widget, render_widget

import numpy as np
import pandas as pd
import plotly.express as px

# --- Data prep ---
df1 = pd.read_excel("P3.xlsx", skiprows=2)
df1 = df1.loc[:, ~df1.columns.str.contains("Unnamed")]
df1.columns = [
    "State",
    "Total_Production_TBtu",
    "Total_Consumption_TBtu",
    "Consumption_Less_Production_TBtu",
]
df1 = df1.dropna()

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

df = pd.merge(df1, df2, on="State", how="inner")
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

df["Status"] = df["Consumption_Less_Production_TBtu"].apply(lambda x: "Net Importer" if x > 0 else "Net Exporter")
df = df.replace([np.inf, -np.inf], np.nan)

state_abbrev = {
    "Alabama": "AL","Alaska": "AK","Arizona": "AZ","Arkansas": "AR","California": "CA",
    "Colorado": "CO","Connecticut": "CT","Delaware": "DE","Florida": "FL","Georgia": "GA",
    "Hawaii": "HI","Idaho": "ID","Illinois": "IL","Indiana": "IN","Iowa": "IA","Kansas": "KS",
    "Kentucky": "KY","Louisiana": "LA","Maine": "ME","Maryland": "MD","Massachusetts": "MA",
    "Michigan": "MI","Minnesota": "MN","Mississippi": "MS","Missouri": "MO","Montana": "MT",
    "Nebraska": "NE","Nevada": "NV","New Hampshire": "NH","New Jersey": "NJ","New Mexico": "NM",
    "New York": "NY","North Carolina": "NC","North Dakota": "ND","Ohio": "OH","Oklahoma": "OK",
    "Oregon": "OR","Pennsylvania": "PA","Rhode Island": "RI","South Carolina": "SC",
    "South Dakota": "SD","Tennessee": "TN","Texas": "TX","Utah": "UT","Vermont": "VT",
    "Virginia": "VA","Washington": "WA","West Virginia": "WV","Wisconsin": "WI","Wyoming": "WY"
}
df["State_Abbrev"] = df["State"].map(state_abbrev)

required_cols = ["State_Abbrev", "Dependency_pct"]
df = df.dropna(subset=required_cols)
df = df.where(pd.notnull(df), None)

# --- UI ---
app_ui = ui.page_fluid(
    ui.h2("U.S. State Energy Dependency & Production Mix (2023)"),
    ui.input_select("state", "Select a State:", choices=["All"] + sorted(df["State"].unique())),
    output_widget("showplot"),
    ui.output_text_verbatim("state_info")
)

# --- Server ---
def server(input, output, session):
    @render_widget
    def showplot():
        selected_state = input.state()

        if selected_state == "All":
            plot_df = df
        else:
            plot_df = df[df["State"] == selected_state]

        fig = px.choropleth(
            plot_df,
            locations="State_Abbrev",
            locationmode="USA-states",
            color="Dependency_pct",
            color_continuous_scale="RdYlGn_r",
            scope="usa",
            hover_name="State",
        )

        # Fix color scale to full dataset so selected state's color matches legend
        fig.update_traces(zmin=df["Dependency_pct"].min(), zmax=df["Dependency_pct"].max())

        fig.update_layout(
            title_text="U.S. State Energy Dependency & Production Mix (2023)",
            geo=dict(bgcolor="rgba(0,0,0,0)")
        )
        return fig

    @output
    @render.text
    def state_info():
        state = input.state()
        if state == "All":
            return "Showing all states."
        row = df[df["State"] == state].iloc[0]
        return (
            f"State: {row['State']}\n"
            f"Production: {row['Total_Production_TBtu']} TBtu\n"
            f"Consumption: {row['Total_Consumption_TBtu']} TBtu\n"
            f"Dependency: {row['Dependency_pct']:.2f}%\n"
            f"Coal %: {row['Coal_pct']:.2f}%\n"
            f"Natural Gas %: {row['NaturalGas_pct']:.2f}%\n"
            f"Status: {row['Status']}"
        )

# --- App ---
app = App(app_ui, server)
