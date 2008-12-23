# -*- coding: utf-8  -*-
""" File containing all standard fixes """
__version__ = '$Id$'

help = """
                       * HTML       -  Convert HTML tags to wiki syntax, and
                                       fix XHTML.
                       * isbn        - Fix badly formatted ISBNs.
                       * syntax     -  Try to fix bad wiki markup. Do not run
                                       this in automatic mode, as the bot may
                                       make mistakes.
                       * syntax-safe - Like syntax, but less risky, so you can
                                       run this in automatic mode.
                       * case-de     - fix upper/lower case errors in German
                       * grammar-de  - fix grammar and typography in German
"""

fixes = {
    # These replacements will convert HTML to wiki syntax where possible, and
    # make remaining tags XHTML compliant.
    'HTML': {
        'regex': True,
        'msg': {
            'ar':u'روبوت: تحويل/تصليح HTML',
            'en':u'Robot: converting/fixing HTML',
            'de':u'Bot: konvertiere/korrigiere HTML',
            'fr':u'Robot: convertit/fixe HTML',
            'he':u'בוט: ממיר/מתקן HTML',
            'ja':u'ロボットによる: HTML転換',
            'ia':u'Robot: conversion/reparation de HTML',
            'lt':u'robotas: konvertuojamas/taisomas HTML',
            'nl':u'Bot: conversie/reparatie HTML',
            'pl':u'Robot konwertuje/naprawia HTML',
            'pt':u'Bot: Corrigindo HTML',
            'sr':u'Бот: Поправка HTML-а',
            'sv': u'Bot: Konverterar/korrigerar HTML',
            'zh':u'機器人: 轉換HTML',
        },
        'replacements': [
            # Everything case-insensitive (?i)
            # Keep in mind that MediaWiki automatically converts <br> to <br />
            # when rendering pages, so you might comment the next two lines out
            # to save some time/edits.
            #r'(?i)<br>':                      r'<br />',
            # linebreak with attributes
            #r'(?i)<br ([^>/]+?)>':            r'<br \1 />',
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
            'de':u'Bot: korrigiere Grammatik',
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
            (u'(?<!\w)(\d+|\d+[\.,]\d+)° C(?=\W|²|³|$)',          ur'\1 °C'),
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
                r'<code>.*</code>', # because of code examples
                r'{{[Zz]itat\|.*?}}',
                ur'{{§\|.*?}}',  # Gesetzesparagraph
                ur'§ ?\d+[a-z]',  # Gesetzesparagraph
                r'Ju 52/1m', # Flugzeugbezeichnung
                r'Ju 52/3m', # Flugzeugbezeichnung
                r'AH-1W',    # Hubschrauberbezeichnung
                r'ZPG-3W',   # Luftschiffbezeichnung
                r'8mm',      # Filmtitel
                r'802.11g',  # WLAN-Standard
                r'DOS/4GW',  # Software
                r'ntfs-3g',  # Dateisystem-Treiber
                r'/\w(,\w)*/',     # Laut-Aufzählung in der Linguistik
                r'[xyz](,[xyz])+', # Variablen in der Mathematik (unklar, ob Leerzeichen hier Pflicht sind)
                r'(?m)^;(.*?)$', # Definitionslisten, dort gibt es oft absichtlich Leerzeichen vor Doppelpunkten
                r'\d+h( |&nbsp;)\d+m', # Schreibweise für Zeiten, vor allem in Film-Infoboxen. Nicht korrekt, aber dafür schön kurz.
                r'(?i)\[\[(Bild|Image|Media):.+?\|', # Dateinamen auslassen
                r'{{bgc\|.*?}}',  # Hintergrundfarbe
                r'<sup>\d+m</sup>',                   # bei chemischen Formeln
                r'\([A-Z][A-Za-z]*(,[A-Z][A-Za-z]*(<sup>.*?</sup>|<sub>.*?</sub>|))+\)' # chemische Formel, z. B. AuPb(Pb,Sb,Bi)Te. Hier sollen keine Leerzeichen hinter die Kommata.
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
            'ar':u'بوت: تصليح تهيئة الويكي',
            'de':u'Bot: Korrigiere Wiki-Syntax',
            'en':u'Bot: Fixing wiki syntax',
            'fr':u'Bot: Corrige wiki-syntaxe',
            'he':u'בוט: מתקן תחביר ויקי',
            'ia':u'Robot: Reparation de syntaxe wiki',
            'ja':u'ロボットによる: wiki構文修正',
            'lt':u'robotas: Taisoma wiki sintaksė',
            'nl':u'Bot: reparatie wikisyntaxis',
            'pl':u'Robot poprawia wiki-składnię',
            'pt':u'Bot: Corrigindo sintaxe wiki',
            'sr':u'Бот: Поправка вики синтаксе',
            'zh':u'機器人: 修正wiki語法',
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
                r'http://.*?object=tx\|',               # regular dash in URL
                r'http://.*?allmusic\.com',             # regular dash in URL
                r'http://.*?allmovie\.com',             # regular dash in URL
                r'http://physics.nist.gov/',            # regular dash in URL
                r'http://www.forum-seniorenarbeit.de/', # regular dash in URL
                r'http://kuenstlerdatenbank.ifa.de/',   # regular dash in URL
                r'&object=med',                         # regular dash in URL
                r'\[CDATA\['                            # lots of brackets
            ],
        }
    },

    # The same as syntax, but restricted to replacements that should
    # be safe to run automatically.
    'syntax-safe': {
        'regex': True,
        'msg': {
            'ar':u'بوت: تصليح تهيئة الويكي',
            'de':u'Bot: Korrigiere Wiki-Syntax',
            'en':u'Bot: Fixing wiki syntax',
            'fr':u'Bot: Corrige wiki-syntaxe',
            'he':u'בוט: מתקן תחביר ויקי',
            'ia':u'Robot: Reparation de syntaxe wiki',
            'ja':u'ロボットによる: wiki構文修正',
            'lt':u'robotas: Taisoma wiki sintaksė',
            'nl':u'Bot: reparatie wikisyntaxis',
            'pl':u'Robot poprawia wiki-składnię',
            'pt':u'Bot: Corrigindo sintaxe wiki',
            'sr':u'Бот: Поправка вики синтаксе',
            'zh':u'機器人: 修正wiki語法',
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

    'case-de': { # German upper / lower case issues
        'regex': True,
        'msg': {
            'de':u'Bot: Korrigiere Groß-/Kleinschreibung',
        },
        'replacements': [
            (r'\batlantische(r|n|) Ozean', r'Atlantische\1 Ozean'),
            (r'\bdeutsche(r|n|) Bundestag\b', r'Deutsche\1 Bundestag'),
            (r'\bdeutschen Bundestags\b', r'Deutschen Bundestags'), # Aufpassen, z. B. 'deutsche Bundestagswahl'
            (r'\bdeutsche(r|n|) Reich\b', r'Deutsche\1 Reich'),
            (r'\bdeutschen Reichs\b', r'Deutschen Reichs'), # Aufpassen, z. B. 'deutsche Reichsgrenzen'
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
            'de':u'Bot: Ersetze Binde-/Gedankenstrich durch "bis"',
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
            'de':u'Bot: korrigiere Links auf Begriffsklärungen',
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
                r'\[\[20. Juli 1944\]\]', # Hitler-Attentat
                r'\[\[17. Juni 1953\]\]', # Ost-Berliner Volksaufstand
                r'\[\[1. April 2000\]\]', # Film
                r'\[\[11. September 2001\]\]', # Anschläge in den USA
                r'\[\[7. Juli 2005\]\]',  # Terroranschläge in Spanien
            ],
        }
    },

    'isbn': {
        'regex': True,
        'msg': {
            'ar': u'روبوت: تصليح صيغة ISBN',
            'de': u'Bot: Korrigiere ISBN-Format',
            'en': u'Robot: Fixing ISBN format',
            'es': u'Arreglando formato ISBN',
            'he': u'בוט: מתקן פורמט ISBN',
            'ja': u'ロボットによる: ISBNフォーマット修正',
            'zh': u'機器人: 修正ISBN格式',
        },
        'replacements': [
            # colon
            (r'ISBN: (\d+)', r'ISBN \1'),
            # Spaces, dashes, or dots instead of hyphens as separators,
            # or spaces between digits and separators.
            # Note that these regular expressions also match valid ISBNs, but
            # these won't be changed.
            (ur'ISBN (978|979) *[\- –\.] *(\d+) *[\- –\.] *(\d+) *[\- –\.] *(\d+) *[\- –\.] *(\d)(?!\d)', r'ISBN \1-\2-\3-\4-\5'), # ISBN13
            (ur'ISBN (\d+) *[\- –\.] *(\d+) *[\- –\.] *(\d+) *[\- –\.] *(\d|X|x)(?!\d)', r'ISBN \1-\2-\3-\4'), # ISBN10
        ],
        'exceptions': {
            'inside-tags': [
                'comment',
            ],
            'inside': [
                r'ISBN (\d(-?)){12}\d',    # matches valid ISBN-13s
                r'ISBN (\d(-?)){9}[\dXx]', # matches valid ISBN-10s
            ],
        }
    },

    #Corrections for Arabic Wikipedia and any Arabic wiki.
    #python replace.py -always -start:! -fix:correct-ar

    'correct-ar': {
        'regex': True,
        'msg': {
            'ar':u'تدقيق إملائي. 528 كلمة مستهدفة حاليًا.',
        },
        'replacements': [
            #(u' ,', u' ،'), #FIXME: Do not replace comma in non-Arabic text, interwiki, image links or <math> syntax.
            (ur'\bإمرأة\b', u'امرأة'),
            (ur'\bالى\b', ur'إلى'),
            (ur'\bإسم\b', u'اسم'),
            (ur'\bالأن\b', u'الآن'),
            (ur'\bالة\b', u'آلة'),
            (ur'\bفى\b', u'في'),
            (ur'\bإبن\b', u'ابن'),
            (ur'\bإبنة\b', u'ابنة'),
            (ur'\bإقتصاد\b', u'اقتصاد'),
            (ur'\bإجتماع\b', u'اجتماع'),
            (ur'\bانجيل\b', u'إنجيل'),
            (ur'\bاجماع\b', u'إجماع'),
            (ur'\bاكتوبر\b', u'أكتوبر'),
            (ur'\bإستخراج\b', u'استخراج'),
            (ur'\bإستعمال\b', u'استعمال'),
            (ur'\bإستبدال\b', u'استبدال'),
            (ur'\bإشتراك\b', u'اشتراك'),
            (ur'\bإستعادة\b', u'استعادة'),
            (ur'\bإستقلال\b', u'استقلال'),
            (ur'\bإنتقال\b', u'انتقال'),
            (ur'\bإتحاد\b', u'اتحاد'),
            (ur'\bاملاء\b', u'إملاء'),
            (ur'\bإستخدام\b', u'استخدام'),
            (ur'\bأحدى\b', u'إحدى'),
            (ur'\bلاكن\b', u'لكن'),
            (ur'\bإثنان\b', u'اثنان'),
            (ur'\bشيئ\b', u'شيء'),
            (ur'\bإحتياط\b', u'احتياط'),
            (ur'\bإقتباس\b', u'اقتباس'),
            (ur'\bادارة\b', u'إدارة'),
            (ur'\bابناء\b', u'أبناء'),
            (ur'\bالانصار\b', u'الأنصار'),
            (ur'\bاشارة\b', u'إشارة'),
            (ur'\bإقرأ\b', u'اقرأ'),
            (ur'\bإمتياز\b', u'امتياز'),
            (ur'\bارق\b', u'أرق'),
            (ur'\bاللة\b', u'الله'),
            (ur'\bإختبار\b', u'اختبار'),
            (ur'==[ ]?روابط خارجية[ ]?==', u'== وصلات خارجية =='),
            (ur'\bارسال\b', u'إرسال'),
            (ur'\bإتصالات\b', u'اتصالات'),
            (ur'\bابو\b', u'أبو'),
            (ur'\bابا\b', u'أبا'),
            (ur'\bاخو\b', u'أخو'),
            (ur'\bاخا\b', u'أخا'),
            (ur'\bاخي\b', u'أخي'),
            (ur'\bاحد\b', u'أحد'),
            (ur'\bاربعاء\b', u'أربعاء'),
            #(ur'\bاول\b', u'أول'), #FIXME: Do not replace this (and all others) in interwiki links. This is an Arabic typo, but it is correct in Farsi.
            (ur'\b(ال|)اهم\b', ur'\1أهم'),
            (ur'\b(ال|)اثقل\b', ur'\1أثقل'),
            (ur'\b(ال|)امجد\b', ur'\1أمجد'),
            (ur'\b(ال|)اوسط\b', ur'\1أوسط'),
            (ur'\b(ال|)اشقر\b', ur'\1أشقر'),
            (ur'\b(ال|)انور\b', ur'\1أنور'),
            (ur'\b(ال|)اصعب\b', ur'\1أصعب'),
            (ur'\b(ال|)اسهل\b', ur'\1أسهل'),
            (ur'\b(ال|)اجمل\b', ur'\1أجمل'),
            (ur'\b(ال|)اقبح\b', ur'\1أقبح'),
            (ur'\b(ال|)اطول\b', ur'\1أطول'),
            (ur'\b(ال|)اقصر\b', ur'\1أقصر'),
            (ur'\b(ال|)اسمن\b', ur'\1أسمن'),
            (ur'\b(ال|)اذكى\b', ur'\1أذكى'),
            (ur'\b(ال|)اكثر\b', ur'\1أكثر'),
            (ur'\b(ال|)افضل\b', ur'\1أفضل'),
            (ur'\b(ال|)اكبر\b', ur'\1أكبر'),
            (ur'\b(ال|)اشهر\b', ur'\1أشهر'),
            (ur'\b(ال|)ابطأ\b', ur'\1أبطأ'),
            (ur'\b(ال|)اماني\b', ur'\1أماني'),
            (ur'\b(ال|)احلام\b', ur'\1أحلام'),
            (ur'\b(ال|)اسماء\b', ur'\1أسماء'),
            (ur'\b(ال|)اسامة\b', ur'\1أسامة'),
            (ur'\bابراهيم\b', u'إبراهيم'),
            (ur'\bاسماعيل\b', u'إسماعيل'),
            (ur'\bايوب\b', u'أيوب'),
            (ur'\bايمن\b', u'أيمن'),
            (ur'\bاوزبكستان\b', u'أوزبكستان'),
            (ur'\bاذربيجان\b', u'أذربيجان'),
            (ur'\bافغانستان\b', u'أفغانستان'),
            (ur'\bانجلترا\b', u'إنجلترا'),
            (ur'\bايطاليا\b', u'إيطاليا'),
            (ur'\bاوربا\b', u'أوروبا'),
            (ur'\bأوربا\b', u'أوروبا'),
            (ur'\bاوغندة\b', u'أوغندة'),
            (ur'\b(ال|)ا(لماني|فريقي|سترالي)(ا|ة|تان|ان|ين|ي|ون|و|ات|)\b', ur'\1أ\2\3'),
            (ur'\b(ال|)ا(وروب|مريك)(ا|ي|ية|يتان|يان|يين|يي|يون|يو|يات|)\b', ur'\1أ\2\3'),
            (ur'\b(ال|)ا(ردن|رجنتين|وغند|سبان|وكران|فغان)(ي|ية|يتان|يان|يين|يي|يون|يو|يات|)\b', ur'\1أ\2\3'),
            (ur'\b(ال|)ا(سرائيل|يران|مارات|نكليز|نجليز)(ي|ية|يتان|يان|يين|يي|يون|يو|يات|)\b', ur'\1إ\2\3'),
            (ur'\b(ال|)(ا|أ)(رثوذكس|رثوذوكس)(ي|ية|يتان|يان|يين|يي|يون|يو|يات|)\b', ur'\1أرثوذكس\4'),
            (ur'\bإست(عمل|خدم|مر|مد|مال|عاض|قام|حال|جاب|قال|زاد|عان|طال)(ت|ا|وا|)\b', ur'است\1\2'),
            (ur'\bإست(حال|قال|طال|زاد|عان|قام|راح|جاب|عاض|مال)ة\b', ur'است\1ة'),
        ]
    },
    'specialpages': {
        'regex': False,
        'msg': {
            'en': u'Robot: Fixing special page capitalisation',
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
}

#
# Load the user fixes file.

from pywikibot import config

try:
    execfile(config.datafilepath("user-fixes.py"))
except IOError:
    pass
