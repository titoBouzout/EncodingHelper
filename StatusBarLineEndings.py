import sublime, sublime_plugin

s = sublime.load_settings('EncodingHelper.sublime-settings')

class StatusBarLineEndings(sublime_plugin.EventListener):

	def on_load(self, v):
		if s.get('show_line_ending_on_status_bar'):
			self.show(v)
		
	def on_post_save(self, v):
		if s.get('show_line_ending_on_status_bar'):
			self.show(v)

	def show(self, v):
		v.set_status('statusbar_line_endings',  v.line_endings());

		