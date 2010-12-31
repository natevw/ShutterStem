ShutterStem is trying to make taking photos fun again.

# Core concepts #

ShutterStem provides an extendable, syncable and scalable photo library build on top of CouchDB. The design of ShutterStem is influenced by the following principles:

0. Photo metadata is coupled to the purpose of taking photos.
(Buzzword: meta)

If photos aren't organized, they're really hard to enjoy. By enabling "information about photos" to be better curated,
ShutterStem will enable photos to be better enjoyed.


1. Photo metadata is decoupled from the original files.
(Buzzword: a database)

ShutterStem prefers to treat the original file as a unmodifiable negative. There are many reasons for this:
- not corrupting original files is hard, and we want photo organization utilities to be easy to build
- it is hard to interchange arbitrary new types of metadata via many image formats (XMP doesn't seem well supported)
- modifying original photo files can mean needing to backup a >5MB file again, because <5kB of data changed
- decoupling the concept of a photo and its metadata from the original file reduces bulk and adds flexibility

Many -- after being burned repeatedly by closed, centralized legacy photo libraries -- insist
that their metadata stay with their original files, so that their curation is under their control.
If the other goals of ShutterStem are met, there are better means of accomplishing the same end.


2. Photo metadata is decoupled from any one application.
(Buzzword: an API)

While the ShutterStem project itself will provide a core set of photo management tools,
its underlying goal is to provide a platform upon which focused, innovative applications may be built.
So a viewer can just show photos well, a geotagger can just geotag well, and a web uploader can just web upload well.
ShutterStem wants to concentrate on being a great hub, so other apps can concentrate on being great spokes.

2b. Photo metadata is decoupled from any one application.
(Buzzword: schemaless...ish)

This also means that no one application limits what sort of metadata or organization scheme may be attached to a photo.
ShutterStem tries to define a useful core of common metadata so that apps may more efficiently collaborate, but is adamant
about also letting any young upstart photo utility mix in whatever additional metadata might be useful for its task.


3. Photo metadata is decoupled from any one computer.
(Buzzword: peer-to-peer replication)

Speaking of hubs, a mainframe sitting beneath a desk at home makes a pretty poor one when a photographer is at a friend's cabin.
ShutterStem must enable photo curation on any device (at least, any device not crippled by anti-competitive censorship),
syncable to any other device without coordination with one "master" library. In fact, ShutterStem should take
care of the syncing itself without placing undue burden on any other part of the system.


4. Photo metadata is decoupled from the "spinning wait cursor"
(Buzzword: scalable)

It's no fun to have a photo library full of great pictures that's completely unusable because it's full of great pictures.
ShutterStem should be able to gracefully handle any number of photos, and enable related applications to do the same.



# Questions one might ask #

Q. So how does ShutterStem manage to pull all of this off?
A. CouchDB pretty much just does it all for us and we just relax.

Q. CouchDB?
A. CouchDB: http://www.building43.com/videos/2010/08/19/a-powerful-replicable-mobilized-database-couchdb/

Q. So if CouchDB does all the work, then what doth ShutterStem?
A. CouchDB is "just" a beautifully architected web filesystem and server, ShutterStem is a standardish way of using CouchDB to manage photos and provides the necessary app-specific infrastructure on top of CouchDB's foundation.

Q. Does ShutterStem require CouchDB?
A. Yes, although in theory ShutterStem's components could be exported to other cultures (e.g. devices crippled by anti-competitive censorship)
