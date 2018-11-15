import os

import conf
from . import db_mongo
from . import fs


# ==== version ====

from collections import namedtuple
# version_info format: (MAJOR, MINOR, MICRO, RELEASE_LEVEL, SERIAL)
# inspired by Python's own sys.version_info, in order to be
# properly comparable using normal operarors, for example:
#  (6,1,0,'beta',0) < (6,1,0,'candidate',1) < (6,1,0,'candidate',2)
#  (6,1,0,'candidate',2) < (6,1,0,'final',0) < (6,1,2,'final',0)
# RELEASE_LEVELS = [ALPHA, BETA, RELEASE_CANDIDATE, FINAL] = ['alpha', 'beta', 'candidate', 'final']
Version = namedtuple('Version', ['major', 'minor', 'micro', 'releaselevel', 'serial'])
version = Version(0, 1, 0, 'alpha', 0)


# ==== init config ====

config = {}
config['MAX_FILE_SIZE'] = conf.MAX_FILE_SIZE
config['SERVER_NAME'] = conf.SERVER_NAME

if os.name == "posix":
	uname = os.uname()
	config['OS_NAME'] = uname.sysname + " " + uname.release + " " + uname.version
else:
	config['OS_NAME'] = os.name


# ==== functions ====

def sendAnswer(conn, status="200 OK", typ="text/plain; charset=utf-8", data=b"", maxage=0):
	conn.send(b"HTTP/1.1 " + status.encode("utf-8") + b"\r\n")
	s = "Server: " + config['SERVER_NAME'] +" (" + config['OS_NAME'] + ")\r\n"
	conn.send(s.encode("utf-8"))
	if maxage > 0:
		s = "Cache-Control: max-age=" + str(maxage) + ", must-revalidate\r\n"
		conn.send(s.encode("utf-8"))
	else:
		conn.send(b"Cache-Control: no-cache, no-store, must-revalidate\r\n")
	conn.send(b"Connection: close\r\n")
	conn.send(b"Content-Type: " + typ.encode("utf-8") + b"\r\n")
	s = "Content-Length: " + str(len(data)) + "\r\n"
	conn.send(s.encode("utf-8"))
	conn.send(b"Content-Language: en, ru\r\n")
	conn.send(b"\r\n") # after the empty string in HTTP data begins
	conn.send(data)


# fn - file name
def sendAnswerFile(conn, fn, typ="image/png"):
	try:
		if not os.path.exists(fn):
			sendAnswer(conn, "404 Not Found")
			return 404
		fSize = os.path.getsize(fn)
		if fSize > config['MAX_FILE_SIZE']:
			print("FileSize ",fSize," > MAX_FILE_SIZE: ",fn)
			s = "Requested file is too big "+str(fSize) +">"+str(config['MAX_FILE_SIZE'])
			sendAnswer(conn, data=s.encode('utf-8'))
			return 1
		r = 0
		file = open(fn, 'rb')
		try:
			sendAnswer(conn, "200 OK", typ, file.read(config['MAX_FILE_SIZE']), 3600)
		except Exception as e:
			r = 500
			sendAnswer(conn, "500 Internal Server Error")
			print(e)
		finally:
			file.close()
	except Exception as e:
		r = 500
		sendAnswer(conn, "500 Internal Server Error")
		print(e)
	return r


def log(s):
	print("[core]: " + s)