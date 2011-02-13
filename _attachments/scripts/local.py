#! /usr/bin/python
from __future__ import with_statement   # needed under Python 2.5 (Leopard default)


import couch
from importer import Importer

from time import sleep
import os
import json

class LocalHelper(couch.External):
    def __init__(self):
        self.importers = {}
    
    def process_folder(self, req):
        source_id = req['path'][2]
        token = req['query'].get('token', None)
        helper = req['query'].get('utility', None)
        if not source_id or not token or not helper:
            return {'code':400, 'json':{'error':True, 'reason':"Required parameter(s) missing"}}
        
        # check that the request is not forged
        with open(helper, 'r') as f:
            first_chunk = f.read(4096)  # token required in first 4k
            if first_chunk.find("<!-- SHUTTERSTEM-TOKEN(%s)TOKEN-SHUTTERSTEM -->" % token) == -1:
                raise Exception()
        
        folder = os.path.dirname(helper)
        allow_originals = req['query'].get('allow_originals', None)
        if allow_originals == 'true':
            # TODO: store this folder to local config w/token and helper path
            return {'code':200, 'json':{'ok':True, 'message':"Originals may be hosted from '%s'." % folder}}
        elif allow_originals is not None:
            # TODO: remove this folder from local config
            return {'code':200, 'json':{'ok':True, 'message':"Originals will NOT be hosted from '%s'." % folder}}
        
        if source_id in self.importers:
            return {'code':409, 'json':{'error':True, 'reason':"An import is already in progress for this source"}}
        
        db_url = "http://%s/%s" % (req['headers']['Host'], req['info']['db_name'])
        self.importers[source_id] = Importer(db_url, source_id, folder)
        
        return {'code':202, 'json':{'ok':True, 'message':"Import of '%s' may now start." % folder}}
    
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

