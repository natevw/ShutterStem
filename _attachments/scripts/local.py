#! /usr/bin/python
from __future__ import with_statement   # needed under Python 2.5 (Leopard default)


import couch
import image
from importer import Importer

from time import sleep
import os
import json

CONFIG = os.path.dirname(os.path.abspath(__file__)) + '/local.config.ini'

class LocalHelper(couch.External):
    def __init__(self):
        self.importers = {}
    
    @property
    def configfile(self):
        if os.path.exists(CONFIG):
            with open(CONFIG, 'r') as file:
                return json.loads(file.read())
        else:
             return {}
    
    @configfile.setter
    def configfile(self, config):
        with open(CONFIG, 'w') as file:
            file.write(json.dumps(config))
    
    @configfile.deleter
    def configfile(self):
        os.remove(CONFIG)
    
    def check_utility(self, utility_path, csrf_token):
        with open(utility_path, 'rb') as f:
            first_chunk = f.read(4096)  # token required in first 4k
            if first_chunk.find("<!-- SHUTTERSTEM-TOKEN(%s)TOKEN-SHUTTERSTEM -->" % csrf_token) == -1:
                raise Exception()
    
    
    def process(self, req):
        _db_name, _this_external, action = req['path'][:3]
        action_subpath = req['path'][3:]
        req['database_url'] = "http://%s/%s" % (req['headers']['Host'], req['info']['db_name'])
        
        utility_path, csrf_token = req['query'].get('utility', None), req['query'].get('token', None)
        if utility_path and csrf_token:
            try:
                self.check_utility(utility_path, csrf_token)
            except Exception:
                sleep(2.5)    # slow down malicious local scanning
                return {'code':400, 'json':{'error':True, 'reason':"Bad request"}}
            else:
                folder, name = os.path.split(utility_path)
                req['utility'] = {'path':utility_path, 'token':csrf_token, 'folder':folder, 'name':name}
        elif req['method'] != 'GET':
            return {'code':400, 'json':{'error':True, 'reason':"Bad request"}}
        
        processor = getattr(self, 'process_%s_%s' % (action, req['method']), None)
        if processor:
            return processor(req, action_subpath)
        
        #return {'body': "<h1>Hello World!</h1>\n<pre>%s</pre>" % json.dumps(req, indent=4)}
        return {'code':400, 'json':{'error':True, 'reason':"Bad request"}}
    
    
    
    def process_image_GET(self, req, subpath):
        image_id, type = subpath[:2]
        image_doc = couch.Database(req['database_url']).read(image_id)
        import_info = image_doc['identifiers']['relative_path']
        source_id = import_info['source']['_id']
        
        config = self.configfile
        folders = config.setdefault('sources', {}).setdefault(source_id, {}).setdefault('folders', {})
        for folder, utility in folders.iteritems():
            # check that the utility (and folder!) is still valid and currently available
            try:
                self.check_utility(os.path.join(folder, utility['name']), utility['token'])
            except Exception:
                continue
            
            image_path = os.path.join(folder, import_info['path'])
            if os.path.exists(image_path):
                # TODO: conjure up appropriate original/export/view
                doc, _ = image.get(image_path, '--thumbnail', type)
                if doc:
                    img = doc.get('_attachments', {}).get('thumbnail/%s.jpg' % type)
                    if img:
                        headers = {'Content-Type':img['content_type']}
                        return {'code':200, 'headers':headers, 'base64':img['data']}
        
        return {'code':404, 'json':{'error':True, 'reason':"No original image could be found"}}
    
    
    def process_import_GET(self, req, subpath):
        source_id = subpath[0]
        importer = self.importers.get(source_id, None)
        if importer:
            return {'json':importer.status()}
        else:
            return {'code':404, 'json':{'error':True, 'reason':"No import is in progress for '%s'." % source_id}}
    
    def process_import_POST(self, req, subpath):
        source_id, action = subpath[:2]
        importer = self.importers.get(source_id, None)
        if not importer and action != 'create':
            return {'code':404, 'json':{'error':True, 'reason':"No import is in progress for '%s'." % source_id}}
        elif action == 'create' and importer:
            return {'code':409, 'json':{'error':True, 'reason':"An import is already in progress for this source"}}
        
        if action == 'create':
            self.importers[source_id] = Importer(req['database_url'], source_id, req['utility']['folder'])
            return {'code':202, 'json':{'ok':True, 'message':"Import will proceed"}}
        elif action == 'begin':
            importer.begin()
            return {'code':202, 'json':{'ok':True, 'message':"Import will proceed"}}
        elif action == 'cancel':
            importer.cancel()
            return {'code':202, 'json':{'ok':True, 'message':"Import is cancelling"}}
        elif action == 'finish':
            importer.finish()
            del self.importers[source_id]
            return {'code':200, 'json':{'ok':True, 'message':"Import finished"}}
        else:
            return {'code':404, 'json':{'error':True, 'reason':"Unknown action"}}
    
    
    def process_folder_POST(self, req, subpath):
        source_id, action = subpath[:2]
        folder = req['utility']['folder']
        config = self.configfile
        folders = config.setdefault('sources', {}).setdefault(source_id, {}).setdefault('folders', {})
        folder_info = folders.setdefault(folder, {})
        
        if action == 'check':
            pass
        elif action == 'allow' or (action == 'update' and folder_info):
            folder_info['name'] = req['utility']['name']
            folder_info['token'] = req['utility']['token']
            self.configfile = config
        elif action == 'disable':
            del folders[folder]
            self.configfile = config
            folder_info = None
        return {'json':{'ok':True, 'allows_originals':bool(folder_info)}}

if __name__ == "__main__":
    LocalHelper().run()

