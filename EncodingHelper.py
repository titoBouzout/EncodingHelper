# coding=utf8
import sublime, sublime_plugin
import codecs
import sys
import os
# sys.path.append(os.path.join(sublime.packages_path(), 'EncodingHelper', 'chardet'))
from chardet.universaldetector import UniversalDetector
import re
import threading
import time

# don't parse binary files, just mark these as binary
				 						#IMAGES-------------------------------------#sublime---------------#fonts-----------#compressed----------------#audio-video--------------------------------------------------#docs------------------------------#misc
BINARY = re.compile('\.(apng|png|jpg|gif|jpeg|bmp|psd|ai|cdr|ico|cache|sublime-package|eot|svgz|ttf|woff|zip|tar|gz|rar|bz2|jar|xpi|mov|mpeg|avi|mpg|flv|wmv|mp3|wav|aif|aiff|snd|wma|asf|asx|pcm|pdf|doc|docx|xls|xlsx|ppt|pptx|rtf|sqlite|sqlitedb|fla|swf|exe)$', re.I);

SETTINGS = sublime.load_settings('EncodingHelper.sublime-settings')

class EncodingOnStatusBarListener(sublime_plugin.EventListener):

	def on_load(self, v, ok = True):

		if not v:
			return
		if v.encoding() == 'Undefined' and ok:
			# give time to sublime just one time
			sublime.set_timeout(lambda:self.on_load(v, False), 120)
			return
		elif v.encoding() == 'Undefined' and not ok:
			v.settings().set('encoding_helper_encoding_sublime', 'UTF-8')

		# if enabled, show encoding on status bar
		if bool(SETTINGS.get('show_encoding_on_status_bar', True)):

			# mark as loading
			v.settings().set('encoding_helper_loading', True)

			if not v.settings().has('encoding_helper_encoding_sublime'):
				v.settings().set('encoding_helper_encoding_sublime', v.encoding())

			#has cached state?
			if v.settings().has('encoding_helper_encoding'):
				v.settings().erase('encoding_helper_loading')
				encoding = v.settings().get('encoding_helper_encoding')
				encoding_sublime = v.settings().get('encoding_helper_encoding_sublime')
				v.set_status('encoding_helper_statusbar', encoding)
				if encoding_sublime != '' and encoding_sublime != encoding and encoding != 'BINARY' and encoding != 'Unknown':
					v.set_status('encoding_helper_statusbar_convertion_status', 'Opened as '+encoding_sublime+' (document maybe broken)')
			else:
				# is the file is there
				file_name = v.file_name()
				if not file_name or file_name == '' or os.path.isfile(file_name) == False:
					v.settings().erase('encoding_helper_loading')
					v.set_status('encoding_helper_statusbar', '');
				#guess
				else:
					v.set_status('encoding_helper_statusbar', '');
					#print 'GuessEncoding'
					GuessEncoding(file_name, SETTINGS.get('fallback_encodings'), v).start()
		else:
			v.erase_status('encoding_helper_statusbar')

	def on_activated(self, v):
		if bool(SETTINGS.get('show_encoding_on_status_bar', True)):
			if v.settings().has('encoding_helper_loading'):
				pass
			else:
				if not v.is_loading():
					self.on_load(v)
		else:
			v.erase_status('encoding_helper_statusbar')

SETTINGS.add_on_change('reload', lambda: EncodingOnStatusBarListener().on_load(sublime.active_window().active_view()))

