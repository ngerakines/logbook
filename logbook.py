import os
import sys
import random
import uuid
import time
import datetime

from dateutil.parser import *

import sqlite3

import tornado.httpserver
import tornado.ioloop
import tornado.web
import tornado.template

import logbook.parser
import git.op

import smtplib

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

evening = 0
morning = 1
afternoon = 2

LOGBOOK_PATH = os.environ.get('LOGBOOK_PATH', '/tmp/logbook.sqlite')

ARCHIVE_DAYS = 7

isNew = False
if os.path.exists(LOGBOOK_PATH) == False:
	isNew = True

conn = sqlite3.connect('/tmp/logbook.sqlite')

SENDGRID_USER = os.environ.get('SENDGRID_USER', 'logbook_account@sendgrid.com')
SENDGRID_PASS = os.environ.get('SENDGRID_PASS', '1234567890')
SENDGRID_TO = os.environ.get('SENDGRID_TO', 'nick+logbook@gerakines.net')
SENDGRID_FROM = os.environ.get('SENDGRID_FROM', 'nick+logbook@gerakines.net')

def saveEntry(entry):
	(message, (tags, users, task, length, when)) = entry
	entry_id = str(uuid.uuid4())
	t_seconds = time.mktime(when.timetuple())
	c = conn.cursor()
	c.execute("insert into entries values (?, ?, ?, ?)", (entry_id, t_seconds, message, 0, ))
	for tag in tags:
		c.execute("insert into tags values (?, ?)", (entry_id, tag, ))
		c.execute("insert into tags_reverse values (?, ?)", (tag, entry_id, ))
	for user in users:
		c.execute("insert into users values (?, ?)", (entry_id, user, ))
		c.execute("insert into users_reverse values (?, ?)", (user, entry_id, ))
	conn.commit()
	c.close()

if isNew:
	c = conn.cursor()
	c.execute('create table entries (id text, date INTEGER, message text, time real)')
	c.execute('create table tags (id text, tag text)')
	c.execute('create table tags_reverse (tag text, id text)')
	c.execute('create table users (id text, user text)')
	c.execute('create table users_reverse (user text, id text)')
	conn.commit()
	c.close()

class MainHandler(tornado.web.RequestHandler):
	def get(self):
		self.render('index.html')

	def post(self):
                git_url = self.get_argument("git_url", None)
                if git_url is not None:
                        filter_opt = self.get_argument("filter_opt")
                        filter_s = self.get_argument("filter_s", None)
                        # sanitize filter_opt
                        if filter_opt == "none": filter_opt = None

                        tmpd = git.op.clone(git_url)
                        commits = git.op.log(tmpd, filter_opt=filter_opt,
                                             filter_s=filter_s)
                        for commit in commits:
                                task = False
                                users = [commit[1]]
                                message = commit[3]
                                when = parse(commit[2], fuzzy=True)
                                tags = [word[1:] for word in message if word[0] == "#"]
                                # add commit hash as a tag
                                tags.append(commit[0])
                                # add name of the repo as a tag
                                # (assumes it is the basename of the path)
                                tags.append(os.path.basename(git_url).split('.git')[0])
                                time = False
                                saveEntry((message, (tags, users, task, time, when)))
                else:
                        message = self.get_argument("message")
                        extra = self.get_argument("extra", "")
                        (tags, users, task, time, when) = parseExtra(extra)
                        saveEntry((message, (tags, users, task, time, when)))
                self.redirect("/")

class ArchiveHandler(tornado.web.RequestHandler):
	def get_entries(self, days):
		c = conn.cursor()
		last_week = datetime.date.today() - datetime.timedelta(days = days)
		c.execute('select * from entries where date > ? order by date desc', (time.mktime(last_week.timetuple()), ))
		entries = []
		for (entry_id, when, message, length) in c.fetchall():
			when = datetime.datetime.fromtimestamp(when)

			last_entry = (None, None)
			if len(entries) > 0:
				last_entry = entries[-1]

			## 1600 to 400: evening
			## 400 to 1200: morning
			## 1200 to 1600: afternoon
			timeslot = evening
			if when.hour >= 4 and when.hour < 12:
				timeslot = morning
			elif when.hour >= 12 and when.hour < 16:
				timeslot = afternoon

			tags = c.execute('select * from tags where id = ?', (entry_id, )).fetchall()
			users = c.execute('select * from users where id = ?', (entry_id, )).fetchall()

			entry = ((entry_id, when, message, length), tags, users)
			if when.date() != last_entry[0] or timeslot != last_entry[1]:
				entry = (when.date(), timeslot, [entry])
				entries.append(entry)
			else:
				last_entry = entries.pop()
				last_entry[2].append(entry)
				entries.append(last_entry)
		return entries

	def get(self):
		entries = self.get_entries(7)
		self.render('archive.html', entries = entries, today = datetime.date.today(), days = ARCHIVE_DAYS)

        def post(self):
                days = int(self.get_argument("days", ARCHIVE_DAYS))
 		entries = self.get_entries(days)
 		self.render('archive.html', entries = entries, today = datetime.date.today(), days = days)

class EmailHandler(ArchiveHandler):
	def get(self):
		entries = self.get_entries(ARCHIVE_DAYS)

		loader = tornado.template.Loader("./")
		html_body = loader.load("archive.html").generate(entries = entries, today = datetime.date.today())

		msg = MIMEMultipart('alternative')
		msg['Subject'] = "Logbook archive generated on %s" % datetime.date.today()
		msg['From'] = SENDGRID_FROM
		msg['To'] = SENDGRID_TO

		msg.attach(MIMEText(html_body, 'html'))
		s = smtplib.SMTP('smtp.sendgrid.net')
		s.login(SENDGRID_USER, SENDGRID_PASS)
		s.sendmail(SENDGRID_FROM, SENDGRID_TO, msg.as_string())
		s.quit()

		self.render('archive.html', entries = entries, today = datetime.date.today(), days = ARCHIVE_DAYS)

def parseExtra(string):
	tags = []
	users = []
	task = False
	time = False
	when = datetime.datetime.now()

	parts = logbook.parser.Parser.parse(string)

	for part in parts:
		if part[0] == "#":
			tags.append(part[1:])
		elif part[0] == "@":
			users.append(part[1:])
		elif part[0] == "!":
			when = parse(part[1:], fuzzy = True)
		elif part == "task":
			task = True
		else:
			if part.find(":") != -1:
				(hour, sep, minute) = part.partition(":")
				time = (hour, minute)
	return (tags, users, task, time, when)

settings = {
	'static_path': os.path.join(os.path.dirname(__file__), 'static')
}

application = tornado.web.Application([
	(r'/', MainHandler),
	(r'/archive', ArchiveHandler),
	(r'/email', EmailHandler),
], **settings)

if __name__ == '__main__':
	port = 8000
	if len(sys.argv) > 1:
		port = int(sys.argv[1])
	http_server = tornado.httpserver.HTTPServer(application)
	http_server.listen(port)
	tornado.ioloop.IOLoop.instance().start()

