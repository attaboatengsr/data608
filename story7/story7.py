import pandas as pd
import plotly.express as px

# -----------------------------
# 1. Example dataset (replace with real EIA data)
# -----------------------------
##data = {
##    "State": ["CA", "TX", "NY", "FL", "WY"],
##    "Production_TBtu": [2500, 20000, 1500, 1200, 18000],
##    "Consumption_TBtu": [6816.7, 13040.7, 3559.3, 4200.5, 1320.8],
##    "Coal_pct": [2, 20, 5, 3, 40],
##    "NaturalGas_pct": [30, 45, 35, 60, 20],
##    "Renewables_pct": [40, 25, 30, 20, 35],
##    "Nuclear_pct": [28, 10, 30, 17, 5],
##    "ImportExport": ["Importer", "Exporter", "Importer", "Importer", "Exporter"]
##}
##
##df = pd.DataFrame(data)


df1 = pd.read_excel("P3.xlsx", skiprows=2)


# Drop columns that start with "Unnamed"
df1 = df1.loc[:, ~df1.columns.str.contains("Unnamed")]

# Rename the remaining columns
df1.columns = [
    "State",
    "Total_Production_TBtu",
    "Total_Consumption_TBtu",
    "Consumption_Less_Production_TBtu"
]

df1 = df1.dropna()


df2 = pd.read_html("https://www.eia.gov/state/seds/data.php?incfile=/state/seds/sep_sum/html/sum_btu_totcb.html&sid=US")[1]
# Skip the first 2 rows
df2 = df2.iloc[2:].reset_index(drop=True)
df2 = df2.dropna()


df2.rename(columns={df2.columns[0]: "State",
                    df2.columns[1]: "Coal",
                    df2.columns[2]: "Natural Gas",
                    df2.columns[3]: "Fuel Oil",
                    df2.columns[4]: "HGL",
                    df2.columns[5]: "Jet Fuel",
                    df2.columns[6]: "Motor Gasoline",
                    df2.columns[7]: "Residual Oil",
                    df2.columns[8]: "Other"}, inplace=True)
#print(df2.columns)



df = pd.merge(df1, df2, on="State")
print(df)




# Dictionary mapping full state names to abbreviations
state_abbrev = {
    "Alabama": "AL", "Alaska": "AK", "Arizona": "AZ", "Arkansas": "AR",
    "California": "CA", "Colorado": "CO", "Connecticut": "CT",
    "Delaware": "DE", "Florida": "FL", "Georgia": "GA", "Hawaii": "HI",
    "Idaho": "ID", "Illinois": "IL", "Indiana": "IN", "Iowa": "IA",
    "Kansas": "KS", "Kentucky": "KY", "Louisiana": "LA", "Maine": "ME",
    "Maryland": "MD", "Massachusetts": "MA", "Michigan": "MI", "Minnesota": "MN",
    "Mississippi": "MS", "Missouri": "MO", "Montana": "MT", "Nebraska": "NE",
    "Nevada": "NV", "New Hampshire": "NH", "New Jersey": "NJ", "New Mexico": "NM",
    "New York": "NY", "North Carolina": "NC", "North Dakota": "ND", "Ohio": "OH",
    "Oklahoma": "OK", "Oregon": "OR", "Pennsylvania": "PA", "Rhode Island": "RI",
    "South Carolina": "SC", "South Dakota": "SD", "Tennessee": "TN", "Texas": "TX",
    "Utah": "UT", "Vermont": "VT", "Virginia": "VA", "Washington": "WA",
    "West Virginia": "WV", "Wisconsin": "WI", "Wyoming": "WY"
}





labels = {
    "Total_Production_TBtu": "Total Production (Trillion Btu)",
    "Total_Consumption_TBtu": "Total Consumption (Trillion Btu)",
    "Consumption_Less_Production_TBtu": "Consumption Minus Production (Trillion Btu)",
    "Coal": "Coal Consumption (Trillion Btu)",
    "Natural Gas": "Natural Gas Consumption (Trillion Btu)",
    "Fuel Oil": "Fuel Oil Consumption (Trillion Btu)",
    "HGL": "Hydrocarbon Gas Liquids (Trillion Btu)",
    "Jet Fuel": "Jet Fuel Consumption (Trillion Btu)",
    "Motor Gasoline": "Motor Gasoline Consumption (Trillion Btu)",
    "Residual Oil": "Residual Oil Consumption (Trillion Btu)",
    "Other": "Other Fuels (Trillion Btu)",
    "Dependency_pct": "Energy Dependency (%)"
}


