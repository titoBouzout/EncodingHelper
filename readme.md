Description
------------------

Encoding Helper is a [Sublime Text](http://www.sublimetext.com/ ) plug-in which provides the following features:

 * attempts to guess encoding of files
 * show encoding on status bar
 * convert to UTF-8 from a variete of encodings organized in a menu.
 * convert to UTF-8 quickly from guessed encoding via menuitem
 * convert to UTF-8 automatically when opening a file via some defined encodings found on User preferences

You should know that attempt to guess the encoding of a file is hard and the results for some encodings is not 100% acurrated. Also, is a task that consume CPU, for this reason this plug-in includes a lot of optimizations.

<img src="http://dl.dropbox.com/u/9303546/SublimeText/EncodingHelper/screenshot.png" border="0"/>

How it works
------------------

When "show_encoding_on_status_bar" is enabled and a file is opened, the plugin attempts to guess the encoding of the file, stopping on first result.

* Check if the file name ends with some well know binary formats ( png, jpg, etc )
 	* Mark as binary
* Check if the file contains the null character '\0' in the first 1048576 bytes (1Mb) of the file
	* Mark as binary
* If the file is larger than 1048576 bytes (1Mb) 
	* Mark as Unknown
* Give to the [chardet](http://pypi.python.org/pypi/chardet ) library no more than 8 seconds to guess the encoding of the file.
	* if timed out (8 seconds) mark as Unknown
	* if returned encoding "None" mark as Binary
	* if returned encoding "ASCII" mark as "UTF-8"
	* if the "confidence" result of the encoding is lower than 0.7, then try with the fallback_encodings set on User preferences. The first which is not failing will set as winner encoding, else set encoding as Unknown.

For your sublime experience:

* all of this runs on own thread.
* files reads in chunks of 8000 bytes
* results are cached in view.settings. Once a file encoding is guessed there is no need to guess the encoding again.

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

dataset huge:
http://www.mauvecloud.net/charsets/index.html

codecs:
http://docs.python.org/library/codecs.html

Installation
------------------

 * Install this repository via "Package Control" http://wbond.net/sublime_packages/package_control

Source-code
------------------

https://github.com/SublimeText/EncodingHelper

Forum Thread
------------------

http://www.sublimetext.com/forum/viewtopic.php?f=5&t=3453

Contribute
------------------

[Consider make a contribution](https://www.paypal.com/cgi-bin/webscr?cmd=_donations&business=extensiondevelopment%40gmail%2ecom&lc=UY&item_name=Tito&item_number=sublime%2dtext%2dside%2dbar%2dplugin&currency_code=USD&bn=PP%2dDonationsBF%3abtn_donateCC_LG%2egif%3aNonHosted )