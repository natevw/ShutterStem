#! /usr/bin/python
from __future__ import with_statement   # needed under Python 2.5 (Leopard default)


import couch

from time import sleep
import os
import json
import uuid
import hashlib
import subprocess

from threading import Thread
from Queue import Queue, Full as QueueFull
from collections import deque

GET_PHOTO = os.path.dirname(os.path.abspath(__file__)) + '/getphoto-osx/build/Release/getphoto';

class Importer(object):
    def _find_image(self, identifiers):
        for type, ident in identifiers.iteritems():
            if type == 'relative_path':
                key = ident['source']['_id'], ident['path']
            else:
                key = ident
            matches = self._db.get([self._DDOC, '_view/by_identifier'], {'$key':key})
            if matches['rows']:
                match = matches['rows'][0]
                return match['id'], match['value']
    
    def _image_doc(self, folder, path):
        full_path = os.path.join(folder, path)
        
        get_photo = [GET_PHOTO, '--thumbnail', '64', '--thumbnail', '512', '--timezone', self._source['time_zone'], full_path]
        p = subprocess.Popen(get_photo, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        out, err = p.communicate()
        #with open("/Users/nathan/Desktop/log.txt", 'w') as f:
        #    f.write(out + '\n')
        #    f.write(err + '\n\n')
        
        if p.returncode:
            return
        
        doc = json.loads(out)
        doc['_id'] = "testfakeimage-%s" % uuid.uuid4().hex
        doc[self._IMAGE_TYPE] = True
        
        idents = doc.setdefault('identifiers', {})
        idents['relative_path'] = {'source':couch.make_ref(self._source), 'path':path}
        with open(full_path, 'rb') as f:
            digester = hashlib.md5()
            while True:
                buff = f.read(524288)
                if not buff:
                    break
                digester.update(buff)
            digest = digester.hexdigest()
        idents['md5'] = digest
        
        return doc
    
    def __init__(self, db_url, source_id, folder):
        self._db = couch.Database(db_url)
        self._source = self._db.read(source_id)
        self._DDOC = '_design/shutterstem'
        self._IMAGE_TYPE = 'testtype-image';
        
        self._cancelled = False
        self._done = False
        self._files = Queue()
        self._recent_image_docs = deque(maxlen=10)
        self._image_docs = Queue(maxsize=30)
        self._imported_refs = Queue()
        
        def find_new_files():
            for (dirpath, dirnames, filenames) in os.walk(folder):
                for filename in filenames:
                    if self._cancelled:
                        break
                    if filename[0] == '.':
                        continue
                    
                    full_path = os.path.join(dirpath, filename)
                    rel_path = os.path.relpath(full_path, folder)
                    identifiers = {'relative_path':{'source':{'_id':source_id}, 'path':rel_path}}
                    if not self._find_image(identifiers):
                        self._files.put(full_path)
                
                if self._cancelled:
                    break
            self._files.put(None)
        
        def get_file_docs():
            while not self._cancelled:
                file = self._files.get()
                if not file:
                    break
                
                path = os.path.relpath(file, folder)
                doc = self._image_doc(folder, path)
                if doc and not self._find_image(doc['identifiers']):
                    while not self._cancelled:
                        try:
                            self._image_docs.put(doc, True, 0.5)
                        except QueueFull:
                            pass
                        else:
                            break
                    
                    doc = json.loads(json.dumps(doc))
                    del doc['_attachments']['thumbnail/512.jpg']
                    self._recent_image_docs.appendleft(doc)
            
            while not self._cancelled:
                try:
                    self._image_docs.put(None, True, 0.5)
                except QueueFull:
                    pass
                else:
                    break
        
        def upload_docs():
            while not self._cancelled:
                doc = self._image_docs.get()
                if not doc:
                    break
                self._db.write(doc)
                self._imported_refs.put({'_id':doc['_id'], '_rev':doc['_rev']})
            self._imported_refs.put(None)
            self._done = True
        
        def delete_docs():
            while True:
                doc = self._imported_refs.get()
                if not doc:
                    break
                self._db.delete(doc)
        
        self._find_files = Thread(target=find_new_files, name="Find new files (%s)" % self._source['_id'])
        self._find_files.daemon = True
        self._find_files.start()
        self._get_file_docs = Thread(target=get_file_docs, name="Prepare image documents (%s)" % self._source['_id'])
        self._get_file_docs.daemon = True
        self._get_file_docs.start()
        self._upload_docs = Thread(target=upload_docs, name="Upload image documents (%s)" % self._source['_id'])
        self._upload_docs.daemon = True
        self._delete_docs = Thread(target=delete_docs, name="Remove documents from cancelled import (%s)" % self._source['_id'])
    
    def begin(self):
        if not self._cancelled:
            self._upload_docs.start()
    
    def cancel(self, remove=True):
        self._cancelled = True
        
        if self._upload_docs.is_alive():
            self._image_docs.put(None)
        else:
            self._imported_refs.put(None)
        
        if remove:
            self._delete_docs.start()
    
    def _is_active(self):
        return any(t.is_alive() for t in (self._find_files, self._get_file_docs, self._upload_docs, self._delete_docs))
    
    def finish(self):
        if self._is_active():
            raise AssertionError("Import still active")
    
    def status(self):
        active = self._is_active()
        imported = self._imported_refs.qsize()
        remaining = self._files.qsize() + self._image_docs.qsize()
        
        if self._cancelled:
            verb = 'cancel'
            remaining = 0
        elif self._done:
            verb = 'done'
            imported -= 1
        elif self._upload_docs.is_alive():
            verb = 'import+scan' if self._find_files.is_alive() else 'import'
            remaining -= 1 if verb == 'import' else 0
        else:
            verb = 'wait+scan' if self._find_files.is_alive() else 'wait'
            remaining -= 1 if verb == 'wait' else 0
        
        return {
            'active': active,
            'imported': imported,
            'remaining': remaining,
            'verb': verb,
            'recent': list(self._recent_image_docs)
        }


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
