# -*- coding: utf-8  -*-
import family
    
# The Lovetoknow internal family, for lovetoknow wikis, including those
# not yet open to the public.

class Family(family.Family):
    def __init__(self):
        family.Family.__init__(self)

        self.name = 'loveto'

        self.langs = {
            '1911': '1911encyclopedia',
            'recipes': 'recipes',
            'video': 'videogames',
            'garden': 'garden',
            'guru': 'webguru',
            'baby': 'baby',
            'business': 'business',
            'buy': 'buy',
            'crafts': 'crafts',
            'diet': 'diet',
            'engagement': 'engagementrings',
            'kids': 'kids',
            'pregnancy': 'pregnancy',
            'sanfrancisco': 'sanfrancisco',
            'scifi': 'sci-fi',
            'travel': 'travel',
            'weddings': 'weddings',
            'wine': 'wine',
            'online': 'online',
            'movies': 'movies',
            'dogs': 'dogs',
            'shoes': 'shoes',
            'cruises': 'cruises',
            'recovery': 'addiction',
            'insurance': 'insurance',
            'makeup': 'makeup',
            'skincare': 'skincare',
            'lingerie': 'lingerie',
            'mortgage': 'mortgage',
            'interiordesign': 'interiordesign',
            'tattoos': 'tattoos',
            'hair': 'hair',
            'dating': 'dating',
            'cellphones': 'cellphones',
            'college': 'college',
            'yoga': 'yoga',
            'celebrity': 'celebrity',
            'sunglasses': 'sunglasses',
            'divorce': 'divorce',
            'creditcards': 'creditcards',
            'cats': 'cats',
            'swimsuits': 'swimsuits',
            'watches': 'watches',
            }

        self.namespaces[4]['1911'] = '1911 Encylopedia'
        self.namespaces[5]['1911'] = '1911 Encylopedia talk'

        self.namespaces[4]['recipes'] = 'LoveToKnow Recipes'
        self.namespaces[5]['recipes'] = 'Talk:LoveToKnow Recipes'
        self.disambiguationTemplates = {
            '_default': [],
            '1911': ['Disamb'],
            }

        self.disambcatname = {
            '1911': 'Disambiguation',}
        
    def path(self, code):
        if code in ['1911','shoes','insurance','makeup','skincare','lingerie',
                    'mortgage','interiordesign','tattoos','hair','dating',
                    'cellphones','college','yoga','celebrity','sunglasses',
                    'divorce','creditcards','cats','swimsuits']:
            return '/index.php'
        else:
            return '/w/index.php'

    def nice_get_address(self, code, name):
        if code in ['recipes','garden','guru']:
            return '/wiki/%s' % (name)
        else:
            return '/%s' % (name)

    # Which version of MediaWiki is used?
    def version(self, code):
        return "1.4.5"

    def hostname(self,code):
        if code == '1911':
            return 'www.1911encyclopedia.org'
        elif code == 'guru':
            return 'www.webguru.com'
        else:
            return self.langs[code] + '.lovetoknow.com'

    def RversionTab(self, code):
        if code == '1911':
            return(r"action=history")
        elif code == 'recipes':
            return(r"table\>\s*\<b>Format")
        elif code == 'crafts':
            return(r'contentSub"></div>\s*<b>Format')
        elif code in ['kids','pregnancy','weddings','wine','tattoos','hair',
                      'dating','celebrity']:
            return(r"div>\s*<b>Formatting")
        else:
            return(r"div>\s*<script")

    def edit_address(self, code, name):
        if code == 'recipes':
            return '%s?title=%s&action=edit&masteredit=1' % (self.path(code), name)
        else:
            return '%s?title=%s&action=edit' % (self.path(code), name)
