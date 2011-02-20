#! /usr/bin/python
from __future__ import with_statement   # needed under Python 2.5 (Leopard default)


import couch

import os
import json
import uuid
import hashlib
import subprocess

from threading import Thread
from Queue import Queue, Full as QueueFull
from collections import deque

GET_PHOTO = os.path.dirname(os.path.abspath(__file__)) + '/getphoto-osx/build/Release/getphoto'

class Importer(object):
    def _find_image(self, identifiers, stale=True):
        for type, ident in identifiers.iteritems():
            if type == 'relative_path':
                key = ident['source']['_id'], ident['path']
            else:
                key = ident
            query = {'$key':key}
            if stale:
                query['stale'] = 'ok'
            matches = self._db.get([self._DDOC, '_view/by_identifier'], query)
            if matches['rows']:
                match = matches['rows'][0]
                return match['id'], match['value']
    
    def _image_doc(self, folder, path):
        full_path = os.path.join(folder, path)
        
        get_photo = [GET_PHOTO, full_path]
        if 'time_zone' in self._source:
            get_photo.extend(['--timezone', self._source['time_zone']])
        get_photo.extend(['--thumbnail', '64', '--thumbnail', '512'])
        
        p = subprocess.Popen(get_photo, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        out, log = p.communicate()
        
        for line in log.split("\n"):
            if not line:
                continue
            try:
                info = json.loads(line)
            except ValueError:
                info = {'error':True, 'fallback_message':"Failed to parse utility log: '%s'" % line}
            info['path'] = "%s/%s" % (self._source['_id'], path)
            self._log.append(info)
        if p.returncode:
            return
        
        try:
            doc = json.loads(out)
        except ValueError:
            info = {'error':True, 'message':"Failed to parse output document: '%s'" % out}
            info['path'] = "%s/%s" % (self._source['_id'], path)
            self._log.append(info)
            return
        if 'original_info' in doc:
            del doc['original_info']
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
        self._IMAGE_TYPE = 'testtype-image'
        
        self._cancelled = False
        self._done = False
        self._files = Queue()
        self._recent_image_docs = deque(maxlen=10)
        self._image_docs = Queue(maxsize=30)
        self._imported_refs = Queue()
        self._log = deque()
        
        def find_new_files():
            self._find_image({'update_identifiers':"Updating identifiers view index before new import."}, stale=False)
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
                if not doc:
                    continue
                
                new_identifiers = json.loads(json.dumps(doc['identifiers']))
                del new_identifiers['relative_path']
                if self._find_image(new_identifiers):
                    continue
                
                while not self._cancelled:
                    try:
                        self._image_docs.put(doc, True, 0.5)
                    except QueueFull:
                        pass
                    else:
                        break
                
                doc = json.loads(json.dumps(doc))
                if 'thumbnail/512.jpg' in doc.get('_attachments', {}):
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
                self._db.remove(doc)
        
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
            'recent': list(self._recent_image_docs),
            'log': list(self._log)
        }
