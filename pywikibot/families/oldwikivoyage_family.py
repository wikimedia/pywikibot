# -*- coding: utf-8 -*-
import family

class Family(family.Family):
    def __init__(self):
        family.Family.__init__(self)
        self.name = 'oldwikivoyage'
        self.langs = {
            'fr': u'fr.wikivoyage-old.org',
            'wts': u'wts.wikivoyage-old.org',
            'en': u'en.wikivoyage-old.org',
            'ru': u'ru.wikivoyage-old.org',
            'de': u'www.wikivoyage-old.org',
            'shared': u'www.wikivoyage-old.org',
            'it': u'www.wikivoyage-old.org',
            'nl': u'nl.wikivoyage-old.org',
            'sv': u'sv.wikivoyage-old.org',
        }

        self.namespaces[1] = self.namespaces.get(1, {})
        self.namespaces[1][u'fr'] = [u'Discuter']
        self.namespaces[2] = self.namespaces.get(2, {})
        self.namespaces[2][u'ru'] = [u'\u0423\u0447\u0430\u0441\u0442\u043d\u0438\u0446\u0430']
        self.namespaces[3] = self.namespaces.get(3, {})
        self.namespaces[3][u'ru'] = [u'\u041e\u0431\u0441\u0443\u0436\u0434\u0435\u043d\u0438\u0435 \u0443\u0447\u0430\u0441\u0442\u043d\u0438\u0446\u044b']
        self.namespaces[3][u'fr'] = [u'Discussion Utilisateur']
        self.namespaces[4] = self.namespaces.get(4, {})
        self.namespaces[4][u'ru'] = [u'Wikivoyage']
        self.namespaces[4][u'fr'] = [u'Wikivoyage']
        self.namespaces[4][u'wts'] = [u'Wikivoyage']
        self.namespaces[4][u'nl'] = [u'Wikivoyage']
        self.namespaces[4]['de'] = [u'Wikivoyage', u'WV']
        self.namespaces[4]['it'] = [u'Wikivoyage']
        self.namespaces[4][u'sv'] = [u'Wikivoyage']
        self.namespaces[4][u'en'] = [u'Wikivoyage']
        self.namespaces[4][u'shared'] = [u'Wikivoyage']
        self.namespaces[5] = self.namespaces.get(5, {})
        self.namespaces[5][u'ru'] = [u'\u041e\u0431\u0441\u0443\u0436\u0434\u0435\u043d\u0438\u0435 Wikivoyage']
        self.namespaces[5][u'fr'] = [u'Discussion Wikivoyage']
        self.namespaces[5][u'wts'] = [u'Wikivoyage talk']
        self.namespaces[5][u'nl'] = [u'Overleg Wikivoyage']
        self.namespaces[5]['de'] = [u'Wikivoyage Diskussion', u'WV talk']
        self.namespaces[5]['it'] = [u'Discussioni Wikivoyage']
        self.namespaces[5][u'sv'] = [u'Wikivoyagediskussion']
        self.namespaces[5][u'en'] = [u'Wikivoyage talk']
        self.namespaces[5][u'shared'] = [u'Wikivoyage talk']
        self.namespaces[6] = self.namespaces.get(6, {})
        self.namespaces[6][u'ru'] = [u'Image', u'\u0418\u0437\u043e\u0431\u0440\u0430\u0436\u0435\u043d\u0438\u0435']
        self.namespaces[6][u'fr'] = [u'Image']
        self.namespaces[6][u'wts'] = [u'Image']
        self.namespaces[6][u'nl'] = [u'Image', u'Afbeelding']
        self.namespaces[6]['de'] = [u'Bild']
        self.namespaces[6]['it'] = [u'Immagine']
        self.namespaces[6][u'sv'] = [u'Image', u'Bild']
        self.namespaces[6][u'en'] = [u'Image']
        self.namespaces[6][u'shared'] = [u'Image']
        self.namespaces[7] = self.namespaces.get(7, {})
        self.namespaces[7][u'ru'] = [u'Image talk', u'\u041e\u0431\u0441\u0443\u0436\u0434\u0435\u043d\u0438\u0435 \u0438\u0437\u043e\u0431\u0440\u0430\u0436\u0435\u043d\u0438\u044f']
        self.namespaces[7][u'fr'] = [u'Image talk', u'Discussion Fichier', u'Discussion Image']
        self.namespaces[7][u'wts'] = [u'Image talk']
        self.namespaces[7][u'nl'] = [u'Image talk', u'Overleg afbeelding']
        self.namespaces[7]['de'] = [u'Bild Diskussion']
        self.namespaces[7]['it'] = [u'Discussioni immagine']
        self.namespaces[7][u'sv'] = [u'Image talk', u'Bilddiskussion']
        self.namespaces[7][u'en'] = [u'Image talk']
        self.namespaces[7][u'shared'] = [u'Image talk']
        self.namespaces[9] = self.namespaces.get(9, {})
        self.namespaces[9][u'sv'] = [u'MediaWiki diskussion']
        self.namespaces[11] = self.namespaces.get(11, {})
        self.namespaces[11][u'fr'] = [u'Discussion Mod\xe8le']
        self.namespaces[13] = self.namespaces.get(13, {})
        self.namespaces[13][u'fr'] = [u'Discussion Aide']
        self.namespaces[13][u'sv'] = [u'Hj\xe4lp diskussion']
        self.namespaces[15] = self.namespaces.get(15, {})
        self.namespaces[15][u'fr'] = [u'Discussion Cat\xe9gorie']
        self.namespaces[200] = self.namespaces.get(200, {})
        self.namespaces[200][u'wts'] = [u'WtTech']
        self.namespaces[201] = self.namespaces.get(201, {})
        self.namespaces[201][u'wts'] = [u'WtTech Talk']
        self.namespaces[100] = self.namespaces.get(100, {})
        self.namespaces[100]['de'] = [u'Portal']
        self.namespaces[100]['it'] = [u'Portale']
        self.namespaces[101] = self.namespaces.get(101, {})
        self.namespaces[101]['de'] = [u'Portal Diskussion']
        self.namespaces[101]['it'] = [u'Discussioni portale']
        self.namespaces[102] = self.namespaces.get(102, {})
        self.namespaces[102]['de'] = [u'Wahl']
        self.namespaces[102]['it'] = [u'Elezione']
        self.namespaces[103] = self.namespaces.get(103, {})
        self.namespaces[103]['de'] = [u'Wahl Diskussion']
        self.namespaces[103]['it'] = [u'Discussioni elezione']
        self.namespaces[104] = self.namespaces.get(104, {})
        self.namespaces[104]['de'] = [u'Thema', u'T']
        self.namespaces[104]['it'] = [u'Tematica']
        self.namespaces[105] = self.namespaces.get(105, {})
        self.namespaces[105]['de'] = [u'Thema Diskussion', u'T talk']
        self.namespaces[105]['it'] = [u'Discussioni tematica']
        self.namespaces[106] = self.namespaces.get(106, {})
        self.namespaces[106]['de'] = [u'News']
        self.namespaces[106]['it'] = [u'Notizie']
        self.namespaces[107] = self.namespaces.get(107, {})
        self.namespaces[107]['de'] = [u'News Diskussion']
        self.namespaces[107]['it'] = [u'Discussioni notizie']
        self.namespaces[-2] = self.namespaces.get(-2, {})
        self.namespaces[-2]['de'] = [u'Media']


    def scriptpath(self, code):
        return {
            'fr': u'/w',
            'wts': u'/w',
            'en': u'/w',
            'ru': u'/w',
            'de': u'/w/de',
            'shared': u'/w/shared',
            'it': u'/w/it',
            'nl': u'/w',
            'sv': u'/w',
        }[code]

    def version(self, code):
        return {
            'fr': u'1.19.1',
            'wts': u'1.19.1',
            'en': u'1.19.1',
            'ru': u'1.19.1',
            'de': u'1.13.1',
            'en': u'1.13.1',
            'it': u'1.13.1',
            'nl': u'1.19.1',
            'sv': u'1.19.1',
            'shared': u'1.13.1',
        }[code]

    def apipath(self, code):
        return family.Family.apipath(self, code)
