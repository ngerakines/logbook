# LogBook

LogBook is a personal journal and record keeping tool. When you complete a notable
task or have an interaction that you want to record, simply type in a brief message
describing it. You can annotate the record with tags and users for grouping and
retrieval. This is my personal replacement for the 37 Signals Backpack feature
"Journal".

# Requirements

* python (tested on 2.6)
* pyparsing
* dateutils
* sqlite3
* tornado

# TODO

* Add duration support in the form of hours:minutes.
* Allow attachment blobs to be added to records.
* Create search handler to display all records by date, tag or user.