class GuessEncoding(threading.Thread):

	def __init__(self, file_name, fallback_encodings = [], v = False,  callback = False):
		threading.Thread.__init__(self)
		self.file_name = file_name

		encoding_list = []
		for encoding in fallback_encodings:
			if encoding != 'ISO88591' and  encoding != 'iso88591' and encoding != 'iso-8859-1' and encoding != 'ISO-8859-1':
				encoding_list.append(encoding)
		self.fallback_encodings = encoding_list

		self.v = v
		if callback == False:
			self.callback = self.on_done
		else:
			self.callback = callback

	def run(self):
		confidence = 0
		size = os.stat(self.file_name).st_size
		if BINARY.search(self.file_name):
			encoding = 'BINARY'
			confidence = 1
		elif size > 1048576 and maybe_binary(self.file_name):
			encoding = 'BINARY'
			confidence = 0.7
		elif size > 1048576: # skip files > 1Mb
			encoding = 'Unknown'
			confidence = 1
		else:
			started_at  = time.time()
			timeout = False

			detector = UniversalDetector()
			fp = open(self.file_name, 'rb')
			line = fp.readline(500)
			while line != '':
				detector.feed(line)
				if time.time() - started_at > 8:
					timeout = True
					break
				line = fp.readline(8000)
			fp.close()
			detector.close()
			if timeout == False or (timeout == True and detector.done):
				encoding = str(detector.result['encoding']).upper()
				confidence = detector.result['confidence']
			else:
				encoding = 'Unknown'
				confidence = 1

			if encoding == 'ASCII':
				encoding = 'UTF-8'
			elif encoding == None or encoding == 'NONE' or encoding == '' or encoding == 'Unknown' or confidence < 0.7:
				if encoding == 'ISO-8859-2' and confidence > 0.69:
					workaround = self.test_fallback_encodings(['UTF-8', 'ISO-8859-1'])
					if workaround != False:
						encoding = workaround
					else:
						encoding = 'Unknown'
				elif encoding != 'ISO-8859-2' and confidence > 0.49:
					if encoding == 'WINDOWS-1252':
						encoding = 'ISO-8859-1'
				else:
					fallback = self.test_fallback_encodings()
					if fallback == False:
						encoding = 'Unknown'
					else:
						encoding = fallback

			# workarounds here
			if encoding == 'ISO-8859-2' or encoding == 'MACCYRILLIC':
				workaround = self.test_fallback_encodings(['UTF-8', 'ISO-8859-1'])
				if workaround != False:
					encoding = workaround

			del detector
		sublime.set_timeout(lambda:self.callback(encoding, confidence), 0)

	def test_fallback_encodings(self, encodings = False):
		if encodings == False:
			encodings = self.fallback_encodings
		for encoding in encodings:
			_encoding = translateCodec(encoding.lower())
			try:
				fp = codecs.open(self.file_name, "rb", _encoding, errors='strict')
				line = fp.readline(500)
				while line != '':
					line = fp.readline(8000)
				fp.close()
				return encoding
			except UnicodeDecodeError:
				fp.close()
		return False

	def on_done(self, encoding, confidence):
		if self.v:
			self.v.settings().set('encoding_helper_encoding', encoding)
			self.v.settings().set('encoding_helper_confidence', confidence)
			self.v.set_status('encoding_helper_statusbar', encoding)

			if not self.v.settings().has('encoding_helper_encoding_sublime'):
				self.v.settings().set('encoding_helper_encoding_sublime', self.v.encoding())
			encoding_sublime = self.v.settings().get('encoding_helper_encoding_sublime')

			if encoding in SETTINGS.get('open_automatically_as_utf8', []) and self.v.is_dirty() == False:
				ConvertToUTF8(self.file_name, encoding, self.v).start()
			else:
				if encoding_sublime != '' and encoding_sublime != encoding and encoding != 'BINARY' and encoding != 'Unknown':
					self.v.set_status('encoding_helper_statusbar_convertion_status', 'Opened as '+encoding_sublime+' (document maybe broken)')
			self.v.settings().erase('encoding_helper_loading')

