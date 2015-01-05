# coding=utf8
import sublime, sublime_plugin
import codecs
import os
from .chardet.universaldetector import UniversalDetector
import re
import threading
import time

# don't parse binary files, just mark these as binary
BINARY = re.compile('\.(apng|png|jpg|gif|jpeg|bmp|psd|ai|cdr|ico|cache|sublime-package|eot|svgz|ttf|woff|zip|tar|gz|rar|bz2|jar|xpi|mov|mpeg|avi|mpg|flv|wmv|mp3|wav|aif|aiff|snd|wma|asf|asx|pcm|pdf|doc|docx|xls|xlsx|ppt|pptx|rtf|sqlite|sqlitedb|fla|swf|exe)$', re.I);

s = {}
Pref = {}
EncodingOnStatusBarListener = {}
debug = False

def plugin_loaded():
	global s, Pref, EncodingOnStatusBarListener

	s = sublime.load_settings('Preferences.sublime-settings')
	if not s.get('show_encoding', False):
		s.set('show_encoding', True)
		sublime.save_settings("Preferences.sublime-settings")

	s = sublime.load_settings('EncodingHelper.sublime-settings')
	Pref = Pref()
	Pref.load();
	s.clear_on_change('reload')
	s.add_on_change('reload', lambda:Pref.load())

	if sublime.platform() in ('linux', 'osx'):
		import sys
		path = os.path.normpath(os.path.dirname(sublime.packages_path())+'/Packages/EncodingHelper/Codecs33-'+sublime.platform()+'-'+sublime.arch()+'/lib')
		if path not in sys.path:
			sys.path.append(path)

	EncodingOnStatusBarListener = EncodingOnStatusBarListener()
	EncodingOnStatusBarListener.init_();

class Pref:
	def load(self):
		import locale
		Pref.tmp_cache_fallback_encodings = {}
		Pref.fallback_encodings = []
		Pref.fallback_encodings.append("UTF-8")
		encoding_data_lang, encoding_data_encoding = locale.getdefaultlocale()
		if encoding_data_encoding:
			Pref.fallback_encodings.append(encoding_data_encoding.upper());
		for encoding in s.get('fallback_encodings', []):
			if encoding:
				Pref.fallback_encodings.append(encoding.upper())
		if not Pref.fallback_encodings or Pref.fallback_encodings == ["UTF-8"]:
			Pref.fallback_encodings = ["UTF-8", "ISO-8859-1"];
		Pref.open_automatically_as_utf8 = []
		for encoding in s.get('open_automatically_as_utf8', []):
			if encoding != '':
				Pref.open_automatically_as_utf8.append(encoding.upper())

		Pref.fallback_encodings = unique(Pref.fallback_encodings)
		Pref.open_automatically_as_utf8 = unique(Pref.open_automatically_as_utf8)

		if debug:
			print('Pref.fallback_encodings')
			print(Pref.fallback_encodings)
			print('Pref.open_automatically_as_utf8')
			print(Pref.open_automatically_as_utf8)

