#! /usr/bin/python

# see http://wiki.apache.org/couchdb/ExternalProcesses for configuration instructions

import json

class CouchExternal(object):
    def run(self):
        import sys
        import json
        
        line = sys.stdin.readline()
        while line:
            response = self.process(json.loads(line))
            sys.stdout.write("%s\n" % json.dumps(response))
            sys.stdout.flush()
            line = sys.stdin.readline()
    
    def process(self, req):
        return {'json':{'ok':True}}


class ShutterStemImporter(CouchExternal):
    def process(self, req):
        return {'body': "<h1>Hello World!</h1>\n<pre>%s</pre>" % json.dumps(req, indent=4)}
        

if __name__ == "__main__":
    import_server = ShutterStemImporter()
    import_server.run()