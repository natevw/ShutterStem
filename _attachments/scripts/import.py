#! /usr/bin/python

# see http://wiki.apache.org/couchdb/ExternalProcesses for configuration instructions

import os
import json

class CouchExternal(object):
    def run(self):
        import sys
        import json
        
        line = sys.stdin.readline()
        while line:
            try:
                response = self.process(json.loads(line))
            except Exception:
                response = {'code':500, 'json':{'error':True, 'reason':"Internal error processing request"}}
            sys.stdout.write("%s\n" % json.dumps(response))
            sys.stdout.flush()
            line = sys.stdin.readline()
    
    def process(self, req):
        return {'json':{'ok':True}}


class ShutterStemImporter(CouchExternal):
    def __init__(self):
        self.imports = {}
    
    def process(self, req):
        source_id = req['path'][2]
        if req['method'] == 'POST':
            token = req['query'].get('csrf_token', None)
            helper = req['query'].get('helper_path', None)
            if not token or not helper or not source_id:
                return {'code':400, 'json':{'error':True, 'reason':"Required parameter(s) missing"}}
            
            # check that the request is not forged
            with open(helper, 'r') as f:
                first_chunk = f.read(4096)  # token required in first 4k
                if first_chunk.find("<!-- SHUTTERSTEM-TOKEN(%s)TOKEN-SHUTTERSTEM -->" % token) == -1:
                    raise Exception()
            
            if source_id in self.imports:
                return {'code':409, 'json':{'error':True, 'reason':"An import is already in progress for this source"}}
            
            info = self.imports[source_id] = {}
            info['folder'] = os.path.dirname(helper)
            # TODO: start import of requested folder in background
            return {'code':202, 'json':{'ok':True, 'message':"Import of '%s' has started." % info['folder']}}
        
        if req['method'] == 'GET':
            # TODO: return status info (w/long polling?)
        
        return {'body': "<h1>Hello World!</h1>\n<pre>%s</pre>" % json.dumps(req, indent=4)}
        

if __name__ == "__main__":
    import_server = ShutterStemImporter()
    import_server.run()