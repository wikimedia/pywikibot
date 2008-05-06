# -*- coding: utf-8  -*-
from pywikibot import family

#
# uncyclopedia_family.py March 21, 2008 for pywikipediabot
#
# The Uncyclomedia family, assorted encyclopedi.as from the Uncyclopedia series.
# This file contains a full set of (currently) fifty languages, excluding forks,
# redirects and mirrors.
#
# Note that some of the wikia in this set are known to have badly incomplete,
# missing or incorrect interwiki maps. Do *not* attempt to invoke interwiki.py
# on Uncyclopedia-related wikis unless you have verified availability of
# links for all language pairs that you will plan to use as interwikis.
#

class Family(family.Family):
    def __init__(self):
	family.Family.__init__(self)
	self.name = 'uncyclopedia'

	self.langs = {
	'ar': 'beidipedia.wikia.com',
	'ast':'nunyepedia.wikia.com',
	'bn': 'bn.uncyc.org',
	'bg': 'bg.oxypedia.net',
	'bs': 'bs.neciklopedija.org',
	'ca': 'valenciclopedia.wikia.com',
	'common': 'commons.uncyclomedia.org',
	'cs': 'necyklopedie.wikia.com',
	'cy': 'cy.uncyclopedia.org.uk',
	'da': 'spademanns.wikia.com',
	'de': 'de.uncyclopedia.org',
	'el': 'frikipaideia.wikia.com',
	'en': 'uncyclopedia.org',
	'eo': 'neciklopedio.wikia.com',
	'es': 'inciclopedia.wikia.com',
	'et': 'ebatsuklopeedia.org',
	'fa': 'fa.uncyc.org',
	'fi': 'hikipedia.info',
	'fr': 'desencyclopedie.wikia.com',
	'got':'unsaiklopedia.org',
	'he': 'eincyclopedia.wikia.com',
	'hr': 'hr.neciklopedija.org',
	'hu': 'unciklopedia.org',
	'id': 'tolololpedia.wikia.com',
	'info': 'uncyclopedia.info',
	'it': 'nonciclopedia.wikia.com',
	'ja': 'ansaikuropedia.org',
	'jv': 'ndhablek.wikia.com',
	'ko': 'uncyclopedia.kr',
	'la': 'uncapaedia.wikia.com',
	'lb': 'kengencyclopedia.org',
	'lt': 'juokopedija.org',
	'lv': 'lv.neciklopedija.org',
	'meta': 'meta.uncyclomedia.org',
	'mg': 'hatsiklopedia.org',
	'mk': 'mk.neciklopedija.org',
	'nl': 'oncyclopedia.net',
	'nn': 'ikkepedia.org',
	'no': 'ikkepedia.org',
	'pl': 'nonsensopedia.wikia.com',
	'pt': 'desciclopedia.ws',
	'ro': 'uncyclopedia.ro',
	'ru': 'absurdopedia.wikia.com',
	'sk': 'necyklopedia.wikia.com',
	'sl': 'butalopedija.org',
	'sr': 'sr.neciklopedija.org',
	'su': 'su.goblogpedia.wikia.com',
	'sv': 'psyklopedin.org',
	'th': 'th.uncyclopedia.info',
	'tr': 'yansiklopedi.org',
	'uk': 'inciklopedia.org',
	'yi': 'keinziklopedie.wikia.com',
	'zh-hk': 'uncyclopedia.hk',
	'zh-tw':'uncyclopedia.tw',
	'zh': 'zh.uncyclopedia.wikia.com',
	}

	#
	# project namespaces & custom namespace lists
	#

	self.namespaces[-2]['ar'] = u'ملف'
	self.namespaces[-2]['bs'] = u'Medija'
	self.namespaces[-2]['he'] = u'מדיה'
	self.namespaces[-2]['hu'] = u'Media'
	self.namespaces[-2]['th'] = u'สื่อ'
	self.namespaces[-2]['zh-hk'] = u'媒體'
	self.namespaces[-2]['zh-tw'] = u'媒體'

	self.namespaces[-1]['bs'] = u'Posebno'
	self.namespaces[-1]['ja'] = u'Special'
	self.namespaces[-1]['jv'] = u'Astamiwa'
	self.namespaces[-1]['lb'] = u'Spezial'
	self.namespaces[-1]['zh-hk'] = u'特殊'
	self.namespaces[-1]['zh-tw'] = u'特殊'

	self.namespaces[1]['ast'] = u'Discusión'
	self.namespaces[1]['bs'] = u'Razgovor'
	self.namespaces[1]['id'] = u'Pembicaraan'
	self.namespaces[1]['ja'] = u'Talk'
	self.namespaces[1]['jv'] = u'Dhiskusi'
	self.namespaces[1]['lb'] = u'Diskussioun'
	self.namespaces[1]['lv'] = u'Diskusija'
	self.namespaces[1]['mg'] = u'Discuter'
	self.namespaces[1]['th'] = u'พูดคุย'
	self.namespaces[1]['zh-hk'] = u'討論'
	self.namespaces[1]['zh-tw'] = u'討論'

	self.namespaces[2]['bs'] = u'Korisnik'
	self.namespaces[2]['jv'] = u'Panganggo'
	self.namespaces[2]['lb'] = u'Benotzer'
	self.namespaces[2]['lv'] = u'Lietotājs'
	self.namespaces[2]['mg'] = u'Utilisateur'
	self.namespaces[2]['pl'] = u'Użytkownik'
	self.namespaces[2]['zh-hk'] = u'用戶'
	self.namespaces[2]['zh-tw'] = u'用戶'

	self.namespaces[3]['ast'] = u'Usuariu discusión'
	self.namespaces[3]['bs'] = u'Razgovor sa korisnikom'
	self.namespaces[3]['da'] = u'Brugerdiskussion'
	self.namespaces[3]['hu'] = u'User talk'
	self.namespaces[3]['id'] = u'Pembicaraan Pengguna'
	self.namespaces[3]['jv'] = u'Dhiskusi Panganggo'
	self.namespaces[3]['lb'] = u'Benotzer Diskussioun'
	self.namespaces[3]['lv'] = u'Lietotāja diskusija'
	self.namespaces[3]['mg'] = u'Discussion Utilisateur'
	self.namespaces[3]['mk'] = u'Разговор со корисник'
	self.namespaces[3]['pl'] = u'Dyskusja użytkownika'
	self.namespaces[3]['th'] = u'คุยกับผู้ใช้'
	self.namespaces[3]['zh-hk'] = u'用戶討論'
	self.namespaces[3]['zh-tw'] = u'用戶討論'

	self.namespaces[4]['ar'] = u'بيضيپيديا'
	self.namespaces[4]['ast'] = u'Nunyepedia'
	self.namespaces[4]['bg'] = u'Oxypedia'
	self.namespaces[4]['bn'] = u'Uncyclopedia'
	self.namespaces[4]['bs'] = u'Neciklopedija'
	self.namespaces[4]['ca'] = u'Valenciclopèdia'
	self.namespaces[4]['common'] = u'UnCommons'
	self.namespaces[4]['cs'] = u'Necyklopedie'
	self.namespaces[4]['cy'] = u'Celwyddoniadur'
	self.namespaces[4]['da'] = u'Spademanns Leksikon'
	self.namespaces[4]['de'] = u'Uncyclopedia'
	self.namespaces[4]['el'] = u'Φρικηπαίδεια'
	self.namespaces[4]['en'] = u'Uncyclopedia'
	self.namespaces[4]['eo'] = u'Neciklopedio'
	self.namespaces[4]['es'] = u'Inciclopedia'
	self.namespaces[4]['et'] = u'Ebatsüklopeedia'
	self.namespaces[4]['fa'] = u'Uncyclopedia'
	self.namespaces[4]['fi'] = u'Hikipedia'
	self.namespaces[4]['fr'] = u'Désencyclopédie'
	self.namespaces[4]['got'] = u'Unsaiklopedia'
	self.namespaces[4]['he'] = u'איןציקלופדיה'
	self.namespaces[4]['hr'] = u'Neciklopedija'
	self.namespaces[4]['hu'] = u'Unciklopédia'
	self.namespaces[4]['id'] = u'Tolololpedia'
	self.namespaces[4]['info'] = u'Uncyclopaedia'
	self.namespaces[4]['it'] = u'Nonciclopedia'
	self.namespaces[4]['ja'] = u'Uncyclopedia'
	self.namespaces[4]['jv'] = u'Ndhablek'
	self.namespaces[4]['ko'] = u'백괴사전'
	self.namespaces[4]['la'] = u'Uncapaedia'
	self.namespaces[4]['lb'] = u'Kengencyclopedia'
	self.namespaces[4]['lt'] = u'Juokopediją'
	self.namespaces[4]['lv'] = u'Neciklopēdija'
	self.namespaces[4]['meta'] = u'UnMeta'
	self.namespaces[4]['mg'] = u'Hatsiklopedia'
	self.namespaces[4]['mk'] = u'Нециклопедий'
	self.namespaces[4]['nl'] = u'Oncyclopedie'
	self.namespaces[4]['nn'] = u'Ikkepedia'
	self.namespaces[4]['no'] = u'Ikkepedia'
	self.namespaces[4]['pl'] = u'Nonsensopedia'
	self.namespaces[4]['pt'] = u'Desciclopédia'
	self.namespaces[4]['ro'] = u'Unciclopedie'
	self.namespaces[4]['ru'] = u'Абсурдопедия'
	self.namespaces[4]['sk'] = u'Necyklopédia'
	self.namespaces[4]['sl'] = u'Butalopedija'
	self.namespaces[4]['sr'] = u'Нециклопедија'
	self.namespaces[4]['su'] = u'Goblogpedia Wiki'
	self.namespaces[4]['sv'] = u'Psyklopedin'
	self.namespaces[4]['th'] = u'ไร้สาระนุกรม'
	self.namespaces[4]['tr'] = u'Yansiklopedi'
	self.namespaces[4]['uk'] = u'Інциклопедія'
	self.namespaces[4]['yi'] = u'קיינציקלאָפעדיע'
	self.namespaces[4]['zh'] = u'伪基百科'
	self.namespaces[4]['zh-hk'] = u'偽基百科'
	self.namespaces[4]['zh-tw'] = u'偽基百科'

	self.namespaces[5]['ar'] = u'نقاش بيضيپيديا'
	self.namespaces[5]['ast'] = u'Nunyepedia discusión'
	self.namespaces[5]['bg'] = u'Oxypedia беседа'
	self.namespaces[5]['bn'] = u'Uncyclopedia আলাপ'
	self.namespaces[5]['bs'] = u'Razgovor s Neciklopedija'
	self.namespaces[5]['ca'] = u'Valenciclopèdia Discussió'
	self.namespaces[5]['common'] = u'UnCommon talk'
	self.namespaces[5]['cs'] = u'Necyklopedie diskuse'
	self.namespaces[5]['cy'] = u'Sgwrs Celwyddoniadur'
	self.namespaces[5]['da'] = u'Spademanns Leksikon-diskussion'
	self.namespaces[5]['de'] = u'Uncyclopedia Diskussion'
	self.namespaces[5]['el'] = u'Φρικηπαίδεια συζήτηση'
	self.namespaces[5]['en'] = u'Uncyclopedia talk'
	self.namespaces[5]['eo'] = u'Neciklopedio diskuto'
	self.namespaces[5]['es'] = u'Inciclopedia Discusión'
	self.namespaces[5]['et'] = u'Ebatsüklopeedia arutelu'
	self.namespaces[5]['fa'] = u'بحث Uncyclopedia'
	self.namespaces[5]['fi'] = u'Keskustelu Hikipediasta'
	self.namespaces[5]['fr'] = u'Discussion Désencyclopédie'
	self.namespaces[5]['got'] = u'Unsaiklopedia talk'
	self.namespaces[5]['he'] = u'שיחת איןציקלופדיה'
	self.namespaces[5]['hr'] = u'Razgovor Neciklopedija'
	self.namespaces[5]['hu'] = u'Unciklopédia vita'
	self.namespaces[5]['id'] = u'Pembicaraan Tolololpedia'
	self.namespaces[5]['info'] = u'Uncyclopædia talk'
	self.namespaces[5]['it'] = u'Discussioni Nonciclopedia'
	self.namespaces[5]['ja'] = u'Uncyclopedia talk'
	self.namespaces[5]['jv'] = u'Dhiskusi Ndhablek'
	self.namespaces[5]['ko'] = u'백괴사전토론'
	self.namespaces[5]['la'] = u'Disputatio Uncapaediae'
	self.namespaces[5]['lb'] = u'Kengencyclopedia Diskussioun'
	self.namespaces[5]['lt'] = u'Juokopediją aptarimas'
	self.namespaces[5]['lv'] = u'Neciklopēdija diskusija'
	self.namespaces[5]['meta'] = u'UnMeta talk'
	self.namespaces[5]['mg'] = u'Discussion Hatsiklopedia'
	self.namespaces[5]['mk'] = u'Разговор за Нециклопедий'
	self.namespaces[5]['nl'] = u'Overleg Oncyclopedie'
	self.namespaces[5]['nn'] = u'Ikkepedia-diskusjon'
	self.namespaces[5]['no'] = u'Ikkepedia-diskusjon'
	self.namespaces[5]['pl'] = u'Dyskusja Nonsensopedia'
	self.namespaces[5]['pt'] = u'Desciclopédia Discussão'
	self.namespaces[5]['ro'] = u'Discuţie Unciclopedie'
	self.namespaces[5]['ru'] = u'Обсуждение Абсурдопедии'
	self.namespaces[5]['sk'] = u'Diskusia k Necyklopédia'
	self.namespaces[5]['sl'] = u'Pogovor o Butalopedija'
	self.namespaces[5]['sr'] = u'Разговор о Нециклопедија'
	self.namespaces[5]['su'] = u'Obrolan Goblogpedia Wiki'
	self.namespaces[5]['sv'] = u'Psyklopedindiskussion'
	self.namespaces[5]['th'] = u'คุยเรื่องไร้สาระนุกรม'
	self.namespaces[5]['tr'] = u'Yansiklopedi tartışma'
	self.namespaces[5]['uk'] = u'Обговорення Інциклопедії'
	self.namespaces[5]['yi'] = u'קיינציקלאָפעדיע רעדן'
	self.namespaces[5]['zh'] = u'伪基百科 talk'
	self.namespaces[5]['zh-hk'] = u'偽基百科討論'
	self.namespaces[5]['zh-tw'] = u'偽基百科討論'

	self.namespaces[6]['ast'] = u'Imaxen'
	self.namespaces[6]['bs'] = u'Slika'
	self.namespaces[6]['id'] = u'Berkas'
	self.namespaces[6]['info'] = u'File'
	self.namespaces[6]['ja'] = u'Image'
	self.namespaces[6]['jv'] = u'Gambar'
	self.namespaces[6]['lb'] = u'Bild'
	self.namespaces[6]['lv'] = u'Attēls'
	self.namespaces[6]['zh-hk'] = u'圖像'
	self.namespaces[6]['zh-tw'] = u'圖像'

	self.namespaces[7]['ast'] = u'Imaxen discusión'
	self.namespaces[7]['bs'] = u'Razgovor o slici'
	self.namespaces[7]['da'] = u'Billeddiskussion'
	self.namespaces[7]['hu'] = u'Kep vita'
	self.namespaces[7]['id'] = u'Pembicaraan Berkas'
	self.namespaces[7]['info'] = u'File talk'
	self.namespaces[7]['jv'] = u'Dhiskusi Gambar'
	self.namespaces[7]['lb'] = u'Bild Diskussioun'
	self.namespaces[7]['lv'] = u'Attēla diskusija'
	self.namespaces[7]['mg'] = u'Discussion Image'
	self.namespaces[7]['mk'] = u'Разговор за слика'
	self.namespaces[7]['th'] = u'คุยเรื่องภาพ'
	self.namespaces[7]['zh-hk'] = u'圖像討論'
	self.namespaces[7]['zh-tw'] = u'圖像討論'

	self.namespaces[8]['bs'] = u'MedijaViki'
	self.namespaces[8]['fi'] = u'MediaWiki'
	self.namespaces[8]['cy'] = u'MediaWici'
	self.namespaces[8]['he'] = u'מדיה ויקי'
	self.namespaces[8]['lb'] = u'MediaWiki'
	self.namespaces[8]['th'] = u'มีเดียวิกิ'
	self.namespaces[8]['zh-hk'] = u'媒體偽基'
	self.namespaces[8]['zh-tw'] = u'媒體偽基'

	self.namespaces[9]['ast'] = u'MediaWiki discusión'
	self.namespaces[9]['bn'] = u'MediaWiki আলাপ'
	self.namespaces[9]['bs'] = u'Razgovor o MedijaVikiju'
	self.namespaces[9]['cy'] = u'Sgwrs MediaWici'
	self.namespaces[9]['da'] = u'MediaWiki-diskussion'
	self.namespaces[9]['fi'] = u'Keskustelu MediaWiki'
	self.namespaces[9]['he'] = u'שיחת מדיה ויקי'
	self.namespaces[9]['hu'] = u'MediaWiki talk'
	self.namespaces[9]['jv'] = u'Dhiskusi MediaWiki'
	self.namespaces[9]['ko'] = u'MediaWiki토론'
	self.namespaces[9]['lb'] = u'MediaWiki Diskussioun'
	self.namespaces[9]['lv'] = u'MediaWiki diskusija'
	self.namespaces[9]['mg'] = u'Discussion MediaWiki'
	self.namespaces[9]['mk'] = u'Разговор за МедијаВики'
	self.namespaces[9]['sv'] = u'MediaWiki diskussion'
	self.namespaces[9]['th'] = u'คุยเรื่องมีเดียวิกิ'
	self.namespaces[9]['zh-hk'] = u'媒體偽基討論'
	self.namespaces[9]['zh-tw'] = u'媒體偽基討論'

	self.namespaces[10]['ast'] = u'Plantilla'
	self.namespaces[10]['bs'] = u'Šablon'
	self.namespaces[10]['ca'] = u'Plantilla'
	self.namespaces[10]['jv'] = u'Cithakan'
	self.namespaces[10]['ko'] = u'틀'
	self.namespaces[10]['lb'] = u'Schabloun'
	self.namespaces[10]['lv'] = u'Veidne'
	self.namespaces[10]['mg'] = u'Modèle'
	self.namespaces[10]['mk'] = u'Шаблон'
	self.namespaces[10]['th'] = u'แม่แบบ'
	self.namespaces[10]['zh-hk'] = u'範本'
	self.namespaces[10]['zh-tw'] = u'範本'

	self.namespaces[11]['ar'] = u'نقاش قالب'
	self.namespaces[11]['ast'] = u'Plantilla discusión'
	self.namespaces[11]['bs'] = u'Razgovor o šablonu'
	self.namespaces[11]['ca'] = u'Plantilla Discussió'
	self.namespaces[11]['da'] = u'Skabelondiskussion'
	self.namespaces[11]['jv'] = u'Dhiskusi Cithakan'
	self.namespaces[11]['ko'] = u'틀토론'
	self.namespaces[11]['lb'] = u'Schabloun Diskussioun'
	self.namespaces[11]['lv'] = u'Veidnes diskusija'
	self.namespaces[11]['mg'] = u'Discussion Modèle'
	self.namespaces[11]['mk'] = u'Разговор за шаблон'
	self.namespaces[11]['th'] = u'คุยเรื่องแม่แบบ'
	self.namespaces[11]['zh-hk'] = u'範本討論'
	self.namespaces[11]['zh-tw'] = u'範本討論'

	self.namespaces[12]['ast'] = u'Ayuda'
	self.namespaces[12]['bs'] = u'Pomoć'
	self.namespaces[12]['cy'] = u'Cymorth'
	self.namespaces[12]['jv'] = u'Pitulung'
	self.namespaces[12]['lb'] = u'Hëllef'
	self.namespaces[12]['lv'] = u'Palīdzība'
	self.namespaces[12]['mg'] = u'Aide'
	self.namespaces[12]['th'] = u'วิธีใช้'
	self.namespaces[12]['zh-hk'] = u'協助'
	self.namespaces[12]['zh-tw'] = u'協助'

	self.namespaces[13]['ast'] = u'Ayuda discusión'
	self.namespaces[13]['bs'] = u'Razgovor o pomoći'
	self.namespaces[13]['cy'] = u'Sgwrs Cymorth'
	self.namespaces[13]['da'] = u'Hjælp-diskussion'
	self.namespaces[13]['jv'] = u'Dhiskusi Pitulung'
	self.namespaces[13]['lb'] = u'Hëllef Diskussioun'
	self.namespaces[13]['lv'] = u'Palīdzības diskusija'
	self.namespaces[13]['mg'] = u'Discussion Aide'
	self.namespaces[13]['mk'] = u'Разговор за помош'
	self.namespaces[13]['sv'] = u'Hjälpdiskussion'
	self.namespaces[13]['th'] = u'คุยเรื่องวิธีใช้'
	self.namespaces[13]['zh-hk'] = u'協助討論'
	self.namespaces[13]['zh-tw'] = u'協助討論'

	self.namespaces[14]['bs'] = u'Kategorija'
	self.namespaces[14]['cy'] = u'Categori'
	self.namespaces[14]['jv'] = u'Kategori'
	self.namespaces[14]['lb'] = u'Kategorie'
	self.namespaces[14]['lv'] = u'Kategorija'
	self.namespaces[14]['mg'] = u'Catégorie'
	self.namespaces[14]['th'] = u'หมวดหมู่'
	self.namespaces[14]['zh-hk'] = u'分類'
	self.namespaces[14]['zh-tw'] = u'分類'

	self.namespaces[15]['ast'] = u'Categoría discusión'
	self.namespaces[15]['bg'] = u'Категория беседа'
	self.namespaces[15]['bs'] = u'Razgovor o kategoriji'
	self.namespaces[15]['cy'] = u'Sgwrs Categori'
	self.namespaces[15]['da'] = u'Kategoridiskussion'
	self.namespaces[15]['jv'] = u'Dhiskusi Kategori'
	self.namespaces[15]['lb'] = u'Kategorie Diskussioun'
	self.namespaces[15]['lv'] = u'Kategorijas diskusija'
	self.namespaces[15]['mg'] = u'Discussion Catégorie'
	self.namespaces[15]['mk'] = u'Разговор за категорија'
	self.namespaces[15]['th'] = u'คุยเรื่องหมวดหมู่'
	self.namespaces[15]['zh-hk'] = u'分類討論'
	self.namespaces[15]['zh-tw'] = u'分類討論'

	self.namespaces[16] = {
	  'fi': u'Foorumi',
	  'got': u'Forum',
	  'info': u'Game',
#	  'ko': u'漢字',
	  'meta': u'UnSource',
	  'nl': u'Portaal',
	  'pt': u'Esplanada',
	  'th': u'อันไซโคลพีเดีย',
	  'zh-hk': u'偽基新聞',
	  'zh-tw': u'偽基新聞'
	}

	self.namespaces[17] = {
	  'fi': u'Keskustelu foorumista',
	  'got': u'Forum gawaurdja',
	  'info': u'Game talk',
#	  'ko': u'討論',
	  'meta': u'UnSource talk',
	  'nl': u'Overleg portaal',
	  'pt': u'Esplanada Discussão',
	  'th': u'คุยเรื่องอันไซโคลพีเดีย',
	  'zh-hk': u'偽基新聞討論',
	  'zh-tw': u'偽基新聞討論'
	}

	self.namespaces[18] = {
	  '_default': '',
	  'fi': u'Hikinews',
	  'got': u'𐌰𐍂𐌼𐌰𐌹𐍉',
#	  'ko': u'백괴나라',
	  'meta': u'UnSpecies',
	  'nl': u'OnNieuws',
	  'pt': u'Fatos',
	  'th': u'ไร้ข่าว',
	  'zh-hk': u'偽基辭典',
	  'zh-tw': u'偽基辭典'
	}

	self.namespaces[19] = {
	  '_default': '',
	  'fi': u'Keskustelu Hikinewseistä',
	  'got': u'𐌰𐍂𐌼𐌰𐌹𐍉 𐌲𐌰𐍅𐌰𐌿𐍂𐌳𐌾𐌰',
#	  'ko': u'백괴나라토론',
	  'meta': u'UnSpecies talk',
	  'nl': u'Overleg OnNieuws',
	  'pt': u'Fatos Discussão',
	  'th': u'คุยเรื่องไร้ข่าว',
	  'zh-hk': u'偽基辭典討論',
	  'zh-tw': u'偽基辭典討論'
	}

	self.namespaces[20] = {
	  '_default': '',
	  'fi': u'Hiktionary',
	  'got': u'𐍆𐌰𐌹𐌰𐌽𐍅𐌰𐌿𐍂𐌳𐌰𐌱𐍉𐌺𐌰',
	  'meta': u'Namespace',
	  'nl': u'Onwoordenboek',
	  'pt': u'Forum',
	  'th': u'ไร้วิทยาลัย',
	  'zh-hk': u'動漫遊戲',
	  'zh-tw': u'動漫遊戲'
	}

	self.namespaces[21] = {
	  '_default': '',
	  'fi': u'Keskustelu Hiktionarysta',
	  'got': u'𐍆𐌰𐌹𐌰𐌽𐍅𐌰𐌿𐍂𐌳𐌰𐌱𐍉𐌺𐌰 𐌲𐌰𐍅𐌰𐌿𐍂𐌳𐌾𐌰',
	  'meta': u'Namespace talk',
	  'nl': u'Overleg Onwoordenboek',
	  'pt': u'Forum Discussão',
	  'th': u'คุยเรื่องไร้วิทยาลัย',
	  'zh-hk': u'動漫遊戲討論',
	  'zh-tw': u'動漫遊戲討論'
	}

	self.namespaces[22] = {
	  'fi': u'Hikikirjasto',
	  'nl': u'OnBoeken',
	  'th': u'ไร้พจนานุกรม',
	  'zh-hk': u'春心蕩漾',
	  'zh-tw': u'春心蕩漾'
	}

	self.namespaces[23] = {
	  'fi': u'Keskustelu hikikirjasta',
	  'nl': u'Overleg OnBoeken',
	  'th': u'คุยเรื่องไร้พจนานุกรม',
	  'zh-hk': u'春心蕩漾討論',
	  'zh-tw': u'春心蕩漾討論'
	}

	self.namespaces[24] = {
	  'fi': u'Hikisitaatit',
	  'th': u'ไร้ชีวประวัติ',
	  'zh-hk': u'主題展館',
	  'zh-tw': u'主題展館'
	}

	self.namespaces[25] = {
	  'fi': u'Keskustelu hikisitaatista',
	  'th': u'คุยเรื่องไร้ชีวประวัติ',
	  'zh-hk': u'主題展館討論',
	  'zh-tw': u'主題展館討論'
	}

	self.namespaces[26] = {
	  'fi': u'Hömppäpedia',
	  'th': u'สภาน้ำชา',
	  'zh-hk': u'論壇',
	  'zh-tw': u'論壇'
	}

	self.namespaces[27] = {
	  'fi': u'Höpinä hömpästä',
	  'th': u'คุยเรื่องสภาน้ำชา',
	  'zh-hk': u'論壇討論',
	  'zh-tw': u'論壇討論'
	}

	self.namespaces[28] = {
	  'fi': u'Hikipeli',
	  'nl': u'Ongerijmd',
	  'th': u'บอร์ด',
	  'zh-hk': u'詞意分道',
	  'zh-tw': u'詞意分道'
	}

	self.namespaces[29] = {
	  'fi': u'Hihitys Hikipelistä',
	  'th': u'คุยเรื่องบอร์ด',
	  'zh-hk': u'詞意分道討論',
	  'zh-tw': u'詞意分道討論'
	}

	self.namespaces[30] = {
	  'pt': u'Deslivros',
	  'th': u'ไร้ซอร์ซ',
	  'zh-hk': u'臺語',
	  'zh-tw': u'臺語'
	}

	self.namespaces[31] = {
	  'pt': u'Deslivros Discussão',
	  'th': u'คุยเรื่องไร้ซอร์ซ',
	  'zh-hk': u'臺語討論',
	  'zh-tw': u'臺語討論'
	}

	self.namespaces[32] = {
	  'ja': u'Portal',
	  'pt': u'Desentrevistas',
	  'th': u'ไร้คำคม',
	  'zh-hk': u'香港語',
	  'zh-tw': u'香港語'
	}

	self.namespaces[33] = {
	  'ja': u'Portal talk',
	  'pt': u'Desentrevistas Discussão',
	  'th': u'คุยเรื่องไร้คำคม',
	  'zh-hk': u'香港語討論',
	  'zh-tw': u'香港語討論'
	}

	self.namespaces[34] = {
	  'th': u'ไร้ภาพ',
	  'zh-hk': u'書面語',
	  'zh-tw': u'書面語'
	}

	self.namespaces[35] = {
	  'th': u'คุยเรื่องไร้ภาพ',
	  'zh-hk': u'書面語討論',
	  'zh-tw': u'書面語討論'
	}

	self.namespaces[36] = {
	  'zh-hk': u'偽基書籍',
	  'zh-tw': u'偽基書籍'
	}

	self.namespaces[37] = {
	  'zh-hk': u'偽基書籍討論',
	  'zh-tw': u'偽基書籍討論'
	}

	self.namespaces[100] = {
	  'de': u'UnNews',
	  'nn': u'Ikkenytt',
	  'no': u'Ikkenytt',
	  'pl': u'Cytaty',
	  'sv': u'PsykNyheter',
	  'tr': u'YanSözlük'
	}

	self.namespaces[101] = {
	  'de': u'UnNews Diskussion',
	  'nn': u'Ikkenytt-diskusjon',
	  'no': u'Ikkenytt-diskusjon',
	  'pl': u'Dyskusja cytatów',
	  'sv': u'PsykNyheter diskussion',
	  'tr': u'YanSözlük tartışma'
	}

	self.namespaces[102] = {
	  'de': u'Undictionary',
	  'en': u'UnNews',
	  'ja': u'UnNews',
	  'nn': u'Ikktionary',
	  'no': u'Ikktionary',
	  'pl': u'NonNews',
	  'sv': u'Forum',
	  'tr': u'YanHaber',
	  }

	self.namespaces[103] = {
	  'de': u'Undictionary Diskussion',
	  'en': u'UnNews talk',
	  'ja': u'UnNews talk',
	  'nn': u'Ikktionary-diskusjon',
	  'no': u'Ikktionary-diskusjon',
	  'pl': u'Dyskusja NonNews',
	  'sv': u'Forumdiskussion',
	  'tr': u'YanHaber tartışma'
	}

	self.namespaces[104] = {
	  'de': u'UnBooks',
	  'en': u'Undictionary',
	  'pl': u'Nonźródła',
	  'sv': u'Psyktionary'
	}

	self.namespaces[105] = {
	  'de': u'UnBooks Diskussion',
	  'en': u'Undictionary talk',
	  'pl': u'Dyskusja nonźródeł',
	  'sv': u'Psyktionary diskussion'
	}

	self.namespaces[106] = {
	  '_default':'',
	  'en': u'Game',
	  'ja': u'Game',
	  'pl': u'Słownik',
	  'pt': u'Desnotícias',
	  'sv': u'PsykCitat'
	}

	self.namespaces[107] = {
	  'en': u'Game talk',
	  'ja': u'Game talk',
	  'pl': u'Dyskusja słownika',
	  'pt': u'Desnotícias Discussão',
	  'sv': u'PsykCitat diskussion'
	}

	self.namespaces[108] = {
	  'en': u'Babel',
	  'pl': u'Gra',
	  'pt': u'Jogo',
	  'sv': u'Spel'
	}

	self.namespaces[109] = {
	  'en': u'Babel talk',
	  'pl': u'Dyskusja gry',
	  'pt': u'Jogo Discussão',
	  'sv': u'Speldiskussion'
	}

	self.namespaces[110] = {
	  'ar': u'Forum',
	  'ast': u'Forum',
	  'ca': u'Forum',
	  'cs': u'Forum',
	  'da': u'Forum',
	  'de': u'Forum',
	  'el': u'Forum',
	  'en': u'Forum',
	  'eo': u'Forum',
	  'es': u'Forum',
	  'fr': u'Forum',
	  'he': u'Forum',
	  'id': u'Forum',
	  'it': u'Forum',
	  'ja': u'Forum',
	  'jv': u'Forum',
	  'la': u'Forum',
	  'nn': u'Forum',
	  'no': u'Forum',
	  'pl': u'Forum',
	  'pt': u'Descionário',
	  'ru': u'Форум',
	  'sk': u'Forum',
	  'su': u'Forum',
	  'sv': u'PsykBöcker',
	  'tr': u'Astroloji',
	  'yi': u'Forum',
	  'zh': u'Forum'
	}

	self.namespaces[111] = {
	  'ar': u'Forum talk',
	  'ast': u'Forum talk',
	  'ca': u'Forum talk',
	  'cs': u'Forum talk',
	  'da': u'Forumdiskussion',
	  'de': u'Forum talk',
	  'el': u'Forum talk',
	  'en': u'Forum talk',
	  'eo': u'Forum talk',
	  'es': u'Forum talk',
	  'fr': u'Discussion Forum',
	  'he': u'Forum talk',
	  'id': u'Forum talk',
	  'it': u'Forum talk',
	  'ja': u'Forum talk',
	  'jv': u'Forum talk',
	  'la': u'Forum talk',
	  'nn': u'Forum-diskusjon',
	  'no': u'Forum-diskusjon',
	  'pl': u'Dyskusja forum',
	  'pt': u'Descionário Discussão',
	  'ru': u'Обсуждение форума',
	  'sk': u'Forum talk',
	  'su': u'Forum talk',
	  'sv': u'PsykBöckerdiskussion',
	  'tr': u'Astroloji tartışma',
	  'yi': u'Forum talk',
	  'zh': u'Forum talk'
	}

	self.namespaces[112] = {
	  'en': u'UnTunes',
	  'es': u'Incinoticias',
	  'fr': u'Désinformation',
	  'ja': u'UnTunes',
	  'nn': u'Hvordan',
	  'no': u'Hvordan',
	  'pl': u'Portal',
	  'tr': u'Forum'
	}

	self.namespaces[113] = {
	  'en': u'UnTunes talk',
	  'es': u'Incinoticias Discusión',
	  'fr': u'Discussion Désinformation',
	  'ja': u'UnTunes talk',
	  'no': u'Hvordan-diskusjon',
	  'pl': u'Dyskusja portalu',
	  'tr': u'Forum tartışma'
	}

	self.namespaces[114] = {
	  'es': u'Incitables',
	  'no': u'Hvorfor',
	  'pl': u'Poradnik'
	}

	self.namespaces[115] = {
	  'es': u'Incitables Discusión',
	  'no': u'Hvorfor-diskusjon',
	  'pl': u'Dyskusja poradnika'
	}

	self.namespaces[120] = {
	  'pt': u'Privado',
	  'tr': u'YanMagazin'
	}

	self.namespaces[121] = {
	  'pt': u'Privado Discussão',
	  'tr': u'YanMagazin tartışma'
	}

	self.namespaces[122] = {
	  'pt': u'Regra'
	}

	self.namespaces[123] = {
	  'pt': u'Regra Discussão'
	}

	# A few selected big languages for things that we do not want to loop over
	# all languages. This is only needed by the titletranslate.py module, so
	# if you carefully avoid the options, you could get away without these
	# for another wiki family.
	self.languages_by_size  = ['en', 'ja', 'pt', 'it', 'pl', 'fr', 'fi', 'es', 'zh-tw', 'de', 'no']     

    def hostname(self,code):
        return self.langs[code]

    def path(self, code):
        if code == 'ko':
           return '/w/index.php'
        return '/index.php'

    def version(self, code):
        return '1.12'

    def apipath(self, code):
        if code == 'ko':
           return '/w/api.php'
        return '/api.php'

    def code2encoding(self,code):
        return 'utf-8'

    def shared_image_repository(self, code):
        return ('common', 'common')
