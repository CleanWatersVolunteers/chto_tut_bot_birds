from datetime import datetime, timedelta
import requests
import json

from zone_detection import detect_zone

ngw_host = 'https://blacksea-monitoring.nextgis.com'
auth = None

with open("../__token_for_map.txt", "r") as f:
    u = f.readline()[:-1]
    p = f.readline()
    auth = (u, p)

NG_TEST = False

layer_match = {'oil':60, 'bird':100, "dead":147}

def add_point(lat, lon, comment, dtime, layer_name, tg_link, count = None, position = None, status_us = None, region = None):
    name, distance = detect_zone(float(lat), float(lon))
    zone_info = ""
    if distance < 5000:
        zone_info = f"\n[Расстояние до зоны отлова: {name} составляет {distance}м]"

    print(f"[..] Zone info {zone_info}")

    feature = dict()
    feature['extensions'] = dict()
    feature['extensions']['attachment'] = None
    feature['extensions']['description'] = None
    feature['fields'] = dict()
    feature['fields']['lat'] = lat
    feature['fields']['lon'] = lon
    feature['fields']['comment'] = "TEST" + comment.replace("\n", ". ") + "\n" + tg_link + zone_info
    feature["source"] = "parser-bot"
    #print(tg_link)
    feature['geom'] = 'POINT (%s %s)' % (lon, lat)
    feature['fields']['dt'] = dtime.isoformat()
    feature['fields']['dt_auto'] = datetime.now().isoformat()
    if count: 
        feature['fields']["count"] = count
    if position: 
        feature['fields']["position"] = position
    if status_us:
        feature['fields']["status_us"] = status_us
    if region:
        feature['fields']['region'] = region

    #create feature
    post_url = ngw_host + '/api/resource/' + str(layer_match[layer_name]) +'/feature/?srs=4326&dt_format=iso'
    print(f"[..] Sending bird to gis: {feature}")
    if NG_TEST == False:
        response = requests.post(post_url, data=json.dumps(feature), auth=auth)
        print(response, response.json())
        feature_id = response.json()['id']

        if response.status_code == 200:
            print("Feature created successfully:", response.json())
        else:
            print("Error creating feature:", response.status_code, response.text)

def get_history():
    #GET /api/resource/(int:id)/export?format=GPKG&srs=4326&zipped=True&fid=ngw_id&encoding=UTF-8
    #GET /api/resource/(int:id)/export?format=CSV&srs=4326&zipped=True&fid=ngw_id&encoding=UTF-8
    #GET /api/resource/(int:id)/csv
    get_url = ngw_host + '/api/resource/' + str(100) +'/geojson'
    
    print(get_url)
    response = requests.get(get_url, auth=auth)
    print(f"DATA: {response.json()}")

