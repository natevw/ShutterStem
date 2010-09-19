#! /usr/bin/python
'''ShutterStem "reference" importer - Imports photo thumbnails and metadata into CouchDB'''

# Written by natevw, 2010 August. Copyright (c) 2010 Calf Trail Software, LLC. (MIT licensed)


SMALL_SIZE = 64     # 64^2 * 4 = 16kB
MEDIUM_SIZE = 512   # 512^2 * 4 = 1MB
RECHECK_HASH = False

# NOTE: argparse requires 2.7, deprecating optparse and tweaking a few things. hooray?
try:
    from argparse import ArgumentParser
    arger = OptionParser(description=__doc__)
    arg_add = arger.add_argument
except:
    from optparse import OptionParser
    arger = OptionParser(description=__doc__, usage="usage: %prog [options] folder")
    arg_add = arger.add_option

arg_add('-s', '--server', dest='host', default="localhost", help="CouchDB server host to use")
arg_add('-p', '--port', dest='port', type=int, default=5984, help="CouchDB server port")
arg_add('-d', '--photos-database', dest='photos_db', default="photos", help="Name of database where thumbnails and metadata are stored")
arg_add('-f', '--files-database', dest='files_db', default="files", help="Name of database where imported file information is stored")
arg_add('-z', '--camera-timezone', dest='camera_tz', default="Z", help="Timezone string to append to image timestamp (Z or +/-HH:MM)")
try:    # ArgumentParser
    arg_add('folder', nargs=1, dest='source_dir', help="Folder from which to import JPEG pictures")
    args = arger.parse_args()
except: # OptionParser
    (args, positional) = arger.parse_args()
    try:
        setattr(args, 'source_dir', positional[0])
    except:
        #arger.print_usage()
        arger.print_help()
        exit(1)

import logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)+8s: %(message)s', datefmt='%Y-%m-%d %H:%M:%S')



# --- Image abstractions for use by core (this implements using PIL) --- #

from PIL import Image, ExifTags
try:
    from cStringIO import cStringIO as StringIO
except ImportError:
    from StringIO import StringIO

def open_image(img_path):
    img = Image.open(img_path)
    exif = {}
    # tip from http://wolfram.kriesing.de/blog/index.php/2006/reading-out-exif-data-via-python#comment-183
    rawExif = img._getexif() or {}
    for tag, value in rawExif.items():
        decoded = ExifTags.TAGS.get(tag, tag)
        if decoded is 'MakerNote':
            # PIL doesn't decode maker notes (well, PIL.TiffImagePlugin.ImageFileDirectory might some) so don't bother
            # storing the big blob o'data. a "real" importer should extract genuinely interesting info (eg lens model)
            continue
        exif[decoded] = value
    if 'GPSInfo' in exif:
        gps_info = {}
        for tag, value in exif['GPSInfo'].items():
            decoded = ExifTags.GPSTAGS.get(tag, tag)
            gps_info[decoded] = value
        exif['GPSInfo'] = gps_info
    if 'Orientation' in exif:
        orient = exif['Orientation']
        # see http://sylvana.net/jpegcrop/exif_orientation.html for handy guide to how to flip/rotate
        ops = {2:Image.FLIP_LEFT_RIGHT, 3:Image.ROTATE_180, 4:Image.FLIP_TOP_BOTTOM, 6:Image.ROTATE_270, 8:Image.ROTATE_90}
        if orient in ops:
            img = img.transpose(ops[orient])
        elif orient == 5:
            img = img.transpose(Image.ROTATE_270).transpose(Image.FLIP_LEFT_RIGHT)
        elif orient == 7:
            img = img.transpose(Image.FLIP_LEFT_RIGHT).transpose(Image.ROTATE_270)
    aspect = float(img.size[0]) / img.size[1]
    img.load()
    return img, exif, aspect

def create_thumbnail(img, size, aspect):
    w = min(size * aspect, size)
    h = min(size / aspect, size)
    #return img.resize((int(round(w)),int(round(h))))   # 3x speed improvment (1.243832 -> 4.210614 photos/sec)
    return img.resize((int(round(w)),int(round(h))), Image.ANTIALIAS)

def get_jpeg_data(img):
    f = StringIO()
    # NOTE: don't use optimize without workaround: http://mail.python.org/pipermail/image-sig/1999-August/000816.html
    img.save(f, 'JPEG', quality=85)
    return f.getvalue()



# --- really basic CouchDB helpers ---

from types import FunctionType, GeneratorType
import httplib, urllib
import json

conn = httplib.HTTPConnection(args.host, args.port)

