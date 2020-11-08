
# Extract Spark-style JSON from planet.osm data.
# Typical invocation:
# spark-submit osm-amenities.py /courses/datasets/openstreetmaps amenities


import pandas as pd
import sys
import re
# python3 osm-expand HLLBC_ATT.csv amenities-vancouver.json.gz osm_expand.json.gz

def main(HLLBC_ATT, osm,output):
	BC_ATT = pd.read_csv(HLLBC_ATT)
	
	# extract only the columns we want
	BC_ATT = BC_ATT[['NAME',"DESCRIPTN","LATITUDE","LONGITUDE","KEYWORDS"]]

	# filter our Non-Vancouver area
	BC_ATT = BC_ATT[(BC_ATT['LONGITUDE'] > -123.5) & (BC_ATT['LONGITUDE'] < -122)]
	BC_ATT = BC_ATT[(BC_ATT['LATITUDE'] > 49) & (BC_ATT['LATITUDE'] < 49.5)]

	# fill in na's and set an extra indicator coloum that this data is from attration dataset
	BC_ATT = BC_ATT.fillna("")
	BC_ATT['is_att'] =1
	BC_ATT = BC_ATT.rename(columns = {"NAME" : "name", "DESCRIPTN" : "amenity", "LATITUDE" : "lat",
				  "LONGITUDE":"lon","KEYWORDS":"Keywords"})

	# clean the useless tailing massage in amenity column
	def correct_amenity(line):
		return re.split(r' ;',line)[0]
	BC_ATT['amenity'] = BC_ATT['amenity'].apply(correct_amenity)
	BC_ATT.head()

	osm_df = pd.read_json(osm,lines = True)
	osm_df['is_att']=0

	# Append two dataframe
	osm_all = osm_df.append(BC_ATT,sort=False)

	osm_all.to_json(output,orient="records",compression = "gzip")



if __name__ == '__main__':
	HLLBC_ATT = sys.argv[1]
	osm = sys.argv[2]
	output = sys.argv[3]
	main(HLLBC_ATT, osm,output)


