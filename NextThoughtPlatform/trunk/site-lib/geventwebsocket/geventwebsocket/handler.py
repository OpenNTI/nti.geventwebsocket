#!/usr/bin/env python
import re
import struct
from hashlib import md5, sha1
import time

from gevent.pywsgi import WSGIHandler
import geventwebsocket as ws



class HandShakeError(ValueError):
	""" Hand shake challenge can't be parsed """
	pass


class WebSocketHandler(WSGIHandler):
	""" Automatically upgrades the connection to websockets. """
	def __init__(self, *args, **kwargs):
		self.websocket_connection = False
		self.allowed_paths = []

		for expression in kwargs.pop('allowed_paths', []):
			if isinstance(expression, basestring):
				self.allowed_paths.append(re.compile(expression))
			else:
				self.allowed_paths.append(expression)

		super(WebSocketHandler, self).__init__(*args, **kwargs)

	def handle_one_response(self, call_wsgi_app=True):
		"""
		If this is a websocket upgrade, places `wsgi.websocket` in the :attr:`environ` dict.

		:return: Result of calling the application if not a websocket Upgrade. Otherwise None.
		"""
		# In case the client doesn't want to initialize a WebSocket connection
		# we will proceed with the default PyWSGI functionality.
		if ('upgrade' not in self.environ.get("HTTP_CONNECTION",'').lower()
			or self.environ.get("HTTP_UPGRADE", '').lower() != "WebSocket".lower()
			or not self.accept_upgrade()):
			return super(WebSocketHandler, self).handle_one_response()

		self.time_start = time.time()
		self.websocket_connection = True
		self.headers_sent = False

		# Detect the Websocket protocol
		if 'HTTP_SEC_WEBSOCKET_VERSION' in self.environ:
			version = int(self.environ['HTTP_SEC_WEBSOCKET_VERSION'])
		elif "HTTP_SEC_WEBSOCKET_KEY1" in self.environ or 'HTTP_SEC_WEBSOCKET_KEY' in self.environ:
			version = 76
		else:
			version = 75

		self.websocket = ws.__dict__['WebSocket' + str(version)](self.socket, self.rfile, self.environ)
		self.environ['wsgi.websocket'] = self.websocket

		protocol = "ws://"
		if self.environ.get( 'HTTP_X_FORWARDED_PROTOCOL', None ) == 'ssl' or self.environ.get( 'SERVER_PORT' ) == 443:
			protocol = "wss://"

		if version in (7,8,13):
			sec_accept = self.environ['HTTP_SEC_WEBSOCKET_KEY'] + '258EAFA5-E914-47DA-95CA-C5AB0DC85B11'
			sec_accept = sha1( sec_accept ).digest().encode( 'base64' )
			sec_accept = sec_accept[0:-1] # base64 sticks an extra \n on there, which really screws us up
			headers = [
				("Upgrade", "WebSocket"),
				("Connection", "Upgrade"),
				("Sec-WebSocket-Accept", sec_accept) ]
			self.start_response( '101 Switching Protocols', headers )
		elif version == 75:
			headers = [
				("Upgrade", "WebSocket"),
				("Connection", "Upgrade"),
				("WebSocket-Origin", self.websocket.origin),
				("WebSocket-Protocol", self.websocket.protocol),
				("WebSocket-Location", protocol + self.environ.get('HTTP_HOST') + self.websocket.path),
			]
			self.start_response("101 Web Socket Protocol Handshake", headers)
		elif version == 76:
			challenge = self._get_challenge()
			headers = [
				("Upgrade", "WebSocket"),
				("Connection", "Upgrade"),
				("Sec-WebSocket-Origin", self.websocket.origin),
				("Sec-WebSocket-Protocol", self.websocket.protocol),
				("Sec-WebSocket-Location", protocol + self.environ.get('HTTP_HOST') + self.websocket.path),
			]

			self.start_response("101 Web Socket Protocol Handshake", headers)
			self.write(challenge)
		else:
			raise Exception("Version not supported: %s" % version)

		if call_wsgi_app:
			def start_response(status, headers, exc_info=None):
				if exc_info:
					try:
						raise exc_info[0], exc_info[1], exc_info[2]
					finally:
						# Avoid dangling circular ref
						exc_info = None
				self.code = int(status.split(' ', 1)[0])
				self.status = status
				self.response_headers = [('-'.join([x.capitalize() for x in key.split('-')]), value) for key, value in headers]
				self.response_headers_list = [x[0] for x in self.response_headers]
				return None
			try:
				self.application(self.environ, start_response)
			finally:
				self.time_finish = time.time()
				self.log_request()

		return

	def accept_upgrade(self):
		"""
		Returns True if request is allowed to be upgraded.
		If self.allowed_paths is non-empty, self.environ['PATH_INFO'] will
		be matched against each of the regular expressions.
		"""

		if getattr( self, 'allowed_paths', None ): # May be missing, we get swizzled to.
			path_info = self.environ.get('PATH_INFO', '')

			for regexps in self.allowed_paths:
				return regexps.match(path_info)

		return True

	def write(self, data):
		if self.websocket_connection:
			self.socket.sendall(data)
		else:
			super(WebSocketHandler, self).write(data)

	def start_response(self, status, headers, exc_info=None):
		if self.websocket_connection and not self.headers_sent:
			self.status = status

			towrite = []
			towrite.append('%s %s\r\n' % (self.request_version, self.status))

			for header in headers:
				towrite.append("%s: %s\r\n" % header)

			towrite.append("\r\n")
			msg = ''.join(towrite)
			self.socket.sendall(msg)
			self.headers_sent = True
			return self.write

		return super(WebSocketHandler, self).start_response(status, headers, exc_info)

	def _get_key_value(self, key_value):
		key_number = int(re.sub("\\D", "", key_value))
		spaces = re.subn(" ", "", key_value)[1]

		if key_number % spaces != 0:
			raise HandShakeError("key_number %d is not an intergral multiple of"
								 " spaces %d" % (key_number, spaces))

		return key_number / spaces

	def _get_challenge(self):
		key1 = self.environ.get('HTTP_SEC_WEBSOCKET_KEY1')
		key2 = self.environ.get('HTTP_SEC_WEBSOCKET_KEY2')

		if not (key1 and key2):
			message = "Client using old/invalid protocol implementation"
			headers = [("Content-Length", str(len(message))),]
			self.start_response("400 Bad Request", headers)
			self.write(message)
			self.close_connection = True
			return

		part1 = self._get_key_value(self.environ['HTTP_SEC_WEBSOCKET_KEY1'])
		part2 = self._get_key_value(self.environ['HTTP_SEC_WEBSOCKET_KEY2'])

		# This request should have 8 bytes of data in the body
		key3 = self.rfile.read(8)

		challenge = ""
		challenge += struct.pack("!I", part1)
		challenge += struct.pack("!I", part2)
		challenge += key3

		return md5(challenge).digest()

	def wait(self):
		return self.websocket.wait()

	def send(self, message):
		return self.websocket.send(message)
