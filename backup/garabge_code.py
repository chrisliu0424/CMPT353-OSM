def False_positive_rate(result,start,end):
    """
    This function calculate the approxiamte false positive rate by counting the result in the reacangle created 
        by the start position and end position
    If we are walking on the street, we can observe everything at least within 40 meters 
        around us(average city street in the United States is 71 feet and 6 inches from curb to curb),  
        so we will adjust our reactangle to 0.0002 wider(for both lat and lon)
    Input: result dataframe containing all posible locations
           start dataframe containing starting latitude and longitude
           end dataframe containing ending latitude and longitude
    Output: approximate False positive rate for the result
    """
    Wider = 0.0002
    if start.loc[0,'lat'] > end.loc[0,'lat']:
        top = start.loc[0,'lat'] + Wider
        bottom = end.loc[0,'lat'] - Wider
    else:
        top = end.loc[0,'lat'] + Wider
        bottom = start.loc[0,'lat'] - Wider
    if start.loc[0,'lon'] > end.loc[0,'lon']:
        right = start.loc[0,'lon'] + Wider
        left = end.loc[0,'lon'] - Wider
    else:
        right = start.loc[0,'lon'] + Wider
        left = start.loc[0,'lon'] - Wider
    return (~(((result['lat'] >= bottom) & (result['lat'] <= top) 
               & (result['lon'] >= left) & (result['lon'] <= right)))).sum()/result.shape[0]


PCA_model = PCA(n_components = 1)
pca_data = PCA_model.fit_transform(osm_data[['lat','lon']])
pca_start = PCA_model.transform(start_df)
pca_end = PCA_model.transform(end_df)
result = osm_data[(pca_data <= pca_start) & (pca_data >= pca_end)]
False_positive_rate(result,start,end)

X = np.stack([start.loc[0,'lon'], end.loc[0,'lon']]).reshape(-1, 1)
y = np.stack([start.loc[0,'lat'], end.loc[0,'lat']]).reshape(-1, 1)
model = LinearRegression()
model.fit(X,y)
model.coef_, model.intercept_
start,end
osm_data['estimate'] = osm_data['lon'] * model.coef_[0] + model.intercept_ 
result = osm_data[(osm_data['lat'] <= osm_data['estimate'] + 0.0002) & 
                  (osm_data['lat'] >= osm_data['estimate'] - 0.0002) &
                  (osm_data['lon'] >= end.loc[0,'lon'] - 0.0002) &
                  (osm_data['lon'] <= start.loc[0,'lon'] + 0.0002)]


start = 6116
end = 6104
i = 0;
route = [start]
while(start != end):
    if (end-start)/size > 1 :
        vertical = start + size    #destination is above
    elif (end-start)/size < -1:
        vertical = start - size    #destination is below
    else:
        vertical = 0               #same row
    right_remain = start % size    #keep on track how many area remain on the right
    if abs(end-start)%size > right_remain :
        horizontal = start + 1     #destination is on the right
    elif abs(end-start)%size == 0 :
        horizontal = 0             #destination is on the same column
    else:
        horizontal = start - 1     #destination is on the left
    #start of the movement
    if vertical == 0 :
        start = horizontal         #move into the horizontal dest  
    elif horizontal == 0 :
        start = vertical           #move into the horizontal dest 
    elif aggragated.iloc[horizontal]['amenity_count'] > aggragated.iloc[vertical]['amenity_count'] :
        start = horizontal
    else:
        start = vertical
    route.append(start)
    i +=1
    if i > 1000:
        break


def distance(data):
    """
    This function calculate the distance between the end location to every places
    Formula taken from https://stackoverflow.com/questions/27928/calculate-distance-between-two-latitude-longitude-points-haversine-formula?page=1&tab=votes#tab-top
    A small modification has been made to return the distance in meter
    Input: dataframe with columns [['lat','lon','end_lat','end_lon']]
    Return: same dataframe but with distance from every location to the end location
    """
    p = pi/180
    a = 0.5 - np.cos((data['end_lat']-data['lat'])*p)/2 + np.cos(data['lat']*p) * np.cos(data['end_lat']*p) * (1-np.cos((data['end_lon']-data['lon'])*p))/2
    data['distance_to_end'] = 12742 * np.arcsin(np.sqrt(a)) * 1000   
    b = 0.5 - np.cos((data['start_lat']-data['lat'])*p)/2 + np.cos(data['lat']*p) * np.cos(data['start_lat']*p) * (1-np.cos((data['start_lon']-data['lon'])*p))/2
    data['distance_from_start'] = 12742 * np.arcsin(np.sqrt(b)) * 1000   
    return data

