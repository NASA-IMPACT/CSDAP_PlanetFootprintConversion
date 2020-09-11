import argparse
import geojsonio
import geopandas
import numpy as np
import pandas as pd
import pyproj

from geopy.distance import great_circle
from shapely.geometry import shape
from shapely.geometry import shape, Point, Polygon, MultiPoint
from sklearn.cluster import DBSCAN
from geopandas import GeoSeries

# This script converts Area of Interest (AOI) footprints from Planet Labs data ordered each month through CSDAP into usaable DESIS tasking regions. The script employs a density algorithm that reduces the number of tasking areas. 

#todo list:
# add doc strings to function
# several tasks could probably be made into functions

# input the csv file
input_csv = input('Please enter the csv file name including the extension: ')
print('You entered:' + input_csv)
planet_order = pd.read_csv(str(input_csv))

# user input to name output file
try:
    year = int(input(
        'Please enter the year that the data was mirrored in the following format yyyy:\n'))
except ValueError:
    print('Warning: The provided year value does not conform to the desired format of yyyy.')
try:
    month = int(input(
        'Please enter the month that the data was mirrored in the following format mm:\n'))
except ValueError:
    print('Warning: The provided month value does not conform to the desired format of mm.')

outfile = 'PlanetAOI_Conversion_' + str(year) + '_' + str(month) + '.csv'

# create a pandas dataframe and prepare to convert to spatial geometry
df = pd.DataFrame(planet_order)
coordinates = 'coordinates'
type = 'type'
Polygon = 'Polygon'
# convert the geojson_geometry to geometry, create geodataframe, and apply a coordinate system
df['geometry'] = df.geojson_geometry.apply(
    lambda x: shape(eval(x.replace('=', ':'))))
gdf = geopandas.GeoDataFrame(
    df, geometry=df['geometry'])
gdf = gdf.set_crs(epsg=4326)

# get the lat/long boundary extents of each polygon and create new variables using envelope and centroid points
gdf['envelope'] = gdf.envelope
gdf['centroid'] = gdf.centroid
envelope = gdf['envelope']
centroid = gdf['centroid']

# functions to extract out individual coordinate points from geometry types


def coord_lister_polygon(geom):
    coords = list(geom.exterior.coords)
    return (coords)


def coord_lister_point(geom):
    coords = list(geom.coords)
    return (coords)


# extract envelope and centroid coords
envelope_list = envelope.geometry.apply(coord_lister_polygon)
centroid_list = centroid.geometry.apply(coord_lister_point)
envelopCoords = pd.DataFrame(envelope_list)
centroidCoords = pd.DataFrame(centroid_list)

# extract out individual coordinate points from envelope (ie polygon extents) and split the coordinate points into x and y columns
# should be a function
envelopCoords['a1'], envelopCoords['a2'], envelopCoords['a3'], envelopCoords['a4'], envelopCoords['a5'] = envelopCoords['envelope'].str[
    0], envelopCoords['envelope'].str[1], envelopCoords['envelope'].str[2], envelopCoords['envelope'].str[3], envelopCoords['envelope'].str[4]
centroidCoords['a5'] = centroidCoords['centroid'].str[0]
envelopCoords['a1.y'], envelopCoords['a1.x'] = envelopCoords['a1'].str[0], envelopCoords['a1'].str[1]
envelopCoords['a2.y'], envelopCoords['a2.x'] = envelopCoords['a2'].str[0], envelopCoords['a2'].str[1]
envelopCoords['a3.y'], envelopCoords['a3.x'] = envelopCoords['a3'].str[0], envelopCoords['a3'].str[1]
envelopCoords['a4.y'], envelopCoords['a4.x'] = envelopCoords['a4'].str[0], envelopCoords['a4'].str[1]
centroidCoords['a5.y'], centroidCoords['a5.x'] = centroidCoords['a5'].str[0], centroidCoords['a5'].str[1]

# for each coordinate points, convert each x and y to a list for the distance function
# should be a function?
# point 1
point1_x = envelopCoords['a1.x'].tolist()
point1_y = envelopCoords['a1.y'].tolist()
# point 2
point2_x = envelopCoords['a2.x'].tolist()
point2_y = envelopCoords['a2.y'].tolist()
# point
point3_x = envelopCoords['a3.x'].tolist()
point3_y = envelopCoords['a3.y'].tolist()
# point 4
point4_x = envelopCoords['a4.x'].tolist()
point4_y = envelopCoords['a4.y'].tolist()
# centroid point
centroid_x = centroidCoords['a5.x'].tolist()
centroid_y = centroidCoords['a5.y'].tolist()

