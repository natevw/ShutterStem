ShutterStem is trying to make taking photos fun again. It is a CouchDB-based photo library that is extendable, syncable and scalable.

# Details #

(TODO: bit more of an overview, link to [philosophy document]())


# Installation #

## Pre-requisites ##
0. You'll need Mac OS X Snow Leopard*, Safari or Chrome**, and some basic nerd skills.
0b. You'll also need to be storing your photos in Finder-accessible folders on your hard drive.

## Part One ##
1. Get CouchDB running on your local machine: <http://www.couchone.com/get#mac>
2. Create a database called "photos" using CouchDB's web interface: <http://localhost:5984/_utils/>
3. Replicate the webapp from http://natevw.couchone.com/shutterstem to your local "photos" database: <http://localhost:5984/_utils/replicator.html>
4. Launch ShutterStem: <http://localhost:5984/photos/_design/shutterstem/index.html> (bookmark this!)

If all has gone well, you will see an empty photo library, with an "Import more..." link beckoning your mouse cursor.

## Part Two ##
*IMPORTANT*: this part has not yet been actually implemented. Follow the "setup local helper" instructions in <https://gist.github.com/849343> for now to get to step 4.
1. Click the "Import more..." link to pull up the ShutterStem dashboard: http://localhost:5984/photos/_design/shutterstem/dashboard.html
2. The dashboard will have you download some scripts that need to run on your local machine: http://localhost:5984/photos/_design/shutterstem/ShutterStem-Local.zip
3. Once you've downloaded the helper script package, unzip it and move the enclosed folder to "/Libary/Application Support/ShutterStem-Local"
4. Now if you hit Refresh, the ShutterStem dashboard should let you create a new "image source": <http://localhost:5984/photos/_design/shutterstem/dashboard.html>


## Usage ##

ShutterStem is mostly a web app, but it needs to deal with files in folders on your hard drive.
To simplify this interaction, ShutterStem has you save special HTML utility documents to folders you want to import from or export to.

An "image source" is a folder where you will often be importing photos from, and where ShutterStem can find original files via relative paths.
You should not move or rename files within an image source, but do your organizing using the ShutterStem database instead.
After you create an image source, you should save or download the utility document in the root of this image source folder.

For example, I copy photos straight off my memory card's into folders by camera:
~/Pictures/PowerShot A70
~/Pictures/PowerShot S60
~/Pictures/Rebel XT
~/Pictures/Rebel T1i (contains images grouped in the camera-created subfolders like 260CANON and 270CANON)

So I've created an image source and placed the corresponding import utility into each one of these folders.
When I want to import new images, I open this utility document and it connects to the ShutterStem helper scripts to manage the import into CouchDB.
Since the folder structure and image names on my hard drive are the same as on the memory cards, I can even save another utility to import directly off of them, e.g.:
"/Volumes/T1I_MEMCARD/DCIM/ShutterStem - Import Rebel T1i.html"


## Fine print ##

Questions? I'm @natevw on Twitter.

* Most of ShutterStem should port well to Ubuntu or older Macs or Amiga or whatever, if you've got some spare time to write a "getphoto" executable for your native platform.
** Most of ShutterStem already works in Firefox 3.5, if you've got some spare time to add -moz- versions of all the -webkit- CSS stuff.


# Architecture #

![Rough architecture diagram](http://natevw.couchone.com/shutterstem/_design/shutterstem/_attachments/architecture_sketch.gif)

ShutterStem organizes photo metadata and thumbnails in a CouchDB database for reliable, replicable storage.
An external plugin hosts import, export and access to originals. Import and export are controlled via
folder utilities that communicate with the external plugin through CouchDB's HTTP interface.

These folder utilities use an iframe and cross-window messaging to communicate the local folder path and user instructions to the backend. There backend can be divided roughly into three primary components, besides CouchDB itself:

1. The webapp and related indexes
CouchDB can not only host JSON documents and file attachments, but also provides some basic infrastructure for writing dynamic, yet scalable, server-side code. Programs built to work within this built-in application layer are know as [Couch apps](http://couchapp.org/page/index), and the basic ShutterStem organizer is written to be hosted directly out of the same CouchDB design document that specifies the related document indexes.

2. The local helper script suite (local.py, which uses image.py, importer.py, exporter.py and couch.py)
This is essentially a web server written in Python, which takes requests for things like "import this folder" or "what's the original for this image?" and
reads from the folders the image utilities are in to access files on the webapp's behalf.
It gets hooked into a URL within your main database as an [external process](http://wiki.apache.org/couchdb/ExternalProcesses) that
CouchDB starts up and uses kind of like a plugin.

3. "getphoto-osx"
This is the completely platform-specific part, which uses (in this case) the image libraries built into OS X to read metadata and pixels from your JPEG and RAW images.
It is designed to interact with the local helper script suite via a command line interface so that similar utilities could be written for other platforms or datasources.


# License #

Released under the MIT License:

Copyright 2010Ð2011 Nathan Vander Wilt.

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.