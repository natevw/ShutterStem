#! /usr/bin/python
from __future__ import with_statement   # needed under Python 2.5 (Leopard default)


import couch
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
    
    def check_utility(self, utility_path, token):
        with open(utility_path, 'r') as f:
            first_chunk = f.read(4096)  # token required in first 4k
            if first_chunk.find("<!-- SHUTTERSTEM-TOKEN(%s)TOKEN-SHUTTERSTEM -->" % token) == -1:
                raise Exception()
    
    def process_folder(self, req):
        source_id = req['path'][2]
        token = req['query'].get('token', None)
        helper = req['query'].get('utility', None)
        if not source_id or not token or not helper:
            return {'code':400, 'json':{'error':True, 'reason':"Required parameter(s) missing"}}
        
        # check that the request is not forged
        self.check_utility(helper, token)
        
        folder, name = os.path.split(helper)
        config = self.configfile
        folders = config.setdefault('sources', {}).setdefault(source_id, {}).setdefault('folders', {})
        
        allow_originals = req['query'].get('allow_originals', 'true' if (folder in folders) else None)
        if allow_originals is not None:
            if allow_originals == 'true':
                # update or set folder utility information
                folders[folder] = {'utility':name, 'token':token}
                message = "Originals may be hosted from '%s' while import utility remains in place." % folder
            else:
                del folders[folder]
                message = "Originals will NOT be hosted from '%s'." % folder
            self.configfile = config
            if 'allow_originals' in req['query']:
                return {'code':200, 'json':{'ok':True, 'message':message}}
        
        originals = folder in folders
        if source_id in self.importers:
            return {'code':409, 'json':{'error':True, 'reason':"An import is already in progress for this source", 'originals':originals}}
        else:
            self.importers[source_id] = Importer("http://%s/%s" % (req['headers']['Host'], req['info']['db_name']), source_id, folder)
            return {'code':202, 'json':{'ok':True, 'message':"Import of '%s' may now start." % folder, 'originals':originals}}
    
    def process_action(self, req):
        action = req['path'][3]
        source_id = req['path'][2]
        if not action or not source_id:
            return {'code':400, 'json':{'error':True, 'reason':"Required parameter(s) missing"}}
        
        if source_id not in self.importers:
            return {'code':404, 'json':{'error':True, 'reason':"No import is in progress for this source"}}
        
        importer = self.importers[source_id]
        
        if action == 'import':
            importer.begin()
            return {'code':202, 'json':{'ok':True, 'message':"Import will proceed"}}
        elif action == 'cancel':
            importer.cancel()
            return {'code':202, 'json':{'ok':True, 'message':"Import is cancelling"}}
        elif action == 'finish':
            importer.finish()
            del self.importers[source_id]
            return {'code':200, 'json':{'ok':True, 'message':"Import finished"}}
        
        return {'code':400, 'json':{'error':True, 'reason':"Unknown action"}}
    
    
    def process_image(self, req):
        image_doc = self.db.read(req.path[2])
        image_path_info = image_doc['identifiers']['relative_path']
        source_id = image_path_info['source']['_id']
        
        config = self.configfile
        folders = config.setdefault('sources', {}).setdefault(source_id, {}).setdefault('folders', {})
        for folder, utility in folders.iteritems():
            # check that the utility (and folder!) is still valid and currently available
            try:
                self.check_utility(os.path.join(folder, utility['name']), utility['token'])
            except Exception:
                continue
            
            image_path = os.path.join(folder, image_path['name'])
            if os.path.exists(image_path):
                # TODO: call GET_PHOTO to conjure up appropriate original/export/view
                break
        
        return {'code':404, 'json':{'error':True, 'reason':"No original image could be found"}}
        
    
    def process(self, req):
        if req['method'] == 'POST' and req['path'][3] == "folder":
            try:
                return self.process_folder(req)
            except Exception:
                sleep(2.5)    # slow down malicious local scanning
                return {'code':400, 'json':{'error':True, 'reason':"Bad request"}}
        
        elif req['method'] == 'POST' and req['path'][3] in ('import', 'cancel', 'finish'):
            try:
                return self.process_action(req)
            except Exception:
                sleep(0.5)
                return {'code':400, 'json':{'error':True, 'reason':"Bad request"}}
        
        #elif True:
        #    return {'body': "<h1>Hello World!</h1>\n<pre>%s</pre>" % json.dumps(req, indent=4)}
        elif req['method'] == 'GET':
            source_id = req['path'][2]
            if source_id not in self.importers:
                return {'code':404, 'json':{'error':True, 'reason':"No import is in progress for '%s'." % source_id}}
            
            status = self.importers[source_id].status()
            return {'json':status}
        
        return {'code':400, 'json':{'error':True, 'reason':"Bad request"}}
        

if __name__ == "__main__":
    LocalHelper().run()

