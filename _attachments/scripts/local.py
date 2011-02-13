#! /usr/bin/python
from __future__ import with_statement   # needed under Python 2.5 (Leopard default)


import couch
from importer import Importer

from time import sleep
import os
import json

class ImportManager(couch.External):
    def __init__(self):
        self.imports = {}
    
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
        
        if source_id in self.imports:
            return {'code':409, 'json':{'error':True, 'reason':"An import is already in progress for this source"}}
        
        info = self.imports[source_id] = {}
        db_url = "http://%s/%s" % (req['headers']['Host'], req['info']['db_name'])
        folder = os.path.dirname(helper)
        info['importer'] = Importer(db_url, source_id, folder)
        
        return {'code':202, 'json':{'ok':True, 'message':"Import of '%s' may now start." % folder}}
    
    def process_action(self, req):
        action = req['path'][3]
        source_id = req['path'][2]
        if not action or not source_id:
            return {'code':400, 'json':{'error':True, 'reason':"Required parameter(s) missing"}}
        
        if source_id not in self.imports:
            return {'code':404, 'json':{'error':True, 'reason':"No import is in progress for this source"}}
        
        info = self.imports[source_id]
        
        if action == 'import':
            info['importer'].begin()
            return {'code':202, 'json':{'ok':True, 'message':"Import will proceed"}}
        elif action == 'cancel':
            info['importer'].cancel()
            return {'code':202, 'json':{'ok':True, 'message':"Import is cancelling"}}
        elif action == 'finish':
            info['importer'].finish()
            del self.imports[source_id]
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
            if source_id not in self.imports:
                return {'code':404, 'json':{'error':True, 'reason':"No import is in progress for '%s'." % source_id}}
            
            status = self.imports[source_id]['importer'].status()
            return {'json':status}
        
        return {'code':400, 'json':{'error':True, 'reason':"Bad request"}}
        

if __name__ == "__main__":
    import_server = ImportManager()
    import_server.run()