class EncodingOnStatusBarListener(sublime_plugin.EventListener):

	def init_(self):
		for window in  sublime.windows():
			self.on_load(window.active_view(), '__init__')

	# this function is called to update the statusbar
	# we need to know wich encoding ST is giving to the file in order to tell: "document maybe broken"
	# we compare the detected encoding of this package with the detected encoding by ST
	def on_encodings_detected(self, v):
		# we give time to ST to "detect" or use the "fallback encoding".
		if v.encoding() == 'Undefined' and v.is_loading():
			encoding_sublime = 'Loading…'
		elif v.encoding() == 'Undefined' and not v.is_loading():
			encoding_sublime = 'UTF-8'
		# ok, sublime was able to set some encoding to this file
		else:
			encoding_sublime = v.encoding()

		# here code, "document maybe broken"
		encoding_encohelp = v.settings().get('encoding_helper_encoding') or ''
		encoding_converted = v.settings().get('encoding_helper_converted') or ''

		if encoding_sublime == 'Hexadecimal' and encoding_encohelp == 'BINARY':
			encoding_encohelp = ''

		if encoding_encohelp == 'Detecting encoding…':
			v.set_status('encoding_helper_statusbar', 'Detecting encoding…')
		elif encoding_converted != None and encoding_converted:
			v.set_status('encoding_helper_statusbar', "Converted to UTF-8 from "+encoding_normalize_for_display(encoding_converted))
		elif encoding_sublime != 'Loading…' and encoding_encohelp != '' and encoding_encohelp != 'Unknown' and encoding_encohelp != 'Detecting encoding…' and encoding_normalize_for_comparation(encoding_sublime) != encoding_normalize_for_comparation(encoding_encohelp):
			v.set_status('encoding_helper_statusbar', 'Opened as '+encoding_normalize_for_display(encoding_sublime)+' detected '+encoding_normalize_for_display(encoding_encohelp)+' (document maybe broken)')
		elif encoding_sublime != 'Loading…' :
			v.set_status('encoding_helper_statusbar', encoding_normalize_for_display(encoding_sublime) if not 'UTF-8' else '')
		else:
			v.set_status('encoding_helper_statusbar', encoding_normalize_for_display(encoding_encohelp) if not 'UTF-8' else '')

	def on_post_save_async(self, v):
		settings = v.settings()
		if not settings.get('is_widget'):
			settings.erase('encoding_helper_converted')
			settings.erase('encoding_helper_encoding')
			settings.erase('encoding_thread_running')
			self.on_load(v, 'on_post_save_async');

	def on_activated(self, v):
		if not v.settings().get('is_widget'):
			self.on_load(v, 'on_activated');

	# try to guess the encoding
	def on_load(self, v, from_where = 'on_load'):
		if debug:
			print('on_load::'+from_where)

		# sublime may knows the encoding of the loaded file at on_load time

		if not v.settings().get('is_widget'):
			self.on_encodings_detected(v);

		if not v or v.settings().get('is_widget'):
			return

		#has cached state?
		if v.settings().has('encoding_helper_encoding'):
			self.on_encodings_detected(v);
		else:
			# if the file is not there, just give up
			file_name = v.file_name()
			if not file_name or file_name == '' or os.path.isfile(file_name) == False:
				v.settings().set('encoding_helper_encoding', '')
				self.on_encodings_detected(v);
			#guess
			else:
				if not v.settings().get('encoding_thread_running', False):
					v.settings().set('encoding_thread_running', True)
					v.set_status('encoding_helper_statusbar', 'Detecting encoding…');
					GuessEncoding(v).start()

	def on_guess_done(self, v, encoding):
		if v:
			if encoding == 'ASCII':
				encoding = 'UTF-8'
			v.settings().set('encoding_helper_encoding', encoding)
			self.on_encodings_detected(v);
			if encoding != '' and encoding != 'UTF-8' and encoding in Pref.open_automatically_as_utf8 and v.is_dirty() == False:
				v.set_status('encoding_helper_statusbar', 'Converting to '+encoding_normalize_for_display(encoding)+'…');
				ConvertToUTF8(v, v.file_name(), encoding).start()

class GuessEncoding(threading.Thread):

	def __init__(self, v):
		self.v = v
		self.file_name = v.file_name()
		threading.Thread.__init__(self)

	def run(self):
		begin = time.time()

		Pref.tmp_cache_fallback_encodings = {}

		file_name = self.file_name

		encoding = ''

		if BINARY.search(file_name):
			encoding = 'BINARY'
		else:
			size = os.stat(file_name).st_size
			maybe_binary_r = maybe_binary(file_name)
			if size > 1048576 and maybe_binary_r:
				encoding = 'BINARY'
			elif maybe_binary_r:
				encoding = 'BINARY'
			elif size > 1048576: # skip files > 1Mb
				encoding = 'Unknown'
			else:
				confidence = 1
				fallback = test_fallback_encodings(file_name)
				if fallback:
					encoding = fallback

				if not encoding:
					if debug:
						print('UniversalDetector::Start::'+str(time.time() - begin)+'::'+file_name)
					detector = UniversalDetector()
					fp = open(file_name, 'rb')
					detector.feed(fp.read(209715))
					fp.close()
					detector.close()
					if detector.done:
						encoding = str(detector.result['encoding']).upper()
						confidence = detector.result['confidence']
					else:
						encoding = 'Unknown'
					if debug:
						print('UniversalDetector::End::'+str(time.time() - begin)+'::'+file_name)
				if not encoding or encoding == 'NONE' or encoding == 'Unknown' or confidence < 0.7:
					fallback = test_fallback_encodings(file_name)
					if fallback:
						encoding = fallback

		Pref.tmp_cache_fallback_encodings = {}

		sublime.set_timeout(lambda:EncodingOnStatusBarListener.on_guess_done(self.v, encoding), 0)

