"""This is a simple script to convert footprints from Planet Labs CSDAP monthly data orders into a usable format for DESIS tasking. It makes the
following assumption:
- Python version >=3.6
- Script is called with path to the NASA Mirror CSV (e.g. "python planet_aoi_conversion.py NASA_Mirror_2020_06NASA_Mirror_2020_06.csv")
- The input CSV is expected to contain the following columns:
    - org_id, org_name, suborg_id, suborg_name, timestamp, user_id, api_key_name, download_item_id, download_item_type, subscription_id, order_reference, 
    plan_name, quota_used_km2, total_downloaded_km2, download_asset_type, geojson_geometry
-Output CSV file includes the following data columns:
    - org_name, downloaded_item_type, quota_used_km2, total_downloaded_km2, download_asset_type, geometry, centroid, minx, miny, maxy, maxx, area_km2
    -file name is the following: 'PlanetAOI_Conversion_(year)_(month).csv'
"""
import geopandas
import pandas as pd

from geopandas import GeoSeries
from shapely.geometry import Polygon
from shapely.geometry import shape
from shapely.wkt import loads as load_wtk

# input the csv file
input_csv = input('Please enter the csv file name including the extension: ')
print('You entered:' + input_csv)
planet_order = pd.read_csv(str(input_csv))

# user input to name output file
try:
    year = int(input(
        'Please enter the year that the data was mirrored in the following format yyyy:\n'))
except ValueError:
    print("Warning: The provided year value does not conform to the desired format of yyyy.")
try:
    month = int(input(
        'Please enter the month that the data was mirrored in the following format mm:\n'))
except ValueError:
    print("Warning: The provided month value does not conform to the desired format of mm.")

outfile = 'PlanetAOI_Conversion_' + str(year) + '_' + str(month) + '.csv'

# create a pandas dataframe
df = pd.DataFrame(planet_order)

# prepare the dataframe to be converted to spatial geometry
coordinates = 'coordinates'
type = 'type'
Polygon = 'Polygon'

# convert the geojson_geometry column to geometry
df['geometry'] = df.geojson_geometry.apply(
    lambda x: shape(eval(x.replace('=', ':'))))

# create a geodataframe
gdf = geopandas.GeoDataFrame(
    df, geometry=df['geometry'])

# set a geographic coordinate system
gdf = gdf.set_crs(epsg=4326)

# find the centroid of each polygon
gdf['centroid'] = gdf.centroid

# Get the minimum latitude and longitude coordinates and add as columns to the geodataframe
boundary = gdf.bounds
gdf['minx'] = boundary['minx']
gdf['miny'] = boundary['miny']
gdf['maxy'] = boundary['maxy']
gdf['maxx'] = boundary['maxx']

# re-project the dataframe to calculate area
proj_gdf = gdf.copy()
proj_gdf = proj_gdf.to_crs(epsg=3857)

# calculate the area in km2 for each polygon and add to a new column
gdf['area_km2'] = proj_gdf['geometry'].area / 10**6

# check the number of rows in the dataframe
length_before = len(gdf)
print('The number of rows in the original file is ' + str(length_before))
# remove rows with duplicate polygon coordinates
gdf.drop_duplicates(subset='geometry', keep=False, inplace=True)
# check the number of rows after removing duplicates
length_after = len(gdf)
removed_rows = length_before - length_after
print('The number of duplicated rows removed is ' + str(removed_rows))

# remove the following columns from the geodataframe
gdf = gdf.drop(['geojson_geometry', 'org_id', 'suborg_id', 'suborg_name', 'timestamp', 'user_id',
                'api_key_name', 'download_item_id', 'plan_name', 'subscription_id', 'order_reference'], axis=1)

# write the geodataframe to a csv file - must convert types 'geometry' to 'str'
gdf.astype({'geometry': str}).to_csv(outfile)
