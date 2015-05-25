# -*- coding: utf-8  -*-
"""File containing all standard fixes."""
#
# (C) Pywikibot team, 2008-2010
#
# Distributed under the terms of the MIT license.
#
from __future__ import unicode_literals

import os.path

from pywikibot import config

__version__ = '$Id$'

parameter_help = u"""
                  Currently available predefined fixes are:

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
                                  https://lists.wikimedia.org/pipermail/wikibots-l/2009-February/000290.html
"""

__doc__ = __doc__ + parameter_help

fixes = {
    # These replacements will convert HTML to wiki syntax where possible, and
    # make remaining tags XHTML compliant.
    'HTML': {
        'regex': True,
        'msg': 'pywikibot-fixes-html',
        'replacements': [
            # Everything case-insensitive (?i)
            # Keep in mind that MediaWiki automatically converts <br> to <br />
            # when rendering pages, so you might comment the next two lines out
            # to save some time/edits.
            (r'(?i)<br *>',                      r'<br />'),
            # linebreak with attributes
            (r'(?i)<br ([^>/]+?)>',            r'<br \1 />'),
            (r'(?i)<b>(.*?)</b>',              r"'''\1'''"),
            (r'(?i)<strong>(.*?)</strong>',    r"'''\1'''"),
            (r'(?i)<i>(.*?)</i>',              r"''\1''"),
            (r'(?i)<em>(.*?)</em>',            r"''\1''"),
            # horizontal line without attributes in a single line
            (r'(?i)([\r\n])<hr[ /]*>([\r\n])', r'\1----\2'),
            # horizontal line without attributes with more text in the same line
            #   (r'(?i) +<hr[ /]*> +',             r'\r\n----\r\n'),
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
            #   (u'([Ss]owohl) ([^,\.]+?), als auch', r'\1 \2 als auch'),
            #   (u'([Ww]eder) ([^,\.]+?), noch', r'\1 \2 noch'),
            #
            # Vorsicht bei Substantiven, z. B. 3-Jähriger!
            (r'(\d+)(minütig|stündig|tägig|wöchig|jährig|minütlich|stündlich'
             r'|täglich|wöchentlich|jährlich|fach|mal|malig|köpfig|teilig'
             r'|gliedrig|geteilt|elementig|dimensional|bändig|eckig|farbig'
             r'|stimmig)', r'\1-\2'),
            # zusammengesetztes Wort, Bindestrich wird durchgeschleift
            (r'(?<!\w)(\d+|\d+[.,]\d+)(\$|€|DM|£|¥|mg|g|kg|ml|cl|l|t|ms|min'
             r'|µm|mm|cm|dm|m|km|ha|°C|kB|MB|GB|TB|W|kW|MW|GW|PS|Nm|eV|kcal'
             r'|mA|mV|kV|Ω|Hz|kHz|MHz|GHz|mol|Pa|Bq|Sv|mSv)([²³]?-[\w\[])', r'\1-\2\3'),
            # Größenangabe ohne Leerzeichen vor Einheit
            # weggelassen wegen vieler falsch Positiver: s, A, V, C, S, J, %
            (r'(?<!\w)(\d+|\d+[.,]\d+)(\$|€|DM|£|¥|mg|g|kg|ml|cl|l|t|ms|min'
             r'|µm|mm|cm|dm|m|km|ha|°C|kB|MB|GB|TB|W|kW|MW|GW|PS|Nm|eV|kcal'
             r'|mA|mV|kV|Ω|Hz|kHz|MHz|GHz|mol|Pa|Bq|Sv|mSv)(?=\W|²|³|$)', r'\1 \2'),
            # Temperaturangabe mit falsch gesetztem Leerzeichen
            (r'(?<!\w)(\d+|\d+[.,]\d+)° C(?=\W|²|³|$)', r'\1 °C'),
            # Kein Leerzeichen nach Komma
            (r'([a-zäöüß](\]\])?,)((\[\[)?[a-zäöüA-ZÄÖÜ])', r'\1 \3'),
            # Leerzeichen und Komma vertauscht
            (r'([a-zäöüß](\]\])?) ,((\[\[)?[a-zäöüA-ZÄÖÜ])', r'\1, \3'),
            # Plenks (d. h. Leerzeichen auch vor dem Komma/Punkt/Ausrufezeichen/Fragezeichen)
            # Achtung bei Französisch: https://de.wikipedia.org/wiki/Plenk#Sonderfall_Franz.C3.B6sisch
            # Leerzeichen vor Doppelpunkt/Semikolon kann korrekt sein, nach irgendeiner Norm für Zitationen.
            (r'([a-zäöüß](\]\])?) ([,.!?]) ((\[\[)?[a-zäöüA-ZÄÖÜ])', r'\1\3 \4'),
            #   (u'([a-z]\.)([A-Z])', r'\1 \2'),
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
                r'{{§\|.*?}}',   # Gesetzesparagraph
                r'§?\d+[a-z]',  # Gesetzesparagraph
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
                r'\d+h( |&nbsp;)\d+m',
                # Schreibweise für Zeiten, vor allem in Film-Infoboxen.
                # Nicht korrekt, aber dafür schön kurz.
                r'(?i)\[\[(Bild|Image|Media):.+?\|',  # Dateinamen auslassen
                r'{{bgc\|.*?}}',                      # Hintergrundfarbe
                r'<sup>\d+m</sup>',                   # bei chemischen Formeln
                r'\([A-Z][A-Za-z]*(,[A-Z][A-Za-z]*(<sup>.*?</sup>|<sub>.*?</sub>|))+\)'
                # chemische Formel, z. B. AuPb(Pb,Sb,Bi)Te.
                # Hier sollen keine Leerzeichen hinter die Kommata.
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
        'msg': 'pywikibot-fixes-syntax',
        'replacements': [
            # external link in double brackets
            (r'\[\[(?P<url>https?://[^\]]+?)\]\]',   r'[\g<url>]'),
            # external link starting with double bracket
            (r'\[\[(?P<url>https?://.+?)\]',   r'[\g<url>]'),
            # external link with forgotten closing bracket
            #   (r'\[(?P<url>https?://[^\]\s]+)\r\n',  r'[\g<url>]\r\n'),
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
        'msg': 'pywikibot-fixes-syntax',
        'replacements': [
            # external link in double brackets
            (r'\[\[(?P<url>https?://[^\]]+?)\]\]',   r'[\g<url>]'),
            # external link starting with double bracket
            (r'\[\[(?P<url>https?://.+?)\]',   r'[\g<url>]'),
            # external link with forgotten closing bracket
            #   (r'\[(?P<url>https?://[^\]\s]+)\r\n',   r'[\g<url>]\r\n'),
            # external link and description separated by a dash, with
            # whitespace in front of the dash, so that it is clear that
            # the dash is not a legitimate part of the URL.
            (r'\[(?P<url>https?://[^\|\] \r\n]+?) +\| *(?P<label>[^\|\]]+?)\]', r'[\g<url> \g<label>]'),
            # dash in external link, where the correct end of the URL can
            # be detected from the file extension. It is very unlikely that
            # this will cause mistakes.
            (r'\[(?P<url>https?://[^\|\] ]+?(\.pdf|\.html|\.htm|\.php|\.asp|\.aspx|\.jsp)) *\|'
             r' *(?P<label>[^\|\]]+?)\]', r'[\g<url> \g<label>]'),
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
            (r'(von \d{3,4}) *(-|&ndash;|–|&mdash;|—) *(\d{3,4})', r'\1 bis \3'),
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
            #   (u'\(\*(\d{3,4})', u'(* \\1'),
            # space after death sign w/ year
            #   (u'†(\d{3,4})', u'† \\1'),
            #   (u'&dagger;(\d{3,4})', u'† \\1'),
            # space after birth sign w/ linked date
            #   (u'\(\*\[\[(\d)', u'(* [[\\1'),
            # space after death sign w/ linked date
            #   (u'†\[\[(\d)', u'† [[\\1'),
            #   (u'&dagger;\[\[(\d)', u'† [[\\1'),
            (r'\[\[(\d+\. (?:Januar|Februar|März|April|Mai|Juni|Juli|August|'
             r'September|Oktober|November|Dezember)) (\d{1,4})\]\]', r'[[\1]] [[\2]]'),
            # Keine führende Null beim Datum (ersteinmal nur bei denen, bei denen auch ein Leerzeichen fehlt)
            (r'0(\d+)\.(Januar|Februar|März|April|Mai|Juni|Juli|August|'
             r'September|Oktober|November|Dezember)', r'\1. \2'),
            # Kein Leerzeichen zwischen Tag und Monat
            (r'(\d+)\.(Januar|Februar|März|April|Mai|Juni|Juli|August|'
             r'September|Oktober|November|Dezember)', r'\1. \2'),
            # Kein Punkt vorm Jahr
            (r'(\d+)\. (Januar|Februar|März|April|Mai|Juni|Juli|August|'
             r'September|Oktober|November|Dezember)\.(\d{1,4})', r'\1. \2 \3'),
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
            # Remove colon between the word ISBN and the number
            (r'ISBN: (\d+)', r'ISBN \1'),
            # superfluous word "number"
            (r'ISBN( number| no\.?| No\.?|-Nummer|-Nr\.):? (\d+)', r'ISBN \2'),
            # Space, minus, dot,  hypen, en dash, em dash, etc. instead of
            # hyphen-minus as separator, or spaces between digits and separators.
            # Note that these regular expressions also match valid ISBNs, but
            # these won't be changed.
            # These two regexes don't verify that the ISBN is of a valid format
            # but just change separators into normal hypens. The isbn script
            # does checks and similar but does only match ISBNs with digits and
            # hypens (and optionally a X/x at the end).
            (r'ISBN (978|979) *[\- −.‐-―] *(\d+) *[\- −.‐-―] *(\d+) '
             r'*[\- −.‐-―] *(\d+) *[\- −.‐-―] *(\d)(?!\d)',
             r'ISBN \1-\2-\3-\4-\5'),  # ISBN-13

            (r'ISBN (\d+) *[\- −.‐-―] *(\d+) *[\- −.‐-―] *(\d+) *[\- −.‐-―] *(\d|X|x)(?!\d)',
             r'ISBN \1-\2-\3-\4'),  # ISBN-10
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
            # FIXME: Do not replace comma in non-Arabic text,
            # interwiki, image links or <math> syntax.
            #   (u' ,', u' ،'),
            # TODO: Basic explanation in English what it does
            (r'\bإمرأة\b', 'امرأة'),
            (r'\bالى\b', 'إلى'),
            (r'\bإسم\b', 'اسم'),
            (r'\bالأن\b', 'الآن'),
            (r'\bالة\b', 'آلة'),
            (r'\bفى\b', 'في'),
            (r'\bإبن\b', 'ابن'),
            (r'\bإبنة\b', 'ابنة'),
            (r'\bإقتصاد\b', 'اقتصاد'),
            (r'\bإجتماع\b', 'اجتماع'),
            (r'\bانجيل\b', 'إنجيل'),
            (r'\bاجماع\b', 'إجماع'),
            (r'\bاكتوبر\b', 'أكتوبر'),
            (r'\bإستخراج\b', 'استخراج'),
            (r'\bإستعمال\b', 'استعمال'),
            (r'\bإستبدال\b', 'استبدال'),
            (r'\bإشتراك\b', 'اشتراك'),
            (r'\bإستعادة\b', 'استعادة'),
            (r'\bإستقلال\b', 'استقلال'),
            (r'\bإنتقال\b', 'انتقال'),
            (r'\bإتحاد\b', 'اتحاد'),
            (r'\bاملاء\b', 'إملاء'),
            (r'\bإستخدام\b', 'استخدام'),
            (r'\bأحدى\b', 'إحدى'),
            (r'\bلاكن\b', 'لكن'),
            (r'\bإثنان\b', 'اثنان'),
            (r'\bإحتياط\b', 'احتياط'),
            (r'\bإقتباس\b', 'اقتباس'),
            (r'\bادارة\b', 'إدارة'),
            (r'\bابناء\b', 'أبناء'),
            (r'\bالانصار\b', 'الأنصار'),
            (r'\bاشارة\b', 'إشارة'),
            (r'\bإقرأ\b', 'اقرأ'),
            (r'\bإمتياز\b', 'امتياز'),
            (r'\bارق\b', 'أرق'),
            (r'\bاللة\b', 'الله'),
            (r'\bإختبار\b', 'اختبار'),
            (r'== ?روابط خارجية ?==', '== وصلات خارجية =='),
            (r'\bارسال\b', 'إرسال'),
            (r'\bإتصالات\b', 'اتصالات'),
            (r'\bابو\b', 'أبو'),
            (r'\bابا\b', 'أبا'),
            (r'\bاخو\b', 'أخو'),
            (r'\bاخا\b', 'أخا'),
            (r'\bاخي\b', 'أخي'),
            (r'\bاحد\b', 'أحد'),
            (r'\bاربعاء\b', 'أربعاء'),
            (r'\bاول\b', 'أول'),
            (r'\b(ال|)اهم\b', r'\1أهم'),
            (r'\b(ال|)اثقل\b', r'\1أثقل'),
            (r'\b(ال|)امجد\b', r'\1أمجد'),
            (r'\b(ال|)اوسط\b', r'\1أوسط'),
            (r'\b(ال|)اشقر\b', r'\1أشقر'),
            (r'\b(ال|)انور\b', r'\1أنور'),
            (r'\b(ال|)اصعب\b', r'\1أصعب'),
            (r'\b(ال|)اسهل\b', r'\1أسهل'),
            (r'\b(ال|)اجمل\b', r'\1أجمل'),
            (r'\b(ال|)اقبح\b', r'\1أقبح'),
            (r'\b(ال|)اطول\b', r'\1أطول'),
            (r'\b(ال|)اقصر\b', r'\1أقصر'),
            (r'\b(ال|)اسمن\b', r'\1أسمن'),
            (r'\b(ال|)اذكى\b', r'\1أذكى'),
            (r'\b(ال|)اكثر\b', r'\1أكثر'),
            (r'\b(ال|)افضل\b', r'\1أفضل'),
            (r'\b(ال|)اكبر\b', r'\1أكبر'),
            (r'\b(ال|)اشهر\b', r'\1أشهر'),
            (r'\b(ال|)ابطأ\b', r'\1أبطأ'),
            (r'\b(ال|)اماني\b', r'\1أماني'),
            (r'\b(ال|)احلام\b', r'\1أحلام'),
            (r'\b(ال|)اسماء\b', r'\1أسماء'),
            (r'\b(ال|)اسامة\b', r'\1أسامة'),
            (r'\bابراهيم\b', 'إبراهيم'),
            (r'\bاسماعيل\b', 'إسماعيل'),
            (r'\bايوب\b', 'أيوب'),
            (r'\bايمن\b', 'أيمن'),
            (r'\bاوزبكستان\b', 'أوزبكستان'),
            (r'\bاذربيجان\b', 'أذربيجان'),
            (r'\bافغانستان\b', 'أفغانستان'),
            (r'\bانجلترا\b', 'إنجلترا'),
            (r'\bايطاليا\b', 'إيطاليا'),
            (r'\bاوربا\b', 'أوروبا'),
            (r'\bأوربا\b', 'أوروبا'),
            (r'\bاوغندة\b', 'أوغندة'),
            (r'\b(ال|)ا(لماني|فريقي|سترالي)(ا|ة|تان|ان|ين|ي|ون|و|ات|)\b',
             r'\1أ\2\3'),
            (r'\b(ال|)ا(وروب|مريك)(ا|ي|ية|يتان|يان|يين|يي|يون|يو|يات|)\b',
             r'\1أ\2\3'),
            (r'\b(ال|)ا(ردن|رجنتين|وغند|سبان|وكران|فغان)'
             r'(ي|ية|يتان|يان|يين|يي|يون|يو|يات|)\b',
             r'\1أ\2\3'),
            (r'\b(ال|)ا(سرائيل|يران|مارات|نكليز|نجليز)'
             r'(ي|ية|يتان|يان|يين|يي|يون|يو|يات|)\b',
             r'\1إ\2\3'),
            (r'\b(ال|)(ا|أ)(رثوذكس|رثوذوكس)(ي|ية|يتان|يان|يين|يي|يون|يو|يات|)\b',
             r'\1أرثوذكس\4'),
            (r'\bإست(عمل|خدم|مر|مد|مال|عاض|قام|حال|جاب|قال|زاد|عان|طال)(ت|ا|وا|)\b',
             r'است\1\2'),
            (r'\bإست(حال|قال|طال|زاد|عان|قام|راح|جاب|عاض|مال)ة\b', r'است\1ة'),
        ],
        'exceptions': {
            'inside-tags': [
                'interwiki',
                'math',
                'ref',
            ],
        }
    },
    # TODO: Support dynamic replacement from Special pages to the localized one
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
        'msg': 'pywikibot-fixes-fckeditor',
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
filename = config.datafilepath('user-fixes.py')
if os.path.exists(filename):
    # load binary, to let compile decode it according to the file header
    with open(filename, 'rb') as f:
        exec(compile(f.read(), filename, 'exec'))
    user_fixes_loaded = True
else:
    user_fixes_loaded = False
