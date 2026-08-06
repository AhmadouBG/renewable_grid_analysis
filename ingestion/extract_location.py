import geopandas as gpd
import numpy as np
from pathlib import Path
# data path
git_repo_root = Path(__file__).parent
data_path = git_repo_root / "data"

# 1. Charger votre fichier GeoJSON (Arrondissements)
geojson_file = data_path / "Limite_arrondissement_du_sénégal.geojson" 
gdf = gpd.read_file(geojson_file)

# 3. Calculer les vrais centres géographiques (Centroids)
# On projette en EPSG:32628 pour un calcul de géométrie précis au Sénégal
gdf_projected = gdf.to_crs(epsg=32628)
centroids_projected = gdf_projected.geometry.centroid

# 4. Reconvertir les points centraux en coordonnées GPS standards (EPSG:4326)
centroids_gps = centroids_projected.to_crs(epsg=4326)

# 5. Extraire les coordonnées dans l'ORDRE MAP (Latitude d'abord, Longitude ensuite)
# Y représente l'axe Nord/Sud (Latitude), X représente l'axe Ouest/Est (Longitude)
gdf['latitude'] = centroids_gps.y
gdf['longitude'] = centroids_gps.x

# 6. CRÉATION DU FORMAT MAP TEXTUEL (Latitude, Longitude)
gdf['map_format'] = gdf['latitude'].astype(str) + ", " + gdf['longitude'].astype(str)

# 7. Nettoyer le tableau en retirant la géométrie lourde du GeoJSON
df_final = gdf.drop(columns='geometry')

# 8. Sélectionner et ordonner les colonnes principales à la fin pour plus de clarté
# (Conserve vos données d'origine et ajoute les nouvelles colonnes météo à la fin)
cols_to_show = ['NOM', 'SUM_SUPERF', 'Shape_Leng', 'latitude', 'longitude', 'map_format']
other_cols = [col for col in df_final.columns if col not in cols_to_show]
df_final = df_final[other_cols + cols_to_show]

# 9. Exporter le résultat final en fichier CSV
df_final.to_csv(data_path / "senegal_arrondissements_location.csv", index=False)

print("Traitement terminé ! Les colonnes respectent scrupuleusement l'ordre Latitude -> Longitude.")
# Aperçu du résultat pour la ligne de Noto
print(df_final[cols_to_show].head())
