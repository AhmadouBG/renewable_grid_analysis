import geopandas as gpd
import numpy as np

# 1. Charger votre fichier GeoJSON (Arrondissements)
geojson_file = "limite_arrondissement_du_senegal.geojson" 
gdf = gpd.read_file(geojson_file)

# 2. Calculer le diamètre en km à partir de la superficie (SUM_SUPERF)
# La formule : 2 * sqrt(Superficie / pi)
gdf['diameter_km'] = 2 * np.sqrt(gdf['SUM_SUPERF'] / np.pi)

# 3. Calculer les vrais centres géographiques (Centroids)
# On projette en EPSG:32628 pour un calcul de géométrie précis au Sénégal
gdf_projected = gdf.to_crs(epsg=32628)
centroids_projected = gdf_projected.geometry.centroid

# 4. Reconvertir les points centraux en coordonnées GPS standards (EPSG:4326)
centroids_gps = centroids_projected.to_crs(epsg=4326)

# 5. Extraire proprement la Latitude (Y) et la Longitude (X)
gdf['latitude'] = centroids_gps.y
gdf['longitude'] = centroids_gps.x

# 6. CRÉATION DU FORMAT MAP (Latitude, Longitude)
# C'est cette colonne textuelle que vous copierez dans Google Maps ou Open-Meteo
gdf['map_format'] = gdf['latitude'].astype(str) + ", " + gdf['longitude'].astype(str)

# 7. Nettoyer le tableau en retirant la géométrie lourde du GeoJSON
df_final = gdf.drop(columns='geometry')

# 8. Exporter le résultat final en fichier CSV
df_final.to_csv("senegal_arrondissements_location.csv", index=False)

print("Traitement terminé avec succès !")
# Aperçu du résultat pour la ligne de Noto
print(df_final[['NOM', 'SUM_SUPERF', 'diameter_km', 'map_format']].head())
