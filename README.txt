Svenweb is a web environment for editing and publishing versioned documents.

It uses a version-controlled repository as its database and works against a
checkout. Currently supported backends are SVN and BZR. BZR is better.

Quickstart::

  virtualenv svenweb; cd svenweb; source bin/activate
  easy_install -e -b . svenweb
  easy_install bzr
  cd svenweb
  python setup.py develop
  bzr init /tmp/bzr
  paster serve paste.ini

The application will now be running on localhost:5052 
against a new BZR repository in /tmp/bzr.

Now navigate to a path to start editing a file there.


What it doesn't do
==================

Svenweb doesn't care about authentication. If you do, you should configure
this outside of svenweb or in an additional WSGI middleware layer.

Likewise svenweb doesn't respect authentication. Commits will all be made
by the system's default user. In a future version this will change to respect
environment variables.

Svenweb doesn't provide in-browser diffs between revisions. I'd like to add
this eventually.

Svenweb doesn't provide RSS for changes. It should.

Svenweb doesn't provide facilities for moving, copying or deleting files
through the web. Adding these will likely be my next priority.


Usage
=====

Svenweb uses a wiki-style workflow for adding new documents: just visit
the URL of the document you want to create. You'll find an edit form.

If you visit /baz/bar/foo/ then the directories /baz/ and /baz/bar/ will
be created and checked in to the repository if they do not yet exist.

Svenweb aggressively redirects redundant versions of all its views:

* If a document /foo was last changed in r5 and you visit /foo?version=8,
  you will be redirected to /foo?version=5.

* If /foo's last change was in r5 and you visit /foo you will be redirected
  to /foo?version=5.

This means that every URL with a ?version parameter can be cached forever
if you want.

Read
----

Visit a document's URL to view its latest version.

Append ?version=5 to view it as of r5.

Write
-----

Visit /foo?view=edit to edit the document stored at /foo.

You can edit the file, and also set a mimetype which will be used when 
serving the file.

You can also add a commit message. If you don't, the default commit message
is "foom."

Index
-----

You can view the contents of a directory by visiting the directory's URL.
Versions work here too; visiting directory /baz/bar/?version=5 will display
the contents of that directory as of r5.

History
-------

You can view a history (changelog) for any file or directory's URL by using
the querystring ?view=history.

For directories, this will display the history of changes within that directory,
including file additions and modifications in subdirectories.

You can use ?version=5 modifiers as well, to see a history of changes up through
the version specified.


Miscellany
==========

Tests
-----

There are the beginnings of a test suite in the ./ftests directory. These are
flunc tests, which run twill scripts over HTTP. You should `easy_install flunc`
if you want to run the tests.

To run them, start a svenweb server on localhost:5052 with
 svenweb.checkout_dir = /tmp/svnco/

Then run 
 ./run-flunc.sh 

It should work with both the SVN and BZR backends.


Templates
---------

The templates are Tempita templates. They are minimal by design. You can fork
them; just change the value of `svenweb.templates_dir` in the `paste.ini` file.


Using bazaar
------------

To use the BZR backend you should be running bzr 2.0 or so. This is for the "index"
view specifically i.e. for directory views. In 2.0 bzr makes it easier to find the
last changed revision of any file within a directory. 

See https://bugs.edge.launchpad.net/bzr/+bug/97715

Note that svenweb's current implementation of the index view WILL NOT WORK
with mod_wsgi because of a call to sys.stdout.flush() in bzrlib.commands
which is triggered by sven.bzr.log -- I really ought to fix this in sven.bzr
by implementing the `log` method more properly, somehow.
