DB = "http://localhost:5984/photos"

if 0:
    FILE = open("/Users/natevw/Desktop/Captions_Sep_25_05.csv", 'r')
    PREFIX = "/Volumes/MAXTOR2/nathan/digipics/"
    SOURCE = "imgsrc-c393ded1a81e71d11859e937dd0004e8"  # A70
else:
    FILE = open("/Users/natevw/Desktop/Captions_Apr_2_2006.csv", 'r')
    PREFIX = "/Volumes/SEAGATE/photos/s60_digipics/"
    SOURCE = "imgsrc-c393ded1a81e71d11859e937dd000f8a"  # S60

# sqlite3 -csv /Users/natevw/Desktop/Captions_Apr_2_2006.db "select * from captions" > Captions_Apr_2_2006.csv

import csv
import logging
from urllib import quote_plus
from collections import namedtuple
from fermini import _transport

CaptionedPhoto = namedtuple("CaptionedPhoto", ['path', 'caption', 'rotate'])

for line in csv.reader(FILE):
    line[0] = line[0].replace(PREFIX, '')
    photo = CaptionedPhoto(*line)
    
    key = quote_plus('["%s","%s"]' % (SOURCE, photo.path))
    lookup_url = '%s/%s?key=%s' % (DB, '_design/shutterstem/_view/by_identifier', key)
    try:
        photo_id = _transport('GET', lookup_url)['rows'][0]['id']
    except IndexError:
        logging.warn("Missing photo for %s", photo.path)
        continue
    
    photo_url = "%s/%s" % (DB, photo_id)
    photo_doc = _transport('GET', photo_url)
    photo_doc['description'] = photo.caption
    if photo.rotate:
        photo_doc['tmp-image_rotation'] = int(photo.rotate)
    _transport('PUT', photo_url, photo_doc)
    logging.info("Wrote caption to %s (%s...)", photo_id,photo.caption[:25])