class Toutf8fromBestGuessCommand(sublime_plugin.WindowCommand):

	def run(self):
		encoding = sublime.active_window().active_view().settings().get('encoding_helper_encoding')
		if encoding != None and encoding != 'UTF-8' and encoding != 'BINARY' and encoding != 'Unknown' and encoding != '' and encoding != 'Detecting encoding…':
			Toutf8fromCommand(sublime_plugin.WindowCommand).run(encoding)

	def description(self):
		try:
			encoding = sublime.active_window().active_view().settings().get('encoding_helper_encoding')
			if encoding != None and encoding != 'UTF-8' and encoding != 'BINARY' and encoding != 'Unknown' and encoding != '' and encoding != 'Detecting encoding…':
				return 'Convert to UTF-8 From '+encoding
			else:
				return 'Convert to UTF-8 From Best Guess'
		except:
			return 'Convert to UTF-8 From Best Guess'

	def is_enabled(self):
		try:
			encoding = sublime.active_window().active_view().settings().get('encoding_helper_encoding')
			if encoding != None and encoding != 'UTF-8' and encoding != 'BINARY' and encoding != 'Unknown' and encoding != '' and encoding != 'Detecting encoding…':
				return True
			else:
				return False
		except:
			return False

class Toutf8fromCommand(sublime_plugin.WindowCommand):

	def run(self, encoding = ''):
		try:
			if encoding == None or encoding == 'UTF-8' or encoding == 'BINARY' or encoding == 'Unknown' or encoding == '' or encoding == 'Detecting encoding…':
				return False
			v = sublime.active_window().active_view()
			file_name = v.file_name()
			if not file_name or file_name == '' or os.path.isfile(file_name) == False:
				return False
			else:
				ConvertToUTF8(v, file_name, encoding).start()
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

	def __init__(self, v, file_name, encoding, callback = False):

		threading.Thread.__init__(self)

		self.file_name = file_name
		self.encoding = encoding
		self.v = v
		self.content = ''
		if callback == False:
			self.callback = False
		else:
			self.callback = True
			self.callback_function = callback

	def run(self):
		_encoding = self.encoding.lower()
		try:
			__encoding = codecs.lookup(_encoding).name
		except:
			__encoding = _encoding;
		try:
			if debug:
				print('ConvertToUTF8::'+__encoding+'::'+self.file_name)
			self.content = open(self.file_name, "r", encoding=__encoding, errors='strict', newline=None).read()
			if len(self.content) != 0:
				if self.callback:
					sublime.set_timeout(lambda:self.callback_function(self.content, self.encoding), 0)
				else:
					sublime.set_timeout(lambda:self.on_done(self.encoding), 0)
		except LookupError:
			# osx, linux oddities
			import _multibytecodec, imp, encodings
			imp.reload(encodings)
			imp.reload(codecs)
			codecs.getencoder(self.encoding)
			try:
				if debug:
					print('ConvertToUTF8::'+__encoding+'::'+self.file_name)
				self.content = open(self.file_name, "r", encoding=__encoding, errors='strict', newline=None).read()
				if len(self.content) != 0:
					if self.callback:
						sublime.set_timeout(lambda:self.callback_function(self.content, self.encoding), 0)
					else:
						sublime.set_timeout(lambda:self.on_done(self.encoding), 0)
			except LookupError:
				sublime.set_timeout(lambda:self.on_lookup_error(self.file_name, self.encoding), 0)
			except:
				sublime.set_timeout(lambda:self.on_error(self.file_name, self.encoding), 0)
		except:
			sublime.set_timeout(lambda:self.on_error(self.file_name, self.encoding), 0)

	def on_done(self, encoding):
		if self.v:
			self.v.run_command('encoding_helper_write_to_view', {"content": self.content});
			self.v.settings().set('encoding_helper_converted', encoding)
			self.v.settings().set('encoding_helper_encoding', 'UTF-8')
			self.v.set_encoding('UTF-8');
			EncodingOnStatusBarListener.on_encodings_detected(self.v);

	def on_error(self, file_name, encoding):
		self.v.settings().set('encoding_helper_encoding', encoding)
		EncodingOnStatusBarListener.on_encodings_detected(self.v);
		sublime.error_message('Unable to convert to UTF-8 from encoding "'+encoding+'" the file: \n'+file_name);

	def on_lookup_error(self, file_name, encoding):
		self.v.settings().set('encoding_helper_encoding', encoding)
		EncodingOnStatusBarListener.on_encodings_detected(self.v);
		sublime.error_message('The encoding "'+encoding+'" is unknown in this system.\n Unable to convert to UTF-8 the file: \n'+file_name);

