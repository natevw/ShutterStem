#! /usr/bin/python
from __future__ import with_statement   # needed under Python 2.5 (Leopard default)


import couch
import image

import os
import uuid
import hashlib

from threading import Thread
from Queue import Queue, Full as QueueFull
from collections import deque

IMAGE_TYPE = 'com.shutterstem.image'


class Importer(object):
    def _find_image(self, identifiers, stale=True):
        for type, ident in identifiers.iteritems():
            if type == 'path':
                key = ident['source']['_id'], ident['name']
            else:
                key = ident
            query = {'$key':key}
            if stale:
                query['stale'] = 'ok'
            matches = self._db.get([self._DDOC, '_view/by_identifier'], query)
            if matches['rows']:
                match = matches['rows'][0]
                return match['id'], match['value']
    
    def _image_doc(self, folder, rel_path):
        full_path = os.path.join(folder, rel_path)
        args = ['--metadata']
        if 'time_zone' in self._source:
            args.extend(['--timezone', self._source['time_zone']])
        args.extend(['--thumbnail', '64', '--thumbnail', '512'])
        doc, logs = image.get(full_path, *args)
        
        for log in logs:
            log['path'] = "%s/%s" % (self._source['_id'], rel_path)
            self._log.append(log)
        
        if not doc:
            return
        
        if 'original_info' in doc:
            del doc['original_info']
        doc['_id'] = "img-%s" % uuid.uuid4().hex
        doc[IMAGE_TYPE] = True
        
        idents = doc.setdefault('identifiers', {})
        idents['path'] = {'source':couch.make_ref(self._source), 'name':rel_path}
        with open(full_path, 'rb') as f:
            md5 = hashlib.md5()
            sha1 = hashlib.sha1()
            while True:
                buff = f.read(524288)
                if not buff:
                    break
                md5.update(buff)
                sha1.update(buff)
        idents['md5'] = md5.hexdigest()
        idents['sha1'] = sha1.hexdigest()
        
        return doc
    
    def __init__(self, db_url, source_id, folder):
        self._db = couch.Database(db_url)
        self._source = self._db.read(source_id)
        self._DDOC = '_design/shutterstem'
        
        self._cancelled = False
        self._done = False
        self._files = Queue()
        self._recent_image_docs = deque()
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
                    rel_path = full_path.split(os.path.join(folder,''), 1)[1]
                    identifiers = {'path':{'source':{'_id':source_id}, 'name':rel_path}}
                    if not self._find_image(identifiers):
                        self._files.put(rel_path)
                if self._cancelled:
                    break
            self._files.put(None)
        
        def get_file_docs():
            while not self._cancelled:
                rel_path = self._files.get()
                if not rel_path:
                    break
                doc = self._image_doc(folder, rel_path)
                if not doc:
                    continue
                
                new_identifiers = image.copy_doc(doc['identifiers'])
                del new_identifiers['path']
                if self._find_image(new_identifiers):
                    continue
                
                while not self._cancelled:
                    try:
                        self._image_docs.put(doc, True, 0.5)
                    except QueueFull:
                        pass
                    else:
                        break
                
                doc = image.copy_doc(doc)
                if 'thumbnail/512.jpg' in doc.get('_attachments', {}):
                    del doc['_attachments']['thumbnail/512.jpg']
                if len(self._recent_image_docs) == 10:  # keep this list small (like maxlen in py2.6)
                        self._recent_image_docs.pop()
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
        
        safe_name = self._source['_id'].encode('ascii', 'replace')      # thread names must be ASCII-only
        self._find_files = Thread(target=find_new_files, name="Find new files (%s)" % safe_name)
        self._find_files.daemon = True
        self._find_files.start()
        self._get_file_docs = Thread(target=get_file_docs, name="Prepare image documents (%s)" % safe_name)
        self._get_file_docs.daemon = True
        self._get_file_docs.start()
        self._upload_docs = Thread(target=upload_docs, name="Upload image documents (%s)" % safe_name)
        self._upload_docs.daemon = True
        self._delete_docs = Thread(target=delete_docs, name="Remove documents from cancelled import (%s)" % safe_name)
    
    def begin(self):
        if self._cancelled or self._done or self._upload_docs.isAlive():
            return
        else:
            self._upload_docs.start()
    
    def cancel(self, remove=True):
        self._cancelled = True
        
        if self._upload_docs.isAlive():
            self._image_docs.put(None)
        else:
            self._imported_refs.put(None)
        
        if remove:
            self._delete_docs.start()
    
    def _is_active(self):
        return any(t.isAlive() for t in (self._find_files, self._get_file_docs, self._upload_docs, self._delete_docs))
    
    def status(self, log_skip=0, log_limit=None, include_recent=False):
        log_start = log_skip
        log_stop = (log_start + log_limit) if log_limit is not None else None
        
        active = self._is_active()
        imported = self._imported_refs.qsize()
        remaining = self._files.qsize() + self._image_docs.qsize()
        
        if self._cancelled:
            verb = 'cancel'
            remaining = 0
        elif self._done:
            verb = 'done'
            imported -= 1
        elif self._upload_docs.isAlive():
            verb = 'import+scan' if self._find_files.isAlive() else 'import'
            remaining -= 1 if verb == 'import' else 0
        else:
            verb = 'wait+scan' if self._find_files.isAlive() else 'wait'
            remaining -= 1 if verb == 'wait' else 0
        
        return {
            'active': active,
            'imported': imported,
            'remaining': remaining,
            'verb': verb,
            'recent': list(self._recent_image_docs) if include_recent else None,
            'log': list(self._log)[log_start:log_stop] if log_limit != 0 else None
        }