# -----------------------------
# 2. Calculate dependency metric
# -----------------------------
##df["Dependency_pct"] = ((df["Consumption_TBtu"] - df["Production_TBtu"]) / df["Consumption_TBtu"]) * 100

##df1["Dependency_pct"] = (
##    (df1["Total_Consumption_TBtu"] - df1["Total_Production_TBtu"])
##    / df1["Total_Consumption_TBtu"]
##) * 100


df["Dependency_pct"] = (
    (df["Total_Consumption_TBtu"] - df["Total_Production_TBtu"])
    / df["Total_Consumption_TBtu"]
) * 100


# Replace placeholders with 0
df = df.replace("(s)", 0).replace("NA", 0)

# Remove commas and whitespace from all string cells
df = df.applymap(lambda x: str(x).replace(",", "").strip() if isinstance(x, str) else x)

# Convert relevant columns to numeric
numeric_cols = ["Coal", "Natural Gas", "Fuel Oil", "Motor Gasoline",
                "Total_Production_TBtu", "Total_Consumption_TBtu"]

df[numeric_cols] = df[numeric_cols].apply(pd.to_numeric, errors="coerce")





df["Coal_pct"] = (df["Coal"] / df["Total_Production_TBtu"]) * 100
df["NaturalGas_pct"] = (df["Natural Gas"] / df["Total_Production_TBtu"]) * 100
#df["Renewables_pct"] = (df["Renewables"] / df["Total_Production_TBtu"]) * 100
#df["Nuclear_pct"] = (df["Nuclear"] / df["Total_Production_TBtu"]) * 100



df["Status"] = df["Consumption_Less_Production_TBtu"].apply(
    lambda x: "Net Importer" if x > 0 else "Net Exporter"
)
# -----------------------------
# 3. Build choropleth map
# -----------------------------


# Add abbreviation column
df["State_Abbrev"] = df["State"].map(state_abbrev)

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
        "Renewables_pct": "% Renewables",
        "Nuclear_pct": "% Nuclear",
        "Status": "Import/Export Status"
    },
    hover_name="State",
    hover_data={
        "Total_Production_TBtu": True,
        "Total_Consumption_TBtu": True,
        "Coal_pct": True,
        "NaturalGas_pct": True,
        "Status": True,
        "Dependency_pct": True
    }
)

# Choropleth using abbreviations
##fig = px.choropleth(
##    df,
##    locations="State_Abbrev",
##    locationmode="USA-states",
##    color="Dependency_pct",
##    color_continuous_scale="RdYlGn_r",
##    scope="usa",
##    labels={"Dependency_pct": "Dependency (%)"},
##    hover_data={
##        "State": True,
##        "Total_Production_TBtu": True,
##        "Total_Consumption_TBtu": True,
##        "Consumption_Less_Production_TBtu": True,
##        "Dependency_pct": True
##    }
##)

fig.update_layout(
    title_text="U.S. State Energy Dependency & Production Mix (2023)",
    geo=dict(bgcolor="rgba(0,0,0,0)")
)

fig.show()







##fig = px.choropleth(
##    df,
##    locations="State",              # must be state abbreviations
##    locationmode="USA-states",
##    color="Dependency_pct",
##    color_continuous_scale="RdYlGn_r",  # green = strong producers, red = vulnerable importers
##    scope="usa",
##    labels={"Dependency_pct": "Dependency (%)"},
##    hover_data={
##        "Production_TBtu": True,
##        "Consumption_TBtu": True,
##        "Coal_pct": True,
##        "NaturalGas_pct": True,
##        "Renewables_pct": True,
##        "Nuclear_pct": True,
##        "ImportExport": True
##    }
##)
##
##fig.update_layout(
##    title_text="U.S. State Energy Dependency & Production Mix (Sample Data)",
##    geo=dict(bgcolor="rgba(0,0,0,0)")
##)
##
##fig.show()



##df = pd.read_excel("P3.xlsx", skiprows=2)
##
##print(df.shape)        # shows (rows, columns)
##print(df.columns)      # shows current column names
##
##
### Drop columns that start with "Unnamed"
##df = df.loc[:, ~df.columns.str.contains("Unnamed")]
##
### Rename the remaining columns
##df.columns = [
##    "State",
##    "Total_Production_TBtu",
##    "Total_Consumption_TBtu",
##    "Consumption_Less_Production_TBtu"
##]
##
##df = df.dropna()
##
##print(df.head())