# determine point 1 distance to the centroid
# should be a function?
geod = pyproj.Geod(ellps='WGS84')

lon0 = centroid_y
lat0 = centroid_x
lon1 = point1_y
lat1 = point1_x

azimuth_forward1, azimuth_backward1, distance1 = geod.inv(
    lon0, lat0, lon1, lat1)

# determine point 2 distance to the centroid
# should be a function
geod = pyproj.Geod(ellps='WGS84')

lon0 = centroid_y
lat0 = centroid_x
lon1 = point2_y
lat1 = point2_x

azimuth_forward2, azimuth_backward2, distance2 = geod.inv(
    lon0, lat0, lon1, lat1)

# determine point 3 distance to the centroid
# should be a function
geod = pyproj.Geod(ellps='WGS84')

lon0 = centroid_y
lat0 = centroid_x
lon1 = point3_y
lat1 = point3_x

azimuth_forward3, azimuth_backward3, distance3 = geod.inv(
    lon0, lat0, lon1, lat1)

# detrmine point 4 distance to the centroid
# should be a function
geod = pyproj.Geod(ellps='WGS84')

lon0 = centroid_y
lat0 = centroid_x
lon1 = point4_y
lat1 = point4_x

azimuth_forward4, azimuth_backward4, distance4 = geod.inv(
    lon0, lat0, lon1, lat1)

# convert distances to arrays and covert from meters to km
# should be a function?
dist1 = np.asarray(distance1)
dist1_km = dist1/1000
dist2 = np.asarray(distance2)
dist2_km = dist2/1000
dist3 = np.asarray(distance3)
dist3_km = dist3/1000
dist4 = np.asarray(distance4)
dist4_km = dist4/1000

# create new dataframe with each point's distance and azimuths, polygon centroid, and polygon extents
distancedf = pd.DataFrame(np.column_stack([dist1_km, azimuth_forward1, dist2_km, azimuth_forward2, dist3_km, azimuth_forward3, dist4_km, azimuth_forward4]), columns=[
                          'distance1', 'azimuth1', 'distance2', 'azimuth2', 'distance3', 'azimuth3', 'distance4', 'azimuth4'])
distancedf['centroid'] = centroid
distancedf['envelope'] = envelope
# remove duplicate polygons (based on polygon extents)
distancedf.drop_duplicates(subset='envelope', keep=False, inplace=True)

# prepare dataframe to compute DCSCAN clustering
distancedf['lat'], distancedf['lon'] = centroidCoords['a5.x'], centroidCoords['a5.y']
xy_coords = distancedf.as_matrix(columns=['lat', 'lon'])

# compute the DBSCAN and determine the number of clusters; reason is to reduce the density of polygons
kms_per_radian = 6371.0088
epsilon = 5 / kms_per_radian
db = DBSCAN(eps=epsilon, min_samples=1, algorithm='ball_tree',
            metric='haversine').fit(np.radians(xy_coords))
cluster_labels = db.labels_
num_clusters = len(set(cluster_labels))
clusters = pd.Series([xy_coords[cluster_labels == n]
                      for n in range(num_clusters)])
print('Number of clusters: {}'.format(num_clusters))

# find the center point for each cluster and return the point with nearest reference point


def get_centermost_point(cluster):
    cluster_centroid = (MultiPoint(cluster).centroid.x,
                        MultiPoint(cluster).centroid.y)
    centermost_point = min(
        cluster, key=lambda point: great_circle(point, cluster_centroid).m)
    return tuple(centermost_point)


centermost_points = clusters.map(get_centermost_point)

# find the centermost points for each cluster from the dataset
lats, lons = zip(*centermost_points)
rep_points = pd.DataFrame({'lon': lons, 'lat': lats})

# get entire row of attributes for each representative point for each cluster
rs = rep_points.apply(lambda row: distancedf[(distancedf['lat'] == row['lat']) | (
    distancedf['lon'] == row['lon'])].iloc[0], axis=1)

# export as a csv file
finaldf = rs.drop(['lat', 'lon'], axis=1)
finaldf.to_csv(outfile, index=False)
