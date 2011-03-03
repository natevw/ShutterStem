#! /usr/bin/python
from __future__ import with_statement   # needed under Python 2.5 (Leopard default)


import couch
import image

import os
import urllib
import base64

from threading import Thread
from Queue import Queue, Full as QueueFull
from collections import deque


class Exporter(object):
    def __init__(self, images_GET, db_url, image_ids, folder, size=None):
        self._cancelled = False
        self._log = deque()
        self._written = Queue()
        self._total_count = len(image_ids)
        # NOTE: export and failure are shared by cancel thread, may become one off
        self._export_count = 0
        self._failure_count = 0
        self._removed_count = 0
        
        
        def export():
            if not os.path.exists(folder):
                os.mkdir(folder)
            
            for id in image_ids:
                if self._cancelled:
                    break
                
                request = {'database_url':db_url}
                request['query'] = {'size':str(size), 'export':'jpeg'} if size else {}
                response = images_GET(request, [id])
                if response.get('code', 200) != 200:
                    self._failure_count += 1
                    self._log.append({'id':id, 'ok':False, 'msg':"Export failed: %(json)s [%(code)u]." % response})
                    continue
                
                name = response['headers']['Content-Disposition'].replace("attachment; filename=", '')
                image_path = os.path.join(folder, name)
                if os.path.exists(image_path):
                    self._failure_count += 1
                    self._log.append({'id':id, 'ok':False, 'msg':"File named %s already exists." % name})
                    continue
                
                if self._cancelled:
                    break
                
                # TODO: this could blow away just-created file, not sure how to avoid race w/Python std libraries
                try:
                    with open(image_path, 'wb') as f:
                        data = base64.decodestring(response['base64'])
                        f.write(data)
                except Exception, e:
                    self._failure_count += 1
                    self._log.append({'id':id, 'ok':False, 'msg':"Failed to save %s: %s" % (name, e)})
                else:
                    self._export_count += 1
                    self._written.put(image_path)
                    self._log.append({'id':id, 'ok':True, 'msg':"Exported as %s." % name})
            self._written.put(None)
        
        def unexport():
            while True:
                path = self._written.get()
                if not path:
                    break
                try:
                    os.remove(path)
                except Exception, e:
                    self._failure_count += 1
                    self._log.append({'id':id, 'ok':False, 'msg':"Failed to remove %s: %s" % (os.path.basename(path), e)})
                else:
                    self._export_count -= 1
                    self._removed_count += 1
                    self._log.append({'id':id, 'ok':True, 'msg':"Removed %s." % os.path.basename(path)})
        
        self._export = Thread(target=export, name="Export to %s" % folder)
        self._export.daemon = True
        self._export.start()
        self._unexport = Thread(target=unexport, name="Remove exported files from %s" % folder)
    
    def cancel(self, remove=True):
        self._cancelled = True
        if remove:
            self._unexport.start()
    
    def status(self, log_skip=0, log_limit=None):
        log_start = log_skip
        log_stop = (log_start + log_limit) if log_limit is not None else None
        
        alive = self._export.isAlive() or (self._cancelled and self._unexport.isAlive())
        return {
            'done': not alive,
            'cancelled': self._cancelled,
            'exported': self._export_count,
            'removed': self._removed_count,
            'failed': self._failure_count,
            'total': self._total_count,
            'log': list(self._log)[log_start:log_stop] if log_limit != 0 else None
        }
