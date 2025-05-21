import streamlit as st
import pandas as pd
import json
import folium
from streamlit_folium import st_folium

# Configuration
st.set_page_config(layout="wide")
st.markdown(
    "<h1 style='text-align: center;'>Carte interactive de l'Alsace</h1>",
    unsafe_allow_html=True,
)

# Chargement des données médicales
df = pd.read_csv("data_med_icp.csv")
df.columns = df.columns.str.strip().str.replace("\n", "").str.replace("  ", " ")
df["UT_x"] = df["UT_x"].astype(str).str.strip().str.upper()

# Appliquer le mapping corrigé pour correspondre au GeoJSON
ut_mapping = {
    "UT STRASBOURG OUEST": "STRASBOURG-3",
    "UT HAGUENAU": "HAGUENAU",
    "UT MOLSHEIM": "MOLSHEIM",
    "UT INGWILLER": "INGWILLER",
    "UT OBERNAI": "OBERNAI",
    "UT LINGOLSHEIM": "LINGOLSHEIM",
    "UT BISCHWILLER": "BISCHWILLER",
    "UT SÉLESTAT": "SÉLESTAT",
    "UT STRASBOURG NORD": "STRASBOURG-3",
    "UT SAVERNE": "SAVERNE",
    "UT BRUMATH": "BRUMATH",
    "UT ERSTEIN": "ERSTEIN",
    "UT STRASBOURG FINKWI": "STRASBOURG-3",
    "UT WISSEMBOURG": "WISSEMBOURG",
    "UT STRASBOURG SUD": "STRASBOURG-3",
    "UT BOUXWILLER": "BOUXWILLER",
}

df["UT_clean"] = df["UT_x"].replace(ut_mapping)

# Chargement du GeoJSON brut
with open("alsace_map.geojson", "r", encoding="utf-8") as f:
    geojson_data = json.load(f)

# Construction d’un DataFrame avec propriétés + géométrie
geo_features = []
for feature in geojson_data["features"]:
    props = feature["properties"]
    props["geometry"] = feature["geometry"]
    geo_features.append(props)

geo_df = pd.DataFrame(geo_features)
geo_df["nom"] = geo_df["nom"].astype(str).str.strip().str.upper()

# Agrégation des effectifs par UT corrigée
charge_par_ut = df["UT_clean"].value_counts().reset_index()
charge_par_ut.columns = ["nom", "effectif"]

# Fusion des données
geo_df = geo_df.merge(charge_par_ut, on="nom", how="left")
geo_df["effectif"] = geo_df["effectif"].fillna(0)
total = geo_df["effectif"].sum()
geo_df["taux_charge"] = (geo_df["effectif"] / total * 100).round(2)

# Création de la carte centrée sur l’Alsace
center = [48.5, 7.5]
m = folium.Map(location=center, zoom_start=8)

# Ajout des polygones interactifs
for _, row in geo_df.iterrows():
    geom = row["geometry"]
    tooltip_text = f"{row['nom']}<br>Effectif : {int(row['effectif'])}<br>Taux de charge : {row['taux_charge']}%"

    if geom["type"] == "Polygon":
        coords = geom["coordinates"][0]
        folium.Polygon(
            locations=[(lat, lon) for lon, lat in coords],
            color="blue",
            fill=True,
            fill_opacity=0.5,
            tooltip=tooltip_text,
        ).add_to(m)

    elif geom["type"] == "MultiPolygon":
        for part in geom["coordinates"]:
            coords = part[0]
            folium.Polygon(
                locations=[(lat, lon) for lon, lat in coords],
                color="blue",
                fill=True,
                fill_opacity=0.5,
                tooltip=tooltip_text,
            ).add_to(m)

for _, row in geo_df.iterrows():
    if row["effectif"] > 0:
        geom = row["geometry"]

        # Obtenir le centre de la zone
        if geom["type"] == "Polygon":
            coords = geom["coordinates"][0]
        elif geom["type"] == "MultiPolygon":
            coords = geom["coordinates"][0][0]
        else:
            continue

        lon_center = sum([pt[0] for pt in coords]) / len(coords)
        lat_center = sum([pt[1] for pt in coords]) / len(coords)

        # Ajouter un cercle sur la carte
        folium.CircleMarker(
            location=(lat_center, lon_center),
            radius=6,
            color="red",
            fill=True,
            fill_opacity=0.9,
            popup=f"{row['nom']}<br>Effectif : {int(row['effectif'])}",
        ).add_to(m)
# Affichage dans Streamlit
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    st_folium(m, width=700, height=700)
