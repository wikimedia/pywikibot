# -*- coding: utf-8  -*-
import family
    
# The Uncyclopaedia family, a satirical set of encyclopaedia wikis.
#

class Family(family.Family):
    def __init__(self):
        family.Family.__init__(self)
        self.name = 'uncyclopedia'
    
        self.langs = {
            "ar": "beidipedia.wikia.com",
            "ast": "nunyepedia.wikia.com",
            "ca": "valenciclopedia.wikia.com",
            "cs": "necyklopedie.wikia.com",
            "da": "spademanns.wikia.com",
            "de": "de.uncyclopedia.org",
            "el": "frikipaideia.wikia.com", 
            "en": "uncyclopedia.org", 
            "eo": "neciklopedio.wikia.com", 
            "es": "inciclopedia.wikia.com", 
            "fa": "fa.uncyc.org", 
            "fi": "hiki.pedia.ws", 
            "fr": "desencyclopedie.wikia.com", 
            "he": "eincyclopedia.wikia.com", 
            "hr": "hr.neciklopedija.org", 
            "hu": "unciklopedia.org", 
            "id": "tolololpedia.wikia.com", 
            "it": "nonciclopedia.wikia.com", 
            "ja": "ja.uncyclopedia.info", 
            "ko": "ko.uncyclopedia.info", 
            "la": "uncapaedia.wikia.com", 
            "lt": "nesamopedija.wikia.com", 
            "lv": "lv.neciklopedija.org", 
            "nl": "oncyclopedia.net", 
            "nn": "ikkepedia.org", 
            "no": "ikkepedia.wikia.com", 
            "pl": "nonsensopedia.wikia.com", 
            "pt": "desciclo.pedia.ws", 
            "ru": "absurdopedia.wikia.com", 
            "sk": "necyklopedia.wikia.com", 
            "sl": "butalo.pedija.org", 
            "sr": "sr.neciklopedija.org", 
            "sv": "psyklopedin.org", 
            "th": "th.uncyclopedia.info", 
            "tr": "yansiklopedi.org", 
            "yi": "keinziklopedie.wikia.com", 
            "zh": "zh.uncyclopedia.wikia.com", 
            "zh-hk": "zh.uncyclopedia.info", 
            "zh-tw": "zh.uncyclopedia.info",
        }
    
        # Most namespaces are inherited from family.Family.
        self.namespaces[1] = {
            '_default': u'Talk',
            'ar': u'نقاش',
            'ca': u'Discussió',
            'da': u'Diskussion',
            'de': u'Diskussion',
            'el': u'Συζήτηση',
            'en': u'Talk',
            'es': u'Discusión',
            'fi': u'Keskustelu',
            'fr': u'Discuter',
            'he': u'שיחה',
            'it': u'Discussione',
            'la': u'Disputatio',
            'no': u'Diskusjon',
            'pl': u'Dyskusja',
            'pt': u'Discussão',
            'ru': u'Обсуждение',
            'sv': u'Diskussion',
            'zh-tw': u'討論',
        }

        self.namespaces[2] = {
            '_default': u'User',
            'ar': u'مستخدم',
            'ca': u'Usuari',
            'da': u'Bruger',
            'de': u'Benutzer',
            'el': u'Χρήστης',
            'en': u'User',
            'es': u'Usuario',
            'fi': u'Käyttäjä',
            'fr': u'Utilisateur',
            'he': u'משתמש',
            'it': u'Utente',
            'la': u'Usor',
            'no': u'Bruker',
            'pl': u'Użytkownik',
            'pt': u'Usuário',
            'ru': u'Участник',
            'sv': u'Användare',
            'zh-tw': u'用戶',
        }

        self.namespaces[3] = {
            '_default': u'User talk',
            'ar': u'نقاش المستخدم',
            'ca': u'Usuari Discussió',
            'da': u'Bruger diskussion',
            'de': u'Benutzer Diskussion',
            'el': u'Συζήτηση χρήστη',
            'en': u'User talk',
            'es': u'Usuario Discusión',
            'fi': u'Keskustelu käyttäjästä',
            'fr': u'Discussion Utilisateur',
            'he': u'שיחת משתמש',
            'it': u'Discussioni utente',
            'la': u'Disputatio Usoris',
            'no': u'Brukerdiskusjon',
            'pl': u'Dyskusja użytkownika',
            'pt': u'Usuário Discussão',
            'ru': u'Обсуждение участника',
            'sv': u'Användardiskussion',
            'zh-tw': u'用戶討論',
        }

        self.namespaces[4] = {
            '_default': u'Uncyclopedia',
            'ar': u'ويكيبيديا',
            'ca': u'Valenciclopèdia',
            'da': u'Spademanns Leksikon',
            'de': u'Uncyclopedia',
            'el': u'Ανεγκυκλοπαίδεια',
            'en': u'Uncyclopedia',
            'es': u'Inciclopedia',
            'fi': u'Hikipedia',
            'fr': u'Désencyclopédie',
            'he': u'איןציקלופדיה',
            'it': u'Nonciclopedia',
            'la': u'Uncapaedia',
            'no': u'Wikipedia',
            'pl': u'Nonsensopedia',
            'pt': u'Desciclopédia',
            'ru': u'Абсурдопедия',
            'sv': u'Psykelopedia',
            'zh': u'伪基百科',
            'zh-tw': u'偽基百科',
        }
        self.namespaces[5] = {
            '_default': u'Uncyclopedia talk',
            'ar': u'نقاش ويكيبيديا',
            'ca': u'Valenciclopèdia Discussió',
            'da': u'Spademanns Leksikon diskussion',
            'de': u'Uncyclopedia Diskussion',
            'el': u'Ανεγκυκλοπαίδεια συζήτηση',
            'en': u'Uncyclopedia talk',
            'es': u'Inciclopedia Discusión',
            'fi': u'Keskustelu Hikipediasta',
            'fr': u'Discussion Désencyclopédie',
            'he': u'שיחת איןציקלופדיה',
            'it': u'Discussioni Nonciclopedia',
            'la': u'Disputatio Uncapaediae',
            'no': u'Wikipedia-diskusjon',
            'pl': u'Dyskusja Nonsensopedia',
            'pt': u'Desciclopédia Discussão',
            'ru': u'Обсуждение Абсурдопедии',
            'sv': u'Psykelopediadiskussion',
            'zh': u'伪基百科 talk',
            'zh-tw': u'偽基百科討論',
        }

        self.namespaces[6] = {
            '_default': u'Image',
            'ar': u'صورة',
            'ca': u'Imatge',
            'da': u'Billede',
            'de': u'Bild',
            'el': u'Εικόνα',
            'es': u'Imagen',
            'fi': u'Kuva',
            'he': u'תמונה',
            'it': u'Immagine',
            'la': u'Imago',
            'no': u'Bilde',
            'pl': u'Grafika',
            'pt': u'Imagem',
            'ru': u'Изображение',
            'sv': u'Bild',
            'zh-tw': u'圖像',
        }

        self.namespaces[7] = {
            '_default': u'Image talk',
            'ar': u'نقاش الصورة',
            'ca': u'Imatge Discussió',
            'da': u'Billede diskussion',
            'de': u'Bild Diskussion',
            'el': u'Συζήτηση εικόνας',
            'es': u'Imagen Discusión',
            'fi': u'Keskustelu kuvasta',
            'fr': u'Discussion Image',
            'he': u'שיחת תמונה',
            'it': u'Discussioni immagine',
            'la': u'Disputatio Imaginis',
            'no': u'Bildediskusjon',
            'pl': u'Dyskusja grafiki',
            'pt': u'Imagem Discussão',
            'ru': u'Обсуждение изображения',
            'sv': u'Bilddiskussion',
            'zh-tw': u'圖像討論',
        }

        self.namespaces[8] = {
            '_default': u'MediaWiki',
            'ar': u'ميدياويكي',
            'he': u'מדיה ויקי',
            'zh-tw': u'媒體維基',
        }

        self.namespaces[9] = {
            '_default': u'MediaWiki talk',
            'ar': u'نقاش ميدياويكي',
            'ca': u'MediaWiki Discussió',
            'da': u'MediaWiki diskussion',
            'de': u'MediaWiki Diskussion',
            'es': u'MediaWiki Discusión',
            'fr': u'Discussion MediaWiki',
            'he': u'שיחת מדיה ויקי',
            'it': u'Discussioni MediaWiki',
            'la': u'Disputatio MediaWiki',
            'no': u'MediaWiki-diskusjon',
            'pl': u'Dyskusja MediaWiki',
            'pt': u'MediaWiki Discussão',
            'ru': u'Обсуждение MediaWiki',
            'sv': u'MediaWiki diskussion',
            'zh-tw': u'媒體維基討論',
        }

        #
        # Custom namespace list for en: (and fi:)
        #
        self.namespaces[100] = {
            '_default':u'Wilde',
            'en':u'Wilde',
            'fi':u'Hikiquote',
        }
        self.namespaces[101] = {
            '_default':u'Wilde talk',
            'en':u'Wilde talk',
            'fi':u'Hiktionary'
        }
        self.namespaces[102] = {
            '_default':u'UnNews',
            'en':u'UnNews',
            'fi':u'Hikikirjasto'
        }
        self.namespaces[103] = {'_default':u'UnNews talk'}
        self.namespaces[104] = {'_default':u'Undictionary'}
        self.namespaces[105] = {'_default':u'Undictionary talk'}
        self.namespaces[106] = {'_default':u'Game'}
        self.namespaces[107] = {'_default':u'Game talk'}
        self.namespaces[108] = {'_default':u'Babel'}
        self.namespaces[109] = {'_default':u'Babel talk'}
        self.namespaces[110] = {'_default':u'Forum'}
        self.namespaces[111] = {'_default':u'Forum talk'}

        # A few selected big languages for things that we do not want to loop over
        # all languages. This is only needed by the titletranslate.py module, so
        # if you carefully avoid the options, you could get away without these
        # for another wiki family.
        self.languages_by_size = ['en', 'pl', 'de', 'es', 'ru', 'fr']

    def hostname(self,code):
        return self.langs[code]

    def scriptpath(self, code):
        return ''

    def version(self, code):
        return "1.12alpha"
