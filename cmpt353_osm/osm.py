import pandas as pd
import numpy as np
import sys
import os
from PIL import Image
from PIL.ExifTags import TAGS
from PIL.ExifTags import GPSTAGS
from os import listdir
from os.path import isfile, join
from math import cos, asin, sqrt, pi

# This Program takes an input directory with Exif files, 
# Output the places of attractions around the calculated route

##################################################################################
#location code from :https://www.quora.com/How-can-I-read-multiple-images-in-Python-presented-in-a-folder
#                    https://developer.here.com/blog/getting-started-with-geocoding-exif-image-metadata-in-python3
def get_exif(file):
    image = Image.open(file)
    image.verify
    exif = image.getexif()
    return exif # return the labelled exif

def get_geotags(lab_exif):# getting the readable geotags
    if not lab_exif:
        raise ValueError("No EXIF data found")

    geotags = {}
    for (i, tag) in TAGS.items():
        if tag == 'GPSInfo':
            if i not in lab_exif:
                raise ValueError("No EXIF geotags found")

            for (j, val) in GPSTAGS.items():
                if j in lab_exif[i]:
                    geotags[val] = lab_exif[i][j]
    return geotags

def trans_to_decimal(dms, ref): # transform the data into coordinates

    degs = dms[0][0] / dms[0][1]
    mins = dms[1][0] / dms[1][1] / 60.0
    secs = dms[2][0] / dms[2][1] / 3600.0
    if ref in ['S', 'W']:
        degs = -degs
        mins = -mins
        secs = -secs
    return round(degs + mins + secs, 3)

def get_coordinates(geotags):
    lat = trans_to_decimal(geotags['GPSLatitude'], geotags['GPSLatitudeRef'])

    lon = trans_to_decimal(geotags['GPSLongitude'], geotags['GPSLongitudeRef'])

    return (lat,lon)
##################################################################################


def get_area_code(osm_input,df,bins_input):
    """
    This function get an big osm_input used for calculating the dataframe df area code
    area code is [(lat_range-1)*bins+1, (lat_range-1)*bins+2, (lat_range-1)*bins+3,...., lat_range*bins
                  .
                  .
                  .
                  .
                  2*bins+1, 2*bins+2, 2*bins+3, 2*bins+4,...., 3*bins
                  1*bins+1, 1*bins+2, 1*bins+3, 1*bins+4,...., 2*bins
                  1,        2,        3,        4,      ,...., bins]
                  with lat_range*bins number of elements
    input: osm_input is a big dataframe that used for calculation
           df is the dataframe that needs area code
           bins of how many evenly divided squares in the x-axis 
    return: df dataframe with area code
    """
    lon_range = osm_input['lon'].max()-osm_input['lon'].min()
    edge = lon_range/bins_input     ##bins of each individual edge
    df['area'] = ((((df['lon']-osm_input['lon'].min())/edge)+1).astype(int))+ bins_input*((df['lat']-osm_input['lat'].min())/edge).astype(int)
    return df


def get_route(route,start,end,agg_df,bins_input):
    """
    This is a recursive function with one start point and one end point.
    This funciton use the matrix approach to get the route(roughly by area)
    input: route that has already travelled
           start area code, 
           end area code,
           dataframe agg_df that contains the number of amenity in that area
           bins of how many evenly divided spaces 
    output: route represented by the area code
    """
    route = route + [start]
    if(start == end):              #base case
        return route
    left_remain = start % bins_input -1   #keep on track how many area remain on the right
    if (end-start) > bins_input - left_remain+1 :
        vertical = start + bins_input    #destination is above
    elif end < start - left_remain :
        vertical = start - bins_input    #destination is below
    else:
        vertical = 0               #same row
    
    if end%bins_input == start%bins_input :
        horizontal = 0             #destination is on the same column
    elif end%bins_input == 0:
        horizontal = start +1
    elif end%bins_input > start%bins_input :
        horizontal = start + 1     #destination is on the right
    else:
        horizontal = start - 1     #destination is on the left
    #start of the movement
    if vertical == 0 :
        start = horizontal         #move into the horizontal dest  
    elif horizontal == 0 :
        start = vertical           #move into the horizontal dest 
    elif agg_df.iloc[horizontal]['amenity_count'] > agg_df.iloc[vertical]['amenity_count'] :
        start = horizontal
    else:
        start = vertical
    return get_route(route,start,end,agg_df,bins_input)    #recursively call the function


def get_whole_route(locations,agg_df,bins_input):
    # Recursively run the get_route function with several points.
    route = []
    i = 0
    while i < (len(locations)-1):
        route = route + get_route(route,locations[i],locations[i+1],agg_df,bins_input)
        i = i + 1
    return route
    
    

def main(input_dir,output):
    files = []                                          ## Convert input file into location DataFrame
    for path in os.listdir(input_dir):
        p = os.path.join(input_dir, path)
        if os.path.isfile(p):
            files.append(p)
    out=[]
    for n in files:
        exif = get_exif(n)
        tags = get_geotags(exif)
        cod = get_coordinates(tags)
        out.append(cod)
    locations_df = pd.DataFrame(out, columns = ['lat','lon'])
    

    osm_df = pd.read_json("osm_expand.json.gz")            ## Read in osm_expand DataFrame
    bins = 100                                             ## Manually set bin size, larger the bins, smaller each area 
    locations_df = get_area_code(osm_df,locations_df,bins) ## Get the arae code for both DataFrame for calculation.
    osm_df= get_area_code(osm_df,osm_df,bins)
    
    # Count the number of amenity in each area, save in another DataFrame for later usage
    aggragated = osm_df.groupby('area').agg('count')['amenity'].reset_index()\
        .rename(columns = {'amenity':'amenity_count'})
    aggragated = pd.DataFrame({"area":np.array(range(np.ceil(bins*(osm_df['lat'].max()-
        osm_df['lat'].min())/((osm_df['lon'].max()-osm_df['lon'].min())/bins)).astype('int')))})\
        .merge(aggragated,on='area',how = 'outer')
    aggragated = aggragated.fillna(0).reset_index()
    osm_df = osm_df.merge(aggragated,on='area')
    
    locations_code = np.array(locations_df['area'])         ## Start of the route calculation
    route = get_whole_route(locations_code,aggragated,bins)
    route_df = osm_df[osm_df['area'].isin(route)]


    Attractions = route_df[route_df['is_att']==1]           ## Extract Result and output to a csv file.
    Attractions = Attractions[['name','amenity','Keywords']]
    Attractions.to_csv(output)
        
    
    
if __name__=='__main__':
    input_dir = sys.argv[1]
    output = sys.argv[2]
    main(input_dir,output)
