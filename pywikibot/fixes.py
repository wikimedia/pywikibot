# -*- coding: utf-8  -*-
"""
File containing all standard fixes

"""

#
# (C) Pywikibot team, 2008-2010
#
# Distributed under the terms of the MIT license.
#
__version__ = '$Id$'
#

help = u"""
                  * HTML        - Convert HTML tags to wiki syntax, and
                                  fix XHTML.
                  * isbn        - Fix badly formatted ISBNs.
                  * syntax      - Try to fix bad wiki markup. Do not run
                                  this in automatic mode, as the bot may
                                  make mistakes.
                  * syntax-safe - Like syntax, but less risky, so you can
                                  run this in automatic mode.
                  * case-de     - fix upper/lower case errors in German
                  * grammar-de  - fix grammar and typography in German
                  * vonbis      - Ersetze Binde-/Gedankenstrich durch "bis"
                                  in German
                  * music       - Links auf Begriffsklärungen in German
                  * datum       - specific date formats in German
                  * correct-ar  - Corrections for Arabic Wikipedia and any
                                  Arabic wiki.
                  * yu-tld      - the yu top-level domain will soon be
                                  disabled, see
                  * fckeditor   - Try to convert FCKeditor HTML tags to wiki
                                  syntax.
                                  http://lists.wikimedia.org/pipermail/wikibots-l/2009-February/000290.html

"""