def maybe_binary(file_name):
	if debug:
		print('maybe_binary::'+file_name)
	fp = open(file_name, 'rb')
	line = fp.read(500);
	read = 500
	null_char = '\x00'.encode();
	while line != '':
		if null_char in line:
			fp.close()
			return True
		read += 8000
		if read > 1048576:
			fp.close()
			return False
		line = fp.read(8000)
	fp.close()
	return False

def test_fallback_encodings(file_name, encodings = False):
	if encodings == False:
		encodings = Pref.fallback_encodings
	for encoding in encodings:
		_encoding = encoding.lower()

		key = 'file_name_'+_encoding
		if key in Pref.tmp_cache_fallback_encodings:
			if not Pref.tmp_cache_fallback_encodings[key]:
				continue
			else:
				return Pref.tmp_cache_fallback_encodings[key]

		try:
			if debug:
				print('test_fallback_encodings::'+_encoding+'::'+file_name)
			fp = codecs.open(file_name, "rb", _encoding, errors='strict')
			fp.read();
			fp.close()
			Pref.tmp_cache_fallback_encodings[key] = encoding
			return encoding
		except UnicodeDecodeError:
			if debug:
				print('test_fallback_encodings_cached::'+_encoding+'::'+file_name)
			Pref.tmp_cache_fallback_encodings[key] = False
			fp.close()
	return False

class EncodingHelperWriteToViewCommand(sublime_plugin.TextCommand):
	def run(self, edit, content):
		view = self.view
		view.replace(edit, sublime.Region(0, view.size()), content);
		view.sel().clear()
		view.sel().add(sublime.Region(0))
		view.end_edit(edit)

def encoding_normalize_for_display(encoding):
	if '(' in encoding:
		encoding = encoding.split('(')[1]
	if encoding != 'Hexadecimal' and encoding != 'BINARY' and encoding[:3] != 'UTF':
		try:
			encoding = codecs.lookup(encoding).name;
		except:
			pass
	return encoding.lower().strip().replace(')', '').replace(' ', '-').replace('_', '-').strip().upper().replace('HEXADECIMAL', 'Hexadecimal').replace('-WITH-BOM', ' with BOM').replace('-LE', ' LE').replace('-BE', ' BE').replace('ISO', 'ISO-').replace('CP', 'CP-');

def encoding_normalize_for_comparation(encoding):
	if '(' in encoding:
		encoding = encoding.split('(')[1]
	if encoding != 'Hexadecimal' and encoding != 'BINARY' and encoding[:3] != 'UTF':
		try:
			encoding = codecs.lookup(encoding).name;
		except:
			pass
	return encoding.strip().upper().replace(' ', '-').replace('_', '-').replace('-WITH-BOM', '').replace('-LE', '').replace('-BE', '').replace(')', '').replace('-', '').replace('_', '').strip();

def unique(seq):
    seen = set()
    seen_add = seen.add
    return [ x for x in seq if not (x in seen or seen_add(x))]