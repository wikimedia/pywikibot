# Pywikibot Framework

[![Build Status](https://secure.travis-ci.org/wikimedia/pywikibot-core.png?branch=master)](http://travis-ci.org/wikimedia/pywikibot-core)

The pywikibot framework is a Python library that interfaces with the [MediaWiki API](https://www.mediawiki.org/wiki/API).
Also included are various general function scripts that can be adapted for different tasks.

## Quick start
```
git clone https://gerrit.wikimedia.org/r/pywikibot/core.git
cd core
git submodule update --init
python pwb.py script_name
```

Our [installation guide](https://www.mediawiki.org/wiki/Manual:Pywikipediabot/Installation) has more details for advanced usage.

## Usage

If you wish to write your own script it's very easy to get started:

```python
import pywikibot
site = pywikibot.Site('en', 'wikipedia')  # The site we want to run our bot on
page = pywikibot.Page(site, 'Wikipedia:Sandbox')
text = page.get()  # The current text on the page
text = text.replace('foo', 'bar')
page.put(text, 'Replacing "foo" with "bar"')  # Saves the page
```

## Contributing

Our code is maintained on Wikimedia's [Gerrit installation](https://gerrit.wikimedia.org/), [learn](https://www.mediawiki.org/wiki/Developer_access) how to get started.

