import pandas as pd
import numpy as np
import sys
import os
from PIL import Image
from PIL.ExifTags import TAGS
from PIL.ExifTags import GPSTAGS
from os import listdir
from os.path import isfile, join

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
    return [lat,lon]


def main(inputs, outputs):
    files = []
    for path in os.listdir(inputs):
        p = os.path.join(inputs, path)
        if os.path.isfile(p):
            files.append(p)
    out=[]
    for n in files:
        exif = get_exif(n)
        tags = get_geotags(exif)
        cod = get_coordinates(tags)
        out.append(cod)
        print(out)
    print(pd.DataFrame(out, columns = ['lat','lon']))
    
        
    
    
if __name__=='__main__':
    inputs = sys.argv[1]
    outputs = sys.argv[2]
    main(inputs, outputs)

#code get from :https://www.quora.com/How-can-I-read-multiple-images-in-Python-presented-in-a-folder
#               https://developer.here.com/blog/getting-started-with-geocoding-exif-image-metadata-in-python3