class Toutf8fromBestGuessCommand(sublime_plugin.WindowCommand):

	def run(self):
		encoding = sublime.active_window().active_view().settings().get('encoding_helper_encoding')
		if encoding != None and encoding != 'UTF-8' and encoding != 'BINARY' and encoding != 'Unknown' and encoding != '':
			Toutf8fromCommand(sublime_plugin.WindowCommand).run(encoding)

	def description(self):
		try:
			encoding = sublime.active_window().active_view().settings().get('encoding_helper_encoding')
			if encoding != None and encoding != 'UTF-8' and encoding != 'BINARY' and encoding != 'Unknown' and encoding != '':
				return 'Convert to UTF-8 From '+encoding
			else:
				return 'Convert to UTF-8 From Best Guess'
		except:
			return 'Convert to UTF-8 From Best Guess'

	def is_enabled(self):
		try:
			encoding = sublime.active_window().active_view().settings().get('encoding_helper_encoding')
			if encoding != None and encoding != 'UTF-8' and encoding != 'BINARY' and encoding != 'Unknown' and encoding != '':
				return True
		except:
			return False

class Toutf8fromCommand(sublime_plugin.WindowCommand):

	def run(self, encoding = ''):
		try:
			if encoding == None or encoding == 'UTF-8' or encoding == 'BINARY' or encoding == 'Unknown' or encoding == '':
				return False
			v = sublime.active_window().active_view()
			file_name = v.file_name()
			if not file_name or file_name == '' or os.path.isfile(file_name) == False:
				return False
			else:
				ConvertToUTF8(file_name, encoding, v).start()
				return True
		except:
			return False

	def is_enabled(self, encoding = ''):
		try:
			file_name = sublime.active_window().active_view().file_name()
			if not file_name or file_name == '' or os.path.isfile(file_name) == False:
				return False
			else:
				return True
		except:
			return False

class ConvertToUTF8(threading.Thread):

	def __init__(self, file_name, encoding, v = False,  callback = False):
		threading.Thread.__init__(self)
		self.file_name = file_name

		self.encoding = encoding
		self.v = v
		if callback == False:
			self.callback = self.on_done
		else:
			self.callback = callback

	def run(self):
		_encoding = translateCodec(self.encoding.lower())
		try:
			content = codecs.open(self.file_name, "rb", _encoding, errors='strict').read()
			if len(content) != 0:
				sublime.set_timeout(lambda:self.callback(content, self.encoding), 0)
		except UnicodeDecodeError, e:
			print e
			sublime.set_timeout(lambda:self.on_error(self.file_name, self.encoding), 0)
		except LookupError, e:
			print e
			sublime.set_timeout(lambda:self.on_lookup_error(self.file_name, self.encoding), 0)

	def on_done(self, content, encoding):
		if self.v:
			edit = self.v.begin_edit()
			self.v.replace(edit, sublime.Region(0, self.v.size()), content);
			self.v.end_edit(edit)
			self.v.settings().set('encoding_helper_encoding_sublime', 'UTF-8')
			self.v.settings().set('encoding_helper_encoding',  'UTF-8')
			if bool(SETTINGS.get('show_encoding_on_status_bar', True)):
				self.v.set_status('encoding_helper_statusbar', 'UTF-8')
			self.v.set_status('encoding_helper_statusbar_convertion_status', 'Converted to UTF-8 from '+encoding)

	def on_error(self, file_name, encoding):
		sublime.error_message('Unable to convert to UTF-8 from encoding "'+encoding+'" the file: \n'+file_name);

	def on_lookup_error(self, file_name, encoding):
		sublime.error_message('The encoding "'+encoding+'" is unknown in this system.\n Unable to convert to UTF-8 the file: \n'+file_name);

def maybe_binary(file_name):
	fp = open(file_name, 'rb')
	line = fp.readline(500)
	read = 500
	while line != '':
		if '\0' in line:
			fp.close()
			return True
		read += 8000
		if read > 1048576:
			fp.close()
			return False
		line = fp.readline(8000)
	fp.close()
	return False

# should map different codecs to what codec.open except to receive
def translateCodec(encoding):
		return str(encoding)
