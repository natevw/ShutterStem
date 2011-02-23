import os
import json
import subprocess

GET_IMAGE = os.path.dirname(os.path.abspath(__file__)) + '/getphoto-osx/build/Release/getphoto'


def get(full_path, *args):
    get_image = [GET_IMAGE, full_path]
    get_image.extend(map(str,args))
    p = subprocess.Popen(get_image, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, log = p.communicate()
    
    doc = None
    messages = []
    for line in log.split("\n"):
        if not line:
            continue
        try:
            info = json.loads(line)
        except ValueError:
            info = {'error':True, 'fallback_message':"Failed to parse utility log: '%s'" % line}
        messages.append(info)
    if not p.returncode:
        try:
            doc = json.loads(out)
        except ValueError:
            messages.append({'error':True, 'message':"Failed to parse output document: '%s'" % out})
    return doc, messages