fixes = {
    # These replacements will convert HTML to wiki syntax where possible, and
    # make remaining tags XHTML compliant.
    'HTML': {
        'regex': True,
        'msg': {
            'ar':  u'روبوت: تحويل/تصليح HTML',
            'be':  u'Бот: карэкцыя HTML',
            'cs':  u'převod/oprava HTML',
            'en':  u'Robot: Converting/fixing HTML',
            'eo':  u'Bot: koredtado de HTMLa teksto',
            'fa':  u'ربات:تبدیل/تصحیح کدهای اچ‌تی‌ام‌ال',
            'de':  u'Bot: konvertiere/korrigiere HTML',
            'fr':  u'Robot: convertit/fixe HTML',
            'he':  u'בוט: ממיר/מתקן HTML',
            'ja':  u'ロボットによる: HTML転換',
            'ksh': u'Bot: vun HTML en Wikikood wandelle',
            'ia':  u'Robot: conversion/reparation de HTML',
            'lt':  u'robotas: konvertuojamas/taisomas HTML',
            'nl':  u'Bot: conversie/reparatie HTML',
            'pl':  u'Robot konwertuje/naprawia HTML',
            'pt':  u'Bot: Corrigindo HTML',
            'ru':  u'Бот: коррекция HTML',
            'sr':  u'Бот: Поправка HTML-а',
            'sv':  u'Bot: Konverterar/korrigerar HTML',
            'uk':  u'Бот: корекцiя HTML',
            'zh':  u'機器人: 轉換HTML',
        },
        'replacements': [
            # Everything case-insensitive (?i)
            # Keep in mind that MediaWiki automatically converts <br> to <br />
            # when rendering pages, so you might comment the next two lines out
            # to save some time/edits.
            #(r'(?i)<br>',                      r'<br />'),
            # linebreak with attributes
            #(r'(?i)<br ([^>/]+?)>',            r'<br \1 />'),
            (r'(?i)<b>(.*?)</b>',              r"'''\1'''"),
            (r'(?i)<strong>(.*?)</strong>',    r"'''\1'''"),
            (r'(?i)<i>(.*?)</i>',              r"''\1''"),
            (r'(?i)<em>(.*?)</em>',            r"''\1''"),
            # horizontal line without attributes in a single line
            (r'(?i)([\r\n])<hr[ /]*>([\r\n])', r'\1----\2'),
            # horizontal line without attributes with more text in the same line
            #(r'(?i) +<hr[ /]*> +',             r'\r\n----\r\n'),
            # horizontal line with attributes; can't be done with wiki syntax
            # so we only make it XHTML compliant
            (r'(?i)<hr ([^>/]+?)>',            r'<hr \1 />'),
            # a header where only spaces are in the same line
            (r'(?i)([\r\n]) *<h1> *([^<]+?) *</h1> *([\r\n])',  r"\1= \2 =\3"),
            (r'(?i)([\r\n]) *<h2> *([^<]+?) *</h2> *([\r\n])',  r"\1== \2 ==\3"),
            (r'(?i)([\r\n]) *<h3> *([^<]+?) *</h3> *([\r\n])',  r"\1=== \2 ===\3"),
            (r'(?i)([\r\n]) *<h4> *([^<]+?) *</h4> *([\r\n])',  r"\1==== \2 ====\3"),
            (r'(?i)([\r\n]) *<h5> *([^<]+?) *</h5> *([\r\n])',  r"\1===== \2 =====\3"),
            (r'(?i)([\r\n]) *<h6> *([^<]+?) *</h6> *([\r\n])',  r"\1====== \2 ======\3"),
            # TODO: maybe we can make the bot replace <p> tags with \r\n's.
        ],
        'exceptions': {
            'inside-tags': [
                'nowiki',
                'comment',
                'math',
                'pre'
            ],
        }
    },

    # Grammar fixes for German language
    # Do NOT run this automatically!
    'grammar-de': {
        'regex': True,
        'msg': {
            'de': u'Bot: korrigiere Grammatik',
        },
        'replacements': [
            #(u'([Ss]owohl) ([^,\.]+?), als auch',                                                            r'\1 \2 als auch'),
            #(u'([Ww]eder) ([^,\.]+?), noch', r'\1 \2 noch'),
            #
            # Vorsicht bei Substantiven, z. B. 3-Jähriger!
            (u'(\d+)(minütig|stündig|tägig|wöchig|jährig|minütlich|stündlich|täglich|wöchentlich|jährlich|fach|mal|malig|köpfig|teilig|gliedrig|geteilt|elementig|dimensional|bändig|eckig|farbig|stimmig)', r'\1-\2'),
            # zusammengesetztes Wort, Bindestrich wird durchgeschleift
            (u'(?<!\w)(\d+|\d+[\.,]\d+)(\$|€|DM|£|¥|mg|g|kg|ml|cl|l|t|ms|min|µm|mm|cm|dm|m|km|ha|°C|kB|MB|GB|TB|W|kW|MW|GW|PS|Nm|eV|kcal|mA|mV|kV|Ω|Hz|kHz|MHz|GHz|mol|Pa|Bq|Sv|mSv)([²³]?-[\w\[])',           r'\1-\2\3'),
            # Größenangabe ohne Leerzeichen vor Einheit
            # weggelassen wegen vieler falsch Positiver: s, A, V, C, S, J, %
            (u'(?<!\w)(\d+|\d+[\.,]\d+)(\$|€|DM|£|¥|mg|g|kg|ml|cl|l|t|ms|min|µm|mm|cm|dm|m|km|ha|°C|kB|MB|GB|TB|W|kW|MW|GW|PS|Nm|eV|kcal|mA|mV|kV|Ω|Hz|kHz|MHz|GHz|mol|Pa|Bq|Sv|mSv)(?=\W|²|³|$)',          r'\1 \2'),
            # Temperaturangabe mit falsch gesetztem Leerzeichen
            (u'(?<!\w)(\d+|\d+[\.,]\d+)° C(?=\W|²|³|$)',          r'\1' + u' °C'),
            # Kein Leerzeichen nach Komma
            (u'([a-zäöüß](\]\])?,)((\[\[)?[a-zäöüA-ZÄÖÜ])',                                                                          r'\1 \3'),
            # Leerzeichen und Komma vertauscht
            (u'([a-zäöüß](\]\])?) ,((\[\[)?[a-zäöüA-ZÄÖÜ])',                                                                          r'\1, \3'),
            # Plenks (d. h. Leerzeichen auch vor dem Komma/Punkt/Ausrufezeichen/Fragezeichen)
            # Achtung bei Französisch: http://de.wikipedia.org/wiki/Plenk#Sonderfall_Franz.C3.B6sisch
            # Leerzeichen vor Doppelpunkt/Semikolon kann korrekt sein, nach irgendeiner Norm für Zitationen.
            (u'([a-zäöüß](\]\])?) ([,\.!\?]) ((\[\[)?[a-zäöüA-ZÄÖÜ])',                                                                          r'\1\3 \4'),
            #(u'([a-z]\.)([A-Z])',                                                                             r'\1 \2'),
        ],
        'exceptions': {
            'inside-tags': [
                'nowiki',
                'comment',
                'math',
                'pre',           # because of code examples
                'source',        # because of code examples
                'startspace',    # because of code examples
                'hyperlink',     # e.g. commas in URLs
                'gallery',       # because of filenames
                'timeline',
            ],
            'text-contains': [
                r'sic!',
                r'20min.ch',     # Schweizer News-Seite
            ],
            'inside': [
                r'<code>.*</code>',  # because of code examples
                r'{{[Zz]itat\|.*?}}',
                r'{{' + u'§' + r'\|.*?}}',   # Gesetzesparagraph
                u'§' + r'?\d+[a-z]',  # Gesetzesparagraph
                r'Ju 52/1m',  # Flugzeugbezeichnung
                r'Ju 52/3m',  # Flugzeugbezeichnung
                r'AH-1W',     # Hubschrauberbezeichnung
                r'ZPG-3W',    # Luftschiffbezeichnung
                r'8mm',       # Filmtitel
                r'802.11g',   # WLAN-Standard
                r'DOS/4GW',   # Software
                r'ntfs-3g',   # Dateisystem-Treiber
                r'/\w(,\w)*/',      # Laut-Aufzählung in der Linguistik
                r'[xyz](,[xyz])+',  # Variablen in der Mathematik (unklar, ob Leerzeichen hier Pflicht sind)
                r'(?m)^;(.*?)$',    # Definitionslisten, dort gibt es oft absichtlich Leerzeichen vor Doppelpunkten
                r'\d+h( |&nbsp;)\d+m',  # Schreibweise für Zeiten, vor allem in Film-Infoboxen. Nicht korrekt, aber dafür schön kurz.
                r'(?i)\[\[(Bild|Image|Media):.+?\|',  # Dateinamen auslassen
                r'{{bgc\|.*?}}',  # Hintergrundfarbe
                r'<sup>\d+m</sup>',                   # bei chemischen Formeln
                r'\([A-Z][A-Za-z]*(,[A-Z][A-Za-z]*(<sup>.*?</sup>|<sub>.*?</sub>|))+\)'  # chemische Formel, z. B. AuPb(Pb,Sb,Bi)Te. Hier sollen keine Leerzeichen hinter die Kommata.
            ],
            'title': [
                r'Arsen',  # chemische Formel
            ],
        }
    },

    # Do NOT run this automatically!
    # Recommendation: First run syntax-safe automatically, afterwards
    # run syntax manually, carefully checking that you're not breaking
    # anything.
    'syntax': {
        'regex': True,
        'msg': {
            'ar':  u'بوت: تصليح تهيئة الويكي',
            'be':  u'Бот: Карэкцыя вiкi-сiнтаксiсу',
            'cs':  u'Oprava wikisyntaxe',
            'de':  u'Bot: Korrigiere Wiki-Syntax',
            'en':  u'Robot: Fixing wiki syntax',
            'eo':  u'Bot: Korektado de vikia sintakso',
            'fa':  u'ربات:تصحیح قالب ویکی‌نویسی',
            'fr':  u'Bot: Corrige wiki-syntaxe',
            'he':  u'בוט: מתקן תחביר ויקי',
            'ia':  u'Robot: Reparation de syntaxe wiki',
            'ja':  u'ロボットによる: wiki構文修正',
            'lt':  u'robotas: Taisoma wiki sintaksė',
            'nl':  u'Bot: reparatie wikisyntaxis',
            'pl':  u'Robot poprawia wiki-składnię',
            'pt':  u'Bot: Corrigindo sintaxe wiki',
            'ru':  u'Бот: Коррекция вики синтаксиса',
            'sr':  u'Бот: Поправка вики синтаксе',
            'uk':  u'Бот: Корекцiя вiкi-синтаксису',
            'zh':  u'機器人: 修正wiki語法',
        },
        'replacements': [
            # external link in double brackets
            (r'\[\[(?P<url>https?://[^\]]+?)\]\]',   r'[\g<url>]'),
            # external link starting with double bracket
            (r'\[\[(?P<url>https?://.+?)\]',   r'[\g<url>]'),
            # external link with forgotten closing bracket
            #(r'\[(?P<url>https?://[^\]\s]+)\r\n',  r'[\g<url>]\r\n'),
            # external link ending with double bracket.
            # do not change weblinks that contain wiki links inside
            # inside the description
            (r'\[(?P<url>https?://[^\[\]]+?)\]\](?!\])',   r'[\g<url>]'),
            # external link and description separated by a dash.
            # ATTENTION: while this is a mistake in most cases, there are some
            # valid URLs that contain dashes!
            (r'\[(?P<url>https?://[^\|\]\s]+?) *\| *(?P<label>[^\|\]]+?)\]', r'[\g<url> \g<label>]'),
            # wiki link closed by single bracket.
            # ATTENTION: There are some false positives, for example
            # Brainfuck code examples or MS-DOS parameter instructions.
            # There are also sometimes better ways to fix it than
            # just putting an additional ] after the link.
            (r'\[\[([^\[\]]+?)\](?!\])',  r'[[\1]]'),
            # wiki link opened by single bracket.
            # ATTENTION: same as above.
            (r'(?<!\[)\[([^\[\]]+?)\]\](?!\])',  r'[[\1]]'),
            # template closed by single bracket
            # ATTENTION: There are some false positives, especially in
            # mathematical context or program code.
            (r'{{([^{}]+?)}(?!})',       r'{{\1}}'),
        ],
        'exceptions': {
            'inside-tags': [
                'nowiki',
                'comment',
                'math',
                'pre',
                'source',        # because of code examples
                'startspace',    # because of code examples
            ],
            'text-contains': [
                r'http://.*?object=tx\|',                # regular dash in URL
                r'http://.*?allmusic\.com',              # regular dash in URL
                r'http://.*?allmovie\.com',              # regular dash in URL
                r'http://physics.nist.gov/',             # regular dash in URL
                r'http://www.forum-seniorenarbeit.de/',  # regular dash in URL
                r'http://kuenstlerdatenbank.ifa.de/',    # regular dash in URL
                r'&object=med',                          # regular dash in URL
                r'\[CDATA\['                             # lots of brackets
            ],
        }
    },

    # The same as syntax, but restricted to replacements that should
    # be safe to run automatically.
    'syntax-safe': {
        'regex': True,
        'msg': {
            'ar':  u'بوت: تصليح تهيئة الويكي',
            'be':  u'Бот: Карэкцыя вiкi-сiнтаксiсу',
            'cs':  u'Oprava wikisyntaxe',
            'de':  u'Bot: Korrigiere Wiki-Syntax',
            'en':  u'Robot: Fixing wiki syntax',
            'eo':  u'Bot: Korektado de vikia sintakso',
            'fa':  u'ربات:تصحیح قالب ویکی‌نویسی',
            'fr':  u'Bot: Corrige wiki-syntaxe',
            'he':  u'בוט: מתקן תחביר ויקי',
            'ia':  u'Robot: Reparation de syntaxe wiki',
            'ja':  u'ロボットによる: wiki構文修正',
            'lt':  u'robotas: Taisoma wiki sintaksė',
            'nl':  u'Bot: reparatie wikisyntaxis',
            'pl':  u'Robot poprawia wiki-składnię',
            'pt':  u'Bot: Corrigindo sintaxe wiki',
            'ru':  u'Бот: Коррекция вики синтаксиса',
            'sr':  u'Бот: Поправка вики синтаксе',
            'uk':  u'Бот: Корекцiя вiкi-синтаксису',
            'zh':  u'機器人: 修正wiki語法',
        },
        'replacements': [
            # external link in double brackets
            (r'\[\[(?P<url>https?://[^\]]+?)\]\]',   r'[\g<url>]'),
            # external link starting with double bracket
            (r'\[\[(?P<url>https?://.+?)\]',   r'[\g<url>]'),
            # external link with forgotten closing bracket
            #(r'\[(?P<url>https?://[^\]\s]+)\r\n',   r'[\g<url>]\r\n'),
            # external link and description separated by a dash, with
            # whitespace in front of the dash, so that it is clear that
            # the dash is not a legitimate part of the URL.
            (r'\[(?P<url>https?://[^\|\] \r\n]+?) +\| *(?P<label>[^\|\]]+?)\]', r'[\g<url> \g<label>]'),
            # dash in external link, where the correct end of the URL can
            # be detected from the file extension. It is very unlikely that
            # this will cause mistakes.
            (r'\[(?P<url>https?://[^\|\] ]+?(\.pdf|\.html|\.htm|\.php|\.asp|\.aspx|\.jsp)) *\| *(?P<label>[^\|\]]+?)\]', r'[\g<url> \g<label>]'),
        ],
        'exceptions': {
            'inside-tags': [
                'nowiki',
                'comment',
                'math',
                'pre',
                'source',        # because of code examples
                'startspace',    # because of code examples
            ],
        }
    },

    'case-de': {  # German upper / lower case issues
        'regex': True,
        'msg': {
            'de': u'Bot: Korrigiere Groß-/Kleinschreibung',
        },
        'replacements': [
            (r'\batlantische(r|n|) Ozean', r'Atlantische\1 Ozean'),
            (r'\bdeutsche(r|n|) Bundestag\b', r'Deutsche\1 Bundestag'),
            (r'\bdeutschen Bundestags\b', r'Deutschen Bundestags'),  # Aufpassen, z. B. 'deutsche Bundestagswahl'
            (r'\bdeutsche(r|n|) Reich\b', r'Deutsche\1 Reich'),
            (r'\bdeutschen Reichs\b', r'Deutschen Reichs'),  # Aufpassen, z. B. 'deutsche Reichsgrenzen'
            (r'\bdritte(n|) Welt(?!krieg)', r'Dritte\1 Welt'),
            (r'\bdreißigjährige(r|n|) Krieg', r'Dreißigjährige\1 Krieg'),
            (r'\beuropäische(n|) Gemeinschaft', r'Europäische\1 Gemeinschaft'),
            (r'\beuropäische(n|) Kommission', r'Europäische\1 Kommission'),
            (r'\beuropäische(n|) Parlament', r'Europäische\1 Parlament'),
            (r'\beuropäische(n|) Union', r'Europäische\1 Union'),
            (r'\berste(r|n|) Weltkrieg', r'Erste\1 Weltkrieg'),
            (r'\bkalte(r|n|) Krieg', r'Kalte\1 Krieg'),
            (r'\bpazifische(r|n|) Ozean', r'Pazifische\1 Ozean'),
            (r'Tag der deutschen Einheit', r'Tag der Deutschen Einheit'),
            (r'\bzweite(r|n|) Weltkrieg', r'Zweite\1 Weltkrieg'),
        ],
        'exceptions': {
            'inside-tags': [
                'nowiki',
                'comment',
                'math',
                'pre',
            ],
            'text-contains': [
                r'sic!',
            ],
        }
    },

    'vonbis': {
        'regex': True,
        'msg': {
            'de': u'Bot: Ersetze Binde-/Gedankenstrich durch "bis"',
        },
        'replacements': [
            # Bindestrich, Gedankenstrich, Geviertstrich
            (u'(von \d{3,4}) *(-|&ndash;|–|&mdash;|—) *(\d{3,4})', r'\1 bis \3'),
        ],
    },

    # some disambiguation stuff for de:
    # python replace.py -fix:music -subcat:Album
    'music': {
        'regex': False,
        'msg': {
            'de': u'Bot: korrigiere Links auf Begriffsklärungen',
        },
        'replacements': [
            (u'[[CD]]', u'[[Audio-CD|CD]]'),
            (u'[[LP]]', u'[[Langspielplatte|LP]]'),
            (u'[[EP]]', u'[[Extended Play|EP]]'),
            (u'[[MC]]', u'[[Musikkassette|MC]]'),
            (u'[[Single]]', u'[[Single (Musik)|Single]]'),
        ],
        'exceptions': {
            'inside-tags': [
                'hyperlink',
            ]
        }
    },

    # format of dates of birth and death, for de:
    # python replace.py -fix:datum -ref:Vorlage:Personendaten
    'datum': {
        'regex': True,
        'msg': {
            'de': u'Bot: Korrigiere Datumsformat',
        },
        'replacements': [
            # space after birth sign w/ year
            #(u'\(\*(\d{3,4})', u'(* \\1'),
            ## space after death sign w/ year
            #(u'†(\d{3,4})', u'† \\1'),
            #(u'&dagger;(\d{3,4})', u'† \\1'),
            ## space after birth sign w/ linked date
            #(u'\(\*\[\[(\d)', u'(* [[\\1'),
            ## space after death sign w/ linked date
            #(u'†\[\[(\d)', u'† [[\\1'),
            #(u'&dagger;\[\[(\d)', u'† [[\\1'),
            (u'\[\[(\d+\. (?:Januar|Februar|März|April|Mai|Juni|Juli|August|September|Oktober|November|Dezember)) (\d{1,4})\]\]', u'[[\\1]] [[\\2]]'),
            # Keine führende Null beim Datum (ersteinmal nur bei denen, bei denen auch ein Leerzeichen fehlt)
            (u'0(\d+)\.(Januar|Februar|März|April|Mai|Juni|Juli|August|September|Oktober|November|Dezember)', r'\1. \2'),
            # Kein Leerzeichen zwischen Tag und Monat
            (u'(\d+)\.(Januar|Februar|März|April|Mai|Juni|Juli|August|September|Oktober|November|Dezember)', r'\1. \2'),
            # Kein Punkt vorm Jahr
            (u'(\d+)\. (Januar|Februar|März|April|Mai|Juni|Juli|August|September|Oktober|November|Dezember)\.(\d{1,4})', r'\1. \2 \3'),
        ],
        'exceptions': {
            'inside': [
                r'\[\[20. Juli 1944\]\]',  # Hitler-Attentat
                r'\[\[17. Juni 1953\]\]',  # Ost-Berliner Volksaufstand
                r'\[\[1. April 2000\]\]',  # Film
                r'\[\[11. September 2001\]\]',  # Anschläge in den USA
                r'\[\[7. Juli 2005\]\]',   # Terroranschläge in Spanien
            ],
        }
    },

    'isbn': {
        'regex': True,
        'msg': 'isbn-formatting',  # use i18n translations
        'replacements': [
            # colon
            (r'ISBN: (\d+)', r'ISBN \1'),
            # superfluous word "number"
            (r'ISBN( number| no\.?| No\.?|-Nummer|-Nr\.):? (\d+)', r'ISBN \2'),
            # Space, minus, dot,  hypen, en dash, em dash, etc. instead of
            # hyphen-minus as separator, or spaces between digits and separators.
            # Note that these regular expressions also match valid ISBNs, but
            # these won't be changed.

            # NOTE
            # The following regexps are in u'...' format because Python 3.3 does not support
            # ur'...' strings. They have been converted by copy-pasting them to Python 2.7
            # and copying back the results.

            # ur'ISBN (978|979) *[\- −\.‐-―] *(\d+) *[\- −\.‐-―] *(\d+) *[\- −\.‐-―] *(\d+) *[\- −\.‐-―] *(\d)(?!\d)'
            (u'ISBN (978|979) *[\\- \u2212\\.\u2010-\u2015] *(\\d+) *[\\- \u2212\\.\u2010-\u2015] *(\\d+) *[\\- \u2212\\.\u2010-\u2015] *(\\d+) *[\\- \u2212\\.\u2010-\u2015] *(\\d)(?!\\d)', r'ISBN \1-\2-\3-\4-\5'),  # ISBN-13

            # ur'ISBN (\d+) *[\- −\.‐-―] *(\d+) *[\- −\.‐-―] *(\d+) *[\- −\.‐-―] *(\d|X|x)(?!\d)'
            (u'ISBN (\\d+) *[\\- \u2212\\.\u2010-\u2015] *(\\d+) *[\\- \u2212\\.\u2010-\u2015] *(\\d+) *[\\- \u2212\\.\u2010-\u2015] *(\\d|X|x)(?!\\d)', r'ISBN \1-\2-\3-\4'),  # ISBN-10
            # missing space before ISBN-10 or before ISBN-13,
            # or non-breaking space.
            (r'ISBN(|&nbsp;| )((\d(-?)){12}\d|(\d(-?)){9}[\dXx])', r'ISBN \2'),
        ],
        'exceptions': {
            'inside-tags': [
                'comment',
                'hyperlink',
            ],
            'inside': [
                r'ISBN (\d(-?)){12}\d',     # matches valid ISBN-13s
                r'ISBN (\d(-?)){9}[\dXx]',  # matches valid ISBN-10s
            ],
        }
    },

    # Corrections for Arabic Wikipedia and any Arabic wiki.
    #   python replace.py -fix:correct-ar -start:! -always

    'correct-ar': {
        'regex': True,
        'msg': {
            'ar': u'تدقيق إملائي',
        },
        'replacements': [
            #(u' ,', u' ،'), # FIXME: Do not replace comma in non-Arabic text, interwiki, image links or <math> syntax.
            (r'\b' + u'إمرأة' + r'\b', u'امرأة'),
            (r'\b' + u'الى' + r'\b', u'إلى'),
            (r'\b' + u'إسم' + r'\b', u'اسم'),
            (r'\b' + u'الأن' + r'\b', u'الآن'),
            (r'\b' + u'الة' + r'\b', u'آلة'),
            (r'\b' + u'فى' + r'\b', u'في'),
            (r'\b' + u'إبن' + r'\b', u'ابن'),
            (r'\b' + u'إبنة' + r'\b', u'ابنة'),
            (r'\b' + u'إقتصاد' + r'\b', u'اقتصاد'),
            (r'\b' + u'إجتماع' + r'\b', u'اجتماع'),
            (r'\b' + u'انجيل' + r'\b', u'إنجيل'),
            (r'\b' + u'اجماع' + r'\b', u'إجماع'),
            (r'\b' + u'اكتوبر' + r'\b', u'أكتوبر'),
            (r'\b' + u'إستخراج' + r'\b', u'استخراج'),
            (r'\b' + u'إستعمال' + r'\b', u'استعمال'),
            (r'\b' + u'إستبدال' + r'\b', u'استبدال'),
            (r'\b' + u'إشتراك' + r'\b', u'اشتراك'),
            (r'\b' + u'إستعادة' + r'\b', u'استعادة'),
            (r'\b' + u'إستقلال' + r'\b', u'استقلال'),
            (r'\b' + u'إنتقال' + r'\b', u'انتقال'),
            (r'\b' + u'إتحاد' + r'\b', u'اتحاد'),
            (r'\b' + u'املاء' + r'\b', u'إملاء'),
            (r'\b' + u'إستخدام' + r'\b', u'استخدام'),
            (r'\b' + u'أحدى' + r'\b', u'إحدى'),
            (r'\b' + u'لاكن' + r'\b', u'لكن'),
            (r'\b' + u'إثنان' + r'\b', u'اثنان'),
            (r'\b' + u'إحتياط' + r'\b', u'احتياط'),
            (r'\b' + u'إقتباس' + r'\b', u'اقتباس'),
            (r'\b' + u'ادارة' + r'\b', u'إدارة'),
            (r'\b' + u'ابناء' + r'\b', u'أبناء'),
            (r'\b' + u'الانصار' + r'\b', u'الأنصار'),
            (r'\b' + u'اشارة' + r'\b', u'إشارة'),
            (r'\b' + u'إقرأ' + r'\b', u'اقرأ'),
            (r'\b' + u'إمتياز' + r'\b', u'امتياز'),
            (r'\b' + u'ارق' + r'\b', u'أرق'),
            (r'\b' + u'اللة' + r'\b', u'الله'),
            (r'\b' + u'إختبار' + r'\b', u'اختبار'),
            (u'==[ ]?روابط خارجية[ ]?==', u'== وصلات خارجية =='),
            (r'\b' + u'ارسال' + r'\b', u'إرسال'),
            (r'\b' + u'إتصالات' + r'\b', u'اتصالات'),
            (r'\b' + u'ابو' + r'\b', u'أبو'),
            (r'\b' + u'ابا' + r'\b', u'أبا'),
            (r'\b' + u'اخو' + r'\b', u'أخو'),
            (r'\b' + u'اخا' + r'\b', u'أخا'),
            (r'\b' + u'اخي' + r'\b', u'أخي'),
            (r'\b' + u'احد' + r'\b', u'أحد'),
            (r'\b' + u'اربعاء' + r'\b', u'أربعاء'),
            (r'\b' + u'اول' + r'\b', u'أول'),
            (r'\b' + u'(ال|)اهم' + r'\b', u'\\1أهم'),
            (r'\b' + u'(ال|)اثقل' + r'\b', u'\\1أثقل'),
            (r'\b' + u'(ال|)امجد' + r'\b', u'\\1أمجد'),
            (r'\b' + u'(ال|)اوسط' + r'\b', u'\\1أوسط'),
            (r'\b' + u'(ال|)اشقر' + r'\b', u'\\1أشقر'),
            (r'\b' + u'(ال|)انور' + r'\b', u'\\1أنور'),
            (r'\b' + u'(ال|)اصعب' + r'\b', u'\\1أصعب'),
            (r'\b' + u'(ال|)اسهل' + r'\b', u'\\1أسهل'),
            (r'\b' + u'(ال|)اجمل' + r'\b', u'\\1أجمل'),
            (r'\b' + u'(ال|)اقبح' + r'\b', u'\\1أقبح'),
            (r'\b' + u'(ال|)اطول' + r'\b', u'\\1أطول'),
            (r'\b' + u'(ال|)اقصر' + r'\b', u'\\1أقصر'),
            (r'\b' + u'(ال|)اسمن' + r'\b', u'\\1أسمن'),
            (r'\b' + u'(ال|)اذكى' + r'\b', u'\\1أذكى'),
            (r'\b' + u'(ال|)اكثر' + r'\b', u'\\1أكثر'),
            (r'\b' + u'(ال|)افضل' + r'\b', u'\\1أفضل'),
            (r'\b' + u'(ال|)اكبر' + r'\b', u'\\1أكبر'),
            (r'\b' + u'(ال|)اشهر' + r'\b', u'\\1أشهر'),
            (r'\b' + u'(ال|)ابطأ' + r'\b', u'\\1أبطأ'),
            (r'\b' + u'(ال|)اماني' + r'\b', u'\\1أماني'),
            (r'\b' + u'(ال|)احلام' + r'\b', u'\\1أحلام'),
            (r'\b' + u'(ال|)اسماء' + r'\b', u'\\1أسماء'),
            (r'\b' + u'(ال|)اسامة' + r'\b', u'\\1أسامة'),
            (r'\b' + u'ابراهيم' + r'\b', u'إبراهيم'),
            (r'\b' + u'اسماعيل' + r'\b', u'إسماعيل'),
            (r'\b' + u'ايوب' + r'\b', u'أيوب'),
            (r'\b' + u'ايمن' + r'\b', u'أيمن'),
            (r'\b' + u'اوزبكستان' + r'\b', u'أوزبكستان'),
            (r'\b' + u'اذربيجان' + r'\b', u'أذربيجان'),
            (r'\b' + u'افغانستان' + r'\b', u'أفغانستان'),
            (r'\b' + u'انجلترا' + r'\b', u'إنجلترا'),
            (r'\b' + u'ايطاليا' + r'\b', u'إيطاليا'),
            (r'\b' + u'اوربا' + r'\b', u'أوروبا'),
            (r'\b' + u'أوربا' + r'\b', u'أوروبا'),
            (r'\b' + u'اوغندة' + r'\b', u'أوغندة'),
            (r'\b' + u'(ال|)ا(لماني|فريقي|سترالي)(ا|ة|تان|ان|ين|ي|ون|و|ات|)' + r'\b', u'\\1أ\\2\\3'),
            (r'\b' + u'(ال|)ا(وروب|مريك)(ا|ي|ية|يتان|يان|يين|يي|يون|يو|يات|)' + r'\b', u'\\1أ\\2\\3'),
            (r'\b' + u'(ال|)ا(ردن|رجنتين|وغند|سبان|وكران|فغان)(ي|ية|يتان|يان|يين|يي|يون|يو|يات|)' + r'\b', u'\\1أ\\2\\3'),
            (r'\b' + u'(ال|)ا(سرائيل|يران|مارات|نكليز|نجليز)(ي|ية|يتان|يان|يين|يي|يون|يو|يات|)' + r'\b', u'\\1إ\\2\\3'),
            (r'\b' + u'(ال|)(ا|أ)(رثوذكس|رثوذوكس)(ي|ية|يتان|يان|يين|يي|يون|يو|يات|)' + r'\b', u'\\1أرثوذكس\\4'),
            (r'\b' + u'إست(عمل|خدم|مر|مد|مال|عاض|قام|حال|جاب|قال|زاد|عان|طال)(ت|ا|وا|)' + r'\b', u'است\\1\\2'),
            (r'\b' + u'إست(حال|قال|طال|زاد|عان|قام|راح|جاب|عاض|مال)ة' + r'\b', u'است\\1ة'),
        ],
        'exceptions': {
            'inside-tags': [
                'interwiki',
                'math',
                'ref',
            ],
        }
    },
    'specialpages': {
        'regex': False,
        'msg': {
            'en': u'Robot: Fixing special page capitalisation',
            'fa': u'ربات: تصحیح بزرگی و کوچکی حروف صفحه‌های ویژه',
        },
        'replacements': [
            (u'Special:Allpages',        u'Special:AllPages'),
            (u'Special:Blockip',         u'Special:BlockIP'),
            (u'Special:Blankpage',       u'Special:BlankPage'),
            (u'Special:Filepath',        u'Special:FilePath'),
            (u'Special:Globalusers',     u'Special:GlobalUsers'),
            (u'Special:Imagelist',       u'Special:ImageList'),
            (u'Special:Ipblocklist',     u'Special:IPBlockList'),
            (u'Special:Listgrouprights', u'Special:ListGroupRights'),
            (u'Special:Listusers',       u'Special:ListUsers'),
            (u'Special:Newimages',       u'Special:NewImages'),
            (u'Special:Prefixindex',     u'Special:PrefixIndex'),
            (u'Special:Protectedpages',  u'Special:ProtectedPages'),
            (u'Special:Recentchanges',   u'Special:RecentChanges'),
            (u'Special:Specialpages',    u'Special:SpecialPages'),
            (u'Special:Unlockdb',        u'Special:UnlockDB'),
            (u'Special:Userlogin',       u'Special:UserLogin'),
            (u'Special:Userlogout',      u'Special:UserLogout'),
            (u'Special:Whatlinkshere',   u'Special:WhatLinksHere'),
        ],
    },
    # yu top-level domain will soon be disabled,
    # see http://lists.wikimedia.org/pipermail/wikibots-l/2009-February/000290.html
    # The following are domains that are often-used.
    'yu-tld': {
        'regex': False,
        'nocase': True,
        'msg': {
            'de':  u'Bot: Ersetze Links auf .yu-Domains',
            'en':  u'Robot: Replacing links to .yu domains',
            'fa':  u'ربات: جایگزینی پیوندها به دامنه‌ها با پسوند yu',
            'fr':  u'Robot: Correction des liens pointant vers le domaine .yu, qui expire en 2009',
            'ksh': u'Bot: de ahle .yu-Domains loufe us, dröm ußjetuusch',
        },
        'replacements': [
            (u'www.budva.cg.yu',             u'www.budva.rs'),
            (u'spc.org.yu',                  u'spc.rs'),
            (u'www.oks.org.yu',              u'www.oks.org.rs'),
            (u'www.kikinda.org.yu',          u'www.kikinda.rs'),
            (u'www.ds.org.yu',               u'www.ds.org.rs'),
            (u'www.nbs.yu',                  u'www.nbs.rs'),
            (u'www.serbia.sr.gov.yu',        u'www.srbija.gov.rs'),
            (u'eunet.yu',                    u'eunet.rs'),
            (u'www.zastava-arms.co.yu',      u'www.zastava-arms.co.rs'),
            (u'www.airportnis.co.yu',        u'www.airportnis.rs'),
            # (u'www.danas.co.yu',             u'www.danas.rs'), # Archive links don't seem to work
            (u'www.belex.co.yu',             u'www.belex.rs'),
            (u'beograd.org.yu',              u'beograd.rs'),
            (u'www.vlada.cg.yu',             u'www.vlada.me'),
            (u'webrzs.statserb.sr.gov.yu',   u'webrzs.stat.gov.rs'),
            (u'www.statserb.sr.gov.yu',      u'webrzs.stat.gov.rs'),
            (u'www.rastko.org.yu',           u'www.rastko.org.rs'),
            (u'www.reprezentacija.co.yu',    u'www.reprezentacija.rs'),
            (u'www.blic.co.yu',              u'www.blic.co.rs'),
            (u'www.beograd.org.yu',          u'www.beograd.org.rs'),
            (u'arhiva.glas-javnosti.co.yu',  u'arhiva.glas-javnosti.rs'),
            (u'www.srpsko-nasledje.co.yu',   u'www.srpsko-nasledje.co.rs'),
            (u'www.dnevnik.co.yu',           u'www.dnevnik.rs'),
            (u'www.srbija.sr.gov.yu',        u'www.srbija.gov.rs'),
            (u'www.kurir-info.co.yu/Arhiva', u'arhiva.kurir-info.rs/Arhiva'),
            (u'www.kurir-info.co.yu/arhiva', u'arhiva.kurir-info.rs/arhiva'),
            (u'www.kurir-info.co.yu',        u'www.kurir-info.rs'),
            (u'arhiva.kurir-info.co.yu',     u'arhiva.kurir-info.rs'),
            (u'www.prvaliga.co.yu',          u'www.prvaliga.rs'),
            (u'www.mitropolija.cg.yu',       u'www.mitropolija.me'),
            (u'www.spc.yu/sr',               u'www.spc.rs/sr'),
            (u'www.sk.co.yu',                u'www.sk.co.rs'),
            (u'www.ekoforum.org.yu',         u'www.ekoforum.org'),
            (u'www.svevlad.org.yu',          u'www.svevlad.org.rs'),
            (u'www.posta.co.yu',             u'www.posta.rs'),
            (u'www.glas-javnosti.co.yu',     u'www.glas-javnosti.rs'),
            (u'www.fscg.cg.yu',              u'www.fscg.co.me'),
            (u'ww1.rts.co.yu/euro',          u'ww1.rts.co.rs/euro'),
            (u'www.rtv.co.yu',               u'www.rtv.rs'),
            (u'www.politika.co.yu',          u'www.politika.rs'),
            (u'www.mfa.gov.yu',              u'www.mfa.gov.rs'),
            (u'www.drzavnauprava.sr.gov.yu', u'www.drzavnauprava.gov.rs'),
        ],
    },
    # These replacements will convert HTML tag from FCK-editor to wiki syntax.
    #
    'fckeditor': {
        'regex': True,
        'msg': {
            'en': u'Robot: Fixing rich-editor html',
            'fa': u'ربات: تصحیح اچ‌تی‌ام‌ال ویرایشگر پیشرفته',
        },
        'replacements': [
            # replace <br> with a new line
            (r'(?i)<br>',                      r'\n'),
            # replace &nbsp; with a space
            (r'(?i)&nbsp;',                      r' '),
        ],
    },
}

#
# Load the user fixes file.

from pywikibot import config

try:
    exec(compile(open(config.datafilepath("user-fixes.py")).read(), config.datafilepath("user-fixes.py"), 'exec'))
except IOError:
    pass