def couch_get(db, docid='', query=None):
    if query:
        query_dict = {}
        for key, value in query.items():
            if key in ['key', 'startkey', 'endkey']:
                value = json.dumps(value)
            elif type(value) == bool:
                value = 'true' if value else 'false'
            elif value is None:
                value = 'null'
            query_dict[key] = value
        query = urllib.urlencode(query_dict)

    path = '/%s/%s' % (db, docid)
    if query:
        path += '?%s' % query
    conn.request('GET', path)
    result = conn.getresponse()

    status = result.status
    data = json.loads(result.read())
    return status, data

def couch_put(db, docid='', doc=None):
    path = '/%s/%s' % (db, docid)
    if doc:
        conn.request('PUT', path, json.dumps(doc))
    else:
        conn.request('PUT', path)
    result = conn.getresponse()
    
    status = result.status
    data = json.loads(result.read())
    return status, data

def couch_create(db, doc, ids):
    '''Put new document until sucessful or non-conflict error'''
    while True:
        if type(ids) is FunctionType:
            docid = ids()
            if type(docid) is GeneratorType:
                ids = docid
                docid = next(ids)
        if type(ids) is list:
            docid = ids.pop()
        else:
            docid = next(ids)
        status, msg = couch_put(db, docid, doc)
        if status == 201:
            doc['_id'] = msg['id']
            doc['_rev'] = msg['rev']
            return status, doc
        elif status != 409:
            if type(ids) is list:
                ids.append(docid)
            return status, msg

def couch_update(db, docid, doc, change):
    '''Update existing document until sucessful or non-conflict error'''
    while True:
        if type(change) is FunctionType:
            change(doc)
        else:
            doc.update(change)
        status, msg = couch_put(db, docid, doc)
        if status == 201:
            doc['_id'] = msg['id']
            doc['_revid'] = msg['rev']
            return status, doc
        elif status == 409:
            status, doc = couch_get(db, docid)
            if status != 200:
                return status, doc
        else:
            return status, msg




# --- core "reference" importer ---

# NOTE: by "reference" I (natevw) mean this importer hopes to set a good example for the basic structure and behaviour
#       around a photo database. The goal is to define a basic core of info that initial clients can design around.
#       However, we heart CouchDB's schemalessness for a reason, so do please feel free to relax a bit.

import time
import os
import hashlib
import base64
import uuid
import subprocess


startTime = time.time()
numPhotosFound = 0
numPhotosImported = 0

# create photos_db if necessary
status, msg = couch_get(args.photos_db)
if status == 404:
    logging.warn("Photos database not found, creating")
    status, msg = couch_put(args.photos_db)
    if status != 201:
        logging.error("Could not create photos database: %s", msg)
        exit(1)
elif status != 200:
    logging.error("Could not access photos database: %s", msg)
    exit(1)
status, msg = couch_get(args.photos_db, '_design/basics')
if status == 404:
    logging.warn("Basic photos app not found, installing")
    app = os.path.join(os.path.dirname(__file__), 'photos-basics')
    subprocess.call(['couchapp', 'push', app, args.photos_db])


# create files_db if necessary
status, msg = couch_get(args.files_db)
if status == 404:
    logging.warn("Files database not found, creating")
    status, msg = couch_put(args.files_db)
    if status != 201:
        logging.error("Could not create files database: %s", msg)
        exit(1)
elif status != 200:
    logging.error("Could not access files database: %s", msg)
    exit(1)
status, msg = couch_get(args.files_db, '_design/basics')
if status == 404:
    logging.warn("Basic files app not found, installing")
    app = os.path.join(os.path.dirname(__file__), 'files-basics')
    subprocess.call(['couchapp', 'push', app, args.files_db])

