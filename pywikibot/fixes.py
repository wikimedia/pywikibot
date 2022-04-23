"""File containing all standard fixes."""
#
# (C) Pywikibot team, 2008-2022
#
# Distributed under the terms of the MIT license.
#
import os.path

from pywikibot import config


parameter_help = """
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
                  * correct-ar  - Typo corrections for Arabic Wikipedia and any
                                  Arabic wiki.
                  * yu-tld      - Fix links to .yu domains because it is
                                  disabled, see:
                                  https://lists.wikimedia.org/pipermail/wikibots-l/2009-February/000290.html
                  * fckeditor   - Try to convert FCKeditor HTML tags to wiki
                                  syntax.
"""

__doc__ += parameter_help

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
            # horizontal line without attributes with more text in same line
            #   (r'(?i) +<hr[ /]*> +',             r'\r\n----\r\n'),
            # horizontal line with attributes; can't be done with wiki syntax
            # so we only make it XHTML compliant
            (r'(?i)<hr ([^>/]+?)>',            r'<hr \1 />'),
            # a header where only spaces are in the same line
            (r'(?i)([\r\n]) *<h1> *([^<]+?) *</h1> *([\r\n])', r'\1= \2 =\3'),
            (r'(?i)([\r\n]) *<h2> *([^<]+?) *</h2> *([\r\n])',
             r'\1== \2 ==\3'),
            (r'(?i)([\r\n]) *<h3> *([^<]+?) *</h3> *([\r\n])',
             r'\1=== \2 ===\3'),
            (r'(?i)([\r\n]) *<h4> *([^<]+?) *</h4> *([\r\n])',
             r'\1==== \2 ====\3'),
            (r'(?i)([\r\n]) *<h5> *([^<]+?) *</h5> *([\r\n])',
             r'\1===== \2 =====\3'),
            (r'(?i)([\r\n]) *<h6> *([^<]+?) *</h6> *([\r\n])',
             r'\1====== \2 ======\3'),
            # TODO: maybe we can make the bot replace <p> tags with \r\n's.
        ],
        'exceptions': {
            'inside-tags': [
                'nowiki',
                'comment',
                'math',
                'pre',
                'syntaxhighlight',
            ],
        }
    },

    # Grammar fixes for German language
    # Do NOT run this automatically!
    'grammar-de': {
        'regex': True,
        'msg': {
            'de': 'Bot: korrigiere Grammatik',
        },
        'replacements': [
            # Vorsicht bei Substantiven, z. B. 3-Jähriger!
            (r'(\d+)(minütig|stündig|tägig|wöchig|jährig|minütlich|stündlich'
             r'|täglich|wöchentlich|jährlich|fach|mal|malig|köpfig|teilig'
             r'|gliedrig|geteilt|elementig|dimensional|bändig|eckig|farbig'
             r'|stimmig)', r'\1-\2'),
            # zusammengesetztes Wort, Bindestrich wird durchgeschleift
            (r'(?<!\w)(\d+|\d+[.,]\d+)(\$|€|DM|£|¥|mg|g|kg|ml|cl|l|t|ms|min'
             r'|µm|mm|cm|dm|m|km|ha|°C|kB|MB|GB|TB|W|kW|MW|GW|PS|Nm|eV|kcal'
             r'|mA|mV|kV|Ω|Hz|kHz|MHz|GHz|mol|Pa|Bq|Sv|mSv)([²³]?-[\w\[])',
             r'\1-\2\3'),
            # Größenangabe ohne Leerzeichen vor Einheit
            # weggelassen wegen vieler falsch Positiver: s, A, V, C, S, J, %
            (r'(?<!\w)(\d+|\d+[.,]\d+)(\$|€|DM|£|¥|mg|g|kg|ml|cl|l|t|ms|min'
             r'|µm|mm|cm|dm|m|km|ha|°C|kB|MB|GB|TB|W|kW|MW|GW|PS|Nm|eV|kcal'
             r'|mA|mV|kV|Ω|Hz|kHz|MHz|GHz|mol|Pa|Bq|Sv|mSv)(?=\W|²|³|$)',
             r'\1 \2'),
            # Temperaturangabe mit falsch gesetztem Leerzeichen
            (r'(?<!\w)(\d+|\d+[.,]\d+)° C(?=\W|²|³|$)', r'\1 °C'),
            # Kein Leerzeichen nach Komma
            (r'([a-zäöüß](\]\])?,)((\[\[)?[a-zäöüA-ZÄÖÜ])', r'\1 \3'),
            # Leerzeichen und Komma vertauscht
            (r'([a-zäöüß](\]\])?) ,((\[\[)?[a-zäöüA-ZÄÖÜ])', r'\1, \3'),
            # Plenks (Leerzeichen vor Komma/Punkt/Ausrufezeichen/Fragezeichen)
            # Achtung bei Französisch:
            # https://de.wikipedia.org/wiki/Plenk#Franz.C3.B6sische_Sprache
            # Leerzeichen vor Doppelpunkt/Semikolon kann korrekt sein,
            # z.B. nach Quellenangaben
            (r'([a-zäöüß](\]\])?) ([,.!?]) ((\[\[)?[a-zäöüA-ZÄÖÜ])',
             r'\1\3 \4'),
        ],
        'exceptions': {
            'inside-tags': [
                'nowiki',
                'comment',
                'gallery',          # because of filenames
                'hyperlink',        # e.g. commas in URLs
                'math',
                'pre',              # because of code examples
                'startspace',       # because of code examples
                'syntaxhighlight',  # because of code examples
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
                # Variablen in der Mathematik
                # (unklar, ob Leerzeichen hier Pflicht sind)
                r'[xyz](,[xyz])+',
                # Definitionslisten, dort gibt es oft absichtlich Leerzeichen
                # vor Doppelpunkten
                r'(?m)^;(.*?)$',
                r'\d+h( |&nbsp;)\d+m',
                # Schreibweise für Zeiten, vor allem in Film-Infoboxen.
                # Nicht korrekt, aber dafür schön kurz.
                r'(?i)\[\[(Bild|Image|Media):.+?\|',  # Dateinamen auslassen
                r'{{bgc\|.*?}}',                      # Hintergrundfarbe
                r'<sup>\d+m</sup>',                   # bei chemischen Formeln
                r'\([A-Z][A-Za-z]*(,[A-Z][A-Za-z]*'
                r'(<sup>.*?</sup>|<sub>.*?</sub>|))+\)'
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
            (r'\[(?P<url>https?://[^\|\]\s]+?) *\| *(?P<label>[^\|\]]+?)\]',
             r'[\g<url> \g<label>]'),
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
                'startspace',       # because of code examples
                'syntaxhighlight',  # because of code examples
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
            (r'\[(?P<url>https?://[^\|\] \r\n]+?) +\| *(?P<label>[^\|\]]+?)\]',
             r'[\g<url> \g<label>]'),
            # dash in external link, where the correct end of the URL can
            # be detected from the file extension. It is very unlikely that
            # this will cause mistakes.
            (r'\[(?P<url>https?://[^\|\] ]+?'
             r'(\.pdf|\.html|\.htm|\.php|\.asp|\.aspx|\.jsp)) *\|'
             r' *(?P<label>[^\|\]]+?)\]', r'[\g<url> \g<label>]'),
        ],
        'exceptions': {
            'inside-tags': [
                'nowiki',
                'comment',
                'math',
                'pre',
                'startspace',       # because of code examples
                'syntaxhighlight',  # because of code examples
            ],
        }
    },

    'case-de': {  # German upper / lower case issues
        'regex': True,
        'msg': {
            'de': 'Bot: Korrigiere Groß-/Kleinschreibung',
        },
        'replacements': [
            (r'\batlantische(r|n|) Ozean', r'Atlantische\1 Ozean'),
            (r'\bdeutsche(r|n|) Bundestag\b', r'Deutsche\1 Bundestag'),
            # Aufpassen, z. B. 'deutsche Bundestagswahl'
            (r'\bdeutschen Bundestags\b', r'Deutschen Bundestags'),
            (r'\bdeutsche(r|n|) Reich\b', r'Deutsche\1 Reich'),
            # Aufpassen, z. B. 'deutsche Reichsgrenzen'
            (r'\bdeutschen Reichs\b', r'Deutschen Reichs'),
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
            'de': 'Bot: Ersetze Binde-/Gedankenstrich durch "bis"',
        },
        'replacements': [
            # Bindestrich, Gedankenstrich, Geviertstrich
            (r'(von \d{3,4}) *(-|&ndash;|–|&mdash;|—) *(\d{3,4})',
             r'\1 bis \3'),
        ],
    },

    # some disambiguation stuff for de:
    # python pwb.py replace -fix:music -subcat:Album
    'music': {
        'regex': False,
        'msg': {
            'de': 'Bot: korrigiere Links auf Begriffsklärungen',
        },
        'replacements': [
            ('[[CD]]', '[[Audio-CD|CD]]'),
            ('[[LP]]', '[[Langspielplatte|LP]]'),
            ('[[EP]]', '[[Extended Play|EP]]'),
            ('[[MC]]', '[[Musikkassette|MC]]'),
            ('[[Single]]', '[[Single (Musik)|Single]]'),
        ],
        'exceptions': {
            'inside-tags': [
                'hyperlink',
            ]
        }
    },

    # format of dates of birth and death, for de:
    # python pwb.py replace -fix:datum -ref:Vorlage:Personendaten
    'datum': {
        'regex': True,
        'msg': {
            'de': 'Bot: Korrigiere Datumsformat',
        },
        'replacements': [
            (r'\[\[(\d+\. (?:Januar|Februar|März|April|Mai|Juni|Juli|August|'
             r'September|Oktober|November|Dezember)) (\d{1,4})\]\]',
             r'[[\1]] [[\2]]'),
            # Keine führende Null beim Datum
            # (erst einmal nur bei fehlenden Leerzeichen)
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
        'generator': [
            r'-search:insource:/nowiki\>ISBN:? *(?:&nbsp;|&\#160;)? *[0-9]/',
            '-namespace:0'],
        'regex': True,
        'msg': 'pywikibot-fixes-isbn',
        'replacements': [
            # Remove colon between the word ISBN and the number
            (r'ISBN: (\d+)', r'ISBN \1'),
            # superfluous word "number"
            (r'ISBN(?: [Nn]umber| [Nn]o\.?|-Nummer|-Nr\.):? (\d+)',
             r'ISBN \1'),
            # Space, minus, dot, hyphen, en dash, em dash, etc. instead of
            # hyphen-minus as separator,
            # or spaces between digits and separators.
            # Note that these regular expressions also match valid ISBNs, but
            # these won't be changed.
            # These two regexes don't verify that the ISBN is of a valid format
            # but just change separators into normal hyphens. The isbn script
            # does checks and similar but does only match ISBNs with digits and
            # hyphens (and optionally a X/x at the end).
            (r'ISBN (978|979) *[\- −.‐-―] *(\d+) *[\- −.‐-―] *(\d+) '
             r'*[\- −.‐-―] *(\d+) *[\- −.‐-―] *(\d)(?!\d)',
             r'ISBN \1-\2-\3-\4-\5'),  # ISBN-13

            (r'ISBN (\d+) *[\- −.‐-―] *(\d+) *[\- −.‐-―] *(\d+) *'
             r'[\- −.‐-―] *(\d|X|x)(?!\d)',
             r'ISBN \1-\2-\3-\4'),  # ISBN-10
            # missing space before ISBN-10 or before ISBN-13,
            # or multiple spaces or non-breaking space.
            (r'ISBN(?: *|&nbsp;)((\d(-?)){12}\d|(\d(-?)){9}[\dXx])',
             r'ISBN \1'),
            # remove <nowiki /> tags
            (r'<nowiki>ISBN:? *(?:&nbsp;|&#160;)? *([0-9\-xX]+)</nowiki>',
             r'ISBN \1'),
        ],
        'exceptions': {
            'inside-tags': [
                'comment',
                'hyperlink',
            ],
            'inside': [
                r'ISBN (97[89]-?)(\d-?){9}\d',  # matches valid ISBN-13s
                r'ISBN (\d-?){9}[\dXx]',  # matches valid ISBN-10s
            ],
        }
    },

    # Typo corrections for Arabic Wikipedia and any Arabic wiki.
    # python pwb.py replace -fix:correct-ar -start:! -always

    'correct-ar': {
        'regex': False,
        'msg': {
            'ar': 'بوت: تدقيق إملائي',
        },
        'replacements': [
            (' إمرأة ', ' امرأة '),
            (' الى ', ' إلى '),
            (' إسم ', ' اسم '),
            (' الأن ', ' الآن '),
            (' اول ', ' أول '),
            (' الة ', ' آلة '),
            (' فى ', ' في '),
            (' اثقل ', ' أثقل '),
            (' إبن ', ' ابن '),
            (' إبنة ', ' ابنة '),
            (' إقتصاد ', ' اقتصاد '),
            (' إجتماع ', ' اجتماع '),
            (' انجيل ', ' إنجيل '),
            (' اجماع ', ' إجماع '),
            (' امريكا ', ' أمريكا '),
            (' اوروبا ', ' أوروبا '),
            (' انجلترا ', ' إنجلترا '),
            (' اكتوبر ', ' أكتوبر '),
            (' اسرائيل ', ' إسرائيل '),
            (' المانيا ', ' ألمانيا '),
            (' ايطاليا ', ' إيطاليا '),
            (' ايران ', ' إيران '),
            (' إستخراج ', ' استخراج '),
            (' إستعمال ', ' استعمال '),
            (' إستبدال ', ' استبدال '),
            (' إشتراك ', ' اشتراك '),
            (' إستعادة ', ' استعادة '),
            (' إستقلال ', ' استقلال '),
            (' إنتقال ', ' انتقال '),
            (' إتحاد ', ' اتحاد '),
            (' الإتحاد ', ' الاتحاد '),
            (' املاء ', ' إملاء '),
            (' إستخدام ', ' استخدام '),
            (' أحدى ', ' إحدى '),
            (' لاكن ', ' لكن '),
            (' الاردن ', ' الأردن '),
            (' إثنان ', ' اثنان '),
            (' شيئ ', ' شيء '),
            (' إحتياط ', ' احتياط '),
            (' إقتباس ', ' اقتباس '),
            (' الامارات ', ' الإمارات '),
            (' اكثر ', ' أكثر '),
            (' افضل ', ' أفضل '),
            (' اكبر ', ' أكبر '),
            (' اشهر ', ' أشهر '),
            (' ادارة ', ' إدارة '),
            (' ابناء ', ' أبناء '),
            (' الانصار ', '  الأنصار '),
            (' اشارة ', ' إشارة '),
            (' إقرأ ', ' اقرأ '),
            (' إمتياز ', ' امتياز '),
            (' ارق ', ' أرق '),
            (' أرثوذوكس ', ' أرثوذكس '),
            (' الأرثوذوكس ', ' الأرثوذكس '),
            (' أرثوذوكسية ', ' أرثوذكسية '),
            (' الأرثوذوكسية ', ' الأرثوذكسية '),
            (' الأرثوذوكسي ', ' الأرثوذكسي '),
            (' ارثوذوكس ', ' أرثوذكس '),
            (' ارثوذوكسي ', ' أرثوذكسي '),
            (' ارثوذوكسية ', ' أرثوذكسية '),
            (' الارثوذوكسية ', ' الأرثوذكسية '),
            (' اللة ', ' الله '),
            (' إختبار ', ' اختبار '),
            (' ارسال ', ' إرسال '),
            (' إتصالات ', ' اتصالات '),
            (' اسامة ', ' أسامة '),
            (' ابراهيم ', ' إبراهيم '),
            (' اسماعيل ', ' إسماعيل '),
            (' ايوب ', ' أيوب '),
            (' ايمن ', ' أيمن '),
            (' ابو ', ' أبو '),
            (' ابا ', ' أبا '),
            (' اخو ', ' أخو '),
            (' اخا ', ' أخا '),
            (' اخي ', ' أخي '),
            (' احد ', ' أحد '),
            (' اربعاء ', ' أربعاء '),
            (' اهم ', ' أهم '),
            (' اوزبكستان ', ' أوزبكستان '),
            (' اذربيجان ', ' أذربيجان '),
            (' افغانستان ', ' أفغانستان '),
            (' امجد ', ' أمجد '),
            (' اوسط ', ' أوسط '),
            (' اشقر ', ' أشقر '),
            (' انور ', ' أنور '),
            (' اصعب ', ' أصعب '),
            (' اسهل ', ' أسهل '),
            (' اجمل ', ' أجمل '),
            (' اقبح ', ' أقبح '),
            (' اطول ', ' أطول '),
            (' اقصر ', ' أقصر '),
            (' اسمن ', ' أسمن '),
            (' اذكى ', ' أذكى '),
            (' اماني ', ' أماني '),
            (' احلام ', ' أحلام '),
            (' اسماء ', ' أسماء '),
            (' ابطأ ', ' أبطأ '),
            (' اوربا ', ' أوروبا '),
            (' أوربا ', ' أوروبا '),
            (' امريكي ', ' أمريكي '),
            (' امريكية ', ' أمريكية '),
            (' امريكيان ', ' أمريكيان '),
            (' امريكيتان ', ' أمريكيتان '),
            (' امريكيون ', ' أمريكيون '),
            (' امريكيات ', ' أمريكيات '),
            (' الامريكي ', ' الأمريكي '),
            (' الامريكية ', ' الأمريكية '),
            (' الامريكيان ', ' الأمريكيان '),
            (' الامريكيتان ', ' الأمريكيتان '),
            (' الامريكيون ', ' الأمريكيون '),
            (' الامريكيات ', ' الأمريكيات '),
            (' اوروبي ', ' أوروبي '),
            (' اوروبية ', ' أوروبية '),
            (' اوروبيان ', ' أوروبيان '),
            (' اوروبيتان ', ' أوروبيتان '),
            (' اوروبيون ', ' أوروبيون '),
            (' اوروبيات ', ' أوروبيات '),
            (' الاوروبي ', ' الأوروبي '),
            (' الاوروبية ', ' الأوروبية '),
            (' الاوروبيان ', ' الأوروبيان '),
            (' الاوروبيتان ', ' الأوروبيتان '),
            (' الاوروبيون ', ' الأوروبيون '),
            (' الاوروبيات ', ' الأوروبيات '),
            (' اسرائيلي ', ' إسرائيلي '),
            (' اسرائيلية ', ' إسرائيلية '),
            (' اسرائيليان ', ' إسرائيليان '),
            (' اسرائيليتان ', ' إسرائيليتان '),
        ],
        'exceptions': {
            'inside-tags': [
                'file',         # because of filenames
                'gallery',      # because of filenames
                'header',       # section headers
                'hyperlink',    # URLs
                'interwiki',
                'ref',
            ],
        }
    },
    # TODO: Support dynamic replacement from Special pages to the localized one
    'specialpages': {
        'regex': False,
        'msg': {
            'ar': 'روبوت: إصلاح حالة حروف الصفحات الخاصة',
            'arz': 'روبوت: تصليح حاله الحروف بتاعه الصفحات الخصوصيه',
            'en': 'Robot: Fixing special page capitalisation',
            'fa': 'ربات: تصحیح بزرگی و کوچکی حروف صفحه‌های ویژه',
        },
        'replacements': [
            ('Special:Allpages',        'Special:AllPages'),
            ('Special:Blockip',         'Special:BlockIP'),
            ('Special:Blankpage',       'Special:BlankPage'),
            ('Special:Filepath',        'Special:FilePath'),
            ('Special:Globalusers',     'Special:GlobalUsers'),
            ('Special:Imagelist',       'Special:ImageList'),
            ('Special:Ipblocklist',     'Special:IPBlockList'),
            ('Special:Listgrouprights', 'Special:ListGroupRights'),
            ('Special:Listusers',       'Special:ListUsers'),
            ('Special:Newimages',       'Special:NewImages'),
            ('Special:Prefixindex',     'Special:PrefixIndex'),
            ('Special:Protectedpages',  'Special:ProtectedPages'),
            ('Special:Recentchanges',   'Special:RecentChanges'),
            ('Special:Specialpages',    'Special:SpecialPages'),
            ('Special:Unlockdb',        'Special:UnlockDB'),
            ('Special:Userlogin',       'Special:UserLogin'),
            ('Special:Userlogout',      'Special:UserLogout'),
            ('Special:Whatlinkshere',   'Special:WhatLinksHere'),
        ],
    },
    # yu top-level domain will soon be disabled, see
    # https://lists.wikimedia.org/pipermail/wikibots-l/2009-February/000290.html
    # The following are domains that are often-used.
    'yu-tld': {
        'regex': False,
        'nocase': True,
        'msg': {
            'ar':  'روبوت: إصلاح الوصلات إلى نطاقات .yu',
            'arz':  'روبوت: تصليح اللينكات للدومين .yu',
            'de':  'Bot: Ersetze Links auf .yu-Domains',
            'en':  'Robot: Replacing links to .yu domains',
            'fa':  'ربات: جایگزینی پیوندها به دامنه‌ها با پسوند yu',
            'fr':  ('Robot: Correction des liens pointant vers le domaine '
                    '.yu, qui expire en 2009'),
            'ksh': 'Bot: de ahle .yu-Domains loufe us, dröm ußjetuusch',
            'sr': 'Бот: Исправљање линкова ка .yu домену',
        },
        'replacements': [
            ('www.budva.cg.yu',             'www.budva.rs'),
            ('spc.org.yu',                  'spc.rs'),
            ('www.oks.org.yu',              'www.oks.org.rs'),
            ('www.kikinda.org.yu',          'www.kikinda.rs'),
            ('www.ds.org.yu',               'www.ds.org.rs'),
            ('www.nbs.yu',                  'www.nbs.rs'),
            ('www.serbia.sr.gov.yu',        'www.srbija.gov.rs'),
            ('eunet.yu',                    'eunet.rs'),
            ('www.zastava-arms.co.yu',      'www.zastava-arms.co.rs'),
            ('www.airportnis.co.yu',        'www.airportnis.rs'),
            ('www.belex.co.yu',             'www.belex.rs'),
            ('beograd.org.yu',              'beograd.rs'),
            ('www.vlada.cg.yu',             'www.vlada.me'),
            ('webrzs.statserb.sr.gov.yu',   'webrzs.stat.gov.rs'),
            ('www.statserb.sr.gov.yu',      'webrzs.stat.gov.rs'),
            ('www.rastko.org.yu',           'www.rastko.org.rs'),
            ('www.reprezentacija.co.yu',    'www.reprezentacija.rs'),
            ('www.blic.co.yu',              'www.blic.co.rs'),
            ('www.beograd.org.yu',          'www.beograd.org.rs'),
            ('arhiva.glas-javnosti.co.yu',  'arhiva.glas-javnosti.rs'),
            ('www.srpsko-nasledje.co.yu',   'www.srpsko-nasledje.co.rs'),
            ('www.dnevnik.co.yu',           'www.dnevnik.rs'),
            ('www.srbija.sr.gov.yu',        'www.srbija.gov.rs'),
            ('www.kurir-info.co.yu/Arhiva', 'arhiva.kurir-info.rs/Arhiva'),
            ('www.kurir-info.co.yu/arhiva', 'arhiva.kurir-info.rs/arhiva'),
            ('www.kurir-info.co.yu',        'www.kurir-info.rs'),
            ('arhiva.kurir-info.co.yu',     'arhiva.kurir-info.rs'),
            ('www.prvaliga.co.yu',          'www.prvaliga.rs'),
            ('www.mitropolija.cg.yu',       'www.mitropolija.me'),
            ('www.spc.yu/sr',               'www.spc.rs/sr'),
            ('www.sk.co.yu',                'www.sk.co.rs'),
            ('www.ekoforum.org.yu',         'www.ekoforum.org'),
            ('www.svevlad.org.yu',          'www.svevlad.org.rs'),
            ('www.posta.co.yu',             'www.posta.rs'),
            ('www.glas-javnosti.co.yu',     'www.glas-javnosti.rs'),
            ('www.fscg.cg.yu',              'www.fscg.co.me'),
            ('ww1.rts.co.yu/euro',          'ww1.rts.co.rs/euro'),
            ('www.rtv.co.yu',               'www.rtv.rs'),
            ('www.politika.co.yu',          'www.politika.rs'),
            ('www.mfa.gov.yu',              'www.mfa.gov.rs'),
            ('www.drzavnauprava.sr.gov.yu', 'www.drzavnauprava.gov.rs'),
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


def _load_file(filename: str) -> bool:
    """Load the fixes from the given filename."""
    if os.path.exists(filename):
        # load binary, to let compile decode it according to the file header
        with open(filename, 'rb') as f:
            exec(compile(f.read(), filename, 'exec'), globals())
        return True

    return False


# Load the user fixes file.
filename = config.datafilepath('user-fixes.py')
user_fixes_loaded = _load_file(filename)
