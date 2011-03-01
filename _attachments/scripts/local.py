#! /usr/bin/python
from __future__ import with_statement   # needed under Python 2.5 (Leopard default)


import couch
import image
from importer import Importer
from exporter import Exporter

from time import sleep
import os
import json
import base64
from cStringIO import StringIO

CONFIG = os.path.dirname(os.path.abspath(__file__)) + '/local.config.ini'

BAD_REQUEST = {'code':400, 'json':{'error':True, 'reason':"Bad request"}}

class LocalHelper(couch.External):
    def __init__(self):
        self.importers = {}
        self.exporters = {}
    
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
        try:
            _db_name, _this_external, action = req['path'][:3]
        except ValueError:
            return BAD_REQUEST
        action_subpath = req['path'][3:]
        req['database_url'] = "http://%s/%s" % (req['headers']['Host'], req['info']['db_name'])
        
        utility_path, csrf_token = req['query'].get('utility', None), req['query'].get('token', None)
        if utility_path and csrf_token:
            try:
                self.check_utility(utility_path, csrf_token)
            except Exception:
                sleep(2.5)    # slow down malicious local scanning
                return BAD_REQUEST
            else:
                folder, name = os.path.split(utility_path)
                req['utility'] = {'path':utility_path, 'token':csrf_token, 'folder':folder, 'name':name}
        elif req['method'] != 'GET':
            return BAD_REQUEST
        
        processor = getattr(self, 'process_%s_%s' % (action, req['method']), None)
        if processor:
            return processor(req, action_subpath)
        
        #return {'body': "<h1>Hello World!</h1>\n<pre>%s</pre>" % json.dumps(req, indent=4)}
        return BAD_REQUEST
    
    
    
    def process_status_GET(self, req, subpath):
        return {'code':200, 'json':{'status':'ok', 'database':req['database_url']}}
    
    
    def _get_original(self, image_path):
        try:
            with open(image_path, 'rb') as f:
                buffer = StringIO()
                base64.encode(f, buffer)
        except Exception:
            return {'code':500, 'json':{'error':True, 'reason':"Failed to get image"}}
        else:
            headers = {'Content-Type':"application/octet-stream"}
            return {'code':200, 'headers':headers, 'base64':buffer.getvalue()}
    
    def _get_jpeg(self, image_path, size, metadata=False):
        name = 'export' if metadata else 'thumbnail'
        doc, _ = image.get(image_path, '--%s' % name, size)
        if doc:
            img = doc.get('_attachments', {}).get('%s/%s.jpg' % (name, size))
            if img:
                headers = {'Content-Type':img['content_type']}
                return {'code':200, 'headers':headers, 'base64':img['data']}
        return {'code':500, 'json':{'error':True, 'reason':"Failed to get image"}}
    
    def process_images_GET(self, req, subpath):
        try:
            image_id = subpath[0]
        except IndexError:
            return BAD_REQUEST
        
        size = req['query'].get('size')
        if size and not size.isdigit():
            size = 'original_size'
        
        image_doc = couch.Database(req['database_url']).read(image_id)
        if not image_doc:
            return {'code':404, 'json':{'error':True, 'reason':"No such image"}}
        import_info = image_doc['identifiers']['relative_path']
        source_id = import_info['source']['_id']
        
        config = self.configfile
        found = False
        folders = config.setdefault('sources', {}).setdefault(source_id, {}).setdefault('folders', {})
        for folder, utility in folders.iteritems():
            # check that the utility (and folder!) is still valid and currently available
            try:
                self.check_utility(os.path.join(folder, utility['name']), utility['token'])
            except Exception:
                continue
            
            image_path = os.path.join(folder, import_info['path'])
            if os.path.exists(image_path):
                found = True
                filename = req['query'].get('as')
                if filename:
                    filename += os.path.splitext(image_path)[1].lower()
                else:
                    filename = os.path.basename(image_path)
                download = {'Content-Disposition': "attachment; filename=%s" % filename}
                
                if not size:
                    response = self._get_original(image_path)
                    response.setdefault('headers', {}).update(download)
                elif req['query'].get('export') == 'jpeg':
                    response = self._get_jpeg(image_path, size, True)
                    response.setdefault('headers', {}).update(download)
                else:
                    response = self._get_jpeg(image_path, size)
                
                if response.get('code', 200) == 200:
                    return response
        
        message = "No original image could be %s" % ('read' if found else 'found')
        return {'code':404, 'json':{'error':True, 'reason':message}}
    
    
    def process_import_GET(self, req, subpath):
        source_id = subpath[0]
        helper = self.importers.get(source_id, None)
        if helper:
            try:
                options = dict(
                    log_skip = int(req['query'].get('log_skip', 0)),
                    log_limit = int(req['query']['log_limit']) if 'log_limit' in req['query'] else None,
                    include_recent = req['query'].get('recent') == 'include',
                )
            except ValueError:
                return BAD_REQUEST
            return {'json':helper.status(**options)}
        else:
            return {'code':404, 'json':{'error':True, 'reason':"No import is in progress for '%s'" % source_id}}
    
    def process_import_POST(self, req, subpath):
        try:
            source_id, action = subpath[:2]
        except ValueError:
            return BAD_REQUEST
        helper = self.importers.get(source_id, None)
        if not helper and action != 'create':
            return {'code':404, 'json':{'error':True, 'reason':"No import is in progress for '%s'" % source_id}}
        elif action == 'create' and helper:
            status = helper.status(log_limit=0)
            status['message'] = "An import is already in progress for this source"
            return {'code':409, 'json':status}
        
        if action == 'create':
            self.importers[source_id] = Importer(req['database_url'], source_id, req['utility']['folder'])
            return {'code':201, 'json':{'ok':True, 'message':"Import created"}}
        elif action == 'begin':
            helper.begin()
            return {'code':202, 'json':{'ok':True, 'message':"Import will proceed"}}
        elif action == 'cancel':
            remove = False if req['query'].get('keep') == 'true' else True
            helper.cancel(remove=remove)
            if remove:
                return {'code':202, 'json':{'ok':True, 'message':"Import is cancelling, removing images"}}
            else:
                return {'code':200, 'json':{'ok':True, 'message':"Import is cancelling"}}
        elif action == 'finish':
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
    
    
    def process_export_GET(self, req, subpath):
        if subpath:
            helper = self.exporters.get(subpath[0], None)
            if helper:
                return {'json':helper.status()}
            else:
                return {'code':404, 'json':{'error':True, 'reason':"No such exporter"}}
        else:
            statii = {}
            for id, helper in self.exporters.iteritems():
                statii[id] = helper.status()
            return {'json':statii}
    
    def process_export_POST(self, req, subpath):
        try:
            action = subpath[0]
        except IndexError:
            return BAD_REQUEST
        
        if action == 'start':
            id = req['uuid']
            
            try:
                data = json.loads(req['body'])
            except Exception:
                return BAD_REQUEST
            
            try:
                image_ids, folder, size = data['images'], data['folder'], data['format']
            except KeyError:
                return BAD_REQUEST
            
            if size == 'original':
                size = None
            self.exporters[id] = Exporter(self.process_images_GET, req['database_url'], image_ids, folder, size)
            return {'code':201, 'json':{'ok':True, 'message':"Export begun", 'id':id}}
        else:
            try:
                id = subpath[1]
            except IndexError:
                return BAD_REQUEST
            
            try:
                helper = self.exporters[id]
            except KeyError:
                return {'code':404, 'json':{'error':True, 'reason':"No such exporter"}}
            
            if action == 'cancel':
                remove = False if req['query'].get('keep') == 'true' else True
                helper.cancel(remove=remove)
                if remove:
                    return {'code':202, 'json':{'ok':True, 'message':"Export is cancelling, removing images"}}
                else:
                    return {'code':200, 'json':{'ok':True, 'message':"Export cancelled"}}
            elif action == 'finish':
                del self.exporters[id]
                return {'code':200, 'json':{'ok':True, 'message':"Export finished"}}
            
        return BAD_REQUEST

if __name__ == "__main__":
    LocalHelper().run()