logging.info("Importing JPEGs from '%s' into http://%s:%u/%s (and /%s)", args.source_dir, args.host, args.port, args.photos_db, args.files_db)
for (dirpath, dirnames, filenames) in os.walk(args.source_dir):
    for filename in filenames:
        if filename[0] == '.':
            continue
        
        if os.path.splitext(filename)[1].lower() != '.jpg':
            # keep this proof-of-concept/cross-platform importer simple (for starters, PIL can't handle RAW files)
            continue
        numPhotosFound += 1
        
        img_path = os.path.join(dirpath, filename)
        logging.debug("Processing file '%s'", img_path)
        
        if not RECHECK_HASH:
            # skip if img_path already has photo via files_db
            file_id = urllib.quote(img_path, '')
            status, file_doc = couch_get(args.files_db, file_id)
            if status == 200:
                if 'photo' in file_doc:
                    logging.info("Skipping - found existing photo (by file path) for file: %s", file_doc)
                    continue
            else:
                file_doc = {}
        
        try:
            f = open(img_path, 'rb')
        except IOError as e:
            logging.info("Could not access '%s' (%s)", img_path, e)
            continue
        digester = hashlib.sha1()
        while True:
            buff = f.read(524288)
            if not buff:
                break
            digester.update(buff)
        sha1 = digester.hexdigest()
        
        if RECHECK_HASH:
            # skip if img_path already has photo via files_db
            file_id = urllib.quote(img_path, '')
            status, file_doc = couch_get(args.files_db, file_id)
            if status == 200:
                if 'sha1' in file_doc and file_doc['sha1'] != sha1:
                    logging.warn("Checksum hash for '%s' has changed (%s -> %s)", img_path, file_doc['sha1'], sha1)
                if 'photo' in file_doc:
                    logging.info("Skipping - found existing photo (by file path) for file: %s", file_doc)
                    continue
            else:
                file_doc = {}
        
        # query a suitable view on photos_db for sha1 (hopefully someday fingerprint too, see below)
        status, result = couch_get(args.photos_db, "_design/basics/_view/by_signature", {'key':sha1})
        if status == 200 and len(result['rows']):
            # update file database with photo info
            photo_id = result['rows'][0]['id']
            couch_put(args.files_db, file_id, {"photo": photo_id, "sha1": sha1})
            logging.info("Skipping - found existing photo (by photo signature) for file: %s", photo_id)
            continue
        
        # query a suitable view on files_db for sha1, to avoid duplicates when original files are identical
        status, result = couch_get(args.files_db, "_design/basics/_view/by_signature", {'key':sha1})
        if status == 200 and len(result['rows']):
            # make sure files database up-to-date with photo info
            file_id = result['rows'][0]['_id']
            status, file_doc = couch_get(args.files_db, file_id)
            if 'photo' in file_doc:
                logging.info("Skipping - found existing photo (by file signature) for file: %s", file_doc)
                continue
        
        # NOTE: None of the above solves the duplicates problem entirely; see note about image fingerprint below.
        
        
        try:
            img, exif, aspect = open_image(img_path)
        except IOError as e:
            logging.warn("Could not open image '%s' (%s)", img_path, e)
            continue
        
        photo_doc = {}
        # NOTE: we very conciously do NOT just dump all of the image's EXIF/IPTC/XMP data into a JSON document!
        #       All we want is information interesting to the casual viewer, perhaps as they are organizing/tagging/captioning.
        #       (We don't want to be replicating a bloated set of obscure data that pertains to the original format only.
        #       Client apps wishing to perform detailed analysis should refer to the original file if it is available.)
        #       That said, we should strive to stand on the shoulders of those giants (especially XMP and MWG) regarding metadata.
        
        # UNDERLYING PHILOSOPHY: ShutterStem is intended to be a human-centric collection of metadata that a photographer or audience
        #                        can use to enjoy and organize photos using any app on any device, even when the originals are unavailable.
        #                        (Likewise, we only store thumbnails, rather than originals, to reduce bandwidth and capacity requirements.)
        
        if 'DateTimeOriginal' in exif:
            # convert to http://www.ietf.org/rfc/rfc3339.txt
            timestamp = exif['DateTimeOriginal'].replace(":", "-", 2).replace(" ", "T")
            if 'SubsecTimeOriginal' in exif:
                timestamp += ".%s" % exif['SubsecTimeOriginal']
            timestamp += args.camera_tz
            photo_doc['timestamp'] = timestamp
        else:
            # no time for us, no time for you, Mr. Lamephoto!
            logging.warn("No timestamp found in '%s'", img_path)
            continue
        
        # handy helpers for exif values
        def exif_ratio(val):
            if val[1] == 1:
                return val[0]
            return float(val[0]) / val[1]
        def exif_coord(val, ref):
            d, m, s = map(exif_ratio, val)
            dd = d + (m + s / 60.0) / 60.0
            if ref == 'S' or ref == 'W':
                dd = -dd
            return dd
        
        photo_doc['system'] = sys_info = {}
        if 'Model' in exif:
            if 'Make' in exif and exif['Model'].find(exif['Make']) == -1:
                sys_info["camera"] = "%s %s" % (exif['Make'], exif['Model'])
            else:
                sys_info["camera"] = exif['Model']
        # unfortunately, PIL image handler doesn't convert MakerNote -> MakerInfo, so the following is just for reference
        if 'Aux' in exif and 'LensModel' in exif['MakerInfo']:    
            sys_info["lens"] = exif['MakerInfo']['LensModel']
        if 'FocalLength' in exif:
            # TODO: this is somewhat meaningless without knowing sensor size, also/instead store 35mm equivalent?
            sys_info["focal_length"] = exif_ratio(exif['FocalLength'])
            # FocalLength, FocalPlaneResolutionUnit, FocalPlaneXResolution, FocalPlaneYResolution
        
        photo_doc['exposure'] = exp_info = {}
        if 'ExposureTime' in exif:
            # note that we preserve fraction for exposure (for the humans among us)
            exp_info["speed"] = "%u/%u" % exif['ExposureTime']
            exp_info["speed"] = exp_info["speed"].replace("/1", "") # simplify
        if 'FNumber' in exif:
            exp_info["aperture"] = exif_ratio(exif['FNumber'])
        if 'ISOSpeedRatings' in exif:
            # NOTE: this is theoretically a multiple value type, but PIL _getexif returns as single value
            # see http://www.awaresystems.be/imaging/tiff/tifftags/privateifd/exif/isospeedratings.html
            exp_info["iso"] = exif['ISOSpeedRatings']
        
        if 'GPSInfo' in exif:
            photo_doc['location'] = gps_info = {}
            gps = exif['GPSInfo']
            if 'GPSLongitude' in gps and 'GPSLongitudeRef' in gps:
                gps_info['longitude'] = exif_coord(gps['GPSLongitude'], gps['GPSLongitudeRef'])
            if 'GPSLatitude' in gps and 'GPSLatitudeRef' in gps:
                gps_info['latitude'] = exif_coord(gps['GPSLatitude'], gps['GPSLatitudeRef'])
            if 'GPSAltitude' in gps and 'GPSAltitudeRef' in gps:
                gps_info['altitude'] = exif_ratio(gps['GPSAltitude'])
                if gps['GPSAltitudeRef'] == 1:
                    gps_info['altitude'] = -gps_info['altitude']
            if 'GPSMapDatum' in gps and len(gps['GPSMapDatum']):
                # do a poor-man's test to verify datum is WGS-84...
                if gps['GPSMapDatum'].find('84'):
                    # ...if not, don't store coordinates with the photo after all
                    del photo_doc['location']
        
        photo_doc['image'] = image_info = {}
        photo_doc['image']['aspect'] = aspect;
        photo_doc['image']['original_sha1'] = sha1;
        photo_doc['image']['original_filename'] = filename;
        # TODO: it'd be great if we could also store a less-fragile image fingerprint for efficient duplicate detection
        
        # TODO: write a one-off script to find all non-medium thumbnails and fix
        photo_doc['tmp_MedQ'] = True
        
        photo_doc['_attachments'] = {}
        jpg_thumbnails = [("small", SMALL_SIZE), ("medium", MEDIUM_SIZE)]
        for name, size in jpg_thumbnails:
            thumb = create_thumbnail(img, size, aspect)
            data_64ed = base64.standard_b64encode(get_jpeg_data(thumb))
            photo_doc['_attachments']["%s.jpg" % name] = {'content_type': "image/jpeg", 'data': data_64ed}
        
        
        def photo_ids():
            # NOTE: we use a random unique id to avoid collisions between databases, however (!)
            #       with a flexible photo workflow we may get "reverse collisions" in the sense that
            #       if a user imports the same photo into two databases and then merges them, we will
            #       have multiple metadata documents when we only want one.
            #
            #       Solving this is the duty of whatever handles sync conflicts; it should detect this
            #       "reverse" collision/conflict situation, use (e.g.) the lowest photo_id as the canonical
            #       and store alias ids somehow in the "image" portion of the photo_doc.
            while True:
                yield uuid.uuid4().hex
        status, photo_doc = couch_create(args.photos_db, photo_doc, photo_ids)
        if status == 201:
            photo_id = photo_doc['_id']
            logging.info("Added photo: %s", photo_id)
        else:
            logging.error("Couldn't create photo: %s", msg)
            continue
        
        status, file_doc = couch_update(args.files_db, file_id, file_doc, {"photo": photo_id, "sha1": sha1})
        if status == 201:
            logging.debug("Stored file info: %s", file_doc)
        else:
            logging.error("Couldn't update file info (%u): %s", status, file_doc)
        
        # now wasn't that fun?!
        numPhotosImported += 1
        
duration = time.time() - startTime
logging.info("Imported %u photos (from %u files found) in %u seconds", numPhotosImported, numPhotosFound, duration)
logging.info("average of %f photos/sec imported (%f photos/sec found)", numPhotosImported / duration, numPhotosFound / duration)

logging.info("Triggering view updates")
couch_get(args.photos_db, "_design/basics/_view/by_date", {'limit':0})
logging.info("Done")
