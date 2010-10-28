Svenweb is a web environment for editing and publishing versioned documents.

It uses a Subversion repository as its database and works against a checkout.
Alternative backends may be supported one day.

To configure it, edit the paste.ini configuration:

 [app:svenweb]
 ...
 svenweb.checkout_dir = /path/to_your/svn/checkout/

The checkout must already exist; svenweb won't create it for you. 

Then you can run it with `paster serve paste.ini`


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

Templates
---------

The templates are Tempita templates. They are minimal by design. You can fork
them; just change the value of `svenweb.templates_dir` in the `paste.ini` file.


What's next
===========

A little speculative roadmap:

0.1: This version.

0.2: Support for bazaar backend.

0.3: Copying, moving and deleting files. Some refactoring of WSGI components.

0.4: Using REMOTE_USER to determine the username to commit with, or something
     like that. More refactoring of WSGI components.

0.5: RSS or atom feeds. Diffs between arbitrary revisions. More refactoring.


