#! /usr/bin/env python

import socket
import sys
import re
import urllib2
import urllib
import base64
import threading

icecast_host = "127.0.0.1"
icecast_port = 8000
icecast_mount = "mystream"

shoutcast_host = "127.0.0.1"
shoutcast_port = 8001
shoutcast_password = ""
shoutcast_admin_password = ""

# Updates metadata in a separate thread as to not interrupt the data transfers
class ASyncMetaUpdater(threading.Thread):
	def __init__(self, text):
		threading.Thread.__init__(self)
		self.text = text
		self.start()
	def run(self):
		try:
			req = urllib2.Request("http://%s:%s/admin.cgi?mode=updinfo&%s" % (shoutcast_host, shoutcast_port, urllib.urlencode({"song":self.text}).replace("+", "%20")))
			httpAuth = base64.encodestring('%s:%s' % ("admin",shoutcast_admin_password))[:-1]
			req.add_header("Authorization", "Basic %s" % httpAuth)
			handle = urllib2.urlopen(req)
			content = handle.read()
		except:
			# Weird? Yep
			print "Updated meta"

# How often icecast sends metadata - automatically detected
icecast_meta_interval = 0

headers = ""

# Connect to icecast 
try:
	sIce = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	sIce.connect((icecast_host, icecast_port))
	
	# Get our stream                            V- this is important.
	sIce.send("GET /%s HTTP/1.0\r\nIcy-MetaData:1\r\nUser-Agent:ice2shout.py/1.1\r\n\r\n" % icecast_mount)
	headers = sIce.recv(8000);
	
	if not "200 OK" in headers:
		print "Error connecting to icecast server stream at: http://%s:%s/%s" % (icecast_host, icecast_port, icecast_mount)
		sys.exit(0)
except:
	print "Error connecting to icecast server stream at: http://%s:%s/%s" % (icecast_host, icecast_port, icecast_mount)
	if headers!="":
		print headers
	sys.exit(0)

try:
	streamName = re.compile(r'icy-name:([^\r]+)').findall(headers)[0]
	streamDescription = re.compile(r'icy-description:([^\r]+)').findall(headers)[0]
	streamGenre = re.compile(r'icy-genre:([^\r]+)').findall(headers)[0]
	streamUrl = re.compile(r'icy-url:([^\r]+)').findall(headers)[0]
	streamBitrate= re.compile(r'icy-br:([^\r]+)').findall(headers)[0]
except:
	print "Error matching Icecast stream info"
	sys.exit(0)

intPatten = re.compile('icy-metaint:([0-9]+)\r\n')
icecastIntervalMatch = intPatten.findall(headers)

if len(icecastIntervalMatch)==0:
	print "Error matching metadata interval"
	print headers
	sys.exit(0)
	
icecast_meta_interval =  int(icecastIntervalMatch[0])

# Connect to Shoutcast
sShout = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sShout.connect((shoutcast_host, shoutcast_port))

# Send the password
sShout.send("%s" % shoutcast_password)
sShout.send("\r\n")

# Usually just OK or OK2
headers = sShout.recv(8000);

if not "OK" in headers:
	print "Error connecting to shoutcast"
	print headers
	sys.exit(0)

# Initialize our stream
contentString = "content-type:%s\r\nicy-name:%s\r\nicy-genre:%s\r\nicy-url:%s\r\nicy-pub:%s\r\nicy-irc:%s\r\nicy-icq:%s\r\nicy-aim:%s\r\nicy-br:%s\r\n\r\n" % (
	"audio/mpeg",
	streamName,
	streamGenre,
	streamUrl,
	"1", # pub
	"",  # irc
	"",  # icq
	"",  # AIM
	streamBitrate
)
sShout.send(contentString)

dataSent = 0
datachunk = icecast_meta_interval

while True:
	lenDownload = datachunk
	if lenDownload>1024:
		lenDownload=1024
	data = sIce.recv(lenDownload)
	if len(data)==0:
		break
	datachunk -= len(data)
	
	if datachunk == 0:
		datachunk=icecast_meta_interval
		metaLength = ord(sIce.recv(1))*16
		if metaLength > 0:
			meta = sIce.recv(metaLength)
			meta=meta[13:]
			meta=meta[0:meta.find("';")]
			print meta
			ASyncMetaUpdater(meta)
	sShout.send(data);
	
	dataSent += len(data)
	if dataSent % 1024 == 0:
		print "TX: %s KB" % str(dataSent/1024)
