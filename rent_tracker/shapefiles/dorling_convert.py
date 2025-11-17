
# install geopandas if not already installed


import geopandas as gpd

# Read the GeoJSON
gdf = gpd.read_file('rent_tracker/shapefiles/county_dorling.geojson')

# Convert to WGS84
gdf_wgs84 = gdf.to_crs('EPSG:4326')

# Save the result
gdf_wgs84.to_file('rent_tracker/shapefiles/dorling_wgs84.geojson', driver='GeoJSON')