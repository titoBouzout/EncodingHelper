Description
------------------

Encoding Helper is a [Sublime Text](http://www.sublimetext.com/ ) plug-in which provides the following features:

 * attempts to guess encoding of files
 * show encoding on status bar
 * show when the current document is maybe broken because was opened with an incorrect encoding
 * convert to UTF-8 from a variete of encodings organized in a menu.
 * convert to UTF-8 quickly from guessed encoding via menuitem
 * convert to UTF-8 automatically when opening a file via some defined encodings found on User preferences

You should know that attempt to guess the encoding of a file is hard and the results for some encodings is not 100% acurrated. Also, is a task that consume CPU, for this reason this plug-in includes a lot of optimizations.

<img src="http://dl.dropbox.com/u/9303546/SublimeText/EncodingHelper/screenshot.png" border="0"/>

Some more info
------------------

* I'm not an expert on encodings, don't talk to me as an expert. I just like a lot to build software compatible with every language using UTF-8
* python chardet library is a port of chardet by Mozilla http://www-archive.mozilla.org/projects/intl/chardet.html
* python chardet library is a 'Gone' project http://feedparser.org/
* By looking for the null character '\0' on files, means that every UTF16 file will be marked as binary ( same as in git source )
* When converting a file to UTF-8 from some other encoding, the plugin calls to codecs.open with the selected encoding as argument. See http://docs.python.org/library/codecs.html
* If you are going to report that some file is reported with an incorrect encoding, please upload the file as is to some reliable resource and provide detailed information. Please be informed that even doing this I'm unable to look into the low levels on why this is happening. This is just to collect data that maybe is informative to someone curious on this topic.
* Just for fun, It would be nice if someone can create a dataset of pure txt files with every char found in a complete list of character sets. This: http://www.mauvecloud.net/charsets/manual/index.html but with the files in this format: http://vancouver-webpages.com/multilingual/russian-koi.html ( without html, without imgs, just text )

Resources
------------------

chardet library:
http://pypi.python.org/pypi/chardet

dataset small:
http://vancouver-webpages.com/multilingual/
http://charsetplus.tripod.com/HTMLs/index.html

dataset huge:
http://www.mauvecloud.net/charsets/index.html

codecs:
http://docs.python.org/library/codecs.html

Installation
------------------

Install this repository via "Package Control" http://wbond.net/sublime_packages/package_control

Source-code
------------------

https://github.com/SublimeText/EncodingHelper

Forum Thread
------------------

http://www.sublimetext.com/forum/viewtopic.php?f=5&t=3453


License
------------------

See license.txt