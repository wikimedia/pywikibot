#!/usr/bin/env python3
"""Script to add properties, identifiers and sources to WikiBase items.

Usage:

    dataextend <item> [<property>[+*]] [args]

In the basic usage, where no property is specified, item is the Q-number
of the item to work on.from html import unescape

If a property (P-number, or the special value 'Wiki' or 'Data') is
specified, only the data from that identifier are added. With a '+'
after it, work starts on that identifier, then goes on to identifiers
after that (including new identifiers added while working on those
identifiers). With a '*' after it, the identifier itself is skipped, but
those coming after it (not those coming before it) are included.

The following parameters are supported:

-always    If this is supplied, the bot will not ask for permission
           after each external link has been handled.

-showonly  Only show claims for a given ItemPage. Don't try to add any
           properties

The bot will load the corresponding pages for these identifiers, and try
to the meaning of that string for the specified type of thing (for
example 'city' or 'gender'). If you want to use it, but not save it
(which can happen if the string specifies a certain value now, but might
show another value elsewhere, or if it is so specific that you're pretty
sure it won't occur a second time), you can provide the Q-number with X
rather than Q. If you do not want to use the string, you can just hit
enter, or give the special value 'XXX' which means that it will be
skipped in each subsequent run as well.

After an identifier has been worked on, there might be a list of names
that has been found, in lc:name format, where lc is a language code. You
can accept all suggested names (answer Y), none (answer N) or ask to get
asked for each name separately (answer S), the latter being the default
if you do not fill in anything.

After all identifiers have been worked on, possible descriptions in
various languages are presented, and you get to choose one. The default
is here 0, which always is the current description for that language.
Finally, for a number of identifiers text is shown that usually gives
parts of the description that are hard to parse automatically, so you
can see if there any additional pieces of data that can be added.

It is advisable to (re)load the item page that the bot has been working
on in the browser afterward, to correct any mistakes it has made, or
cases where a more precise and less precise value have both been
included.

.. versionadded:: 7.2
"""
#
# (C) Pywikibot team, 2020-2023
#
# Distributed under the terms of the MIT license.
#
import codecs
import datetime
import re
from collections import defaultdict
from contextlib import suppress
from html import unescape
from textwrap import shorten
from typing import Optional
from urllib.parse import quote, unquote

import pywikibot
from pywikibot.backports import List, Tuple
from pywikibot.bot import SingleSiteBot, input_yn, suggest_help
from pywikibot.comms import http
from pywikibot.data import sparql
from pywikibot.exceptions import (
    APIError,
    InvalidTitleError,
    NoPageError,
    OtherPageSaveError,
    ServerError,
)
from pywikibot.tools.collections import DequeGenerator


class DataExtendBot(SingleSiteBot):

    update_options = {
        'restrict': '',
        'showonly': False,
    }

    """The Bot."""

    QRE = re.compile(r'Q\d+')
    PQRE = re.compile(r'[PQ]\d+')

    def __init__(self, **kwargs):
        """Initializer."""
        super().__init__(**kwargs)
        self.labels = {}
        self.data = defaultdict(dict)
        self.noname = set()
        self.labelfile = 'labels.txt'
        self.datafile = 'defaultdata.txt'
        self.nonamefile = 'noname.txt'
        self.loaddata()
        self.analyzertype = {
            'P213': IsniAnalyzer,
            'P214': ViafAnalyzer,
            'P227': GndAnalyzer,
            'P244': LcAuthAnalyzer,
            'P245': UlanAnalyzer,
            'P268': BnfAnalyzer,
            'P269': SudocAnalyzer,
            'P271': CiniiAnalyzer,
            'P345': ImdbAnalyzer,
            'P396': SbnAnalyzer,
            'P409': LibrariesAustraliaAnalyzer,
            'P434': MusicBrainzAnalyzer,
            'P454': StructuraeAnalyzer,
            'P496': OrcidAnalyzer,
            'P497': CbdbAnalyzer,
            'P535': FindGraveAnalyzer,
            'P549': MathGenAnalyzer,
            'P586': IpniAuthorsAnalyzer,
            # 'P590': GnisAnalyzer, <http redirect loop>
            'P640': LeonoreAnalyzer,
            'P648': OpenLibraryAnalyzer,
            'P650': RkdArtistsAnalyzer,
            'P651': BiografischPortaalAnalyzer,
            'P691': NkcrAnalyzer,
            'P723': DbnlAnalyzer,
            'P781': SikartAnalyzer,
            'P839': ImslpAnalyzer,
            'P902': HdsAnalyzer,
            'P906': SelibrAnalyzer,
            'P950': BneAnalyzer,
            'P1005': PtbnpAnalyzer,
            # 'P1006': NtaAnalyzer,
            'P1015': BibsysAnalyzer,
            'P1138': KunstindeksAnalyzer,
            'P1146': IaafAnalyzer,
            # 'P1153': ScopusAnalyzer, <requires login>
            'P1185': RodovidAnalyzer,
            'P1220': IbdbAnalyzer,
            'P1233': IsfdbAnalyzer,
            'P1263': NndbAnalyzer,
            'P1273': CanticAnalyzer,
            'P1280': ConorSiAnalyzer,
            'P1284': MunzingerAnalyzer,
            # 'P1305': SkyScraperAnalyzer, <forbidden>

            # <changed, content is not on page any more>
            # 'P1315': PeopleAustraliaAnalyzer,
            'P1367': ArtUkAnalyzer,
            'P1368': LnbAnalyzer,
            'P1415': OxfordAnalyzer,
            'P1422': SandrartAnalyzer,
            'P1440': FideAnalyzer,
            'P1447': SportsReferenceAnalyzer,
            'P1463': PrdlAnalyzer,
            'P1469': FifaAnalyzer,
            'P1556': ZbmathAnalyzer,
            'P1580': UBarcelonaAnalyzer,
            'P1607': DialnetAnalyzer,
            'P1615': ClaraAnalyzer,
            'P1648': WelshBioAnalyzer,
            'P1667': TgnAnalyzer,
            # 'P1695': NlpAnalyzer, <id doesn't work anymore>
            'P1707': DaaoAnalyzer,
            # 'P1711': BritishMuseumAnalyzer, <does not load>
            'P1741': GtaaAnalyzer,
            'P1749': ParlementPolitiekAnalyzer,
            'P1795': AmericanArtAnalyzer,
            'P1802': EmloAnalyzer,
            'P1816': NpgPersonAnalyzer,
            'P1819': GenealogicsAnalyzer,
            'P1838': PssBuildingAnalyzer,
            'P1871': CerlAnalyzer,
            'P1952': MetallumAnalyzer,
            'P1953': DiscogsAnalyzer,
            'P1977': ArchivesDuSpectacleAnalyzer,
            'P1986': ItalianPeopleAnalyzer,
            'P1988': DelargeAnalyzer,
            'P2005': HalensisAnalyzer,
            # 'P2013': FacebookAnalyzer, <requires being logged in>
            'P2016': AcademiaeGroninganaeAnalyzer,
            'P2029': UlsterAnalyzer,
            'P2038': ResearchGateAnalyzer,
            'P2041': NgvAnalyzer,
            'P2089': JukeboxAnalyzer,
            'P2163': FastAnalyzer,
            'P2168': SvenskFilmAnalyzer,
            'P2191': NilfAnalyzer,
            'P2252': NgaAnalyzer,
            'P2268': OrsayAnalyzer,
            'P2332': ArtHistoriansAnalyzer,
            'P2340': CesarAnalyzer,
            'P2342': AgorhaAnalyzer,
            'P2349': StuttgartAnalyzer,
            'P2372': OdisAnalyzer,
            'P2381': AcademicTreeAnalyzer,
            'P2383': CthsAnalyzer,
            'P2446': TransfermarktAnalyzer,
            'P2454': KnawAnalyzer,
            'P2456': DblpAnalyzer,
            'P2469': TheatricaliaAnalyzer,
            # 'P2533': WomenWritersAnalyzer, #fully opaque
            'P2604': KinopoiskAnalyzer,
            'P2605': CsfdAnalyzer,
            'P2639': FilmportalAnalyzer,
            'P2728': CageMatchAnalyzer,
            'P2732': PerseeAnalyzer,
            'P2750': PhotographersAnalyzer,
            'P2753': CanadianBiographyAnalyzer,
            'P2829': IWDAnalyzer,
            'P2843': BenezitAnalyzer,
            'P2915': EcarticoAnalyzer,
            'P2940': RostochiensiumAnalyzer,
            'P2941': MunksRollAnalyzer,
            'P2944': PlarrAnalyzer,
            'P2945': BookTradeAnalyzer,
            'P2949': WikitreeAnalyzer,
            'P2963': GoodreadsAnalyzer,
            'P2977': LbtAnalyzer,
            'P3029': NationalArchivesAnalyzer,
            'P3107': LdifAnalyzer,
            'P3109': PeakbaggerAnalyzer,
            'P3138': OfdbAnalyzer,
            'P3154': RunebergAuthorAnalyzer,
            'P3159': UGentAnalyzer,
            'P3283': BandcampAnalyzer,
            'P3314': Chess365Analyzer,
            'P3346': HkmdbAnalyzer,
            'P3351': AdultFilmAnalyzer,
            'P3360': NobelPrizeAnalyzer,
            'P3392': SurmanAnalyzer,
            'P3410': CcedAnalyzer,
            'P3413': LeopoldinaAnalyzer,
            'P3429': EnlightenmentAnalyzer,
            'P3430': SnacAnalyzer,
            'P3630': BabelioAnalyzer,
            'P3782': ArtnetAnalyzer,
            'P3786': DanskefilmAnalyzer,
            'P3788': BnaAnalyzer,
            'P3790': AnimeConsAnalyzer,
            'P3829': PublonsAnalyzer,
            'P3844': SynchronkarteiAnalyzer,
            'P3924': TrackFieldFemaleAnalyzer,
            'P3925': TrackFieldMaleAnalyzer,
            'P4124': WhosWhoFranceAnalyzer,
            'P4145': AthenaeumAnalyzer,
            'P4158': AutoresArAnalyzer,
            'P4206': FoihAnalyzer,
            'P4228': EoasAnalyzer,
            # 'P4293': PM20Analyzer, <content in frame with unclear url>
            'P4399': ItauAnalyzer,
            'P4432': AKLAnalyzer,
            'P4459': SpanishBiographyAnalyzer,
            'P4548': CommonwealthGamesAnalyzer,
            'P4585': AccademiaCruscaAnalyzer,
            'P4629': OnlineBooksAnalyzer,
            'P4657': NumbersAnalyzer,
            'P4663': DacsAnalyzer,
            'P4666': CinemagiaAnalyzer,
            'P4687': PeintresBelgesAnalyzer,
            'P4749': AuteursLuxembourgAnalyzer,
            'P4759': LuminousAnalyzer,
            'P4769': GameFaqsAnalyzer,
            'P4823': AmericanBiographyAnalyzer,
            'P4872': GeprisAnalyzer,
            'P4887': WebumeniaAnalyzer,
            'P4927': InvaluableAnalyzer,
            'P4929': AinmAnalyzer,
            'P4985': TmdbAnalyzer,
            'P5034': LibraryKoreaAnalyzer,
            'P5068': KunstenpuntAnalyzer,
            'P5239': ArtistsCanadaAnalyzer,
            'P5240': RollDaBeatsAnalyzer,
            'P5246': PornhubAnalyzer,
            'P5267': YoupornAnalyzer,
            'P5273': NelsonAtkinsAnalyzer,
            'P5329': ArmbAnalyzer,
            'P5359': OperoneAnalyzer,
            'P5361': BnbAnalyzer,
            'P5365': InternetBookAnalyzer,
            'P5375': BiuSanteAnalyzer,
            'P5394': PoetsWritersAnalyzer,
            'P5308': ScottishArchitectsAnalyzer,
            'P5357': SFAnalyzer,
            'P5368': NatGeoCanadaAnalyzer,
            'P5370': EntomologistAnalyzer,
            'P5408': FantasticFictionAnalyzer,
            'P5415': WhonameditAnalyzer,
            'P5421': TradingCardAnalyzer,
            'P5491': BedethequeAnalyzer,
            'P5492': Edit16Analyzer,
            'P5504': RismAnalyzer,
            'P5534': OmdbAnalyzer,
            'P5540': RedTubeAnalyzer,
            'P5570': NoosfereAnalyzer,
            'P5597': ArtcyclopediaAnalyzer,
            'P5645': AcademieFrancaiseAnalyzer,
            'P5731': AngelicumAnalyzer,
            'P5739': PuscAnalyzer,
            'P5747': CwaAnalyzer,
            'P5794': IgdbAnalyzer,
            'P5819': MathOlympAnalyzer,
            'P5882': MuziekwebAnalyzer,
            'P6127': LetterboxdAnalyzer,
            'P6167': BritishExecutionsAnalyzer,
            'P6188': BdfaAnalyzer,
            'P6194': AustrianBiographicalAnalyzer,
            'P6231': BdelAnalyzer,
            'P6295': ArticArtistAnalyzer,
            'P6517': WhoSampledAnalyzer,
            'P6575': AcademieRouenAnalyzer,
            'P6578': MutualAnalyzer,
            'P6594': GuggenheimAnalyzer,
            'P6770': SnsaAnalyzer,
            'P6815': UvaAlbumAnalyzer,
            'P6821': AlvinAnalyzer,
            'P6844': AbartAnalyzer,
            'P6873': IntraTextAnalyzer,
            'P7032': RepertoriumAnalyzer,
            'P7293': PlwabnAnalyzer,
            'P7796': BewebAnalyzer,
            'P7902': DeutscheBiographieAnalyzer,
            'P8287': WorldsWithoutEndAnalyzer,
            'P8696': BelgianPhotographerAnalyzer,
            'P8795': AlkindiAnalyzer,
            'P8848': ConorAlAnalyzer,
            'P8849': ConorBgAnalyzer,
            'P8851': ConorSrAnalyzer,
            'P8914': ZobodatAnalyzer,
            'P9017': OxfordMedievalAnalyzer,
            # 'P9046': AdSAnalyzer, hard to analyze JavaScript
            'P9113': PatrinumAnalyzer,
            'P9430': JwaAnalyzer,
            'fomu.atomis.be': FotomuseumAnalyzer,
            'catalogo.bn.gov.ar': BibliotecaNacionalAnalyzer,
            'www.brooklynmuseum.org': BrooklynMuseumAnalyzer,
            'www.vondel.humanities.uva.nl': OnstageAnalyzer,
            'www.ias.edu': IasAnalyzer,
            'kunstaspekte.art': KunstaspekteAnalyzer,
            'www.nationaltrustcollections.org.uk': NationalTrustAnalyzer,
            'www.oxfordartonline.com': BenezitUrlAnalyzer,
            'exhibitions.univie.ac.at': UnivieAnalyzer,
            'weber-gesamtausgabe.de': WeberAnalyzer,
            'Wiki': WikiAnalyzer,
            'Data': BacklinkAnalyzer,
            'www.deutsche-biographie.de': DeutscheBiographieAnalyzer,
        }

    def label(self, title):
        if title.startswith('!date!'):
            return self.showtime(self.createdateclaim(title[6:]))
        if title.startswith('!q!'):
            return title[3:]
        if not self.PQRE.fullmatch(title):
            return title

        if title in self.labels:
            return self.labels[title]

        item = self.page(title)
        try:
            labels = item.get()['labels']
        except NoPageError:
            labels = {}
        for lang in ['en', 'nl', 'de', 'fr', 'es', 'it', 'af', 'nds', 'li',
                     'vls', 'zea', 'fy', 'no', 'sv', 'da', 'pt', 'ro', 'pl',
                     'cs', 'sk', 'hr', 'et', 'fi', 'lt', 'lv', 'tr', 'cy']:
            if lang in labels:
                try:
                    label = labels[lang]['value']
                except TypeError:
                    label = labels[lang]
                break
        else:
            label = title
        self.labels[title] = label
        return label

    def loaddata(self):
        """Read data from files."""
        param = {'mode': 'r', 'encoding': 'utf-8'}

        with suppress(IOError), codecs.open(self.labelfile, **param) as f:
            for line in f.readlines():
                key, value = line.strip().split(':', 1)
                self.labels[key] = value

        with suppress(IOError), codecs.open(self.datafile, **param) as f:
            for line in f.readlines():
                parts = line.strip().split(':')
                # assume len(parts) > 1
                dtype, *keys, value = parts
                key = ':'.join(keys)
                self.data[dtype][key] = value

        with suppress(IOError), codecs.open(self.nonamefile, **param) as f:
            self.noname = {line.strip() for line in f.readlines()}

    def teardown(self) -> None:
        """Save data to files."""
        param = {'mode': 'w', 'encoding': 'utf-8'}

        with codecs.open(self.labelfile, **param) as f:
            for item in self.labels:
                f.write(f'{item}:{self.labels[item]}\n')

        with codecs.open(self.datafile, **param) as f:
            for dtype in self.data:
                for key in self.data[dtype]:
                    f.write('{}:{}:{}\n'.format(dtype, key,
                                                self.data[dtype][key]))

        with codecs.open(self.nonamefile, **param) as f:
            for noname in self.noname:
                f.write(f'{noname}\n')

    def page(self, title):
        """Dispatch title and return the appropriate Page object."""
        title = title.rsplit(':', 1)[-1]
        if title.startswith('Q'):
            return pywikibot.ItemPage(self.site, title)
        if title.startswith('P'):
            return pywikibot.PropertyPage(self.site, title)
        raise ValueError(f'Invalid title {title}')

    @staticmethod
    def showtime(time):
        if time is None:
            return 'unknown'
        result = str(time.year)
        if time.precision < 9:
            result = 'ca. ' + result
        if time.precision >= 10:
            result = f'{time.month}-{result}'
        if time.precision >= 11:
            result = f'{time.day}-{result}'
        if time.precision >= 12:
            result = f'{result} {time.hour}'
        if time.precision >= 13:
            result = f'{result}:{time.minute}'
        if time.precision >= 14:
            result = f'{result}:{time.second}'
        return result

    def showclaims(self, claims):
        pywikibot.info('Current information:')
        for prop in claims:
            for claim in claims[prop]:
                if claim.type == 'wikibase-item':
                    if claim.getTarget() is None:
                        pywikibot.info(f'{self.label(prop)}: unknown')
                    else:
                        pywikibot.info(
                            '{}: {}'
                            .format(self.label(prop),
                                    self.label(claim.getTarget().title())))
                elif claim.type == 'time':
                    pywikibot.info('{}: {}'
                                   .format(self.label(prop),
                                           self.showtime(claim.getTarget())))
                elif claim.type in ['external-id', 'commonsMedia']:
                    pywikibot.info('{}: {}'.format(self.label(prop),
                                                   claim.getTarget()))
                elif claim.type == 'quantity':
                    pywikibot.info(
                        '{}: {} {}'
                        .format(self.label(prop),
                                claim.getTarget().amount,
                                self.label(
                                    claim.getTarget().unit.split('/')[-1])))
                else:
                    pywikibot.info('Unknown type {} for property {}'
                                   .format(claim.type, self.label(prop)))

    MONTHNUMBER = {
        '1': 1, '01': 1, 'i': 1,
        '2': 2, '02': 2, 'ii': 2,
        '3': 3, '03': 3, 'iii': 3,
        '4': 4, '04': 4, 'iv': 4,
        '5': 5, '05': 5, 'v': 5,
        '6': 6, '06': 6, 'vi': 6,
        '7': 7, '07': 7, 'vii': 7,
        '8': 8, '08': 8, 'viii': 8,
        '9': 9, '09': 9, 'ix': 9,
        '10': 10, 'x': 10,
        '11': 11, 'xi': 11,
        '12': 12, 'xii': 12,
        'january': 1, 'jan': 1,
        'february': 2, 'feb': 2, 'febr': 2,
        'march': 3, 'mar': 3,
        'april': 4, 'apr': 4,
        'may': 5,
        'june': 6, 'jun': 6,
        'july': 7, 'jul': 7,
        'august': 8, 'aug': 8,
        'september': 9, 'sep': 9, 'sept': 9,
        'october': 10, 'oct': 10,
        'november': 11, 'nov': 11,
        'december': 12, 'dec': 12,
        'gennaio': 1, 'gen': 1, 'genn': 1,
        'febbraio': 2, 'febb': 2, 'febbr': 2,
        'marzo': 3, 'marz': 3,
        'aprile': 4,
        'maggio': 5, 'mag': 5, 'magg': 5,
        'giugno': 6, 'giu': 6,
        'luglio': 7, 'lug': 7, 'lugl': 7,
        'agosto': 8, 'ago': 8, 'agost': 8, 'ag': 8,
        'settembre': 9, 'set': 9, 'sett': 9,
        'ottobre': 10, 'ott': 10, 'otto': 10,
        'novembre': 11,
        'dicembre': 12, 'dic': 12,
        'januari': 1,
        'februari': 2,
        'maart': 3, 'maa': 3, 'mrt': 3,
        'mei': 5,
        'juni': 6,
        'juli': 7,
        'augustus': 8,
        'oktober': 10, 'okt': 10,
        'janvier': 1,
        'février': 2, 'fevrier': 2, 'fév': 2, 'fev': 2, 'f\\xe9vrier': 2,
        'mars': 3,
        'avril': 4, 'avr': 4,
        'mai': 5,
        'juin': 6,
        'juillet': 7,
        'août': 8, 'aout': 8, 'aoû': 8, 'aou': 8,
        'septembre': 9,
        'octobre': 10,
        'décembre': 12, 'déc': 12,
        'januar': 1, 'jänner': 1,
        'februar': 2,
        'märz': 3, 'm\\xe4rz': 3,
        'dezember': 12, 'dez': 12,
        'eanáir': 1, 'eanair': 1,
        'feabhra': 2,
        'márta': 3, 'marta': 3,
        'aibreán': 4, 'aibrean': 4,
        'bealtaine': 5,
        'meitheamh': 6,
        'iúil': 7, 'iuil': 7,
        'lúnasa': 8, 'lunasa': 8,
        'meán fómhair': 9, 'mean fomhair': 9,
        'deireadh fómhair': 10, 'deireadh fomhair': 10,
        'samhain': 11,
        'nollaig': 12,
        'styczeń': 1, 'stycznia': 1,
        'luty': 2, 'lutego': 2,
        'marzec': 3, 'marca': 3,
        'kwiecień': 4, 'kwietnia': 4,
        'maj': 5, 'maja': 5,
        'czerwiec': 6, 'czerwca': 6,
        'lipiec': 7, 'lipca': 7,
        'sierpień': 8, 'sierpnia': 8,
        'wrzesień': 9, 'września': 9,
        'październik': 10, 'października': 10,
        'listopad': 11, 'listopada': 11,
        'grudzień': 12, 'grudnia': 12,
        'enero': 1,
        'febrero': 2,
        'abril': 4,
        'mayo': 5,
        'junio': 6,
        'julio': 7,
        'septiembre': 9,
        'octubre': 10,
        'noviembre': 11,
        'diciembre': 12,
        'gener': 1,
        'febrer': 2,
        'març': 3,
        'maig': 5,
        'juny': 6,
        'juliol': 7,
        'setembre': 9,
        'desembre': 12,
    }

    def createdateclaim(self, text):
        text = text.strip()
        year = None
        month = None
        day = None
        m = re.search(r'[{\|](\d{4})\|(\d+)\|(\d+)[\|}]', text)
        if m:
            year = int(m[1])
            month = int(m[2])
            day = int(m[3])
        m = re.fullmatch(r'(\d{1,4})(?:年頃|\.)?', text)
        if m:
            year = int(m[1])
            month = None
            day = None
        if re.fullmatch(r'(?:1\d{3}|20[01]\d)[01]\d[0123]\d', text):
            year = int(text[:4])
            month = int(text[4:6])
            day = int(text[6:])
        if re.fullmatch(r'\d{4}-\d{2}', text):
            year = int(text[:4])
            month = int(text[-2:])
        m = re.match(r'(\d{1,2})[-/](\d{4})', text)
        if m:
            year = int(m[2])
            month = int(m[1])
        m = re.fullmatch(r'(\d+)[-./|](\d{1,2})[-./|](\d{1,2})', text)
        if m:
            year = int(m[1])
            month = int(m[2])
            day = int(m[3])
        m = re.fullmatch(
            r'(\d{1,2})[-./|]\s*(\d{1,2})[-./|]\s*(\d{3,4})\.?', text)
        if m:
            year = int(m[3])
            month = int(m[2])
            day = int(m[1])
        m = re.fullmatch(r'(\d{1,2})[-./\s]([iIvVxX]+)[-./\s](\d{4})', text)
        if m:
            year = int(m[3])
            try:
                month = self.MONTHNUMBER[m[2].lower()]
            except KeyError:
                raise ValueError(f"Don't know month {m[2]}")
            day = int(m[1])
        m = re.fullmatch(r"(\d+)(?:\.|er|eme|ème)?[\s.]\s*(?:d'|d[aei] )?"
                         r'([^\s.]{2,})\.?[\s.]\s*(\d+)', text)
        if m:
            year = int(m[3])
            try:
                month = self.MONTHNUMBER[m[2].lower()]
            except KeyError:
                raise ValueError(f"Don't know month {m[2]}")
            day = int(m[1])
        m = re.fullmatch(
            r'(\d{4})\.?[\s.]\s*([^\s.]{3,})\.?[\s.]\s*(\d+)', text)
        if m:
            year = int(m[1])
            try:
                month = self.MONTHNUMBER[m[2].lower()]
            except KeyError:
                raise ValueError(f"Don't know month {m[2]}")
            day = int(m[3])
        m = re.match(r"(\d+) (?:de |d')?(\w+[a-z]\w+) de (\d+)", text)
        if m:
            year = int(m[3])
            try:
                month = self.MONTHNUMBER[m[2].lower()]
            except KeyError:
                raise ValueError(f"Don't know month {m[2]}")
            day = int(m[1])
        m = re.fullmatch(r'(\w*[a-zA-Z]\w*)\.? (\d+)', text)
        if m:
            year = int(m[2])
            try:
                month = self.MONTHNUMBER[m[1].lower()]
            except KeyError:
                raise ValueError(f"Don't know month {m[1]}")
        m = re.fullmatch(
            r'(\w+)\.? (\d{1,2})(?:st|nd|rd|th)?\.?\s*,\s*(\d{3,4})', text)
        if m:
            year = int(m[3])
            try:
                month = self.MONTHNUMBER[m[1].lower()]
            except KeyError:
                raise ValueError(f"Don't know month {m[1]}")
            day = int(m[2])
        m = re.match(r'(\d{4}),? (\d{1,2}) (\w+)', text)
        if m:
            year = int(m[1])
            try:
                month = self.MONTHNUMBER[m[3].lower()]
            except KeyError:
                raise ValueError(f"Don't know month {m[1]}")
            day = int(m[2])
        m = re.match(r'(\d+)年(\d+)月(\d+)日', text)
        if m:
            year = int(m[1])
            month = int(m[2])
            day = int(m[3])
        m = re.fullmatch(r'(\d+)年', text)
        if m:
            year = int(m[1])
        if day == 0:
            day = None
        if day is None and month == 0:
            month = None
        if month and month > 12:
            raise ValueError('Date seems to have an invalid month number {}'
                             .format(month))
        if day and day > 31:
            raise ValueError('Date seems to have an invalid day number {}'
                             .format(day))
        if not year:
            raise ValueError(f"Can't interpret date {text}")
        return pywikibot.WbTime(year=year, month=month, day=day, precision=9
                                if month is None
                                else 10 if day is None else 11)

    QUANTITYTYPE = {
        'meter': 'Q11573', 'metre': 'Q11573', 'm': 'Q11573',
        'meters': 'Q11573', 'metres': 'Q11573', 'м': 'Q11573',
        'centimeter': 'Q174728', 'centimetre': 'Q174728', 'cm': 'Q174728',
        'foot': 'Q3710', 'feet': 'Q3710', 'ft': 'Q3710',
        'mile': 'Q253276', 'mi': 'Q253276',
        'kilometer': 'Q828224', 'kilometre': 'Q828224', 'km': 'Q828224',
        'minute': 'Q7727', 'minutes': 'Q7727', 'min': 'Q7727',
        'minuten': 'Q7727',
        'second': 'Q11574', 's': 'Q11574',
        'kilogram': 'Q11570', 'kg': 'Q11570',
        'lb': 'Q100995', 'lbs': 'Q100995', 'pond': 'Q100995',
    }

    def createquantityclaim(self, text):
        m = re.match(r'(\d+(?:\.\d+)?)\s*([a-z]\w*)', text.replace(',', '.'))
        amount = m[1]
        name = m[2].lower()
        return pywikibot.WbQuantity(amount,
                                    unit=pywikibot.ItemPage(
                                        self.site, self.QUANTITYTYPE[name]),
                                    site=self.site)

    def treat(self, item) -> None:
        """Process the ItemPage."""
        item.get()
        claims = item.claims
        self.showclaims(claims)
        if self.opt.showonly:
            return

        longtexts = []
        newdescriptions = defaultdict(set)
        updatedclaims = {prop: claims[prop] for prop in claims}
        dorestrict = True
        continueafterrestrict = False

        restrict_end = self.opt.restrict and self.opt.restrict[-1]
        if restrict_end in ('+', '*'):
            self.opt.restrict = self.opt.restrict[:-1]
            continueafterrestrict = True

        if restrict_end == '*':
            dorestrict = False

        unidentifiedprops = []
        failedprops = []
        claims['Wiki'] = [Quasiclaim(page.title(force_interwiki=True,
                                                as_link=True)[2:-2])
                          for page in item.iterlinks()]
        claims['Data'] = [Quasiclaim(item.title())]
        propstodo = DequeGenerator(claims)
        propsdone = set()

        for prop in propstodo:
            descriptions = item.descriptions
            labels = item.labels
            aliases = item.aliases

            # This can happen after reloading
            if prop not in claims.keys():
                continue

            if self.opt.restrict:
                if prop != self.opt.restrict:
                    continue
                if continueafterrestrict:
                    self.opt.restrict = ''
                if not dorestrict:
                    continue

            for mainclaim in claims[prop]:
                if mainclaim.type != 'external-id' and prop != 'P973':
                    continue

                identifier = mainclaim.getTarget()
                try:
                    analyzertype = self.analyzertype[identifier.split('/')[2]
                                                     if prop == 'P973'
                                                     else prop]
                except KeyError:
                    unidentifiedprops.append(prop)
                    continue

                analyzer = analyzertype(identifier, self.data,
                                        item.title(), self)
                newclaims = analyzer.findclaims() or []

                if newclaims is None:
                    failedprops.append(prop)
                    newclaims = []

                if not self.opt.always:
                    pywikibot.info('Found here:')
                    for claim in newclaims:
                        try:
                            pywikibot.info(
                                '{}: {}'.format(self.label(claim[0]),
                                                self.label(claim[1])))
                        except ValueError:
                            newclaims = [nclaim
                                         for nclaim in newclaims
                                         if nclaim != claim]

                if self.opt.always or input_yn('Save this?', default=True):
                    for claim in newclaims:
                        if claim[0] in updatedclaims \
                           and self.isinclaims(claim[1],
                                               updatedclaims[claim[0]]):
                            if claim[2]:
                                source = None
                                if claim[2].dbid:
                                    id_ = 'P143' if claim[2].iswiki else 'P248'
                                    source = pywikibot.Claim(self.site, id_)
                                    source.setTarget(
                                        pywikibot.ItemPage(self.site,
                                                           claim[2].dbid))

                                id_ = 'P4656' if claim[2].iswiki else 'P854'
                                url = pywikibot.Claim(self.site, id_)

                                if claim[2].sparqlquery:
                                    url.setTarget(pywikibot.ItemPage(
                                        self.site, claim[1]).full_url())
                                else:
                                    url.setTarget(claim[2].url)

                                if claim[2].iswiki or claim[2].isurl:
                                    iddata = None
                                else:
                                    iddata = pywikibot.Claim(self.site, prop)
                                    iddata.setTarget(identifier)

                                if url is None:
                                    date = None
                                else:
                                    date = pywikibot.Claim(self.site, 'P813')
                                    date.setTarget(
                                        self.createdateclaim(
                                            min(datetime.datetime.now()
                                                .strftime('%Y-%m-%d'),
                                                datetime.datetime.utcnow()
                                                .strftime('%Y-%m-%d'))))

                                if not analyzer.showurl:
                                    url = None

                                sourceparts = [source, url, iddata, date]
                                sourcedata = [sourcepart
                                              for sourcepart in sourceparts
                                              if sourcepart is not None]

                                pywikibot.info('Sourcing {}: {}'
                                               .format(self.label(claim[0]),
                                                       self.label(claim[1])))

                                # probably means the sourcing is already there
                                with suppress(APIError):
                                    updatedclaims[claim[0]][self.getlocnumber(
                                        claim[1],
                                        updatedclaims[claim[0]])].addSources(
                                            sourcedata)
                        else:
                            if claim[0] not in propsdone:
                                propstodo.append(claim[0])

                            createdclaim = pywikibot.Claim(self.site, claim[0])

                            if self.QRE.fullmatch(claim[1]):
                                createdclaim.setTarget(pywikibot.ItemPage(
                                    self.site, claim[1]))

                            elif claim[1].startswith('!date!'):
                                try:
                                    target = self.createdateclaim(claim[1][6:])
                                except ValueError as ex:
                                    pywikibot.info(
                                        'Unable to analyze date "{}" for {}: {}'
                                        .format(claim[1][6:],
                                                self.label(claim[0]), ex))
                                    pywikibot.input('Press enter to continue')
                                    target = None

                                if target is None:
                                    continue

                                createdclaim.setTarget(target)

                            elif claim[1].startswith('!q!'):
                                target = self.createquantityclaim(
                                    claim[1][3:].strip())

                                if target is None:
                                    continue

                                createdclaim.setTarget(target)

                            elif claim[1].startswith('!i!'):
                                createdclaim.setTarget(
                                    pywikibot.page.FilePage(self.site,
                                                            claim[1][3:]))
                            else:
                                createdclaim.setTarget(claim[1])

                            pywikibot.info('Adding {}: {}'
                                           .format(self.label(claim[0]),
                                                   self.label(claim[1])))

                            try:
                                item.addClaim(createdclaim)
                            except OtherPageSaveError as ex:
                                if claim[1].startswith('!i!'):
                                    pywikibot.info(
                                        'Unable to save image {}: {}'
                                        .format(claim[1][3:], ex))
                                    continue

                                raise

                            if claim[0] in updatedclaims:
                                updatedclaims[claim[0]].append(createdclaim)
                            else:
                                updatedclaims[claim[0]] = [createdclaim]

                            if claim[2]:
                                if claim[2].dbid:
                                    if claim[2].iswiki:
                                        source = pywikibot.Claim(self.site,
                                                                 'P143')
                                    else:
                                        source = pywikibot.Claim(self.site,
                                                                 'P248')
                                    source.setTarget(
                                        pywikibot.ItemPage(self.site,
                                                           claim[2].dbid))
                                else:
                                    source = None

                                if claim[2].iswiki:
                                    url = pywikibot.Claim(self.site, 'P4656')
                                else:
                                    url = pywikibot.Claim(self.site, 'P854')

                                if claim[2].sparqlquery:
                                    url.setTarget(
                                        pywikibot.ItemPage(
                                            self.site, claim[1]).full_url())
                                else:
                                    url.setTarget(claim[2].url)

                                if claim[2].iswiki or claim[2].isurl:
                                    iddata = None
                                else:
                                    iddata = pywikibot.Claim(self.site, prop)
                                    iddata.setTarget(identifier)

                                if url is None:
                                    date = None
                                else:
                                    date = pywikibot.Claim(
                                        self.site, 'P813')
                                    date.setTarget(self.createdateclaim(
                                        min(datetime.datetime.now().strftime(
                                            '%Y-%m-%d'),
                                            datetime.datetime.utcnow().strftime('%Y-%m-%d'))))
                                if not analyzer.showurl:
                                    url = None

                                sourcedata = [source, url, iddata, date]
                                sourcedata = [sourcepart
                                              for sourcepart in sourcedata
                                              if sourcepart is not None]
                                pywikibot.info('Sourcing {}: {}'
                                               .format(self.label(claim[0]),
                                                       self.label(claim[1])))

                                try:
                                    createdclaim.addSources(
                                        [s for s in sourcedata
                                         if s is not None])
                                except AttributeError:
                                    try:
                                        updatedclaims[claim[0]][
                                            self.getlocnumber(
                                                claim[1],
                                                updatedclaims[claim[0]])
                                        ].addSources(sourcedata)
                                    except AttributeError:
                                        if prop not in propsdone:
                                            propstodo.append(prop)
                                        pywikibot.info('Sourcing failed')

                for language, description in analyzer.getdescriptions():
                    newdescriptions[language].add(
                        shorten(description.rstrip('.'), width=249,
                                placeholder='...'))
                newnames = analyzer.getnames()
                newlabels, newaliases = self.definelabels(
                    labels, aliases, newnames)
                if newlabels:
                    item.editLabels(newlabels)
                if newaliases:
                    item.editAliases(newaliases)
                if newlabels or newaliases:
                    item.get(force=True)
                    claims = item.claims
                    claims['Wiki'] = [
                        Quasiclaim(
                            page.title(force_interwiki=True,
                                       as_link=True)[2:-2])
                        for page in item.iterlinks()
                    ]
                    claims['Data'] = [Quasiclaim(item.title())]
                    descriptions = item.descriptions
                    labels = item.labels
                    aliases = item.aliases
                if analyzer.longtext():
                    longtexts.append((analyzer.dbname,
                                      analyzer.longtext()))

            propsdone.add(prop)
            item.get(force=True)
            claims = item.claims
            claims['Wiki'] = [Quasiclaim(page.title(force_interwiki=True,
                                                    as_link=True)[2:-2])
                              for page in item.iterlinks()]
            claims['Data'] = [Quasiclaim(item.title())]

        editdescriptions = {}
        for language in newdescriptions.keys():
            newdescription = self.definedescription(
                language, descriptions.get(language),
                newdescriptions.get(language))
            if newdescription:
                editdescriptions[language] = newdescription
        if editdescriptions:
            item.editDescriptions(editdescriptions)
        for prop in unidentifiedprops:
            pywikibot.info('Unknown external {} ({})'
                           .format(prop, self.label(prop)))
        for prop in failedprops:
            pywikibot.info('External failed to load: {} ({})'
                           .format(prop, self.label(prop)))
        if longtexts:
            if unidentifiedprops or failedprops:
                pywikibot.input('Press Enter to continue')
            pywikibot.info('== longtexts ==')
            for longtext in longtexts:
                pywikibot.info(f'\n== {longtext[0]} ==\n{longtext[1]}')
                pywikibot.input('(press enter)')

    @staticmethod
    def definedescription(language, existingdescription, suggestions):
        possibilities = [existingdescription] + list(suggestions)

        pywikibot.info(f'\nSelect a description for language {language}:')
        pywikibot.info('Default is to keep the old value (0)')
        for i, pos in enumerate(possibilities):
            if pos is None:
                pywikibot.info(f'{i}: No description')
            else:
                pywikibot.info(f'{i}: {pos}')
        answer = pywikibot.input('Which one to choose? ')
        try:
            answer = int(answer)
        except ValueError:
            answer = 0
        if answer:
            return possibilities[answer]
        return None

    def definelabels(self, existinglabels, existingaliases, newnames):
        realnewnames = defaultdict(list)
        anythingfound = False
        for (language, name) in newnames:
            name = name.strip()
            if name.lower() == (existinglabels.get(language) or '').lower() \
               or name.lower() in (n.lower()
                                   for n in existingaliases.get(language, [])):
                continue

            if name not in realnewnames[language] and name not in self.noname:
                realnewnames[language].append(name)
                anythingfound = True

        if anythingfound:
            pywikibot.info('\nNew names found:')
            for language in realnewnames.keys():
                for name in realnewnames[language]:
                    pywikibot.info(f'{language}: {name}')
            result = pywikibot.input('Add these names? (y/n/[S]elect/x) ')
            if not result or result[0].upper() not in 'YNX':
                chosennewnames = defaultdict(list)
                for language in realnewnames.keys():
                    for name in realnewnames[language]:
                        result = pywikibot.input(f'{language}: {name} - ')
                        if (not result) or result[0].upper() == 'Y':
                            chosennewnames[language].append(name)
                        elif result[0].upper() == 'X':
                            self.noname.add(name)
                realnewnames = chosennewnames
                result = 'Y'
            if result[0].upper() == 'X':
                for language in realnewnames.keys():
                    for name in realnewnames[language]:
                        self.noname.add(name)
            elif result[0].upper() != 'N':
                returnvalue = [{}, {}]
                for language in realnewnames:
                    if language in existinglabels:
                        returnvalue[1][language] = existingaliases.get(
                            language, []) + realnewnames[language]
                    else:
                        returnvalue[0][language] = realnewnames[language][0]
                        if realnewnames[language]:
                            returnvalue[1][language] = existingaliases.get(
                                language, []) + realnewnames[language][1:]
                return returnvalue
        return [{}, {}]

    def isclaim(self, value, claim):
        try:
            if value.startswith('!date!'):
                value = value[6:]
            if value.startswith('!q!'):
                value = re.search(r'\d+(?:\.\d+)?', value)[0]
            elif value.startswith('!i!'):
                value = value[3:].strip()

            if str(claim.getTarget()) == value:
                return True
            if claim.type == 'wikibase-item' \
               and claim.getTarget().title() == value:
                return True
            if claim.type == 'commonsMedia' \
                    and claim.getTarget().title().split(
                        ':', 1)[1].replace('_', ' ') == value.replace('_', ' '):
                return True
            if claim.type == 'time' \
               and self.showtime(claim.getTarget()) == self.showtime(
                   self.createdateclaim(value)):
                return True

        except (ValueError, AttributeError):
            return False

    def isinclaims(self, value, claims):
        return any(self.isclaim(value, claim) for claim in claims)

    def getlocnumber(self, value, claims):
        for pair in zip(range(len(claims)), claims):
            if self.isclaim(value, pair[1]):
                return pair[0]
        raise ValueError


class Quasiclaim:

    def __init__(self, title):
        """Initializer."""
        self._target = title

    @property
    def type(self):
        return 'external-id'

    def getTarget(self):  # noqa: N802
        """Return the target value of this QuasiClaim."""
        return self._target


class Analyzer:
    TAGRE = re.compile('<[^<>]*>')
    SCRIPTRE = re.compile('(?s)<script.*?</script>')

    def __init__(self, id, data=None, item=None, bot=None):
        """Initializer."""
        self.id = id
        self.data = defaultdict(dict) if data is None else data
        self.dbname = None
        self.urlbase = None
        self.urlbase2 = None
        self.urlbase3 = self.urlbase4 = None
        self.showurl = True
        self.dbid = None
        self.dbitem = None
        self.dbproperty = None
        self.hrtre = None
        self.language = 'en'
        self.escapeunicode = False
        self.escapehtml = False
        self.escapeurl = False
        self.item = item
        self.iswiki = False
        self.sparqlquery = None
        self.isurl = False
        self.skipfirst = False
        self.bot = bot
        self.setup()
        self.site = pywikibot.Site().data_repository()

    def setup(self):
        """To be used for putting data into subclasses."""

    @property
    def url(self):
        usedurl = self.urlbase
        if usedurl is None:
            if not self.sparqlquery:
                pywikibot.info(
                    f'\n### Skipping {self.dbname} ({self.dbproperty}) ###')
            return None
        return usedurl.format(id=quote(self.id))

    @property
    def alturl(self):
        if self.urlbase2:
            return self.urlbase2.format(id=quote(self.id))
        return None

    @property
    def extraurls(self) -> List[str]:
        if not self.urlbase3:
            return []

        if self.urlbase4:
            return [self.urlbase3.format(id=quote(self.id)),
                    self.urlbase4.format(id=quote(self.id))]

        return [self.urlbase3.format(id=quote(self.id))]

    @staticmethod
    def commastrip(term):
        term = re.sub(r'(?:\s|&nbsp;)+', ' ', term)
        term = term.strip().strip(',').rstrip('.').strip()
        term = term.split('(')[0]
        if ',' in term:
            if term.split(',')[1].strip().lower() in ['jr', 'sr']:
                term += '.'
            else:
                if term.strip()[-1] != term.strip()[-1].lower():
                    term = term.strip() + '.'
                term = term.split(',', 1)[1] + ' ' + term.split(',', 1)[0]
        term = re.sub(r'\s*-\s*', '-', term)
        return unescape(term).strip()

    def getdata(self, dtype, text, ask=True):
        text = text.strip('. ').lower().replace('\\n', ' ').replace(
            '\n', ' ').replace('%20', ' ').strip()
        text = re.sub(' +', ' ', text)

        if not text:
            return None
        if dtype in self.data and text in self.data[dtype]:

            if self.data[dtype][text] == 'XXX':
                return None

            return self.data[dtype][text]

        if not ask:
            return None

        pywikibot.info(f"Trying to get a {dtype} out of '{text}'")
        answer = pywikibot.input(
            'Type Qnnn to let it point to Qnnn from now on,\n'
            'Xnnn to let it point to Qnnn only now,\n'
            'XXX to never use it, or nothing to not use it now')
        if answer.startswith('Q'):
            self.data[dtype][text] = answer
        elif answer.upper() == 'XXX':
            self.data[dtype][text] = 'XXX'
            answer = None
        elif answer.startswith('X'):
            answer = 'Q' + answer[1:]
        else:
            answer = None
        return answer

    def findclaims(self) -> List[Tuple[str, str, Optional['Analyzer']]]:
        if not self.id or not (self.url or self.sparqlquery):
            return []

        self.html = ''
        newclaims = []
        pywikibot.info()
        pagerequest = None
        if not self.skipfirst:
            for used, base in enumerate(self.urlbase, self.urlbase2):
                if used and not base:
                    continue
                self.urlbase = base
                pywikibot.info(f'Getting {self.url}')
                with suppress(ServerError, ConnectionError):
                    pagerequest = http.fetch(self.url)
                    break
            else:
                pywikibot.info(f'Unable to load {self.url}')
                return []

        if pagerequest:
            self.html = pagerequest.text

        for extraurl in self.extraurls:
            pywikibot.info(f'Getting {extraurl}')
            try:
                pagerequest = http.fetch(extraurl)
            except (ServerError, ConnectionError):
                pywikibot.info('Unable to receive altpage')
            else:
                self.html += '\n' + pagerequest.text

        if self.sparqlquery:
            self.html = str(sparql.SparqlQuery().select(self.sparqlquery))

        if not self.html:
            return []

        if self.escapeunicode:
            self.html = self.html.encode().decode('unicode-escape')
        if self.escapehtml:
            self.html = unescape(self.html)
        if self.escapeurl:
            self.html = unquote(self.html)
        self.html = self.prepare(self.html)

        pywikibot.info(f'\n=== {self.dbname} ({self.dbproperty}) ====')
        if self.hrtre:
            match = re.compile('(?s)' + self.hrtre).search(self.html)
            if match:
                text = match[1]
                text = text.replace('\\n', '\n')
                text = text.replace('\\t', '\t')
                text = text.replace('\\r', '\n')
                text = text.replace('\r', '\n')
                text = text.replace('\t', ' ')
                oldtext = ''
                while oldtext != text:
                    oldtext = text
                    text = self.SCRIPTRE.sub('', text)
                oldtext = ''
                while oldtext != text:
                    oldtext = text
                    text = self.TAGRE.sub(' ', text)
                while '&nbsp;' in text:
                    text = text.replace('&nbsp;', ' ')
                while '  ' in text:
                    text = text.replace('  ', ' ')
                while '\n ' in text:
                    text = text.replace('\n ', '\n')
                while '\n\n' in text:
                    text = text.replace('\n\n', '\n')
                text = text.strip()
                pywikibot.info(text)
        pywikibot.info('-' * (len(self.dbname) + 8))
        for (function, prop) in [
            (self.findinstanceof, 'P31'),
            (self.findfirstname, 'P735'),
            (self.findlastname, 'P734'),
        ]:
            result = function(self.html)
            if result:
                newclaims.append((prop, result.strip(), None))

        for (function, prop) in [
            (self.findcountries, 'P17'),
            (self.findspouses, 'P26'),
            (self.findpartners, 'P451'),
            (self.findworkplaces, 'P937'),
            (self.findresidences, 'P551'),
            (self.findoccupations, 'P106'),
            (self.findworkfields, 'P101'),
            (self.findpositions, 'P39'),
            (self.findtitles, 'P97'),
            (self.findemployers, 'P108'),
            (self.findranks, 'P410'),
            (self.findschools, 'P69'),
            (self.findethnicities, 'P172'),
            (self.findcrimes, 'P1399'),
            (self.findcomposers, 'P86'),
            (self.findmoviedirectors, 'P57'),
            (self.findartdirectors, 'P3174'),
            (self.findscreenwriters, 'P58'),
            (self.findproducers, 'P162'),
            (self.finddirectorsphotography, 'P344'),
            (self.findmovieeditors, 'P1040'),
            (self.findproductiondesigners, 'P2554'),
            (self.findsounddesigners, 'P5028'),
            (self.findcostumedesigners, 'P2515'),
            (self.findmakeupartists, 'P4805'),
            (self.findarchitects, 'P84'),
            (self.findgenres, 'P136'),
            (self.findengines, 'P408'),
            (self.findgamemodes, 'P404'),
            (self.findcast, 'P161'),
            (self.findmaterials, 'P186'),
            (self.finddevelopers, 'P178'),
            (self.findpublishers, 'P123'),
            (self.findprodcoms, 'P272'),
            (self.finddistcoms, 'P750'),
            (self.findoriglanguages, 'P364'),
            (self.findcolors, 'P462'),
            (self.findlanguagesspoken, 'P1412'),
            (self.findlanguages, 'P407'),
            (self.findnativelanguages, 'P103'),
            (self.findpseudonyms, 'P742'),
            (self.findparts, 'P527'),
            (self.findpartofs, 'P361'),
            (self.findinstruments, 'P1303'),
            (self.findlabels, 'P264'),
            (self.findsports, 'P641'),
            (self.findawards, 'P166'),
            (self.findnominations, 'P1411'),
            (self.findmemberships, 'P463'),
            (self.findsportteams, 'P54'),
            (self.findparties, 'P102'),
            (self.findbranches, 'P241'),
            (self.findconflicts, 'P607'),
            (self.findteampositions, 'P413'),
            (self.findpolitical, 'P1142'),
            (self.findstudents, 'P802'),
            (self.finddocstudents, 'P185'),
            (self.findteachers, 'P1066'),
            (self.findadvisors, 'P184'),
            (self.findinfluences, 'P737'),
            (self.finddegrees, 'P512'),
            (self.findmajors, 'P812'),
            (self.findparticipations, 'P1344'),
            (self.findnationalities, 'P27'),
            (self.findsportcountries, 'P1532'),
            (self.findreligions, 'P140'),
            (self.findchildren, 'P40'),
            (self.findsiblings, 'P3373'),
            (self.findkins, 'P1038'),
            (self.findincollections, 'P6379'),
            (self.findinworks, 'P1441'),
            (self.findmovements, 'P135'),
            (self.findorigcountries, 'P495'),
            (self.findwebpages, 'P973'),
            (self.findsources, 'P1343'),
            (self.findchoriginplaces, 'P1321'),
            (self.findpatronof, 'P2925'),
            (self.findnotableworks, 'P800'),
            (self.findparticipantins, 'P1344'),
            (self.findplatforms, 'P400'),
            (self.findfranchises, 'P8345'),
            (self.findvoices, 'P412'),
        ]:
            results = function(self.html) or []
            for result in results:
                if result is not None and str(result).strip() and result != self.item:
                    newclaims.append((prop, result.replace('\n', ' '), self))

        for (function, prop) in [
            (self.findfirstnames, 'P735'),
            (self.findlastnames, 'P734'),
        ]:
            results = function(self.html) or []
            for result in results:
                if result is not None and str(result).strip() \
                   and result != self.item:
                    newclaims.append((prop, result.replace('\n', ' '), None))

        for (function, prop) in [
            (self.findcountry, 'P17'),
            (self.findgender, 'P21'),
            (self.findfather, 'P22'),
            (self.findmother, 'P25'),
            (self.findreligion, 'P140'),
            (self.findadminloc, 'P131'),
            (self.findlocation, 'P276'),
            (self.findformationlocation, 'P740'),
            (self.findbirthplace, 'P19'),
            (self.finddeathplace, 'P20'),
            (self.findmannerdeath, 'P1196'),
            (self.findcausedeath, 'P509'),
            (self.findburialplace, 'P119'),
            (self.findorigcountry, 'P495'),
            (self.findnationality, 'P27'),
            (self.findethnicity, 'P172'),
            (self.findorientation, 'P91'),
            (self.findaddress, 'P969'),
            (self.findhaircolor, 'P1884'),
            (self.finduse, 'P366'),
            (self.findmountainrange, 'P4552'),
            (self.findviaf, 'P214'),
            (self.findrelorder, 'P611'),
            (self.findtwitter, 'P2002'),
            (self.findfacebook, 'P2013'),
            (self.findfacebookpage, 'P4003'),
            (self.findchoriginplace, 'P1321'),
            (self.findwebsite, 'P856'),
            (self.findvoice, 'P412'),
            (self.findfamily, 'P53'),
            (self.findgens, 'P5025'),
            (self.findchesstitle, 'P2962'),
            (self.findfeastday, 'P841'),
            (self.findbloodtype, 'P1853'),
            (self.findeyecolor, 'P1340'),
        ]:
            result = function(self.html)
            if result and not (
                prop == 'P856' and 'wikipedia.org' in result
                    or prop in ['P2013', 'P4003'] and result == 'pages'):
                newclaims.append((prop, result.strip(), self))

        for (function, prop) in [
            (self.findbirthdate, 'P569'),
            (self.finddeathdate, 'P570'),
            (self.findbaptismdate, 'P1636'),
            (self.findburialdate, 'P4602'),
            (self.findinception, 'P571'),
            (self.findpremiere, 'P1191'),
            (self.finddissolution, 'P576'),
            (self.findpubdate, 'P577'),
            (self.findfloruitstart, 'P2031'),
            (self.findfloruitend, 'P2032'),
        ]:
            result = function(self.html)
            if result:
                result = result.strip()
                if '?' not in result and re.search(r'\d{3}', result):
                    newclaims.append((prop, '!date!' + result, self))
        for (function, prop) in [
            (self.findpubdates, 'P577'),
        ]:
            results = function(self.html) or []
            for result in results:
                result = result.strip()
                if '?' not in result and re.search(r'\d{3}', result):
                    newclaims.append((prop, '!date!' + result, self))
        for function in [self.findfloruit]:
            result = function(self.html)
            if result:
                result = result.strip().lstrip('(').rstrip(')')
                result = result.replace('–', '-').replace('‑', '-')
                if '-' in result:
                    (start, end) = (r.strip() for r in result.split('-', 1))
                    if start == end:
                        newclaims.append(('P1317', '!date!' + start, self))
                    else:
                        newclaims.append(('P2031', '!date!' + start, self))
                        newclaims.append(('P2032', '!date!' + end, self))
                else:
                    newclaims.append(
                        ('P1317', '!date!' + result.strip(), self))

        for (function, prop) in [
            (self.findfloorsabove, 'P1101'),
            (self.findfloorsbelow, 'P1139'),
        ]:
            result = function(self.html)
            if result:
                newclaims.append((prop, str(int(result)), self))

        for (function, prop) in [
            (self.findheights, 'P2048'),
            (self.findweights, 'P2067'),
            (self.findelevations, 'P2044'),
            (self.finddurations, 'P2047'),
            (self.findprominences, 'P2660'),
            (self.findisolations, 'P2659'),
        ]:
            results = function(self.html) or []
            for result in results:
                if result and result.strip():
                    newclaims.append((prop, '!q!' + result, self))

        for (function, prop) in [
            (self.findimage, 'P18'),
            (self.findcoatarms, 'P94'),
            (self.findsignature, 'P109'),
            (self.findlogo, 'P154'),
        ]:
            result = function(self.html)
            if result:
                result = re.sub('(<.*?>)', '', result)
                result = result.split('>')[-1]
                if len(result.strip()) > 2 and '.' in result:
                    newclaims.append((prop, '!i!' + result, self))

        result = self.findisni(self.html)
        if result:
            m = re.search(r'(\d{4})\s*(\d{4})\s*(\d{4})\s*(\w{4})', result)
            if m:
                newclaims.append(('P213', '{} {} {} {}'
                                  .format(*m.groups()), self))

        for (prop, result) in self.findmixedrefs(self.html) or []:
            if result is not None:
                result = result.strip()
                if prop in ['P1309', 'P1255']:
                    result = result.replace('vtls', '')
                elif prop == 'P1368':
                    result = result.split('-')[-1]
                elif prop == 'P409':
                    result = result.strip().lstrip('0')
                elif prop == 'P396' and '\\' not in result:
                    result = result.replace('%5C', '\\')
                    if '\\' not in result:
                        m = re.match(r'^(.*?)(\d+)', result)
                        result = 'IT\\ICCU\\{}\\{}'.format(*m.groups())
                if result:
                    newclaims.append((prop, result, self))

        pywikibot.info()
        for (function, prop) in [
            (self.findcoords, 'coordinates'),
        ]:
            result = function(self.html)
            if result:
                pywikibot.info(f'Please add yourself: {prop} - {result}')
        return newclaims

    def prepare(self, html: str):
        return html

    @staticmethod
    def singlespace(text):
        text = text.replace('\n', ' ')
        while '  ' in text:
            text = text.replace('  ', ' ')
        return text.strip()

    def getdescriptions(self):
        return [
            (self.language, self.singlespace(unescape(self.TAGRE.sub(' ', x))))
            for x in self.finddescriptions(self.html) or [] if x
        ] + [
            (language, self.singlespace(unescape(self.TAGRE.sub(' ', x))))
            for (language, x) in self.findlanguagedescriptions(self.html) or []
            if x
        ]

    def longtext(self):
        result = self.TAGRE.sub(' ', self.findlongtext(self.html) or '')
        result = result.replace('\t', '\n').replace('\r', '')
        while '  ' in result:
            result = result.replace('  ', ' ')
        if '\n ' in result:
            result = result.replace('\n ', '\n')
        if ' \n' in result:
            result = result.replace(' \n', '\n')
        while '\n\n' in result:
            result = result.replace('\n\n', '\n')
        return result.strip()

    def finddescriptions(self, html: str):
        return [self.finddescription(html)]

    def getlanguage(self, code):
        if not code:
            return self.language

        translation = {
            'cz': 'cs',
            'hbo': 'he',
            'simple': 'en',
            'be-tarask': 'be-x-old',
            'nb': 'no',
        }
        if code in translation:
            return translation[code]
        if code[-1] in '123456789':
            return self.getlanguage(code[:-1])
        return code.replace('_', '-')

    def findwikipedianames(self, html: str):
        links = self.findallbyre(
            r'//(\w+\.wikipedia\.org/wiki/[^\'"<>\s]+)', html)
        return [(self.getlanguage(link.split('.')[0]),
                 unescape(unquote(link.split('/')[-1].replace(
                     '_', ' '))).split('(')[0]) for link in links]

    def getnames(self):
        return [
            (self.language, self.commastrip(term))
            for term in self.findnames(self.html) or []
            if term and term.strip()] \
            + [(self.getlanguage(language), self.commastrip(term))
               for (language, term) in self.findlanguagenames(self.html) or []
               if term and term.strip()] + self.findwikipedianames(self.html)

    def __getattr__(self, name):
        """Return None if the function is not defined in subclass."""
        prefix = 'find'
        funcnames = {
            'address', 'adminloc', 'advisors', 'architects', 'artdirectors',
            'awards', 'baptismdate', 'birthdate', 'birthplace', 'bloodtype',
            'branches', 'burialdate', 'burialplace', 'cast', 'causedeath',
            'chesstitle', 'children', 'choriginplace', 'choriginplaces',
            'coatarms', 'colors', 'composers', 'conflicts', 'coords',
            'costumedesigners', 'countries', 'country', 'crimes', 'deathdate',
            'deathplace', 'degrees', 'description', 'developers',
            'directorsphotography', 'dissolution', 'distcoms', 'docstudents',
            'durations', 'elevations', 'employers', 'engines', 'ethnicities',
            'ethnicity', 'eyecolor', 'facebook', 'facebookpage', 'family',
            'father', 'feastday', 'firstname', 'firstnames', 'floorsabove',
            'floorsbelow', 'floruit', 'floruitend', 'floruitstart',
            'formationlocation', 'franchises', 'gamemodes', 'gender',
            'genres', 'gens', 'haircolor', 'height', 'heights', 'image',
            'inception', 'incollections', 'influences', 'instanceof',
            'instruments', 'inworks', 'isni', 'isolations', 'kins', 'labels',
            'languagedescriptions', 'languagenames', 'languages',
            'languagesspoken', 'lastname', 'lastnames', 'location', 'logo',
            'longtext', 'majors', 'makeupartists', 'mannerdeath', 'materials',
            'memberships', 'mixedrefs', 'mother', 'mountainrange', 'movements',
            'moviedirectors', 'movieeditors', 'nationalities', 'nationality',
            'nativelanguages', 'nominations', 'notableworks', 'occupations',
            'orientation', 'origcountries', 'origcountry', 'origlanguages',
            'participantins', 'participations', 'parties', 'partners',
            'partofs', 'parts', 'patronof', 'platforms', 'political',
            'positions', 'premiere', 'prodcoms', 'producers',
            'productiondesigners', 'prominences', 'pseudonyms', 'pubdate',
            'pubdates', 'publishers', 'ranks', 'religion', 'religions',
            'relorder', 'residences', 'schools', 'screenwriters', 'siblings',
            'signature', 'sounddesigners', 'sources', 'sportcountries',
            'sports', 'sportteams', 'spouses', 'students', 'teachers',
            'teampositions', 'titles', 'twitter', 'use', 'viaf', 'voice',
            'voices', 'webpages', 'website', 'weight', 'weights', 'workfields',
            'workplaces',
        }
        pre, sep, post = name.partition(prefix)
        if not pre and sep == prefix and post in funcnames:
            return lambda html: None
        if not pre and sep == prefix and post == 'names':
            return lambda html: []
        return super().__getattribute__(name)

    def finddefaultmixedrefs(self, html, includesocial=True):
        defaultmixedrefs = [
            ('P214', self.findbyre(r'viaf.org/(?:viaf/)?(\d+)', html)),
            ('P227', self.findbyre(r'd-nb\.info/(?:gnd/)?([\d\-xX]+)', html)),
            ('P244', self.findbyre(
                r'id\.loc\.gov/authorities/\w+/(\w+)', html)),
            ('P244', self.findbyre(r'https?://lccn\.loc\.gov/(\w+)', html)),
            ('P245', self.findbyre(
                r'https?://www.getty.edu/[^"\'\s]+subjectid=(\w+)', html)),
            ('P245', self.findbyre(r'getty.edu/page/ulan/(\w+)', html)),
            ('P268', self.findbyre(
                r'https?://catalogue.bnf.fr/ark./\d+/(?:cb)?(\w+)', html)),
            ('P268', self.findbyre(r'data\.bnf\.fr/ark:/\d+/cb(\w+)', html)),
            ('P269', self.findbyre(r'https?://\w+.idref.fr/(\w+)', html)),
            ('P345', self.findbyre(r'https?://www.imdb.com/\w+/(\w+)', html)),
            ('P349', self.findbyre(
                r'https?://id.ndl.go.jp/auth/[^"\'\s]+/(\w+)', html)),
            ('P396', self.findbyre(
                r'opac\.sbn\.it/opacsbn/opac/[^<>\'"\s]+\?bid=([^\s\'"<>]+)',
                html)),
            ('P409', self.findbyre(
                r'https?://nla.gov.au/anbd.aut-an(\w+)', html)),
            ('P434', self.findbyre(
                r'https?://musicbrainz.org/\w+/([\w\-]+)', html)),
            ('P496', self.findbyre(r'https?://orcid.org/([\d\-]+)', html)),
            ('P535', self.findbyre(
                r'https?://www.findagrave.com/memorial/(\w+)', html)),
            ('P535', self.findbyre(
                r'https?://www.findagrave.com/cgi-bin/fg.cgi\?[^<>"\']*id=(\w+)',
                html)),
            ('P549', self.findbyre(
                r'genealogy.math.ndsu.nodak.edu/id.php\?id=(\w+)', html)),
            ('P650', self.findbyre(
                r'https?://rkd.nl(?:/\w+)?/explore/artists/(\w+)', html)),
            ('P651', self.findbyre(
                r'biografischportaal\.nl/persoon/(\w+)', html)),
            ('P723', self.findbyre(
                r'dbnl\.(?:nl|org)/auteurs/auteur.php\?id=(\w+)', html)),
            ('P723', self.findbyre(
                r'data.bibliotheken.nl/id/dbnla/(\w+)', html)),
            ('P866', self.findbyre(r'perlentaucher.de/autor/([\w\-]+)', html)),
            ('P902', self.findbyre(
                r'hls-dhs-dss.ch/textes/\w/[A-Z]?(\d+)\.php', html)),
            ('P906', self.findbyre(
                r'libris.kb.se/(?:resource/)?auth/(\w+)', html)),
            ('P950', self.findbyre(
                r'catalogo.bne.es/[^"\'\s]+authority.id=(\w+)', html)),
            ('P1006', self.findbyre(
                r'data.bibliotheken.nl/id/thes/p(\d+X?)', html)),
            ('P1047', self.findbyre(
                r'catholic-hierarchy.org/\w+/b(.+?)\.html', html)),
            ('P1220', self.findbyre(r'//ibdb.com/person.php\?id=(\d+)', html)),
            ('P1233', self.findbyre(
                r'https?://www.isfdb.org/cgi-bin/ea.cgi\?(\d+)', html)),
            ('P1415', self.findbyre(
                r'doi\.org/\d+\.\d+/ref:odnb/(\d+)', html)),
            ('P1417', self.findbyre(
                r'https://www.britannica.com/([\w\-/]+)', html)),
            ('P1422', self.findbyre(r'ta.sandrartnet/-person-(\w+)', html)),
            ('P1563', self.findbyre(
                r'https?://www-history.mcs.st-andrews.ac.uk/Biographies/([^\'"<>\s]+)', html)),
            ('P1728', self.findbyre(
                r'https?://www.allmusic.com/artist/[\w\-]*?(mn/d+)', html)),
            ('P1749', self.findbyre(
                r'https?://www.parlement(?:airdocumentatiecentrum)?.(?:com|nl)/id/(\w+)', html)),
            ('P1788', self.findbyre(
                r'huygens.knaw.nl/vrouwenlexicon/lemmata/data/([^"\'<>\s]+)', html)),
            ('P1802', self.findbyre(
                r'https?://emlo.bodleian.ox.ac.uk/profile/person/([\w\-]+)', html)),
            ('P1842', self.findbyre(
                r'https?://gameo.org/index.php\?title=([^\'"\s]+)', html)),
            ('P1871', self.findbyre(
                r'https?://(?:data|thesaurus).cerl.org/(?:thesaurus|record)/(\w+)', html)),
            ('P1871', self.findbyre(
                r'thesaurus.cerl.org/cgi-bin/record.pl\?rid=(\w+)', html)),
            ('P1902', self.findbyre(
                r'https?://open.spotify.com/artist/(\w+)', html)),
            ('P1907', self.findbyre(
                r'https?://adb.anu.edu.au/biography/([\w\-]+)', html)),
            ('P1938', self.findbyre(
                r'https?://www.gutenberg.org/ebooks/author/(\d+)', html)),
            ('P1953', self.findbyre(
                r'https?://www.discogs.com/(\w+/)?artist/(\d+)', html)),
            ('P1986', self.findbyre(
                r'treccani.it/enciclopedia/([\w\-_]+)_\(Dizionario-Biografico\)', html)),
            ('P2016', self.findbyre(
                r'hoogleraren\.ub\.rug\.nl/hoogleraren/(\w+)', html)),
            ('P2038', self.findbyre(
                r'https?://www.researchgate.net/profile/([^\'"<>\s\?]+)', html)),
            ('P2163', self.findbyre(r'id\.worldcat\.org/fast/(\d+)', html)),
            ('P2332', self.findbyre(r'/arthistorians\.info/(\w+)', html)),
            ('P2372', self.findbyre(r'odis\.be/lnk/([\w_]+)', html)),
            ('P2373', self.findbyre(
                r'https?://genius.com/artists/([^\s\'"]*)', html)),
            ('P2397', self.findbyre(r'youtube\.com/channel/([\w\-_]+)', html)),
            ('P2454', self.findbyre(
                r'https?://www.dwc.knaw.nl/[^\'"\s]+=(\w+)', html)),
            ('P2456', self.findbyre(
                r'https?://dblp.uni-trier.de/pid/([\w/]+)', html)),
            ('P2469', self.findbyre(r'theatricalia.com/person/(\w+)', html)),
            ('P2639', (self.findbyre(
                r'filmportal.de/person/(\w+)', html) or '').lower() or None),
            ('P2722', self.findbyre(r'deezer.com/artist/(\w+)', html)),
            ('P2799', self.findbyre(
                r'cervantesvirtual.com/person/(\d+)', html)),
            ('P2850', self.findbyre(
                r'https?://itunes.apple.com(?:/\w{2})?/(?:id)?(\d+)', html)),
            ('P2909', self.findbyre(
                r'https?://www.secondhandsongs.com/artist/(\w+)', html)),
            ('P2915', self.findbyre(
                r'vondel.humanities.uva.nl/ecartico/persons/(\d+)', html)),
            ('P2941', self.findbyre(
                r'munksroll.rcplondon.ac.uk/Biography/Details/(\d+)', html)),
            ('P2949', self.findbyre(
                r'www\.wikitree\.com/wiki/(\w+-\d+)', html)),
            ('P2963', self.findbyre(
                r'goodreads\.com/author/show/(\d+)', html)),
            ('P2969', self.findbyre(r'goodreads\.com/book/show/(\d+)', html)),
            ('P3040', self.findbyre(
                r'https?://soundcloud.com/([\w\-]+)', html)),
            ('P3192', self.findbyre(
                r'https?://www.last.fm/music/([^\'"\s]+)', html)),
            ('P3217', self.findbyre(
                r'https?://sok.riksarkivet.se/sbl/Presentation.aspx\?id=(\d+)', html)),
            ('P3217', self.findbyre(
                r'https?://sok.riksarkivet.se/sbl/artikel/(\d+)', html)),
            ('P3241', self.findbyre(
                r'https?://www.newadvent.org/cathen/(\w+)\.htm', html)),
            ('P3265', self.findbyre(
                r'https?://myspace.com/([\w\-_/]+)', html)),
            ('P3365', self.findbyre(
                r'treccani.it/enciclopedia/([\w\-_]+)', html)),
            ('P3368', self.findbyre(
                r'https?://prabook.com/web/[^/<>"\']+/(\d+)', html)),
            ('P3368', self.findbyre(
                r'prabook.com/web/person-view.html\?profileId=(\d+)', html)),
            ('P3435', self.findbyre(r'vgmdb\.net/artist/(\w+)', html)),
            ('P3478', self.findbyre(r'songkick\.com/artists/(\w+)', html)),
            ('P3630', self.findbyre(
                r'https?://www.babelio.com/auteur/[^<>\'"\s]+/(\d+)', html)),
            ('P3854', self.findbyre(
                r'soundtrackcollector.com/\w+/(\w+)', html)),
            ('P4013', self.findbyre(r'https?://giphy.com/(\w+)', html)),
            ('P4073', self.findbyre(r'(\w+)\.wikia\.com', html)),
            ('P4198', self.findbyre(
                r'play.google.com/store/music/artist\?id=(\w+)', html)),
            ('P4223', self.findbyre(
                r'treccani.it/enciclopedia/([\w\-_]+)_\(Enciclopedia-Italiana\)', html)),
            ('P4228', self.findbyre(
                r'www.eoas.info/biogs/([^\s]+)\.html', html)),
            ('P4228', self.findbyre(
                r'www.eoas.info%2Fbiogs%2F([^\s]+)\.html', html)),
            ('P4252', self.findbyre(
                r'www.mathnet.ru/[\w/\.]+\?.*?personid=(\w+)', html)),
            ('P4862', self.findbyre(
                r'https?://www.amazon.com/[\w\-]*/e/(\w+)', html)),
            ('P5357', self.findbyre(
                r'sf-encyclopedia.com/entry/([\w_]+)', html)),
            ('P5404', self.findbyre(
                r'rateyourmusic.com/artist/([^\'"<>\s]+)', html)),
            ('P5431', self.findbyre(
                r'https?://www.setlist.fm/setlists/[\w\-]*?(\w+).html', html)),
            ('P5570', self.findbyre(
                r'www.noosfere.org/[\w\./]+\?numauteur=(\w+)', html)),
            ('P5882', self.findbyre(
                r'www\.muziekweb\.nl/\w+/(\w+)', html)),
            ('P5924', self.findbyre(
                r'lyrics.wikia.com/wiki/([^\'"<>\s]*)', html)),
            ('P6194', self.findbyre(
                r'biographien\.ac.\at/oebl/oebl_\w/[^\s\.]+\.', html)),
            ('P6517', self.findbyre(
                r'whosampled.com/([^\'"<>/\s]+)', html)),
            ('P6594', self.findbyre(
                r'gf\.org/fellows/all-fellows/([\w\-]+)', html)),
            ('P7032', self.findbyre(
                r'historici.nl/Onderzoek/Projecten/Repertorium/app/personen/(\d+)', html)),
            ('P7032', self.findbyre(
                r'repertoriumambtsdragersambtenaren1428-1861/app/personen/(\d+)', html)),
            ('P7195', self.findbyre(
                r'https?://www.bandsintown.com/\w+/(\d+)', html)),
            ('P7545', self.findbyre(
                r'https?://www.askart.com/artist/[\w_]*/(\d+)/', html)),
            ('P7620', self.findbyre(
                r'treccani.it/enciclopedia/([\w\-]+)_\(Enciclopedia_dei_Papi\)', html)),
            ('P7902', self.findbyre(
                r'www.deutsche-biographie.de/pnd(\w+)\.html', html)),
            ('P8034', self.findbyre(
                r'viaf.org/viaf/sourceID/BAV\|(\w+)', html)),
            ('P9029', self.findbyre(
                r'viceversalitterature\.ch/author/(\d+)', html)),
        ]
        if includesocial:
            defaultmixedrefs += [
                ('P2002', self.findbyre(
                    r'https?://(?:www\.)?twitter.com/#?(\w+)', html)),
                ('P2003', self.findbyre(
                    r'https?://(?:\w+\.)?instagram.com/([^/\s\'"]{2,})', html)),
                ('P2013', self.findbyre(
                    r'https?://www.facebook.com/(?:pg/)?([^/\s\'"<>\?]+)', html)),
                ('P2847', self.findbyre(
                    r'https?://plus.google.com/(\+?\w+)', html)),
                ('P2850', self.findbyre(
                    r'https?://itunes.apple.com/(?:\w+/)?artist/(?:\w*/)?[a-z]{0,2}(\d{3,})', html)),
                ('P3258', self.findbyre(
                    r'https?://([\w\-]+)\.livejournal.com', html)),
                ('P3258', self.findbyre(
                    r'https?://users\.livejournal.com/(\w+)', html)),
                ('P3265', self.findbyre(
                    r'https?://www.myspace.com/([\w\-]+)', html)),
                ('P3283', self.findbyre(
                    r'https?://([^/"\']+)\.bandcamp.com', html)),
                ('P4003', self.findbyre(
                    r'https?://www.facebook.com/pages/([^\s\'"<>\?]+)', html)),
                ('P4175', self.findbyre(
                    r'https://www.patreon.com/([\w\-]+)', html)),
                ('P6634', self.findbyre(
                    r'\.linkedin\.com/in/([\w\-]+)', html)),
            ]
        result = [pair for pair in defaultmixedrefs
                  if pair[0] != self.dbproperty]
        isniresult = re.search(
            r'isni\.org/isni/(\d{4})(\d{4})(\d{4})(\w{4})', html)
        if isniresult:
            result.append(('P213', '{} {} {} {}'.format(*isniresult.groups())))
        commonsresult = self.findbyre(
            r'commons\.wikimedia\.org/wiki/\w+:([^\'"<>\s]+)', html)
        if commonsresult:
            result += [('P18', '!i!' + commonsresult)]
        return [r for r in result if r[1]
                and not (r[0] == 'P2002' and r[1] == 'intent')
                and not (r[0] == 'P2013' and r[1].startswith('pages'))
                and not (r[0] == 'P2013' and r[1] in ['pg', 'plugins',
                                                      'sharer'])
                and not (r[0] == 'P214' and r[1].lower() == 'sourceid')
                and not (r[0] == 'P3258' and r[1].lower() in ['users',
                                                              'comunity',
                                                              'www'])
                and r[1].lower() != 'search'
                and not (r[0] == 'P3365' and ('(Dizionario_Biografico)' in r[1] or '(Enciclopedia-Italiana)' in r[1] or '(Enciclopedia-dei-Papi)' in r[1]))
                and not (r[0] == 'P2013' and '.php' in r[1])]

    def findbyre(self, regex, html, dtype=None, skips=None, alt=None) -> str:
        if not skips:
            skips = []
        if not alt:
            alt = []
        m = re.search(regex, html)
        if not m:
            return None
        if dtype:
            alt = [dtype] + alt
        for alttype in alt:
            if self.getdata(alttype, m[1], ask=False) \
               and self.getdata(alttype, m[1], ask=False) != 'XXX':
                return self.getdata(alttype, m[1], ask=False)
        for skip in skips:
            if self.getdata(skip, m[1], ask=False) \
               and self.getdata(skip, m[1], ask=False) != 'XXX':
                return None
        if dtype:
            return self.getdata(dtype, m[1])
        return m[1]

    def findallbyre(self, regex, html, dtype=None, skips=None,
                    alt=None) -> List[str]:
        if not skips:
            skips = []
        if not alt:
            alt = []
        if dtype:
            alt = [dtype] + alt
        matches = re.findall(regex, html)
        result = set()
        for match in matches:
            doskip = False
            for alttype in alt:
                if self.getdata(alttype, match, ask=False) and self.getdata(
                        alttype, match, ask=False) != 'XXX':
                    result.add(self.getdata(alttype, match, ask=False))
                    doskip = True
                    break
            for skip in skips:
                if self.getdata(skip, match, ask=False) and self.getdata(
                        skip, match, ask=False) != 'XXX':
                    doskip = True
            if doskip:
                continue
            if dtype:
                newresult = self.getdata(dtype, match)
                if newresult:
                    result.add(newresult)
            else:
                result.add(match)
        return list(result)


class IsniAnalyzer(Analyzer):
    def setup(self):
        self.dbproperty = 'P213'
        self.dbid = 'Q423048'
        self.dbname = 'International Standard Name Identifier'
        self.id = self.id.replace(' ', '')
        self.id = self.id[:4] + '+' + self.id[4:8] + '+' + self.id[8:12] + '+' + self.id[12:]
        self.urlbase = 'http://www.isni.org/{id}'
        self.urlbase3 = 'https://isni.oclc.org/DB=1.2/CMD?ACT=SRCH&IKT=8006&TRM=ISN%3A{id}&TERMS_OF_USE_AGREED=Y&terms_of_use_agree=send'
        self.skipfirst = True
        self.hrtre = '(<span class="rec.mat.long">.*?</span>)Sources'
        self.isperson = False
        self.language = 'en'

    @property
    def url(self):
        # TODO: check whether this is right or needed
        return f'http://www.isni.org/{self.id}'.replace(' ', '')

    def findlanguagenames(self, html: str):
        # TODO: check whether this is right or needed
        section = self.findbyre(r'(?s)>Name</td></tr>(.*?)</tr>', html)
        if section:
            return [('en', name) for name in self.findallbyre(r'(?s)<span>(.*?)(?:\([^{}<>]*\))?\s*</span>', section)]

    def getvalues(self, field, html, dtype=None) -> List[str]:
        section = self.findbyre('(?s)<td class="rec_lable"><div><span>%s:.*?<td class="rec_title">(.*?)</td>', html)
        if section:
            return self.findallbyre('<span>(.*?)<', html, dtype)
        return []

    def findnames(self, html) -> List[str]:
        return [self.findbyre(r'([^\(]*)', name)
                for name in self.getvalues('Name', html)]

    def finddescriptions(self, html: str):
        return [self.findbyre(r'\((.*?)\)', name) for name in self.getvalues('Name', html)]

    def findinstanceof(self, html: str):
        result = self.findbyre(r'<span class="rec.mat.long"><img alt="(.*?)"', html, 'instanceof')
        self.isperson = result == 'Q5'
        return result

    def findmixedrefs(self, html: str):
        return self.finddefaultmixedrefs(html, includesocial=False)

    def findoccupations(self, html: str):
        if self.isperson:
            return self.getvalues('Creation role', html, 'occupation')

    def findbirthdate(self, html: str):
        if self.isperson:
            dates = self.getvalues('Dates', html)
            if dates:
                return self.findbyre(r'(.*?)-', dates[0])

    def finddeathdate(self, html: str):
        if self.isperson:
            dates = self.getvalues('Dates', html)
            if dates:
                return self.findbyre(r'-(.*?)', dates[0])


class ViafAnalyzer(Analyzer):
    def setup(self):
        self.dbproperty = 'P214'
        self.dbid = 'Q54919'
        self.dbname = 'Virtual International Authority File'
        self.urlbase = 'https://viaf.org/viaf/{id}/'
        self.hrtre = '(<ns1:Document.*?)<ns1:history>'
        self.language = 'en'
        self.escapehtml = True
        self.sourcelanguage = {
            'DNB': 'de',
            'LC': 'en',
            'JPG': 'en',
            'SUDOC': 'fr',
            'NDL': 'ja',
            'NLA': 'en',
            'NKC': 'cs',
            'SELIBR': 'sv',
            'NLI': 'he',
            'BNE': 'es',
            'PTBNP': 'pt',
            'NTA': 'nl',
            'BIBSYS': 'nb',
            'BAV': 'en',
            'NUKAT': 'pl',
            'BNC': 'ca',
            'EGAXA': 'en',
            'LNB': 'lv',
            'NSK': 'hr',
            'LAC': 'en',
            'NLP': 'pl',
            'BNCHL': 'es',
            'N6I': 'en',
            'FAST': 'en',
            'RERO': 'fr',
            'B2Q': 'fr',
            'DBC': 'da',
            'BLBNB': 'pt',
            'KRNLK': 'ko',
            'ISNI': 'en',
            'BNF': 'fr',
            'DE663': 'de',
            'WKP': 'en',
            'VLACC': 'nl',
            'ERRR': 'et',
            'NII': 'ja',
            'BNL': 'fr',
            'SWNL': 'fr',
            'NLR': 'ru',
            'ICCU': 'it',
            'LNL': 'ar',
            'W2Z': 'nb',
            'LIH': 'lt',
            'UIY': 'is',
            'CAOONL': 'en',
            'SIMACOB': 'sl',
            'CYT': 'zh',
            'SZ': 'de',
            'PLWABN': 'pl',
            'NLB': 'en',
            'SKMASNL': 'sk',
            'ARBABN': 'es',
            'J9U': 'he',
            'GRATEVE': 'el',
        }

    def getid(self, name, html):
        result = self.findbyre(fr'>{name}\|([^<>]+)', html)
        if result:
            return result.replace(' ', '')
        return None

    def findlanguagenames(self, html: str):
        languagenames = set()
        for section in self.findallbyre(r'(?s)<ns1:x\d+>(.*?)</ns1:x\d+>', html):
            for name in self.findallbyre(r'<ns1:subfield code="a">(.*?)<', section):
                for source in self.findallbyre(r'<ns1:s>(.*?)<', section):
                    languagenames.add((self.sourcelanguage[source], name))
        names = [name[1] for name in languagenames]
        for name in self.findallbyre(r'<ns1:subfield code="a">(.*?)<', html):
            if name not in names:
                languagenames.add(('en', name))
        return languagenames

    def findlanguagedescriptions(self, html: str):
        result = set()
        for section in self.findallbyre(r'(?s)<ns1:x\d+>(.*?)</ns1:x\d+>', html):
            for name in self.findallbyre(r'<ns1:subfield code="c">(.*?)<', section):
                for source in self.findallbyre(r'<ns1:s>(.*?)<', section):
                    result.add((self.sourcelanguage[source], name))
        names = [name[1] for name in result]
        for name in self.findallbyre(r'<ns1:subfield code="c">(.*?)<', html):
            if name not in names:
                result.add(('en', name))
        return result

    def findgender(self, html: str):
        return self.findbyre(r'<ns1:gender>([^<>]+)</ns1:gender>', html, 'gender')

    def findnationalities(self, html: str):
        section = self.findbyre(r'<ns1:nationalityOfEntity>(.*?)</ns1:nationalityOfEntity>', html)
        if section:
            return self.findallbyre(r'<ns1:text>([^<>]+)</ns1:text>', section, 'country')
        return None

    def findlanguagesspoken(self, html: str):
        section = self.findbyre(r'<ns1:languageOfEntity>(.*?)</ns1:languageOfEntity>', html)
        if section:
            return self.findallbyre(r'<ns1:text>([^<>]+)</ns1:text>', section, 'language')
        return None

    def findoccupations(self, html: str):
        sections = self.findallbyre(r'<ns1:occupation>(.*?)</ns1:occupation>', html)
        section = '\n'.join(sections)
        return self.findallbyre(r'<ns1:text>(.*?)</ns1:text>', section, 'occupation')

    def findworkfields(self, html: str):
        sections = self.findallbyre(r'<ns1:fieldOfActivity>(.*?)</ns1:fieldOfActivity>', html)
        section = '\n'.join(sections)
        return self.findallbyre(r'<ns1:text>(.*?)</ns1:text>', section, 'subject')

    def findmixedrefs(self, html: str):
        result = [
            ('P214', self.findbyre(r'<ns0:directto>(\d+)<', html)),
            ('P227', self.getid('DNB', html)),
            ('P244', self.getid('LC', html)),
            ('P245', self.getid('JPG', html)),
            ('P269', self.getid('SUDOC', html)),
            ('P271', self.getid('NII', html)),
            ('P349', self.getid('NDL', html)),
            ('P396', self.getid('ICCU', html)),
            ('P409', self.getid('NLA', html)),
            ('P691', self.getid('NKC', html)),
            ('P906', self.getid('SELIBR', html)),
            ('P949', self.getid('NLI', html)),
            ('P950', self.getid('BNE', html)),
            ('P1005', self.getid('PTBNP', html)),
            ('P1006', self.getid('NTA', html)),
            ('P1015', self.getid('BIBSYS', html)),
            ('P1017', self.getid('BAV', html)),
            ('P1207', self.getid('NUKAT', html)),
            ('P1255', self.getid('SWNL', html)),
            ('P1273', self.getid('BNC', html)),
            ('P1309', self.getid('EGAXA', html)),
            ('P1368', self.getid('LNB', html)),
            ('P1375', self.getid('NSK', html)),
            ('P1670', self.getid('LAC', html)),
            ('P1695', (self.getid('NLP', html) or '').upper() or None),
            # ('P1946', self.getid('N6I', html)), #obsolete
            ('P2163', self.getid('FAST', html)),
            # ('P3065', self.getid('RERO', html)),
            ('P3280', self.getid('B2Q', html)),
            ('P3348', self.getid('GRATEVE', html)),
            ('P3846', self.getid('DBC', html)),
            ('P4619', self.getid('BLBNB', html)),
            ('P5034', self.getid('KRNLK', html)),
            ('P5504', self.getid('DE663', html)),
            ('P7293', self.getid('PLWABN', html)),
            ('P7369', (self.getid('BNCHL', html) or '')[-9:] or None),
            ('P8034', (self.getid('BAV', html) or '').replace('_', '/') or None),
            ('P268', self.findbyre(r'"http://catalogue.bnf.fr/ark:/\d+/cb(\w+)"', html)),
            ('P1566', self.findbyre(r'"http://www.geonames.org/(\w+)"', html)),
        ]
        iccu = self.getid('ICCU', html)
        if iccu:
            result += [('P396', fr'IT\ICCU\{iccu[:4]}\{iccu[4:]}')]
        result += self.finddefaultmixedrefs(html)
        return result

    def findisni(self, html: str):
        return self.getid('ISNI', html)

    def findnotableworks(self, html: str):
        works = self.findallbyre(r'<ns1:work>(.*?)</ns1:work>', html)
        works = [(len(re.findall('(<ns1:s>)', work)), work) for work in works]
        works.sort(reverse=True)
        works = works[:5]
        works = [work for work in works if work[0] > 2]
        return [self.findbyre(r'<ns1:title>(.*?)<', work[1], 'work') for work in works]


class GndAnalyzer(Analyzer):
    def setup(self):
        self.dbproperty = 'P227'
        self.dbid = 'Q36578'
        self.dbname = 'Gemeinsame Normdatei'
        self.urlbase = 'https://portal.dnb.de/opac.htm?method=simpleSearch&cqlMode=true&query=nid%3D{id}'
        self.hrtre = '(<table id="fullRecordTable".*?/table>)'
        self.language = 'de'
        self.escapehtml = True

    def finddescriptions(self, html: str):
        return [
            self.findbyre(r'(?s)<strong>Weitere Angaben</strong>.*?<td[^<>]*>(.*?)</td>', html),
            self.findbyre(r'(?s)<strong>Systematik</strong>.*?<td[^<>]*>\s*[^\s]+(.*?)</td>', html),
            self.findbyre(r'(?s)<strong>Beruf\(e\)</strong>.*?<td[^<>]*>(.*?)</td>', html),
        ]

    def findlongtext(self, html: str):
        return re.sub(r'\s', ' ', self.findbyre(r'(?s)(<table id="fullRecordTable" .*?</table>)', html) or ''). \
            replace('<tr>', '\n')

    def findnames(self, html) -> List[str]:
        result = []
        section = self.findbyre(
            r'(?s)<strong>Sachbegriff</strong>.*?(<td.*?>(.*?)</td>)', html)
        if section:
            result += self.findallbyre(r'>([^<>\(]*)', section)

        section = self.findbyre(
            r'(?s)<strong>Person</strong>.*?(<td.*?>(.*?)</td>)', html)
        if section:
            result += self.findallbyre(r'>([^<>\(]*)', section)

        section = self.findbyre(
            r'(?s)<strong>Synonyme</strong>.*?(<td.*?>(.*?)</td>)', html)
        if section:
            result += self.findallbyre(r'>([^<>\(]*)', section)

        section = self.findbyre(
            r'(?s)<strong>Andere Namen</strong>.*?(<td.*?>(.*?)</td>)', html)
        if section:
            result += self.findallbyre(r'>([^<>\(]*)', section)
        return result

    def findinstanceof(self, html: str):
        result = self.findbyre(r'(?s)<strong>Typ</strong>.*?<td.*?>(.*?)(?:\(|</)', html, 'instanceof')
        if not result and '<strong>Person</strong>' in html:
            result = 'Q5'
        self.isperson = result == 'Q5'
        return result

    def findbirthdate(self, html: str):
        return self.findbyre(r'(?s)Lebensdaten:([^<>]*?)-', html)

    def finddeathdate(self, html: str):
        return self.findbyre(r'(?s)Lebensdaten:[^<>]*?-([^<>\(\)]*)', html)

    def findnationalities(self, html: str):
        if self.isperson:
            section = self.findbyre(r'(?s)<strong>Land</strong>.*?<td.*?>(.*?)</td>', html)
            if section:
                return self.findallbyre(r'([\w\s]+)\(', section, 'country')

    def findcountries(self, html: str):
        if not self.isperson:
            section = self.findbyre(r'(?s)<strong>Land</strong>.*?<td.*?>(.*?)</td>', html)
            if section:
                return self.findallbyre(r'([\w\s]+)\(', section, 'country')

    def findbirthplace(self, html: str):
        return self.findbyre(r'(?s)Geburtsort:\s*(?:<[^<>]*>)?([^<>&]*)', html, 'city') or\
            self.findbyre(r'(?s)([\s\w]+)\(Geburtsort\)', html, 'city')

    def finddeathplace(self, html: str):
        return self.findbyre(r'(?s)Sterbeort:\s*(?:<[^<>]*>)?([^<>&]*)',
                             html, 'city')

    def findworkplaces(self, html: str):
        return (
            self.findallbyre(
                r'(?s)Wirkungsort:\s*(?:<[^<>]*>)?([^<>]*)\(\d{3}',
                html, 'city')
            or self.findallbyre(
                r'(?s)Wirkungsort:\s*(?:<[^<>]*>)?([^<>]*)', html, 'city')) \
                + self.findallbyre(r'(?s)([\s\w]+)\(Wirkungsort\)',
                                   html, 'city')

    def findoccupations(self, html: str):
        result = []
        sectionfound = False
        for sectionname in [r'Beruf\(e\)', r'Funktion\(en\)', 'Weitere Angaben']:
            if sectionname == 'Weitere Angaben' and sectionfound:
                continue
            section = self.findbyre(r'(?s)<strong>{}</strong>(.*?)</tr>'
                                    .format(sectionname), html)
            if section:
                sectionfound = True
                result += self.findallbyre(r'(?s)[>;,]([^<>;,]*)', section, 'occupation')
        return result

    def findgender(self, html: str):
        return self.findbyre(r'(?s)<strong>Geschlecht</strong>.*?>([^<>]+)</td', html, 'gender')

    def findinstruments(self, html: str):
        section = self.findbyre(r'(?s)<strong>Instrumente.*?<td[^<>]*>(.*?)</td>', html)
        if section:
            section = self.TAGRE.sub('', section)
            section = re.sub(r'(?s)(\([^()]*\))', ';', section)
            return self.findallbyre(r'(?s)([\s\w]+)', section, 'instrument')

    def findvoice(self, html: str):
        section = self.findbyre(r'(?s)<strong>Instrumente.*?<td[^<>]*>(.*?)</td>', html)
        if not section:
            return None
        if '(' in section:
            return self.findbyre(r'(?s)([\s\w]+)\(', section, 'voice')
        return self.findbyre(r'(?s)([\s\w]+)', section, 'voice')

    def findlanguagesspoken(self, html: str):
        if self.isperson:
            section = self.findbyre(r'(?s)<strong>Sprache.*?<td[^<>]*>(.*?)</td>', html)
            if section:
                return self.findallbyre(r'([^{});]*)\(', section, 'language')

    def finddegrees(self, html: str):
        section = self.findbyre(r'(?s)Akademischer Grad.*?<td[^<>]*>(.*?)</td>', html)
        if section:
            return self.findallbyre(r'([^<>]+)', section, 'degree')

    def findsiblings(self, html: str):
        section = self.findbyre(r'(?s)<strong>Beziehungen zu Personen</strong>.*?(<td.*?</td>)', html)
        if section:
            return self.findallbyre(r'(?s)([^<>]*)(?:</a> )?\((?:Bruder|Schwester)\)', section, 'person')

    def findspouses(self, html: str):
        section = self.findbyre(r'(?s)<strong>Beziehungen zu Personen</strong>.*?(<td.*?</td>)', html)
        if section:
            return self.findallbyre(r'(?s)([^<>]*)(?:</a> )?\((?:Ehemann|Ehefrau)\)', section, 'person')

    def findchildren(self, html: str):
        section = self.findbyre(r'(?s)<strong>Beziehungen zu Personen</strong>.*?(<td.*?</td>)', html)
        if section:
            return self.findallbyre(r'(?s)([^<>]*)(?:</a> )?\((?:Sohn|Tochter)\)', section, 'person')

    def findfather(self, html: str):
        section = self.findbyre(r'(?s)<strong>Beziehungen zu Personen</strong>.*?(<td.*?</td>)', html)
        if section:
            return self.findbyre(r'(?s)([^<>]*)(?:</a> )?\(Vater\)', section, 'person')

    def findmother(self, html: str):
        section = self.findbyre(r'(?s)<strong>Beziehungen zu Personen</strong>.*?(<td.*?</td>)', html)
        if section:
            return self.findbyre(r'(?s)([^<>]*)(?:</a> )?\(Mutter\)', section, 'person')

    def findpseudonyms(self, html: str):
        section = self.findbyre(r'(?s)<strong>Beziehungen zu Personen</strong>.*?(<td.*?</td>)', html)
        if section:
            return [self.findbyre(r'Pseudonym: <a[^<>]*>(.*?)<', section)]

    def findwebsite(self, html: str):
        return self.findbyre(r'Homepage[^<>]*<a[^<>]*href="(.*?)"', html)

    def findwebpages(self, html: str):
        return self.findallbyre(r'Internet[^<>]*<a[^<>]*href="(.*?)"', html)

    def findworkfields(self, html: str):
        result = self.findallbyre(r'(?s)Fachgebiet:(.*?)<', html, 'subject')
        sections = self.findallbyre(r'(?s)<strong>Thematischer Bezug</strong>.*?(<td.*?</td>)', html)
        for section in sections:
            subjects = self.findallbyre(r'>([^<>]*)<', section)
            for subject in subjects:
                if ':' in subject:
                    result += self.findallbyre(r'([\w\s]+)', subject[subject.find(':') + 1:], 'subject')
                else:
                    result += self.findallbyre(r'(.+)', subject, 'subject')

        return result

    def findemployers(self, html: str):
        section = self.findbyre(r'(?s)<strong>Beziehungen zu Organisationen</strong>.*?(<td.*?</td>)', html)
        if section:
            return self.findallbyre(r'(?s)[>;]([^<>;]*)[<;]', section,
                                    'employer', alt=['university'])
        return self.findallbyre(r'Tätig an (?:d\w\w )?([^<>;]*)', html,
                                'employer', alt=['university'])

    def findsources(self, html: str):
        section = self.findbyre(r'(?s)<strong>Quelle</strong>.*?<td[^<>]*(>.*?<)/td>', html)
        if section:
            subsections = self.findallbyre(r'>([^<>]*)<', section)
            result = []
            for subsection in subsections:
                result += self.findallbyre(r'([^;]+)', subsection, 'source')
            return result

    def findmemberships(self, html: str):
        section = self.findbyre(r'(?s)<strong>Beziehungen zu Organisationen</strong>.*?(<td.*?</td>)', html)
        if section:
            return self.findallbyre(r'>([^<>]*)</a>', section, 'organization', skips=['religious order', 'employer', 'university'])

    def findrelorder(self, html: str):
        section = self.findbyre(r'(?s)<strong>Beziehungen zu Organisationen</strong>.*?(<td.*?</td>)', html)
        if section:
            return self.findbyre(r'>([^<>]*)</a>', section, 'religious order', skips=['organization', 'employer', 'university'])

    def findfloruit(self, html: str):
        return self.findbyre(r'(?s)Wirkungsdaten:(.*?)<', html)

    def findmixedrefs(self, html: str):
        return self.finddefaultmixedrefs(html)


class LcAuthAnalyzer(Analyzer):
    def setup(self):
        self.dbproperty = 'P244'
        self.dbid = 'Q13219454'
        self.dbname = 'Library of Congress Authorities'
        # self.urlbase = None
        self.hrtre = '(<h1.*?)<h3>(?:Editorial Notes|Change Notes|Sources|Alternate Formats)'
        self.language = 'en'
        self.escapehtml = True

    @property
    def url(self):
        if self.isperson:
            return 'http://id.loc.gov/authorities/names/{id}.html'.format(
                id=self.id)
        if self.id.startswith('s'):
            return 'http://id.loc.gov/authorities/subjects/{id}.html'.format(
                id=self.id)
        return None

    @property
    def isperson(self):
        return self.id.startswith('n')

    def findinstanceof(self, html: str):
        return self.findbyre(r'MADS/RDF ([^<>]+)', html, 'instanceof')

    def findnames(self, html) -> List[str]:
        section = self.findbyre(
            r'(?s)<h3>Variants</h3><ul[^<>]*>(.*?)</ul>', html)
        if section:
            result = self.findallbyre(r'>([^<>]*)?(?:,[\s\d\-]+)<', section)
        else:
            result = []

        return result \
            + self.findallbyre(r'skos:prefLabel">(.*?)(?:</|, \d)', html) \
            + self.findallbyre(r'skosxl:literalForm">(.*?)(?:<|, \d)', html)

    def finddescriptions(self, html: str):
        result = [self.findbyre(r'<title>([^<>]*)-', html)]
        section = self.findbyre(r'(?s)<h3>Sources</h3>(.*?)</ul>', html)
        if section:
            result += self.findallbyre(r'\(([^<>]*?)\)', section)
        return result

    def findlongtext(self, html: str):
        return self.findbyre(r'(?s)<h3>Sources</h3>(.*?)</ul>', html)

    def findfirstname(self, html: str):
        if self.isperson:
            return self.findbyre(r'<h1[^<>]*>[^<>]*?,\s*(\w*)', html, 'firstname')

    def findlastname(self, html: str):
        if self.isperson:
            return self.findbyre(r'h1[^<>]*>([^<>]*?),', html, 'lastname')

    def findbirthdate(self, html: str):
        result = self.findbyre(r'<li><h3>Birth Date</h3><ul[^<>]*>(\d{8})<', html)
        if result:
            return f'{result[6:]}-{result[4:6]}-{result[:4]}'

        result = (
            self.findbyre(r'(?s)Birth Date</h3><.*?>(?:\(.*?\))?([^<>]*?)</ul>', html)
            or self.findbyre(r'[\s\(]b\.\s+([\w\-/]+)', html)
            or self.findbyre(r'skos:prefLabel">[^<>]*, (\d+)-', html)
        )
        if result and '[' not in result:
            m = re.match(r'(\d+)[/\-](\d+)[/\-](\d+)', result)
            if m:
                result = '{}-{}-{}'.format(
                    m[2], m[1], m[3] if len(m[3]) > 2 else '19' + m[3]
                )
            return result

        return None

    def finddeathdate(self, html: str):
        result = self.findbyre(r'<li><h3>Death Date</h3><ul[^<>]*>(\d{8})<', html)
        if result:
            return f'{result[6:]}-{result[4:6]}-{result[:4]}'

        result = (
            self.findbyre(r'(?s)Death Date</h3><.*?>(?:\(.*?\))?([^<>]*?)</ul>', html)
            or self.findbyre(r'skos:prefLabel">[^<>]*, \d+-(\d+)', html)
        )
        if result and '[' not in result:
            m = re.match(r'(\d+)[/\-](\d+)[/\-](\d+)', result)
            if m:
                result = '{}-{}-{}'.format(
                    m[2], m[1], m[3] if len(m[3]) > 2 else '19' + m[3]
                )
            return result

        return None

    def findbirthplace(self, html: str):
        return self.findbyre(
            r'(?s)Birth Place</h3><.*?>(?:\([^<>]*\))?([^<>]+)\s*(?:\([^<>]*\))?\s*</?[au]', html, 'city')

    def finddeathplace(self, html: str):
        return self.findbyre(
            r'(?s)Death Place</h3><.*?>(?:\([^<>]*\))?([^<>]+)\s*(?:\([^<>]*\))?\s*</?[au]', html, 'city')

    def findgender(self, html: str):
        return self.findbyre(r'(?s)Gender</h3><.*?>([^<>]*)(?:<[^<>]*>|\s)*</ul>', html, 'gender')

    def findoccupations(self, html: str):
        section = self.findbyre(r'(?s)Occupation</h3>(.*?)<h3', html)
        if section:
            return self.findallbyre(r'>([^<>]+)</a>', section, 'occupation')

    def findrelorder(self, html: str):
        section = self.findbyre(r'(?s)Affiliation</h3>.*?(<ul.*?</ul>)', html)
        if section:
            for result in self.findallbyre(r'>([^<>]+)</a', section, 'religious order',
                                           skips=['employer', 'university']):
                if result:
                    return result

    def findemployers(self, html: str):
        section = self.findbyre(r'(?s)Affiliation</h3>.*?(<ul.*?</ul>)', html)
        if section:
            return self.findallbyre(r'>([^<>]+)</a', section, 'employer', alt=['university'])

    def findlanguagesspoken(self, html: str):
        if self.isperson:
            sections = self.findallbyre(r'(?s)Associated Language[^<>]*</h3>.*?(<ul.*?</ul>)', html)
            result = []
            for section in sections:
                result += self.findallbyre(r'>([^<>]+)</a', section, 'language')
            return result

        return None

    def findworkfields(self, html: str):
        section = self.findbyre(r'(?s)Field of Activity</h3>.*?(<ul.*?</ul>)', html)
        if section:
            return self.findallbyre(r'>([^<>]+)</a', section, 'subject')

        return None

    def findmixedrefs(self, html: str):
        return self.finddefaultmixedrefs(html, includesocial=False)


class UlanAnalyzer(Analyzer):
    def setup(self):
        self.dbproperty = 'P245'
        self.dbid = 'Q2494649'
        self.dbname = 'ULAN'
        self.urlbase = 'https://www.getty.edu/vow/ULANFullDisplay?find=&role=&nation=&subjectid={id}'
        self.hrtre = '(Record Type:.*?)Sources and Contributors:'
        self.language = 'en'

    def finddescription(self, html: str):
        return self.findbyre(r'(?s)<SPAN CLASS=page>.*?</B>\s*\((.*?)\)', html)

    def findlongtext(self, html: str):
        return self.findbyre(r'(?s)<B>Note:\s*</B>(.*?)</', html)

    def findnames(self, html) -> List[str]:
        section = self.findbyre(r'<B>Names:</B>.*<TR>(.*?)</TABLE>', html)
        if section:
            return self.findallbyre(r'<B>(.*?)<', section)
        return []

    def findinstanceof(self, html: str):
        result = self.findbyre(r'Record Type:.*?>(.*?)<', html, 'instanceof')
        self.isperson = result == 'Q5'
        return result

    def findlastname(self, html: str):
        if self.isperson:
            return self.findbyre(r'(?s)<SPAN CLASS=page><B>([^<>]*?),', html, 'lastname')

    def findfirstname(self, html: str):
        if self.isperson:
            return self.findbyre(r'(?s)<SPAN CLASS=page><B>[^<>]*?,\s*([\w\-]+)', html, 'firstname')

    def findnationality(self, html: str):
        if self.isperson:
            return self.findbyre(r'(?s)Nationalities:.*<SPAN CLASS=page>([^<>]*)\(', html, 'country')

    def country(self, html: str):
        if not self.isperson:
            return self.findbyre(r'(?s)Nationalities:.*<SPAN CLASS=page>([^<>]*)\(', html, 'country')

    def findoccupations(self, html: str):
        if self.isperson:
            section = self.findbyre(r'(?s)>Roles:<.*?<TR>(.*?)</TABLE>', html)
            if section:
                return self.findallbyre(r'>([^<>\(\)]+)[<\(]', section, 'occupation')

    def findgender(self, html: str):
        return self.findbyre(r'Gender:<.*?>(.*?)<', html, 'gender')

    def findbirthplace(self, html: str):
        return self.findbyre(r'Born:.*?>([^<>]*)\(', html, 'city')

    def finddeathplace(self, html: str):
        return self.findbyre(r'Died:.*?>([^<>]*)\(', html, 'city')

    def findlocation(self, html: str):
        if not self.isperson:
            return self.findbyre(r'location:.*?<A.*?>([^<>]*)\(', html, 'city')

    def findbirthdate(self, html: str):
        if self.isperson:
            result = self.findbyre(r'</B>\s*\([^<>]*,([^<>]*)-', html)
            if result and 'ctive' not in result:
                return result

    def finddeathdate(self, html: str):
        if self.isperson:
            part = self.findbyre(r'</B>\s*\([^<>]*,([^<>]*-[^<>\)]*)', html)
            if part and 'ctive' not in part:
                return self.findbyre(r'-([^<>\)]*)', part)

    def findworkplaces(self, html: str):
        return self.findallbyre(r'>active:(?:\s|&nbsp;|<[^<>]*>)*([^<>]*)\(', html, 'city')

    def findchildren(self, html: str):
        return self.findallbyre(r'(?s)>parent of.*?<A[^<>]*>(.*?)<', html, 'person')

    def findfather(self, html: str):
        result = self.findallbyre(r'(?s)>child of.*?<A[^<>]*>(.*?)<', html, 'male-person')
        if result:
            return result[0]

    def findmother(self, html: str):
        result = self.findallbyre(r'(?s)>child of.*?<A[^<>]*>(.*?)<', html, 'female-person')
        if result:
            return result[0]

    def findsiblings(self, html: str):
        return self.findallbyre(r'(?s)>sibling of.*?<A[^<>]*>(.*?)<', html, 'person')

    def findstudents(self, html: str):
        return self.findallbyre(r'(?s)>teacher of.*?<A[^<>]*>(.*?)<', html, 'artist')

    def findteachers(self, html: str):
        return self.findallbyre(r'(?s)>sibling of.*?<A[^<>]*>(.*?)<', html, 'artist')


class BnfAnalyzer(Analyzer):
    def setup(self):
        self.dbproperty = 'P268'
        self.dbid = 'Q19938912'
        self.dbname = 'Bibliothèque nationale de France'
        self.urlbase = 'http://catalogue.bnf.fr/ark:/12148/cb{id}'
        self.hrtre = '(<div class="notice" id="ident">.*?)<div class="notice line"'
        self.language = 'fr'
        self.escapehtml = True

    def finddescriptions(self, html: str):
        return self.findallbyre(r'<meta name="DC.subject" lang="fre" content="(.*?)"', html)

    def findnames(self, html) -> List[str]:
        return self.findallbyre(r'<span class="gras">(.*?)<', html)

    def findlongtext(self, html: str):
        return self.findbyre(r'(?s)<div[^<>]*"description">(.*?)</div>', html)

    def findinstanceof(self, html: str):
        self.isperson = 'Notice de personne' in html
        if self.isperson:
            return 'Q5'
        # else
        return self.findbyre(r'(?s)Type de[^<>]+:.*?>([^<>]*)</', html, 'instanceof')

    def findnationality(self, html: str):
        if self.isperson:
            return self.findbyre(r'(?s)Pays[^<>]*:.*?<span.*?>(.*?)</', html, 'country')

    def findcountry(self, html: str):
        if not self.isperson:
            return self.findbyre(r'(?s)Pays[^<>]*:.*?<span.*?>(.*?)</', html, 'country')

    def findlanguagesspoken(self, html: str):
        if self.isperson:
            result = []
            section = self.findbyre(r'(?s)Langue\(s\).*?(<.*?>)\s*</div>', html)
            if section:
                section = section.replace('ancien ', 'ancien###')
                section = self.TAGRE.sub(' ', section)
                section = section.replace('###', ' ')
                result = self.findallbyre(r'([\w\s&;]{3,})', section, 'language')
            result += self.findallbyre(r'aussi(?: écrit)? en ([\w]+)', html, 'language')
            result += self.findallbyre(r'aussi(?: écrit)? en [\w\s]+ et en ([\w]+)', html, 'language')
            result += self.findallbyre(r'[tT]radu(?:cteur|it) du (.+?) en ', html, 'language')
            result += self.findallbyre(r'[tT]radu(?:cteur|it) .+? en ([\w\s]+)', html, 'language')
            return result

    def findgender(self, html: str):
        return self.findbyre('(?s)Sexe[^<>]+:.*?<span.*?>(.*?)</', html, 'gender')

    def findbirthdate(self, html: str):
        section = self.findbyre(r'(?s)Naissance.*?(<.*?>)\s*</div>', html)
        if section:
            result = self.findbyre(r'>([^<>]+?),', section) or self.findbyre(r'>([^<>]+?)</', section)
            if result and '..' not in result and re.search(r'\d{4}', result):
                return result
        return None

    def findbirthplace(self, html: str):
        section = self.findbyre(r'(?s)Naissance.*?(<.*?>)\s*</div>', html)
        if section:
            result = self.findbyre(',([^<>]+)<', section, 'city')
        if not result:
            result = self.findbyre(r'Née? à ([\w\s]+)', html, 'city')
        return result

    def finddeathdate(self, html: str):
        section = self.findbyre(r'(?s)Mort[^<>]*:.*?(<.*?>)\s*</div>', html)
        if section:
            result = self.findbyre(r'>([^<>]+?),', section) or self.findbyre(r'>([^<>]+?)</', section)
            if result and re.search(r'\d{4}', result):
                return result

    def finddeathplace(self, html: str):
        section = self.findbyre(r'(?s)Mort[^<>]*:.*?(<.*?>)\s*</div>', html)
        if section:
            return self.findbyre(r',([^<>]+)<', section, 'city')

    def findisni(self, html: str):
        return self.findbyre(r'ISNI ([\d\s]*)', html) or self.findbyre(r'isni/(\w+)', html)

    def findoccupations(self, html: str):
        section = self.findbyre(r'(?s)"description">\s*<span[^<>]*>(.*?)</span>', html)
        if section:
            result = []
            texts = []
            for subsection in section.split(' et '):
                texts += self.findallbyre(r'(\w[\-\s\w&\']+)', subsection)
            for text in texts[:8]:
                result.append(self.findbyre(r'(.+)', text, 'occupation'))
            return result
        return None

    def findworkfields(self, html: str):
        return self.findallbyre(r"[Pp]rofesseur d[eu']([\w\s]+)? [àa]u?x? ", html, 'subject') + \
               self.findallbyre(r"[Ss]pécialiste d[eu']s?([\w\s]+) [àa]u?x? ", html, 'subject') + \
               self.findallbyre(r'[Ss]pécialisée? en ([\w\s]+) [àa]u?x? ', html, 'subject') + \
               self.findallbyre(r"[Pp]rofesseur d[eu']([\w\s]+)", html, 'subject') + \
               self.findallbyre(r"[Ss]pécialiste d[eu']s?([\w\s]+)", html, 'subject') + \
               self.findallbyre(r'[Ss]pécialisée? en ([\w\s]+)', html, 'subject')

    def findemployers(self, html: str):
        sections = self.findallbyre(r'En poste\s*:(.*?)[\(<]', html)
        result = []
        for section in sections:
            result += self.findallbyre(r'([^;]*)', section, 'employer', alt=['university'])
        return result


class SudocAnalyzer(Analyzer):
    def setup(self):
        self.dbproperty = 'P269'
        self.dbid = 'Q47757534'
        self.dbname = 'SUDOC'
        self.urlbase = 'https://www.idref.fr/{id}'
        self.hrtre = '(<div id="editzone">.*?)<p>Informations sur la notice</p>'
        self.language = 'fr'
        self.escapehtml = True

    def finddescriptions(self, html: str):
        return self.findallbyre(r'(?s)Notice de type</span>.*?([^<>]*)</span>', html) \
            + self.findallbyre(r'(?s)<span class="detail_label">Note publique d\'information.*?"detail_value">(.*?)<',
                               html)

    def findnames(self, html) -> List[str]:
        result = []
        section = self.findbyre(
            r"(?s)<p>Point d'accès autorisé</p>(.*)<p>", html)
        if section:
            result += self.findallbyre(r'(?s)<b>(.*?)[\(<]', section)

        section = self.findbyre(
            r"(?s)<p>Variantes de point d'accès</p>(.*)<p>", html)
        if section:
            result += self.findallbyre(r'(?s)<b>(.*?)[\(<]', section)

        return result

    def findlongtext(self, html: str):
        return '\n'.join(self.findallbyre(r'(?s)<span class="detail_value">(.*?)</span>', html))

    def findinstanceof(self, html: str):
        return self.findbyre(r'(?s)Notice de type</span>.*?([^<>]*)</span>', html, 'instanceof')

    def findlanguagesspoken(self, html: str):
        result = self.findallbyre("Traducteur de l['ea](.*?)vers", html, 'language') +\
                 self.findallbyre("Traducteur de .*? vers l['ea](.*?)<", html, 'language')
        section = self.findbyre(r'(?s)<span id="Langues" class="DataCoded">(.*?)</span>', html)
        if section:
            result += self.findallbyre(r'([\w\s\(\)]+)', section, 'language')
        return result

    def findnationality(self, html: str):
        return self.findbyre(r'(?s)<span id="PaysISO3166" class="DataCoded">(.*?)</span>', html, 'country')

    def findbirthdate(self, html: str):
        result = self.findbyre(r'(?s)Date de naissance[^<>]*</b><span[^<>]*>([^<>]*)<', html)
        if result:
            return ''.join([char for char in result if char in '0123456789-/'])

    def finddeathdate(self, html: str):
        result = self.findbyre(r'(?s)Date de mort[^<>]*</b><span[^<>]*>([^<>]*)<', html)
        if result:
            return ''.join([char for char in result if char in '0123456789-/'])

    def findgender(self, html: str):
        return self.findbyre(r'<span id="Z120_sexe" class="DataCoded">(.*?)</span>', html, 'gender')

    def findisni(self, html: str):
        return self.findbyre(r'http://isni.org/isni/(\w+)', html)

    def findmixedrefs(self, html: str):
        return self.finddefaultmixedrefs(html)

    def findbirthplace(self, html: str):
        return self.findbyre(r'ieu de naissance.? (.*?)[\.<>]', html, 'city')

    def finddeathplace(self, html: str):
        return self.findbyre(r'ieu de décès.? (.*?)[\.<>]', html, 'city')

    def findoccupations(self, html: str):
        sections = self.findallbyre(r'(?s)<div class="detail_chaqueNoteBio">.*?<span class="detail_value">(.*?)<', html)
        texts = []
        for section in sections:
            for sectionpart in section.split(' et '):
                texts += self.findallbyre(r'([^\.,;]+)', sectionpart)
        return [self.findbyre(r'(.+)', text.strip().lstrip('-'), 'occupation') for text in texts[:8]]


class CiniiAnalyzer(Analyzer):
    def setup(self):
        self.dbproperty = 'P271'
        self.dbid = 'Q10726338'
        self.dbname = 'CiNii'
        self.urlbase = 'https://ci.nii.ac.jp/author/{id}'
        self.hrtre = '(<div class="itemheading authordata">.*?)<div class="resultlist">'
        self.language = 'ja'

    def findnames(self, html) -> List[str]:
        section = self.findbyre(r'(?s)<h1[^<>]>(.*?)</h1>', html) or ''
        return (
            self.findallbyre(
                r'(?s)<span>(.*?)(?:, b\. \d+)?\s*</span>', section)
            + self.findallbyre(r'"seefm">(.*?)(?:, b\. \d+)?\s*[<\(（]', html)
        )

    def findinstanceof(self, html: str):
        return 'Q5'

    def findfirstname(self, html: str):
        return self.findbyre(r'(?s)<h1[^<>]*>[^<>]*<span>[^<>]*?,\s*([\w\-]+)', html, 'firstname')

    def findlastname(self, html: str):
        return self.findbyre(r'(?s)<h1[^<>]*>[^<>]*<span>([^<>]+?),', html, 'lastname')

    def findbirthdate(self, html: str):
        return self.findbyre(r', b\. (\d+)', html)


class ImdbAnalyzer(Analyzer):
    def setup(self):
        self.dbproperty = 'P345'
        self.dbid = 'Q37312'
        self.dbname = 'Internet Movie Database'
        self.urlbase = None
        if self.isfilm:
            self.hrtre = '(<h1.*?)<h2>Frequently Asked Questions'
        elif self.isperson:
            self.hrtre = '(<h1.*?</table>)'
        self.language = 'en'
        self.escapeurl = True

    @property
    def url(self):
        if self.isfilm:
            return f'https://www.imdb.com/title/{self.id}/'
        if self.isperson:
            return f'https://www.imdb.com/name/{self.id}/'
        return None

    @property
    def isfilm(self):
        return self.id.startswith('tt')

    @property
    def isperson(self):
        return self.id.startswith('nm')

    def finddescription(self, html: str):
        result = self.findbyre(r'<meta name="description" content="(.*?)"', html)
        if result:
            return '.'.join(result.split('.')[:2])

    def findlongtext(self, html: str):
        return self.findbyre(r'(?s)<div class="inline">(.*?)<', html)

    def findnames(self, html: str):
        result = self.findbyre(r'\'og:title\' content="(.*)"', html) or ''
        return [result.replace(' - IMDb', '')]

    def findinstanceof(self, html: str):
        if self.isfilm:
            return 'Q11424'
        if self.isperson:
            return 'Q5'
        return None

    def findorigcountry(self, html: str):
        if self.isfilm:
            return self.findbyre(r'(?s)Country:.*?>([^<>]+)</a>', html, 'country')

    def findpubdate(self, html: str):
        if self.isfilm:
            return self.findbyre(r'span id="titleYear">\(\s*(?:<[^<>]*>)?(.*?)</', html)

    def findmoviedirectors(self, html: str):
        section = self.findbyre(r'(?s)>Director:(<.*?</div>)', html)
        if section:
            return self.findallbyre(r'"name">([^<>]*)</span>', section, 'filmmaker')

    def findscreenwriters(self, html: str):
        section = self.findbyre(r'(?s)>Writer:(<.*?</div>)', html)
        if section:
            return self.findallbyre(r'"name">([^<>]*)</span>', section, 'filmmaker')

    def findcast(self, html: str):
        section = self.findbyre(r'(?s)>Credited cast:(<.*?</table>)', html)
        if section:
            return self.findallbyre(r'"name">([^<>]*)</span>', section, 'actor')

    def findprodcoms(self, html: str):
        section = self.findbyre(r'(?s)>Production Co:(<.*?</div>)', html)
        if section:
            return self.findallbyre(r'"name">([^<>]*)</span>', section, 'filmcompany')

    def findgenres(self, html: str):
        section = self.findbyre(r'(?s)>Genres:(<.*?</div>)', html)
        if section:
            return self.findallbyre(r'(?s)>([^<>]*)</a>', section, 'film-genre', alt=['genre'])

    def findoriglanguages(self, html: str):
        section = self.findbyre(r'(?s)>Language:(<.*?</div>)', html)
        if section:
            return self.findallbyre(r'(?s)>([^<>]*)</a>', section, 'language')

    def finddurations(self, html: str):
        section = self.findbyre(r'(?s)>Runtime:(<.*?</div>)', html)
        if section:
            return [self.findbyre(r'(?s)>([^<>]*)</time>', section)]

    def findcolors(self, html: str):
        result = self.findbyre(r'(?s)>Color:.*?>([^<>]+)</a>', html, 'film-color')
        if result:
            return [result]

    def findoccupations(self, html: str):
        section = self.findbyre(r'(?s)"jobTitle": (".*?"|\[.*?\])', html)
        if section:
            occupations = self.findallbyre(r'"(.*?)"', section, 'film-occupation', alt=['occupation'])
            return ['Q2526255' if result == 'Q3455803' else result for result in occupations]

    def findbirthdate(self, html: str):
        return self.findbyre(r'"birthDate": "(.*?)"', html)

    def finddeathdate(self, html: str):
        return self.findbyre(r'"deathDate": "(.*?)"', html)

    def findbirthplace(self, html: str):
        return self.findbyre(r'birth_place=(.*?)[&"]', html, 'city')

    def finddeathplace(self, html: str):
        return self.findbyre(r'death_place=(.*?)[&"]', html, 'city')


class SbnAnalyzer(Analyzer):
    def setup(self):
        self.dbproperty = 'P396'
        self.dbid = None
        self.dbname = 'SBN'
        self.urlbase = 'http://opac.sbn.it/opacsbn/opac/iccu/scheda_authority.jsp?bid={id}'
        self.hrtre = '(<tbody>.*?</tbody>)'
        self.language = 'it'

    def findnames(self, html) -> List[str]:
        result = [self.findbyre(r'(?s)Nome autore.*?<a .*?>(.*?)[<&\(]', html)]
        section = self.findbyre(r'(?s)Forme varianti.*?(<.*?)</tr>', html)
        if section:
            result += self.findallbyre(r'(?s)>([^<>]*)</div>', section)
        return result

    def finddescription(self, html: str):
        return self.findbyre(r'(?s)Nota informativa.*?"detail_value">(.*?)<', html)

    def findlongtext(self, html: str):
        return self.findbyre(r'(?s)Nota informativa.*?"detail_value">(.*?)<', html)

    def findinstanceof(self, html: str):
        return self.findbyre(r'(?s)Tipo autore.*?detail_value">(.*?)</td>', html, 'instanceof')

    def findbirthdate(self, html: str):
        return self.findbyre(r'(?s)Datazione\s*</td>\s*<td[^<>]*>(?:[^<>]*,)?([^<>]*?)-', html)

    def finddeathdate(self, html: str):
        return self.findbyre(r'(?s)Datazione\s*</td>\s*<td[^<>]*>[^<>]*-(.*?)<', html)

    def findoccupations(self, html: str):
        section = self.findbyre(
            r'(?s)Nota informativa.*?detail_value">([^<>]*?)\.', html)
        if not section:
            return None
        if ',' in section or ';' in section:
            return self.findallbyre(r'([^,;]+)', section, 'occupation')
        return self.findallbyre(r'(\w{3,})', section, 'occupation')

    def findbirthplace(self, html: str):
        return self.findbyre(r'Nato ad? ([^<>]+) e morto', html, 'city') or \
               self.findbyre(r'Nato ad? ([^<>]+?)[,\(\.]', html, 'city') or \
               self.findbyre(r'Nato e morto ad? ([^<>,\(\.]+)', html, 'city') or \
               self.findbyre(r'Nato ad? ([^<>\.]+)', html, 'city')

    def finddeathplace(self, html: str):
        return self.findbyre(r'[mM]orto ad? ([^<>\.\(]+) nel', html, 'city') or \
               self.findbyre(r'[mM]orto ad? ([^<>\.\(]+)', html, 'city')

    def findlanguagesspoken(self, html: str):
        section = self.findbyre(r'Lingua.*?detail_value">(.*?)<', html)
        if section:
            return self.findallbyre(r'(\w{3,})', section, 'language')

    def findisni(self, html: str):
        return self.findbyre(r'http://isni.org/isni/(\w+)', html)

    def findrelorder(self, html: str):
        section = self.findbyre(r'(?s)Nota informativa.*?detail_value">([^<>]*?)\.', html) or ''
        if 'gesuita' in section.lower():
            return 'Q36380'
        return None


class LibrariesAustraliaAnalyzer(Analyzer):
    def setup(self):
        self.dbproperty = 'P409'
        self.dbid = None
        self.dbname = 'National Library of Australia'
        self.urlbase = 'https://librariesaustralia.nla.gov.au/search/display?dbid=auth&id={id}'
        self.hrtre = '<!--Record summary-->(.*?)<!--Record summary-->'
        self.language = 'en'

    def finddescription(self, html: str):
        return self.findbyre(r'(?s)Heading:.*?">([^<>])*</a>', html)

    def findnames(self, html) -> List[str]:
        result = self.findallbyre(r'(?s)<title>([^<>]*?)(?:<|\(|\s-\s)', html)
        return [','.join(r.split(',')[:2]) for r in result]

    def findbirthdate(self, html: str):
        result = self.findbyre(r'(?s)<dt>Birth:</dt>.*?<li>(.*?)-?</li>', html)
        if result:
            if 'approx' not in result and 'active' not in result:
                return result
        else:
            section = self.findbyre(r'(?s)<dt>Heading:</dt>.*?>([^<>]*)</a', html)
            if section and 'approx' not in section and 'active' not in section:
                result = self.findbyre(r',([^,]*)-', section)
                return result if result else section
        return None

    def findbirthplace(self, html: str):
        result = self.findbyre(r'(?s)<dt>Birth:</dt>(?:\s|<[^<>]*>)*<li>[^<>]*</li>\s*<li>(.*?)</li>', html)
        if result:
            return self.getdata('city', result)
        return None

    def finddeathdate(self, html: str):
        result = self.findbyre(r'(?s)<dt>Death:</dt>.*?<li>(.*?)</li>', html)
        if result:
            if 'approx' not in result:
                return result
        else:
            section = self.findbyre(r'(?s)<dt>Heading:</dt>.*?>([^<>]*)-?</a', html)
            if section:
                result = self.findbyre(r'-([^,\-]*)', section)
                if result and 'approx' not in result:
                    return result

    def findfirstname(self, html: str):
        section = self.findbyre(r'(?s)<dt>Heading:</dt>.*?>([^<>]*)</a', html)
        pywikibot.info(section)
        if section:
            return self.findbyre(r',\s*(\w+)', section, 'firstname')

    def findlastname(self, html: str):
        section = self.findbyre(r'(?s)<dt>Heading:</dt>.*?>([^<>]*)</a', html)
        if section:
            return self.findbyre(r'([^,]*),', section, 'lastname')

    def finddeathplace(self, html: str):
        result = self.findbyre(r'(?s)<dt>Death:</dt>(?:\s|<[^<>]*>)*<li>[^<>]*</li>\s*<li>(.*?)</li>', html)
        if result:
            return self.getdata('city', result)

    def findoccupations(self, html: str):
        section = self.findbyre(r'(?s)<dt>Occupations:</dt>.*?<li>(.*?)</li>', html)
        if section:
            return self.findallbyre(r'(\w+)', section, 'occupation')

    def findmixedrefs(self, html: str):
        result = self.findbyre(r'(?s)<dt>LC number:</dt>.*?<li>(.*?)</li>', html)
        if result:
            result = result.replace(' ', '')
            results = self.findallbyre(r'[a-z]+\d+', result)
            return [('P244', result) for result in results]


class MusicBrainzAnalyzer(Analyzer):
    def setup(self):
        self.dbproperty = 'P434'
        self.dbid = 'Q19832969'
        self.dbname = 'MusicBrainz'
        self.urlbase = 'https://musicbrainz.org/artist/{id}'
        self.urlbase3 = 'https://musicbrainz.org/artist/{id}/relationships'
        self.hrtre = '(<h2 class="artist-information">.*?)<div id="footer">'
        self.language = 'en'

    def finddescription(self, html: str):
        return self.findbyre(r'<div class="wikipedia-extract-body wikipedia-extract-collapse"><p>(.+?)</p>', html)

    def findnames(self, html) -> List[str]:
        return self.findallbyre(r'(?s)<dd class="sort-name">(.*?)</dd>', html)

    def findinstanceof(self, html: str):
        result = self.findbyre(r'<dd class="type">(.*?)</dd>', html, 'instanceof')
        self.isperson = result == 'Q5'
        return result

    def findinception(self, html: str):
        return self.findbyre(r'(?s)<dt>Founded:</dt>.*?<dd[^<>]*>(.*?)[<\(]', html)

    def finddissolution(self, html: str):
        return self.findbyre(r'(?s)<dt>Dissolved:</dt>.*?<dd[^<>]*>(.*?)[<\(]', html)

    def findformationlocation(self, html: str):
        if not self.isperson:
            return self.findbyre(r'(?s)<dt>Founded in:</dt>.*?<bdi>(\w+)', html, 'city') \
                   or self.findbyre(r'(?s)<dt>Founded in:</dt>.*?<bdi>(.*?)</bdi>', html, 'city') \
                   or self.findbyre(r'(?s)<dt>Area:</dt>.*?<bdi>(.*?)</bdi>', html, 'city')

    def findorigcountry(self, html: str):
        if not self.isperson:
            return self.findbyre(r'(?s)<dt>Area:</dt>.*?<bdi>(.*?)</bdi>', html, 'country')

    def findnationality(self, html: str):
        if self.isperson:
            return self.findbyre(r'(?s)<dt>Area:</dt>.*?<bdi>(.*?)</bdi>', html, 'country')

    def findisni(self, html: str):
        return self.findbyre(r'/isni/(\w+)', html)

    def findviaf(self, html: str):
        return self.findbyre(r'"https://viaf.org/viaf/(\w+)/?"', html)

    def findwebsite(self, html: str):
        return self.findbyre(r'(?s)<th>offici.le website:.*?<bdi>(.*?)<', html) or \
               self.findbyre(r'<li class="home-favicon"><a href="(.*?)">', html)

    def findtwitter(self, html: str):
        return self.findbyre(r'<li class="twitter-favicon"><a href="[^"]*">@([^<>]*)</a>', html)

    def findfacebook(self, html: str):
        return self.findbyre(r'<li class="facebook-favicon"><a href="https://www.facebook.com/([^/"]+)/?">', html)

    def findgender(self, html: str):
        return self.findbyre(r'class="gender">(.*?)</', html, 'gender')

    def findbirthdate(self, html: str):
        return self.findbyre(r'(?s)<dt>Born:</dt>.*?<dd[^<>]*>(.*?)[<\(]', html)

    def finddeathdate(self, html: str):
        return self.findbyre(r'(?s)<dt>Died:</dt>.*?<dd[^<>]*>(.*?)[<\(]', html)

    def findbirthplace(self, html: str):
        section = self.findbyre(r'(?s)<dt>Born in:</dt>\s*(<dd.*?</dd>)', html)
        if section:
            return self.getdata('city', self.TAGRE.sub('', section))

    def finddeathplace(self, html: str):
        section = self.findbyre(r'(?s)<dt>Died in:</dt>\s*(<dd.*?</dd>)', html)
        if section:
            return self.getdata('city', self.TAGRE.sub('', section))

        section = self.findbyre(r'(?s)<h2>Genres</h2>(.*?)<h\d', html)
        if section:
            return self.findallbyre('>(.*?)<', section, 'music-genre', alt=['genre'])
        return None

    def findmixedrefs(self, html: str):
        return self.finddefaultmixedrefs(html, includesocial=False) + \
            [('P4862', self.findbyre(r'<li class="amazon-favicon"><a href="[^"]*amazon[^"\?]*/(B\w+)[\?"]', html))] +\
            [('P3453', result) for result in self.findallbyre(r'<dd class="ipi-code">(.*?)</dd>', html)]


class StructuraeAnalyzer(Analyzer):
    def setup(self):
        self.dbproperty = 'P454'
        self.dbid = 'Q1061861'
        self.dbname = 'Structurae'
        self.urlbase = 'http://en.structurae.de/structures/data/index.cfm?ID={id}'
        self.hrtre = '(<h1.*?)Participants</h2>'
        self.language = 'en'

    def finddescription(self, html: str):
        return self.findbyre(r'<meta name="Description" content="(.*?)"', html)

    def findlongtext(self, html: str):
        return self.findbyre(r'(?s)<div class="js-acordion-body" id="notes">\s*<p>(.*?)</div>', html)

    def findlanguagenames(self, html: str):
        return [(m[0], m[1].replace('-', ' '))
                for m in re.findall(r'(?s)"alternate"[^<>]*hreflang="(\w+)"[^<>]*/([^<>"]*)">', html)]

    def findnames(self, html) -> List[str]:
        return [
            self.findbyre(r'(?s)<h1[^<>]*>(.*?)<', html),
            self.findbyre(r'(?s)Name in [^<>]*</th>[^<>]*<td>(.*?)<', html),
        ]

    def findinstanceof(self, html: str):
        return 'Q41176'

    def findinception(self, html: str):
        return self.findbyre(r'(?s)<th>Completion.*?>([^<>]+)</a>', html)

    def finduse(self, html: str):
        return self.findbyre(r'(?s)Function / usage:.*?>([^<>]+)</a>', html, 'function')

    def findlocation(self, html: str):
        return self.findbyre(r"(?s)itemprop='containedInPlace'.*?<strong>(.*?)</", html, 'city')

    def findcountry(self, html: str):
        return self.findbyre(r"itemprop='containedInPlace'.*>([^<>]+)</span>", html, 'country')

    def findaddress(self, html: str):
        return self.findbyre(r'itemprop="address">([^<>]+)</', html)

    def findcoords(self, html: str):
        lat = self.findbyre(r'itemprop="latitude" content="(.*?)"', html)
        lon = self.findbyre(r'itemprop="longitude" content="(.*?)"', html)
        if lat and lon:
            return f'{lat} {lon}'

    def findheights(self, html: str):
        return [self.findbyre(r'(?s)<td>height</td>.*<td>(.*?)</td>', html)]

    def findfloorsabove(self, html: str):
        return self.findbyre(r'(?s)<td>number of floors \(above ground\)</td>.*<td>(.*?)</td>', html)


class SelibrAnalyzer(Analyzer):
    def setup(self):
        self.dbproperty = 'P906'
        self.dbid = 'Q1798125'
        self.dbname = 'LIBRIS'
        self.urlbase = 'https://libris.kb.se/auth/{id}'
        # self.urlbase = None
        self.hrtre = '(.*)'
        self.language = 'en'

    def finddescription(self, html: str):
        return self.findbyre(r'<h1>(.*?)</', html)

    def findlongtext(self, html: str):
        return self.findbyre(r'(?s)<div class="bio">(.*?)</div>', html)

    def findinstanceof(self, html: str):
        return 'Q5'

    def findviaf(self, html: str):
        return self.findbyre(r'http://viaf.org/viaf/(\w+)', html)

    def findnames(self, html) -> List[str]:
        return self.findallbyre(r'(?s)<h1[^<>]*>[^<>]*:([^<>]*?)[,<]', html)


class BneAnalyzer(Analyzer):
    def setup(self):
        self.dbproperty = 'P950'
        self.dbid = None
        self.dbname = 'Biblioteca Nacional de España'
        self.urlbase = 'http://datos.bne.es/persona/{id}.html'
        self.hrtre = '(<h1.*?)<h3>Descarga en otros formatos'
        self.language = 'es'

    def findnames(self, html) -> List[str]:
        return self.findallbyre('<h3>(.*?)<', html)

    def finddescriptions(self, html: str):
        return [
            self.findbyre(r'"og:description" content="([^"]+),', html),
            self.findbyre(r'"og:description" content="Descubre ([^"]+),', html),
            self.findbyre(r'"og:description" content="([^"]+)"', html),
            self.findbyre(r'"og:title" content="(.+?)"', html),
            self.findbyre(r'(?s)class="bio">.*?<p>(.*?)</p>', html),
        ]

    def findlongtext(self, html: str):
        return self.findbyre(r'(?s)<table class="table table-condensed table-responsive">(.*?)</table>', html)

    def findlastname(self, html: str):
        return self.findbyre(r'<h1>([^<>]+),', html, 'lastname')

    def findfirstname(self, html: str):
        return self.findbyre(r'<h1>[^<>]+,\s*([\w\-]+)', html, 'firstname')

    def findbirthdate(self, html: str):
        result = self.findbyre(r'(?s)Año de nacimiento:\s*<span>(.*?)<', html) or \
                 self.findbyre(r'<h1>[^<>]+\((?:n\.\s*)?([^\)<>-]+?)[–\-\)]', html)
        if result and 'fl.' not in result and not result.strip().startswith('m.') and '1' in result:
            return result

    def finddeathdate(self, html: str):
        result = self.findbyre(r'(?s)Año de fallecimiento:\s*<span>(.*?)<', html)
        if result:
            return result
        preresult = self.findbyre(r'<h1>(.*?)</h1>', html)
        if preresult and 'fl.' not in preresult:
            return self.findbyre(r'<h1>[^<>]+\([^<>]+[–\-]([^<>]+\d{4}[^<>]+)\)', html)

    def findbirthplace(self, html: str):
        return self.findbyre(r'(?s)Lugar de nacimiento:\s*<span>(.*?)<', html, 'city')

    def finddeathplace(self, html: str):
        return self.findbyre(r'(?s)Lugar de fallecimiento:\s*<span>(.*?)<', html, 'city')

    def findviaf(self, html: str):
        return self.findbyre(r'"http://viaf.org/viaf/(\w+)/?"', html)

    def findisni(self, html: str):
        return self.findbyre(r'"http://isni-url.oclc.nl/isni/(\w+)"', html)

    def findmixedrefs(self, html: str):
        return self.finddefaultmixedrefs(html)

    def findoccupations(self, html: str):
        section = self.findbyre(r'(?s)<h4>Categoría profesional:(.*?)</h4>', html)
        if section:
            return self.findallbyre(r'([^<>,]*)', section, 'occupation')
        return None

    def findworkfields(self, html: str):
        section = self.findbyre(r'(?s)<h4>Campo de actividad:(.*?)</h4>', html)
        if section:
            return self.findallbyre(r'([^<>,]*)', section, 'subject')
        return None

    def findlanguagesspoken(self, html: str):
        section = self.findbyre(r'(?s)<h4>>Lengua:(.*?)</h4>', html)
        if section:
            return self.findallbyre(r'([^<>,])*', section, 'subject')
        return None


class OrcidAnalyzer(Analyzer):
    def setup(self):
        self.dbproperty = 'P496'
        self.dbid = None
        self.dbname = 'Orcid'
        self.urlbase = 'https://orcid.org/{id}'
        self.language = 'en'
        self.hrtre = r'(<div class="workspace-section">.*?)</i>\s*Works\('

    def findinstanceof(self, html: str):
        return 'Q5'

    def findnames(self, html) -> List[str]:
        return self.findallbyre(r'(?s)"(?:full|other)-name">(.*?)<', html)

    def finddescriptions(self, html: str):
        return [
            self.findbyre(r'(?s)<div class="bio-content">(.*?)<', html),
            self.findbyre(r'(?s)<div class="bio-content">(.*?)</div>', html)
        ]

    def findlongtext(self, html: str):
        return self.findbyre(r'(?s)<div class="bio-content">(.*?)</div>', html)

    def findnationalities(self, html: str):
        return self.findallbyre(r'"country">(.*?)<', html, 'country')

    def findschools(self, html: str):
        pywikibot.info('Check education and affiliations by hand!')


class CbdbAnalyzer(Analyzer):
    def setup(self):
        self.dbproperty = 'P497'
        self.dbid = 'Q13407958'
        self.dbname = 'China Biographical Database'
        self.urlbase = 'https://cbdb.fas.harvard.edu/cbdbapi/person.php?id={id}'
        self.language = 'zh'
        self.hrtre = r'(<table style="font-size:smaller">.*?)<hr>'

    def findlanguagenames(self, html: str):
        return [
            ('en', self.findbyre(r'<b>索引/中文/英文名稱</b>:[^<>]*/([^<>]*)<', html)),
            ('zh', self.findbyre(r'<b>索引/中文/英文名稱</b>:[^<>]*?/([^<>]*)/', html))
        ]

    def findbirthdate(self, html: str):
        return self.findbyre(r'(?s)<b>生年</b>[^<>]*\(([^<>]*?)\)', html)

    def finddeathdate(self, html: str):
        return self.findbyre(r'(?s)<b>卒年</b>[^<>]*\(([^<>]*?)\)', html)

    def findlongtext(self, html: str):
        return self.findbyre(r'(?s)註.*?<td>(.*?)</td>', html)

    def findnationalities(self, html: str):
        return [
            self.findbyre(r'(?s)<b>生年</b>:\s*(.)', html, 'dynasty')
            or self.findbyre(r'(?s)<b>生年</b>:\s*(..)', html, 'dynasty'),
            self.findbyre(r'(?s)<b>卒年</b>:\s*(.)', html, 'dynasty')
            or self.findbyre(r'(?s)<b>卒年</b>:\s*(..)', html, 'dynasty')
        ]


class FindGraveAnalyzer(Analyzer):

    def setup(self):
        self.dbproperty = 'P535'
        self.dbid = 'Q63056'
        self.dbname = 'Find a Grave'
        self.urlbase = 'https://www.findagrave.com/memorial/{id}'
        self.language = 'en'
        self.hrtre = r'(<h1.*?</table>)'

    def getvalue(self, name, html, category=None):
        return self.findbyre(fr'{name}: "(.*?)"', html, category)

    def findnames(self, html) -> List[str]:
        return [self.getvalue('shareTitle', html)]

    def findlongtext(self, html: str):
        return self.findbyre(r'(?s) id="fullBio">(.*?)<', html)

    def finddeathdate(self, html: str):
        return self.getvalue('deathDate', html) or \
               self.findbyre(r'"deathDate">(.*?)<', html) or \
               self.getvalue('deathYear', html)

    def findburialplace(self, html: str):
        return self.getvalue('cemeteryName', html, 'cemetary') or \
               self.getvalue('cemeteryCityName', html, 'city') or \
               self.getvalue('locationName', html, 'city')

    def findfirstname(self, html: str):
        return self.getvalue('firstName', html, 'firstname')

    def findlastname(self, html: str):
        return self.getvalue('lastName', html, 'lastname')

    def findbirthdate(self, html: str):
        return self.findbyre(r'"birthDate">(.*?)<', html) or \
               self.getvalue('birthYear', html)

    def findbirthplace(self, html: str):
        return self.findbyre(r'"birthPlace">(.*?)<', html, 'city')

    def finddeathplace(self, html: str):
        return self.findbyre(r'"deathPlace">(.*?)<', html, 'city')

    def findfather(self, html: str):
        result = self.getvalue('fatherName', html, 'person')
        if result:
            return result
        section = self.findbyre(r'(?s)>Ouders</b>(.*?)</ul>', html)
        if section:
            result = self.findallbyre(r'(?s)<h4[^<>]*>(.*?)</h4>', section, 'male-person')
            result = [r for r in result if r]
            if result:
                return result[0]

    def findmother(self, html: str):
        result = self.getvalue('motherName', html, 'person')
        if result:
            return result
        section = self.findbyre(r'(?s)>Ouders</b>(.*?)</ul>', html)
        if section:
            result = self.findallbyre(r'(?s)<h4[^<>]*>(.*?)</h4>', section, 'female-person')
            result = [r for r in result if r]
            if result:
                return result[0]

    def findspouses(self, html: str):
        result = self.findallbyre(r'sp\d+Name: "(.*?)"', html, 'person')
        if result:
            return result
        section = self.findbyre(r'(?s)>Partners</b>(.*?)</ul>', html)
        if section:
            return self.findallbyre(r'(?s)<h4[^<>]*>(.*?)</h4>', section, 'person')

    def findsiblings(self, html: str):
        section = self.findbyre(r'(?s)>Broer[^<>]*zus[^<>]*</b>(.*?)</ul>', html)
        if section:
            return self.findallbyre(r'(?s)<h4[^<>]*>(.*?)</h4>', section, 'person')

    def findchildren(self, html: str):
        section = self.findbyre(r'(?s)>Kinderen</b>(.*?)</ul>', html)
        if section:
            return self.findallbyre(r'(?s)<h4[^<>]*>(.*?)</h4>', section, 'person')


class IpniAuthorsAnalyzer(Analyzer):

    def setup(self):
        self.dbproperty = 'P586'
        self.dbid = 'Q922063'
        self.dbname = 'International Plant Names Index'
        self.urlbase = 'http://www.ipni.org/ipni/idAuthorSearch.do?id={id}'
        self.language = 'en'
        self.hrtre = '</h2>(.*?)<p>View the'

    def findinstanceof(self, html: str):
        return 'Q5'

    def findnames(self, html) -> List[str]:
        result = self.findallbyre(r'(?s)<h3>(.*?)[\(<]', html)
        section = self.findbyre(
            r'(?s)<h4>Alternative Names:\s*</h4(>.*?<)h/d', html)
        if section:
            result += self.findallbyre(r'(?)>([^<>]*)<', section)
        return result

    def findlastname(self, html: str):
        return self.findbyre(r'(?s)<h3>([^<>]*?),', html, 'lastname')

    def findfirstname(self, html: str):
        return self.findbyre(r'(?s)<h3>[^<>]*,\s*([\w\-]+)', html, 'firstname')

    def findlongtext(self, html: str):
        return self.findbyre(r'(?s)<h4>Comment:\s*</h4>(.*?)<h\d', html)

    def findbirthdate(self, html: str):
        return self.findbyre(r'(?s)<h3>[^<>]*\((\d+)-', html)

    def finddeathdate(self, html: str):
        return self.findbyre(r'(?s)<h3>[^<>]*\([^<>]*?-(\d+)\)', html)

    def findmixedrefs(self, html: str):
        return [('P428', self.findbyre(r'(?s)<h4>Standard Form:\s*</h4>\s*<p>(.*?)<', html))]

    def findworkfields(self, html: str):
        section = self.findbyre(r'(?s)<h4>Area of Interest:\s*</h4>\s*<p>(.*?)</p>', html)
        if section:
            return self.findallbyre(r'([^,]*)', section, 'subject')

    def findsources(self, html: str):
        section = self.findbyre(r'(?s)<h4>Information Source:</h4>\s*<p>(.*?)</p>', html)
        if section:
            return self.findallbyre(r'([^,]*)', section, 'source')

    def findnationalities(self, html: str):
        section = self.findbyre(r'(?s)<h4>Countries:\s*</h4>(.*?)(?:<h|<p>View)', html)
        if section:
            return self.findallbyre(r'(?s)>(.*?)<', section, 'country')


class GnisAnalyzer(Analyzer):

    def setup(self):
        self.dbproperty = 'P590'
        self.dbid = None
        self.dbname = 'GNIS'
        self.urlbase = 'https://geonames.usgs.gov/apex/f?p=gnispq:3:::NO::P3_FID:{id}'
        self.language = 'en'

    def findnames(self, html) -> List[str]:
        return self.findbyre(r'Name:</td><td[^<>]*>(.*?)<', html)

    def findinstanceof(self, html: str):
        return self.findbyre(
            r'Class:</td><td[^<>]*>(.*?)[<\(]', html, 'instanceof')

    def findelevations(self, html: str):
        return [
            self.findbyre(r'Elevation:</td><td[^<>]*>(\d+)/', html) + ' feet',
            self.findbyre(r'Elevation:</td><td[^<>]*>\d+/(\d+)', html) + ' m'
        ]

    def findadminloc(self, html: str):
        return self.findbyre(r'"COUNTY_NAME">(.*?)<', html, 'county') or \
               self.findbyre(r'"STATE_NAME">(.*?)<', html, 'county')

    def findcountry(self, html: str):
        return 'Q30'

    def findcoords(self, html: str):
        lat = self.findbyre(r'"LAT">(.*?)<', html)
        lon = self.findbyre(r'"LONGI">(.*?)<', html)
        if lat and lon:
            return f'{lat} {lon}'


class MathGenAnalyzer(Analyzer):
    def setup(self):
        self.dbproperty = 'P549'
        self.dbid = 'Q829984'
        self.dbname = 'Mathematics Genealogy Project'
        self.urlbase = 'https://www.genealogy.math.ndsu.nodak.edu/id.php?id={id}'
        self.hrtre = '(<h2.*?)We welcome any additional information.'
        self.language = 'en'
        self.escapehtml = True

    def findnames(self, html) -> List[str]:
        return [self.findbyre(r'(?s)<h2[^<>]*>(.*?)<', html)]

    def findinstanceof(self, html: str):
        return 'Q5'

    def finddegrees(self, html: str):
        return self.findallbyre(r'(?s)>\s*(Ph\.D\.)\s*<', html, 'degree')

    def findschools(self, html: str):
        return self.findallbyre(r'(?s)>\s*Ph\.D\.\s*<[^<>]*>(.*?)<', html, 'university')

    def findadvisors(self, html: str):
        return self.findallbyre(r'(?s)Advisor[^<>]*:[^<>]*<[^<>]*>(.*?)<', html, 'scientist')

    def finddocstudents(self, html: str):
        section = self.findbyre(r'(?s)Students:.*?<table[^<>]*>(.*?)</table>', html)
        if not section:
            section = self.findbyre(r'(?s)<th>Descendants</th>(.*?)</table>', html)
        if section:
            return self.findallbyre(r'(?s)<a[^<>]*>(.*?)<', section, 'scientist')


class LeonoreAnalyzer(Analyzer):
    def setup(self):
        self.dbproperty = 'P640'
        self.dbid = 'Q2886420'
        self.dbname = 'Léonore'
        self.urlbase = 'http://www2.culture.gouv.fr/public/mistral/leonore_fr?ACTION=CHERCHER&FIELD_1=COTE&VALUE_1={id}'
        self.hrtre = '(<TABLE VALIGN=TOP .*?</TABLE>)'
        self.language = 'fr'
        self._results = None
        self.escapeunicode = True

    def getvalue(self, field, html, dtype=None):
        return self.findbyre(
            r'(?s)>\s*{}\s*<.*?<TD[^<>]*>(?:<[^<>]*>|\s)*([^<>]+)</'
            .format(field), html, dtype)

    def findinstanceof(self, html: str):
        return 'Q5'

    def findnames(self, html) -> List[str]:
        try:
            return [
                self.getvalue('Prénoms', html) + ' '
                + self.getvalue('Nom', html).title()
            ]
        except TypeError:
            return []

    def findlastname(self, html: str):
        return self.getvalue('Nom', html, 'lastname')

    def findfirstname(self, html: str):
        return self.getvalue('Prénoms', html, 'firstname')

    def findbirthdate(self, html: str):
        return self.getvalue('Date de naissance', html)

    def findbirthplace(self, html: str):
        return self.getvalue('Lieu de naissance', html, 'city')

    def findgender(self, html: str):
        return self.getvalue('Sexe', html, 'gender')


class OpenLibraryAnalyzer(Analyzer):

    def setup(self):
        self.dbproperty = 'P648'
        self.dbid = 'Q1201876'
        self.dbname = 'Open Library'
        self.urlbase = 'https://openlibrary.org/works/{id}'
        self.hrtre = '(<h1.*?)</div>'
        self.language = 'en'

    def finddescription(self, html: str):
        return self.findbyre(r'description" content="(.*?)"', html)

    def findnames(self, html) -> List[str]:
        return self.findallbyre(r'<title>([^<>]*)\|', html) \
            + self.findallbyre('itemprop="name">(.*?)<', html)

    def findlongtext(self, html: str):
        return self.findbyre(r'<div id="contentBody">(.*?)<div class="clearfix">', html)

    def findinstanceof(self, html: str):
        return self.findbyre('og:type" content="(.*?)"', html, 'instanceof')

    def findbirthdate(self, html: str):
        return self.findbyre('<span itemprop="birthDate">(.*?)<', html)

    def finddeathdate(self, html: str):
        return self.findbyre('<span itemprop="deathDate">(.*?)<', html)


class RkdArtistsAnalyzer(Analyzer):
    def setup(self):
        self.dbproperty = 'P650'
        self.dbid = 'Q17299517'
        self.dbname = 'RKDartists'
        self.urlbase = 'https://rkd.nl/nl/explore/artists/{id}'
        self.hrtre = '(<div class="fieldGroup.*?)<script>'
        self.language = 'nl'
        self.escapehtml = True

    def findinstanceof(self, html: str):
        return 'Q5'

    def finddescription(self, html: str):
        return self.findbyre(r'"og:description" content="(.*?)"', html)

    def findlongtext(self, html: str):
        return self.findbyre(r'(?s)<div class="left">(.*?)<dt>Permalink</dt>', html)

    def findnames(self, html) -> List[str]:
        return [
            self.findbyre(r'(?s)itemprop="name">(.*?)<', html),
            self.findbyre(r'(?s)<h2[^<>]*>(.*?)<', html)
        ] + self.findallbyre(r'itemprop="alternateName">(.*?)<', html)

    def findgender(self, html: str):
        return self.findbyre(r'(?s)itemprop="gender">(.*?)<', html, 'gender')

    def findoccupations(self, html: str):
        section = self.findbyre(r'(?s)Kwalificaties\s*</dt>.*?<dd>(.*?)</dd>', html)
        if section:
            return self.findallbyre(r'">([^<>]+)</span>', section, 'occupation')

    def findbirthplace(self, html: str):
        return self.findbyre(r'itemprop="birthPlace">([^<>]*),', html, 'city') or \
               self.findbyre(r'itemprop="birthPlace">([^<>]*)<', html, 'city')

    def findbirthdate(self, html: str):
        return self.findbyre(r'itemprop="birthDate">([^<>]*?)[</]', html)

    def finddeathplace(self, html: str):
        return self.findbyre(r'itemprop="deathPlace">([^<>]*),', html, 'city') or \
               self.findbyre(r'itemprop="deathPlace">([^<>]*)<', html, 'city')

    def finddeathdate(self, html: str):
        return self.findbyre(r'itemprop="deathDate">([^<>]*?)[</]', html)

    def findworkplaces(self, html: str):
        section = self.findbyre(r'(?s)Werkzaam in.*?<ul>(.*?)</ul>', html)
        if section:
            return self.findallbyre(r'>([^<>]+)</a>', section, 'city')

    def findstudents(self, html: str):
        section = self.findbyre(r'(?s)Leraar van.*?<dd>(.*?)</dd>', html)
        if section:
            return self.findallbyre(r'>([^<>]*)</span>', section, 'artist')

    def findteachers(self, html: str):
        section = self.findbyre(r'(?s)Leerling van.*?<dd>(.*?)</dd>', html)
        if section:
            return self.findallbyre(r'>([^<>]*)</span>', section, 'artist')

    def findinfluences(self, html: str):
        section = self.findbyre(r'(?s)Be.nvloed door.*?<dd>(.*?)</dd>', html)
        if section:
            return self.findallbyre(r'>([^<>]*)</span>', section, 'artist')

    def findschools(self, html: str):
        section = self.findbyre(r'(?s)<dt>\s*Opleiding\s*</dt>.*?<dd>(.*?)</dd>', html)
        if section:
            return self.findallbyre(r'>([^<>]+)</a>', section, 'university')

    def findnationalities(self, html: str):
        return self.findallbyre(r'itemprop="nationality">(.*?)<', html, 'country')

    def findgenres(self, html: str):
        return self.findallbyre(r'Onderwerpen\s*<em>(.*?)<', html, 'art-genre', alt=['genre'])

    def findmovements(self, html: str):
        return self.findallbyre(r'Stroming\s*<em>(.*?)<', html, 'movement')

    def findsiblings(self, html: str):
        return self.findallbyre(r'[bB]roer van ([^<>]*)', html, 'person') + \
               self.findallbyre(r'[zZ]us(?:ter)? van ([^<>]*)', html, 'person')

    def findfather(self, html: str):
        return self.findbyre(r'[zZ]oon van ([^<>]*)', html, 'male-person', skips=['female-person']) or \
               self.findbyre(r'[dD]ochter van ([^<>]*)', html, 'male-person', skips=['female-person'])

    def findmother(self, html: str):
        return self.findbyre(r'[zZ]oon van ([^<>]*)', html, 'female-person', skips=['male-person']) or \
               self.findbyre(r'[dD]ochter van ([^<>]*)', html, 'female-person', skips=['male-person'])

    def findmemberships(self, html: str):
        return self.findallbyre(r'Lid van[^<>]*<em>(.*?)<', html, 'organization')

    def findmixedrefs(self, html: str):
        return self.finddefaultmixedrefs(html, includesocial=False)

    def findfloruit(self, html: str):
        return self.findbyre(r'(?s)<dt>\s*Werkzame periode\s*</dt>\s*<dd>(.*?)<', html)


class BiografischPortaalAnalyzer(Analyzer):
    def setup(self):
        self.dbproperty = 'P651'
        self.dbid = 'Q1868372'
        self.dbname = 'Biografisch Portaal'
        self.urlbase = 'http://www.biografischportaal.nl/persoon/{id}'
        self.hrtre = '(<h1.*)<h2'
        self.language = 'nl'

    def finddescription(self, html: str):
        return self.findbyre(r'(?s)<th>(geboren.*?)</table>', html)

    def findnames(self, html) -> List[str]:
        result = [self.findbyre(r'(?s)<title>(.*?)<', html)]
        section = self.findbyre(
            r'(?s)<th>alternatieve namen</th>(.*?)</tr>', html)
        if section:
            result += self.findallbyre('<li>(.*?)<', section)
        return result

    def findlongtext(self, html: str):
        return self.findbyre(r'(?s)<div class="levensbeschrijvingen">(.*?)<!-- content end', html)

    def findbirthplace(self, html: str):
        return self.findbyre(r'(?s)<th>geboren</th>[^<>]*<td>[^<>]*<span><br\s*/>([^<>]*)<', html, 'city')

    def findbirthdate(self, html: str):
        result = self.findbyre(r'(?s)<th>geboren</th>[^<>]*<td>(.*?)<', html)
        if result and 'tussen' not in result:
            return result

    def finddeathplace(self, html: str):
        return self.findbyre(r'(?s)<th>gestorven</th>[^<>]*<td>[^<>]*<span><br\s*/>([^<>]*)<', html, 'city')

    def finddeathdate(self, html: str):
        result = self.findbyre(r'(?s)<th>gestorven</th>[^<>]*<td>(.*?)<', html)
        if result and 'tussen' not in result:
            return result

    def findmixedrefs(self, html: str):
        return self.finddefaultmixedrefs(html)

    def findgender(self, html: str):
        return self.findbyre(r'(?s)<th>sekse</th>.*?<li>(.*?)<', html, 'gender')

    def findsources(self, html: str):
        return self.findallbyre(r'(?s)<a class="external_link open_in_new_window"[^<>]*>(.*?)<', html, 'source')


class NkcrAnalyzer(Analyzer):
    def setup(self):
        self.dbproperty = 'P691'
        self.dbid = 'Q13550863'
        self.dbname = 'NKC'
        self.urlbase = 'https://aleph.nkp.cz/F/?func=find-c&local_base=aut&ccl_term=ica={id}'
        self.language = 'cs'
        self.hrtre = '(<table width=100%>.*?)<script language='

    def prepare(self, html: str):
        return html.replace('&nbsp;', ' ')

    def getvalue(self, field, html, dtype=None):
        return self.findbyre(fr'(?s)<td[^<>]*>\s*{field}\s*</td>\s*<td[^<>]*>(?:<[^<>]*>)*(.*?)<', html, dtype)

    def findlongtext(self, html: str):
        return self.getvalue(r'Biogr\./Hist\. .daje', html)

    def findinstanceof(self, html: str):
        return 'Q5'

    def findnames(self, html) -> List[str]:
        result = [
            self.getvalue('Z.hlav.', html),
            self.getvalue('Pseudonym', html)
        ]
        return [','.join(r.split(',')[:-1]) for r in result if r]

    def finddescription(self, html: str):
        return self.getvalue(r'Biogr\./Hist\. .daje', html)

    def findnationality(self, html: str):
        section = self.getvalue('Související zem.', html) or\
                  self.getvalue(r'Biogr\./Hist\. .daje', html)
        if section:
            return self.findbyre(r'(\w+)', section, 'country')
        return None

    def findbirthdate(self, html: str):
        return self.findbyre(r'[Nn]arozena? ([\d\.\s]*\d)', html)

    def finddeathdate(self, html: str):
        return self.findbyre(r'[Zz]em.ela? ([\d\.\s]*\d)', html)

    def findbirthplace(self, html: str):
        return self.findbyre(r'[Nn]arozena? [\d\.\s]* v ([\w\s]*)', html, 'city')

    def finddeathplace(self, html: str):
        return self.findbyre(r'[Zz]em.ela [\d\.\s]* v ([\w\s]*)', html, 'city')

    def findoccupations(self, html: str):
        section = self.getvalue(r'Biogr\./Hist\. .daje', html)
        if section:
            if 'special' in section:
                section = section[:section.find('special')]
            parts = section.split(' a ')
            result = []
            for part in parts:
                result += self.findallbyre(r'([^\,\.;]*)', part, 'occupation')
            return result
        return None

    def findrelorder(self, html: str):
        return self.getvalue(r'Související org\.', html, 'religious order')

    def findlanguagesspoken(self, html: str):
        section = self.getvalue('Jazyk', html)
        if section:
            return self.findallbyre(r'([^;]+)', section, 'language')

    def findworkfields(self, html: str):
        results = []
        for regex in [
            r'[oO]dborník v (.*?)[\.<]',
            r'[sS]pecial\w* (?:se )?(?:v|na) (.*?)[\.<]',
            r'[zZ]abývá se (.*?)[\.<]',
            r'Zaměřuje se na (.*?)[\.<]',
            r'[oO]boru (.*?)[\.<]',
            r'[zZ]aměřený na (.*?)[\.<]',
        ]:
            sections = self.findallbyre(regex, html)
            for section in sections:
                parts = section.split(' a ')
                for part in parts:
                    if part.startswith('v '):
                        part = part[2:]
                    results += self.findallbyre(r'([\w\s]+)', part.replace(' v ', ' '), 'subject')
        return results


class DbnlAnalyzer(Analyzer):
    def setup(self):
        self.dbproperty = 'P723'
        self.dbid = 'Q2451336'
        self.dbname = 'DBNL'
        self.urlbase = 'http://www.dbnl.org/auteurs/auteur.php?id={id}'
        self.language = 'nl'
        self.hrtre = '(<p><span class="label">.*?)<form class="mainsearchform"'
        self.escapehtml = True

    def findnames(self, html) -> List[str]:
        return [
            self.findbyre(r'<title>(.*?)[&<·]', html),
            self.findbyre(r'"naam">(?:<[^<>]*>)*([^<>]+)<', html),
            self.findbyre(r'href="#naam">(.*?)<', html),
        ]

    def findlongtext(self, html: str):
        return self.findbyre(r'(?s)<article[^<>]*>(.*?)</article>', html)

    def findbirthdate(self, html: str):
        return self.findbyre(r'>geboren(?:<[^<>]*>)*<i>(.*?)<', html)

    def findbirthplace(self, html: str):
        return self.findbyre(r'>geboren.*? te (?:<[^<>]*>)*([^<>]+)<', html, 'city')

    def finddeathdate(self, html: str):
        return self.findbyre(r'>overleden(?:<[^<>]*>)*<i>(.*?)<', html)

    def findburialdate(self, html: str):
        result = self.findbyre(r'(\d+ \w+ \(begraven\) \d+)', html)
        if result:
            return result.replace('(begraven) ', '')
        return None

    def finddeathplace(self, html: str):
        return self.findbyre(r'>overleden<.*?> te (?:<[^<>]*>)*([^<>]+)<', html, 'city')

    def findwebpages(self, html: str):
        result = []
        section = self.findbyre(r'(?s)<section id="websites">.*?<table>(.*?)</table>', html)
        if section:
            result += self.findallbyre(r'>([^<>]*)</a>', section)
        section = self.findbyre(r'(?s)<h\d[^<>]*>Biografie[^<>]*(<.*?)</table>', html)
        if section:
            results = self.findallbyre(r'<a href="(.*?)"', section)
            result += ['https://www.dbnl.org/' + result.lstrip('/') for result in results]
        return result

    def findsources(self, html: str):
        section = self.findbyre(r'(?s)<h\d[^<>]*>Biografie[^<>]*(<.*?)</table>', html)
        if section:
            return self.findallbyre(r'>([^<>]*)</a>', section, 'source')


class SikartAnalyzer(Analyzer):
    def setup(self):
        self.dbproperty = 'P781'
        self.dbid = 'Q683543'
        self.dbname = 'SIKART'
        self.urlbase = 'http://www.sikart.ch/KuenstlerInnen.aspx?id={id}'
        self.language = 'de'
        self.hrtre = '<!-- content_start -->(.*?)<!-- content_end -->'
        self.escapehtml = True

    def getvalue(self, field, html, dtype=None):
        return self.findbyre(r'(?s)>{}<.*?<div[^<>]*>(.*?)<'
                             .format(field), html, dtype)

    def findinstanceof(self, html: str):
        return 'Q5'

    def findnames(self, html) -> List[str]:
        return [
            self.findbyre(r'<title>([^<>]+?)-', html),
            self.findbyre(r'<h1>(.*?)<', html)
        ]

    def finddescriptions(self, html: str):
        return [
            self.getvalue('Vitazeile', html),
            self.getvalue('Vitazeile', html).split('.')[0]
        ]

    def findlongtext(self, html: str):
        return self.findbyre(r'(?s)<!-- content_start -->(.*)<!-- content_end -->', html)

    def findlastname(self, html: str):
        return self.findbyre(r'token.lastname=(\w+)', html, 'lastname')

    def findfirstname(self, html: str):
        return self.findbyre(r'token.firstname=([\w\-]+)', html, 'firstname')

    def findbirthdate(self, html: str):
        dates = self.getvalue('Lebensdaten', html)
        if dates:
            return self.findbyre(r'\*\s*([\d\.]+)', dates)

    def findbirthplace(self, html: str):
        dates = self.getvalue('Lebensdaten', html)
        if dates:
            return self.findbyre(r'\*\s*[\d\.]+\s*(.*?),', dates, 'city')

    def finddeathdate(self, html: str):
        dates = self.getvalue('Lebensdaten', html)
        if dates:
            return self.findbyre(r'†(?:\s|&nbsp;)*([\d\.]+)', dates)

    def finddeathplace(self, html: str):
        dates = self.getvalue('Lebensdaten', html)
        if dates:
            return self.findbyre(r'†(?:\s|&nbsp;)*[\d\.]+(.*)', dates, 'city')

    def findchoriginplaces(self, html: str):
        section = self.getvalue('Bürgerort', html)
        if section:
            return self.findallbyre(r'([\w\s\-]+)', section, 'city')

    def findnationality(self, html: str):
        return self.getvalue('Staatszugehörigkeit', html, 'country')

    def findoccupations(self, html: str):
        section = self.getvalue('Vitazeile', html)
        if section:
            result = []
            splitter = 'et' if ' et ' in section else 'und'
            for subsection in section.split('.')[0].split(' {} '
                                                          .format(splitter)):
                result += self.findallbyre(r'([\w\s]+)', subsection,
                                           'occupation')
            return result

    def findmixedrefs(self, html: str):
        return self.finddefaultmixedrefs(html)


class ImslpAnalyzer(Analyzer):
    def setup(self):
        self.dbproperty = 'P839'
        self.dbid = 'Q523660'
        self.dbname = 'International Music Score Library Project'
        self.urlbase = 'https://imslp.org/wiki/{id}'
        self.isperson = self.id.startswith('Category:')
        self.hrtre = r'(<h\d.*?)<h2'
        self.language = 'nl'

    def findinstanceof(self, html: str):
        if self.isperson:
            return 'Q5'
        raise NotImplementedError  # analysis only made for persons

    def findbirthdate(self, html: str):
        return self.findbyre(r'</h2>\(([^<>]*?)—', html)

    def finddeathdate(self, html: str):
        return self.findbyre(r'</h2>\([^<>]*?—([^<>]*?)\)', html)

    def findlanguagenames(self, html: str):
        result = [('nl', x) for x in self.findallbyre(r'<h2>\s*<span[^<>]*>(.*?)</span>', html)]
        section = self.findbyre(r'Andere Namen/Transliteraties:(.*?)<', html)
        if section:
            parts = section.split(',')
            for part in parts:
                subparts = self.findallbyre(r'((?:[^,\(]|\([^\(\)]*\))*)', part)
                for subpart in subparts:
                    if '(' in subpart:
                        result += [(lang.strip(), subpart[:subpart.find('(')]) for lang in
                                   self.findbyre(r'\(.*?)\)', subpart).split(',')]
                    else:
                        result.append(('nl', subpart))
        section = self.findbyre(r'Aliassen:(.*)', html)
        if section:
            parts = self.findallbyre(r'(<span.*?/span>', section)
            for part in parts:
                result += [(language.strip(), self.findbyre(r'>([^<>]*)</span>', part)) for language in
                           self.findbyre(r'<span title="(.*?)">', part).split(',')]
        return result

    def findmixedrefs(self, html: str):
        return self.finddefaultmixedrefs(html)


class HdsAnalyzer(Analyzer):
    def setup(self):
        self.id = f'{int(self.id):06d}'
        self.dbproperty = 'P902'
        self.dbid = 'Q642074'
        self.dbname = 'Historical Dictionary of Switzerland'
        self.urlbase = 'https://hls-dhs-dss.ch/de/articles/{id}/'
        self.hrtre = '(<h1.*?<!-- noindex -->)'
        self.language = 'de'
        self.escapeunicode = True

    def finddescription(self, html: str):
        return self.findbyre(r'property="og:description" content="(.*?)"', html)

    def findlongtext(self, html: str):
        return self.findbyre(r'(?s)(<h1.*?<!-- noindex -->)', html)

    def findnames(self, html) -> List[str]:
        return [self.findbyre(r'(?s)<title>(.*?)<', html)]

    def findfirstname(self, html: str):
        return self.findbyre(r'<span itemprop="givenName">(.*?)</span>', html, 'firstname')

    def findlastname(self, html: str):
        return self.findbyre(r'<span itemprop="familyName">(.*?)</span>', html, 'lastname')

    def findbirthdate(self, html: str):
        return self.findbyre(r'<span itemprop="birthDate">(.*?)</span>', html)

    def finddeathdate(self, html: str):
        return self.findbyre(r'<span itemprop="deathDate">(.*?)</span>', html)

    def findbirthplace(self, html: str):
        return self.findbyre(r'<img alt="geboren"[^<>]*>\s*[^\s]*\s*([\w\s-]*)', html, 'city')

    def finddeathplace(self, html: str):
        return self.findbyre(r'<img alt="gestorben"[^<>]*>\s*[^\s]*\s*([\w\s-]*)', html, 'city')

    def findmixedrefs(self, html: str):
        return self.finddefaultmixedrefs(html, includesocial=False)


class NtaAnalyzer(Analyzer):
    def setup(self):
        self.dbproperty = 'P1006'
        self.dbid = None
        self.dbname = 'NTA'
        self.urlbase = 'http://data.bibliotheken.nl/doc/thes/p{id}'
        self.hrtre = '(<h1.*?)<div id="bnodes">'
        self.language = 'nl'

    def finddescription(self, html: str):
        return self.findbyre(r'<h1><span>(.*?)<', html)

    def findnames(self, html) -> List[str]:
        result = [self.findbyre(r'(?s)<title>(.*?)<', html)]
        section = self.findbyre(r'(?s)alternateName</span>(.*?)<label', html)
        if section:
            result += self.findallbyre(
                r'(?s)<div class="fixed">(.*?)[&<]', html)
        return result

    def findinstanceof(self, html: str):
        return self.findbyre(r'http://schema.org/(.*?)[&"\']', html, 'instanceof')

    def finddeathdate(self, html: str):
        return self.findbyre(r'(?s)<span>deathDate</span>.*?<span.*?>(.*?)[&<]', html)

    def findbirthdate(self, html: str):
        return self.findbyre(r'(?s)<span>birthDate</span>.*?<span.*?>(.*?)[&<]', html)

    def findfirstname(self, html: str):
        return self.findbyre(r'(?s)<span>givenName</span>.*?<span.*?>(.*?)[&<]', html, 'firstname')

    def findlastname(self, html: str):
        return self.findbyre(r'(?s)<span>familyName</span>.*?<span.*?>(.*?)[&<]', html, 'lastname')

    def findviaf(self, html: str):
        return self.findbyre(r'http://viaf.org/viaf/(\d+)', html)


class PtbnpAnalyzer(Analyzer):
    def setup(self):
        self.dbproperty = 'P1005'
        self.dbid = None
        self.dbname = 'Biblioteca Nacional de Portugal'
        self.urlbase = 'http://urn.bn.pt/nca/unimarc-authorities/txt?id={id}'
        self.hrtre = '(.*)'
        self.language = 'pt'
        self.escapehtml = True

    def findnames(self, html) -> List[str]:
        return [self.TAGRE.sub(' ', text).replace('$b', '')
                for text in self.findallbyre(
                    r'>[24]00<.*?\$a(.*?\$b.*?)(?:<br>|\$|$)', html)]

    def finddescription(self, html: str):
        return self.findbyre(r'>830<.*?\$a.*?</font>([^<>]*)', html)

    def findnationality(self, html: str):
        return self.findbyre(r'>102<.*?\$a(?:<[^<>]*>)*([^<>]+)', html, 'country')

    def findlongtext(self, html: str):
        return '\n'.join(self.findallbyre(r'>830<.*?\$a.*?</font>([^<>]*)', html))

    def findbirthdate(self, html: str):
        result = self.findbyre(r'>200<.*?\$f.*?</font>([^<>]*)-', html)
        if result and 'ca ' not in result and 'fl.' not in result:
            return result

    def finddeathdate(self, html: str):
        result = self.findbyre(r'>200<.*?\$f.*?</font>[^<>]*-([^<>,]*)', html)
        if result and 'ca ' not in result and 'fl.' not in result:
            return result

    def findfirstname(self, html: str):
        return self.findbyre(r'>200<.*?\$b</b></font>([^<>]*?),?\s*<', html, 'firstname')

    def findlastname(self, html: str):
        return self.findbyre(r'>200<.*?\$a</b></font>(.*?),?<', html, 'lastname')


class BibsysAnalyzer(Analyzer):
    def setup(self):
        self.dbproperty = 'P1015'
        self.dbid = None
        self.dbname = 'BIBSYS'
        self.urlbase = 'https://authority.bibsys.no/authority/rest/authorities/html/{id}'
        self.hrtre = '(<body>.*)'
        self.language = 'en'

    def findnames(self, html) -> List[str]:
        return self.findallbyre(
            r'<td>[^<>]*name[^<>]*</td><td>([^<>]*)</td>', html)

    def findinstanceof(self, html: str):
        return self.findbyre(r'<td>Authority type</td><td>(.*?)</td>', html, 'instanceof')

    def findisni(self, html: str):
        return self.findbyre(r'<td>isni</td><td>(.*?)</td>', html)

    def findviaf(self, html: str):
        return self.findbyre(r'http://viaf.org/viaf/(\w+)', html) or \
               self.findbyre(r'<td>viaf</td><td>(.*?)</td>', html)

    def findfirstname(self, html: str):
        return self.findbyre(r'<td>Personal name</td><td>[^<>]*,\s*(\w+)', html, 'firstname')

    def findlastname(self, html: str):
        return self.findbyre(r'<td>Personal name</td><td>([^<>]*),', html, 'lastname')

    def findbirthdate(self, html: str):
        return self.findbyre(r'<td>Dates associated with a name</td><td>([^<>]*)-', html)

    def finddeathdate(self, html: str):
        return self.findbyre(r'<td>Dates associated with a name</td><td>[^<>]*-([^<>]*)', html)


class KunstindeksAnalyzer(Analyzer):
    def setup(self):
        self.dbproperty = 'P1138'
        self.dbid = 'Q3362041'
        self.dbname = 'Kunstindeks Danmark'
        self.urlbase = 'https://www.kulturarv.dk/kid/VisKunstner.do?kunstnerId={id}'
        self.urlbase3 = 'https://www.kulturarv.dk/kid/SoegKunstnerVaerker.do?kunstnerId={id}&hitsPerPage=1000'
        self.hrtre = 'Information from Kunstindeks Danmark</h2>(.*?)</table>'
        self.language = 'da'

    def findnames(self, html) -> List[str]:
        return [
            self.findbyre(r':([^<>]*)</h1>', html),
            self.findbyre(r'Name:\s*</b>(.*?)<', html)
        ]

    def findlongtext(self, html: str):
        return self.findbyre(r'(?s)(<h1>.*?)<td class="right\d', html)

    def findlastname(self, html: str):
        return self.findbyre(r'(?s)<b>Name: </b>([^<>]*),', html, 'lastname')

    def findfirstname(self, html: str):
        return self.findbyre(r'(?s)<b>Name: </b>[^<>]*,\s*([\w\-]+)', html, 'firstname')

    def findbirthplace(self, html: str):
        return self.findbyre(r'(?s)<b>Born: </b>([^<>]*),', html, 'city')

    def findbirthdate(self, html: str):
        return self.findbyre(r'(?s)<b>Born: </b>[^<>]*?([\d\-]+)\s*<', html)

    def finddeathplace(self, html: str):
        return self.findbyre(r'(?s)<b>Died: </b>([^<>]*),', html, 'city')

    def finddeathdate(self, html: str):
        return self.findbyre(r'(?s)<b>Died: </b>[^<>]*?([\d\-]+)\s*<', html)

    def findoccupations(self, html: str):
        section = self.findbyre(r'(?s)Occupation: </b>(.*?)<', html)
        if section:
            return self.findallbyre(r'([\s\w]+)', section, 'occupation')

    def findgender(self, html: str):
        return self.findbyre(r'(?s)Sex: </b>(.*?)<', html, 'gender')

    def findnationality(self, html: str):
        return self.findbyre(r'(?s)Nationality: </b>(.*?)<', html, 'country')

    def findincollections(self, html: str):
        return self.findallbyre(r'museumId=[^<>]*>(.*?)<', html, 'museum')


class IaafAnalyzer(Analyzer):
    def setup(self):
        self.dbproperty = 'P1146'
        self.dbid = None
        self.dbname = 'IAAF'
        self.urlbase = 'https://www.iaaf.org/athletes/athlete={id}'
        self.hrtre = '(<div class="row offset.*? <div class="clearfix">)'
        self.language = 'en'

    def findnames(self, html) -> List[str]:
        return [self.findbyre(r'(?s)<h1>(.*?)<', html)]

    def findlongtext(self, html: str):
        return self.findbyre(r'(?s)<div class="modal-body athletepopup">(.*?)</script>', html)

    def instanceof(self, html: str):
        return 'Q5'

    def findoccupations(self, html: str):
        return ['Q11513337']

    def findsports(self, html: str):
        return ['Q542']

    def findnationality(self, html: str):
        return self.findbyre(r'(?s)COUNTRY.*?>([^<>]*)</span>', html, 'country')

    def findbirthdate(self, html: str):
        return self.findbyre(r'(?s)DATE OF BIRTH\s*<br\s*/>(.*?)<', html)


class ScopusAnalyzer(Analyzer):
    def setup(self):
        self.dbproperty = 'P1153'
        self.dbid = 'Q371467'
        self.dbname = 'Scopus'
        self.urlbase = 'https://www.scopus.com/authid/detail.uri?authorId={id}'
        self.hrtre = '(<h2.*?)<h4'
        self.language = 'en'

    def findinstanceof(self, html: str):
        return 'Q5'

    def findnames(self, html) -> List[str]:
        result = self.findallbyre(
            r'name="authorPreferredName" value="(.*?)"', html)
        section = self.findbyre(
            r'(?s)(<div id="otherNameFormatBadges".*?</div>)', html)
        if section:
            result += self.findallbyre(r'>(.*?)<', section)
        return result

    def findworkfields(self, html: str):
        section = self.findbyre(r'(?s)(<div id="subjectAreaBadges".*?</div>)', html)
        if section:
            return self.findallbyre(r'>(.*?)<', section, 'subject')

    def findmixedrefs(self, html: str):
        return self.finddefaultmixedrefs(html)

    def findemployers(self, html: str):
        section = self.findbyre(r'(?s)<div class="authAffilcityCounty">(.*?)</div>', html)
        if section:
            return self.findallbyre(r'>([^<>]*)</span>', section, 'employer', alt=['university'])

    def findworkplaces(self, html: str):
        section = self.findbyre(r'(?s)<div class="authAffilcityCounty">(.*?)</div>', html)
        if section:
            return self.findallbyre(r'(?s)>,([^<>],[^<>]*)<', section.replace('\n', ' '), 'city')


class RodovidAnalyzer(Analyzer):
    def setup(self):
        self.dbproperty = 'P1185'
        self.dbid = 'Q649227'
        self.dbname = 'Rodovid'
        self.urlbase = 'https://en.rodovid.org/wk/Person:{id}'
        self.hrtre = '<table class="persondata">(.*?<h2>.*?)<h2'
        self.language = 'en'
        self.escapehtml = True

    def findnames(self, html) -> List[str]:
        return [
            self.findbyre(r'<title>(.*?)(?: [bd]\. |<)', html),
            self.findbyre(r'<h1[^<>]*>(.*?)(?: [bd]\. |<)', html),
            self.findbyre(
                r'(?s)<b>Full name[^<>]*</b>\s*</td><td>(.*?)<', html)
        ]

    def findlongtext(self, html: str):
        return self.findbyre(r'(?s)<span class="mw-headline">Notes</span></h2>\s*<p>(.*?)<h\d', html)

    def findbirthdate(self, html: str):
        section = self.findbyre(r'(?s)Events</span></h2>(.*?)<h2', html)
        return self.findbyre(r'<b>([^<>]*)</b>birth:', section)

    def findbirthplace(self, html: str):
        section = self.findbyre(r'(?s)Events</span></h2>(.*?)<h2', html)
        return self.findbyre(r'>birth: <[^<>]*>(.*?)<', section, 'city')

    def finddeathdate(self, html: str):
        section = self.findbyre(r'(?s)Events</span></h2>(.*?)<h2', html)
        return self.findbyre(r'<b>([^<>]*)</b>death:', section)

    def finddeathplace(self, html: str):
        section = self.findbyre(r'(?s)Events</span></h2>(.*?)<h2', html)
        return self.findbyre(r'death: <[^<>]*>(.*?)<', section, 'city')

    def findchildren(self, html: str):
        section = self.findbyre(r'(?s)Events</span></h2>(.*?)<h2', html)
        return self.findallbyre(r"child birth:.*?Person:\d+'>(.*?)<", section, 'person')

    def findspouses(self, html: str):
        section = self.findbyre(r'(?s)Events</span></h2>(.*?)<h2', html)
        return self.findallbyre(r"marriage</a>.*?Person:\d+'>(.*?)<", section, 'person')

    def findfamily(self, html: str):
        section = self.findbyre(r'(?s)<b>Lineage\s*</b>(.*?)</tr>', html)
        if section:
            return self.findbyre(r'>([^<>]*)</a>', section, 'family')

    def findgender(self, html: str):
        return self.findbyre(r'(?s)Sex\s*</b>\s*</td><td>(.*?)<', html, 'gender')

    def findfather(self, html: str):
        section = self.findbyre(r'(?s)<b>Parents</b>(.*?)</tr>', html)
        if section:
            return self.findbyre(r"♂.*?Person:\d+'>(.*?)<", section, 'person')

    def findmother(self, html: str):
        section = self.findbyre(r'(?s)<b>Parents</b>(.*?)</tr>', html)
        if section:
            return self.findbyre(r"♀.*?Person:\d+'>(.*?)<", section, 'person')

    def findreligions(self, html: str):
        return self.findallbyre(r'(?s)religion:\s*<.*?>([^<>]+)<.*?></p>', html, 'religion')

    def findtitles(self, html: str):
        section = self.findbyre(r'(?s)Events</span></h2>(.*?)<h2', html)
        return self.findallbyre(r'title:.*?<a[^<>]*>(.*?)<', section, 'title')


class IbdbAnalyzer(Analyzer):
    def setup(self):
        self.dbproperty = 'P1220'
        self.dbid = 'Q31964'
        self.dbname = 'IBDB'
        self.urlbase = 'https://www.ibdb.com/person.php?id={id}'
        self.hrtre = '(<h1>.*?)<div class="dottedLine">'
        self.language = 'en'

    def finddescription(self, html: str):
        return self.findbyre(r'<meta name="description" content="(.*?)"', html)

    def findnames(self, html) -> List[str]:
        section = self.findbyre(
            r'(?s)<b>Also Known As</b>\s*</div>\s*<div[^<>]*>(.*?)</div>',
            html)
        if section:
            result = self.findallbyre(r'([^\[\]<>]*?)[\[<]', section)
        else:
            result = []
        return result + [self.findbyre(r'<title>([^<>]*?) – ', html)]

    def findlongtext(self, html: str):
        parts = self.findallbyre(r'"personDescription"[^<>]*>(.*?)<', html)
        if parts:
            return ' '.join(parts)

    def findoccupations(self, html: str):
        section = self.findbyre(r'(?s)<div class="s12 wrapper tag-block-compact extramarg">(.*?)</div>', html)
        if section:
            return self.findallbyre(r'>([^<>]*)<', section, 'theater-occupation', alt=['occupation'])

    def findbirthdate(self, html: str):
        return self.findbyre(r'(?s)<div class="xt-lable">Born</div>\s*<div class="xt-main-title">(.*?)</div>', html)

    def findbirthplace(self, html: str):
        return self.findbyre(
            r'(?s)<div class="xt-lable">Born</div>\s*<div class="xt-main-title">'
            r'[^<>]*</div>\s*<div class="xt-main-moreinfo">(.*?)</div>',
            html, 'city')

    def finddeathdate(self, html: str):
        return self.findbyre(r'(?s)<div class="xt-lable">Died</div>\s*<div class="xt-main-title">(.*?)</div>', html)

    def finddeathplace(self, html: str):
        return self.findbyre(
            r'(?s)<div class="xt-lable">Died</div>\s*<div class="xt-main-title">[^<>]*</div>'
            r'\s*<div class="xt-main-moreinfo">(.*?)</div>',
            html, 'city')

    def findgender(self, html: str):
        return self.findbyre(r'(?s)<div class="xt-lable">Gender</div>\s*<div class="xt-main-title">(.*?)</div>', html,
                             'gender')

    def findawards(self, html: str):
        section = self.findbyre(r'(?s)<div id="awards".*?>(.*?)</table>', html)
        if section:
            parts = self.findallbyre(r'(?s)(<tr><th.*?</tr>\s*<tr>.*?</tr>)', section)
            result = []
            for part in parts:
                if '[nominee]' not in part:
                    result.append(self.findbyre(r'<th[^<>]*>(.*?)<', section, 'award'))
            return result

    def findnominations(self, html: str):
        section = self.findbyre(r'(?s)<div id="awards".*?>(.*?)</table>', html)
        if section:
            parts = self.findallbyre(r'(?s)(<tr><th.*?</tr>\s*<tr>.*?</tr>)', section)
            result = []
            for part in parts:
                if '[nominee]' in part:
                    result.append(self.findbyre(r'<th[^<>]*>(.*?)<', section, 'award'))
            return result

    def findspouses(self, html: str):
        return self.findallbyre(r'(?s)(?:Wife|Husband) of(?:<[^<>]*>|\s)*(.*?)<', html, 'person')

    def findpartners(self, html: str):
        return self.findallbyre(r'(?s)Partner of(?:<[^<>]*>|\s)*(.*?)<', html, 'person')


class IsfdbAnalyzer(Analyzer):
    def setup(self):
        self.dbproperty = 'P1233'
        self.dbid = 'Q2629164'
        self.dbname = 'Internet Speculative Fiction Database'
        self.urlbase = 'http://www.isfdb.org/cgi-bin/ea.cgi?{id}'
        self.hrtre = '<div class="ContentBox">(.*?)<div class="ContentBox">'
        self.language = 'en'
        self.escapeunicode = True

    def prepare(self, html: str):
        return html.replace('\\n', '\n')

    def findnames(self, html) -> List[str]:
        return self.findallbyre(r'(?s)<b>Author:</b>(.*?)<', html) \
            + self.findallbyre(r'(?s)Name:</b>(.*?)<', html) \
            + self.findallbyre(r'dir="ltr">(.*?)<', html)

    def findlongtext(self, html: str):
        return self.findbyre(r'(?s)<div class="ContentBox">(.*?)<div class="ContentBox">', html)

    def findinstanceof(self, html: str):
        return 'Q5'

    def findfirstname(self, html: str):
        return self.findbyre(r'(?s)Legal Name:</b>[^<>]+,\s*([\w\-]+)', html, 'firstname')

    def findlastname(self, html: str):
        return self.findbyre(r'(?s)Legal Name:</b>([^<>]*),', html, 'lastname')

    def findbirthplace(self, html: str):
        return self.findbyre(r'(?s)Birthplace:</b>(.*?)<', html, 'city')

    def finddeathplace(self, html: str):
        return self.findbyre(r'(?s)Deathplace:</b>(.*?)<', html, 'city')

    def findbirthdate(self, html: str):
        return self.findbyre(r'(?s)Birthdate:</b>(.*?)<', html)

    def finddeathdate(self, html: str):
        return self.findbyre(r'(?s)Deathdate:</b>(.*?)<', html)

    def findlanguagesspoken(self, html: str):
        section = self.findbyre(r'(?s)Language:</b>(.*?)<', html)
        if section:
            return self.findallbyre(r'(\w+)', section, 'language')

    def findmixedrefs(self, html: str):
        return self.finddefaultmixedrefs(html)

    def findgenres(self, html: str):
        section = self.findbyre(r'(?s)Author Tags:</b>(.*?)<(?:/ul|li)', html)
        if section:
            return self.findallbyre(r'>(.*?)<', section, 'literature-genre', alt=['genre'])


class NndbAnalyzer(Analyzer):
    def setup(self):
        self.dbproperty = 'P1263'
        self.dbid = 'Q1373513'
        self.dbname = 'NNDB'
        self.urlbase = 'https://www.nndb.com/people/{id}/'
        self.hrtre = r'(<font size=\+3.*?)<font size=-1>'
        self.language = 'en'

    def getvalue(self, field, dtype=None, bold=True):
        rawtext = self.findbyre(r'{}{}:{}\s*(.+?)<(?:br|p)>'
                                .format('<b>' if bold else ' ', field,
                                        '</b>' if bold else ''),
                                self.html)
        if rawtext:
            text = self.TAGRE.sub('', rawtext)
            return self.findbyre(r'(.+)', text, dtype)

    def getvalues(self, field, dtype=None, bold=True) -> List[str]:
        rawtexts = self.findallbyre(
            r'{}{}:{}\s*(.+?)<(?:br|p)>'.format('<b>' if bold else ' ', field, '</b>' if bold else ''), self.html)
        texts = [self.TAGRE.sub('', rawtext) for rawtext in rawtexts]
        return [self.findbyre(r'(.+)', text, dtype) for text in texts]

    def findinstanceof(self, html: str):
        return 'Q5'

    def finddescription(self, html: str):
        return self.getvalue('Executive summary')

    def findnames(self, html) -> List[str]:
        return [
            self.findbyre(r'<title>(.*?)<', html),
            self.findbyre(r'<font size=\+3.*?>\s*<b>(.*?)<', html),
            self.getvalue('AKA'),
        ]

    def findbirthdate(self, html: str):
        return (self.getvalue('Born') or '').replace('-', ' ')

    def finddeathdate(self, html: str):
        return (self.getvalue('Died') or '').replace('-', ' ')

    def findbirthplace(self, html: str):
        return self.getvalue('Birthplace', 'city')

    def finddeathplace(self, html: str):
        return self.getvalue('Location of death', 'city')

    def findcausedeath(self, html: str):
        return self.getvalue('Cause of death', 'causedeath')

    def findmannerdeath(self, html: str):
        return self.getvalue('Cause of death', 'mannerdeath')

    def findgender(self, html: str):
        return self.getvalue('Gender', 'gender')

    def findethnicity(self, html: str):
        return self.getvalue('Race or Ethnicity', 'ethnicity')

    def findoccupations(self, html: str):
        result = self.getvalue('Occupation')
        if result:
            return self.findallbyre(r'([\w\s]+)', result, 'occupation')

    def findnationality(self, html: str):
        return self.getvalue('Nationality', 'country')

    def findspouses(self, html: str):
        return self.getvalues('Wife', 'person') + self.getvalues('Husband', 'person')

    def findfather(self, html: str):
        return self.getvalue('Father', 'person')

    def findmother(self, html: str):
        return self.getvalue('Mother', 'person')

    def findsiblings(self, html: str):
        return self.getvalues('Brother', 'person') + self.getvalues('Sister', 'person')

    def findchildren(self, html: str):
        return self.getvalues('Son', 'person') + self.getvalues('Daughter', 'person')

    def findorientation(self, html: str):
        return self.getvalue('Sexual orientation', 'orientation')

    def findschools(self, html: str):
        return self.getvalues('High School', 'university', bold=False) + \
               self.getvalues('University', 'university', bold=False)

    def findemployers(self, html: str):
        return self.getvalues('Teacher', 'employer', bold=False) + \
               self.getvalues('Professor', 'employer', bold=False)

    def findresidences(self, html: str):
        return [self.findbyre(r'Resides in ([^<>]+)', html, 'city')]

    def findwebsite(self, html: str):
        return self.getvalue('Official Website')


class MarcAnalyzer(Analyzer):
    def setup(self):
        self.dbproperty = None
        self.dbid = None
        self.dbname = 'MARC'
        self.urlbase = None
        self.hrtre = '(.*)'
        self.language = 'en'

    def getvalue(self, field, html, dtype=None, alt=None):
        return self.findbyre(
            '(?s)<td[^<>]*class="eti">{}</td>.*?<td[^<>]*class="sub">(.*?)<'
            .format(field), html, dtype, alt=alt)

    def getvalues(self, field, html, dtype=None, alt=None) -> List[str]:
        result = []
        for preresult in self.findallbyre(
            '(?s)<td[^<>]*class="eti">{}</td>.*?<td[^<>]*class="sub">(.*?)<'
                .format(field), html, dtype, alt=alt):
            result += preresult.split('|')
        return result

    def findnames(self, html) -> List[str]:
        return self.getvalues(100, html) + self.getvalues(400, html)

    def findlanguagesspoken(self, html: str):
        return self.getvalues(377, html, 'language')

    def findwebpages(self, html: str):
        return self.getvalues(856, html)

    def findmixedrefs(self, html: str):
        return self.finddefaultmixedrefs(html)


class CanticAnalyzer(MarcAnalyzer):
    def setup(self):
        MarcAnalyzer.setup(self)
        self.dbproperty = 'P1273'
        self.dbname = 'CANTIC'
        self.urlbase = 'http://cantic.bnc.cat/registres/fitxa/{id}/{id}'
        self.urlbase2 = 'http://cantic.bnc.cat/registres/marc/{id}'
        # self.skipfirst = True
        self.language = 'ca'

    def finddescriptions(self, html: str):
        section = ' '.join(self.getvalues(670, html))
        return self.findallbyre(r'\((.*?)\)', section)

    def findlongtext(self, html: str):
        return '\n'.join(self.getvalues(670, html))


class ConorAnalyzer(Analyzer):
    def setup(self):
        self.dbproperty = None
        self.dbid = None
        self.dbname = 'CONOR'
        self.urlbase = None
        self.hrtre = '(<table[^<>]*table-striped.*?</table>)'
        self.language = 'en'
        self.escapehtml = True

    def findinstanceof(self, html: str):
        return 'Q5'

    def findnames(self, html) -> List[str]:
        return self.findallbyre(r'<h\d+>(.*?)<', html)

    def findlongtext(self, html: str):
        return self.findbyre('(?s)<div[^<>]*"gare-[^<>]*>(.*?)</pre>', html)

    def findmixedrefs(self, html: str):
        return self.finddefaultmixedrefs(html)

    def findoccupations(self, html: str):
        section = self.finddescription(html)
        if section:
            return self.findallbyre(r'([\w\s]+)', section, 'occupation')
        return None


class ConorSiAnalyzer(ConorAnalyzer):
    def setup(self):
        ConorAnalyzer.setup(self)
        self.dbproperty = 'P1280'
        self.dbid = 'Q16744133'
        self.dbname = 'CONOR.SI'
        self.urlbase = 'https://plus.cobiss.si/opac7/conor/{id}'
        self.language = 'sl'

    def findnames(self, html) -> List[str]:
        result = super().findnames(html)
        for sectionname in ['Osebno ime', 'Variante osebnega imena']:
            section = self.findbyre(r'(?s)<td>{}</td>.*?<a[^<>]*>(.*?)<'
                                    .format(sectionname), html)
            if section:
                result += [
                    ','.join(name.split(',')[:-1])
                    for name in self.findallbyre('([^=;]+)', section)
                ] + self.findallbyre('([^=;]+)', section)
        return result

    def finddescription(self, html: str):
        return self.findbyre(r'(?s)<td>Opombe</td>\s*<td>(.*?)</td>', html)

    def findnationalities(self, html: str):
        section = self.findbyre(r'(?s)<td>Dr[^<>]*ava</td>\s*<td>(.*?)[\(<]', html)
        if section:
            return self.findallbyre(r'([^\(\);<>,]+)', section, 'country')
        return None

    def findlanguagesspoken(self, html: str):
        section = self.findbyre(r'(?s)<td>Jezik[^<>]*</td>\s*<td>(.*?)</td>', html)
        if section:
            return self.findallbyre(r'([^\(\);<>,]+)', section, 'language')

    def findlastname(self, html: str):
        return self.findbyre(r'(?s)<td>Osebno ime</td>.*?<a[^<>]*>([^<>]*?),', html, 'lastname')

    def findfirstname(self, html: str):
        return self.findbyre(r'(?s)<td>Osebno ime</td>.*?<a[^<>]*>[^<>,]*,\s*(\w+)', html, 'firstname')

    def findbirthdate(self, html: str):
        return self.findbyre(r'(?s)<td>Osebno ime</td>.*?<a[^<>]*>[^<>]*,([^<>,]*)-', html)

    def finddeathdate(self, html: str):
        return self.findbyre(r'(?s)<td>Osebno ime</td>.*?<a[^<>]*>[^<>]*-([^<>]*?)<', html)


class ConorAlAnalyzer(ConorAnalyzer):
    def setup(self):
        ConorAnalyzer.setup(self)
        self.dbpropperty = 'P8848'
        self.dbid = 'Q101552645'
        self.dbname = 'CONOR.AL'
        self.urlbase = 'https://opac.al.cobiss.net/opac7/conor/{id}'
        self.language = 'sq'

    def findnationality(self, html: str):
        return self.findbyre(r'(?s)<td>Shteti</td>\s*<td>(.*?)[\(<]', html, 'country')

    def findlanguagesspoken(self, html: str):
        section = self.findbyre(r'(?s)<td>Gjuha[^<>]*</td>\s*<td>(.*?)</td>', html)
        if section:
            return self.findallbyre(r'([^\(\);<>,]+)', section, 'language')
        return None

    def findlastname(self, html: str):
        return self.findbyre(r'(?s)<td>Emri vetjak</td>.*?<a[^<>]*>([^<>]*?),', html, 'lastname')

    def findfirstname(self, html: str):
        return self.findbyre(r'(?s)<td>Emri vetjak</td>.*?<a[^<>]*>[^<>,]*,\s*(\w+)', html, 'firstname')

    def findbirthdate(self, html: str):
        return self.findbyre(r'(?s)<td>Emri vetjak</td>.*?<a[^<>]*>[^<>]*,([^<>,]*)-', html)

    def finddeathdate(self, html: str):
        return self.findbyre(r'(?s)<td>Emri vetjak</td>.*?<a[^<>]*>[^<>]*-([^<>]*?)<', html)


class ConorBgAnalyzer(ConorAnalyzer):
    def setup(self):
        ConorAnalyzer.setup(self)
        self.dbproperty = 'P8849'
        self.dbid = 'Q101552639'
        self.dbname = 'CONOR.BG'
        self.urlbase = 'https://opac.bg.cobiss.net/opac7/conor/{id}'
        self.language = 'bg'

    def findnames(self, html) -> List[str]:
        result = ConorAnalyzer.findnames(self, html)
        for sectionname in ['Име на лице', 'Вариант на име на лице']:
            section = self.findbyre(r'(?s)<td>{}</td>.*?<a[^<>]*>(.*?)<'
                                    .format(sectionname), html)
            if section:
                result += [
                    ','.join(name.split(',')[:-1])
                    for name in self.findallbyre('([^=;]+)', section)
                ] + self.findallbyre('([^=;]+)', section)
        return result

    def finddescription(self, html: str):
        return self.findbyre(r'(?s)<td>Забележки</td>\s*<td>(.*?)</td>', html)

    def findfirstnames(self, html: str):
        return [self.findbyre(r',\s*(\w+)', name, 'firstname')
                for name in self.findnames(html)[:2]]

    def findlastnames(self, html: str):
        return [self.findbyre('([^,]+)', name, 'lastname')
                for name in self.findnames(html)[:2]]

    def findnationality(self, html: str):
        return self.findbyre(r'(?s)<td>Държава</td>\s*<td>(.*?)[\(<]', html, 'country')

    def findlanguagesspoken(self, html: str):
        section = self.findbyre(r'(?s)<td>Език [^<>]*</td>\s*<td>(.*?)</td>', html)
        if section:
            return self.findallbyre(r'([^\(\);<>,]+)', section, 'language')
        return None


class ConorSrAnalyzer(ConorAnalyzer):
    def setup(self):
        ConorAnalyzer.setup(self)
        self.dbproperty = 'P8851'
        self.dbid = 'Q101552642'
        self.dbname = 'CONOR.SR'
        self.urlbase = 'https://plus.sr.cobiss.net/opac7/conor/{id}'
        self.language = 'sr'

    def findnames(self, html) -> List[str]:
        result = ConorAnalyzer.findnames(self, html)
        for sectionname in ['Лично име', 'Варијанте личног имена']:
            section = self.findbyre(r'(?s)<td>{}</td>.*?<a[^<>]*>(.*?)<'
                                    .format(sectionname), html)
            if section:
                result += [','.join(name.split(',')[:-1])
                           for name in self.findallbyre('([^=;]+)', section)]
        return result

    def finddescription(self, html: str):
        return self.findbyre(r'(?s)<td>Напоменe</td>\s*<td>(.*?)</td>', html)

    def findfirstnames(self, html: str):
        return [self.findbyre(r',\s*(\w+)', name, 'firstname')
                for name in self.findnames(html)[:2]]

    def findlastnames(self, html: str):
        return [self.findbyre('([^,]+)', name, 'lastname')
                for name in self.findnames(html)[:2]]

    def findnationality(self, html: str):
        return self.findbyre(r'(?s)<td>Држава</td>\s*<td>(.*?)[\(<]', html, 'country')

    def findlanguagesspoken(self, html: str):
        section = self.findbyre(r'(?s)<td>Језик [^<>]*</td>\s*<td>(.*?)</td>', html)
        if section:
            return self.findallbyre(r'([^\(\);<>,]+)', section, 'language')
        return None


class MunzingerAnalyzer(Analyzer):
    def setup(self):
        self.dbproperty = 'P1284'
        self.dbid = 'Q974352'
        self.dbname = 'Munzinger'
        self.urlbase = 'https://www.munzinger.de/search/go/document.jsp?id={id}'
        self.hrtre = '<div class="content">(.*?)<div class="mitte-text">'
        self.language = 'de'

    def findinstanceof(self, html: str):
        return 'Q5'

    def findnames(self, html) -> List[str]:
        return [
            self.findbyre(r'(?s)<title>([^<>]*) - ', html),
            self.findbyre(r'<h1>(.*?)</h1>', html)
        ]

    def finddescriptions(self, html: str):
        return [
            self.findbyre(r'(?s)</h1>(.*?)<', html),
            self.findbyre(r'"description" content="[^<>"]*:(.*?)"', html)
        ]

    def findlongtext(self, html: str):
        return self.findbyre(r'(?s)(<h2 id=".*)<br style="clear:both;"', html)

    def findoccupations(self, html: str):
        section = self.findbyre(r'(?s)</h1>(.*?)<', html)
        if section:
            return self.findallbyre(r'([^;]*)', section, 'occupation', skips=['degree'])

    def findbirthdate(self, html: str):
        return self.findbyre(r'(?s)Geburtstag:(?:<[^<>]*>|\s)*((?:\d+\. \w+)? \d{3,4})', html)

    def findbirthplace(self, html: str):
        return self.findbyre(r'(?s)Geburtstag:(?:<[^<>]*>|\s)*(?:\d+\. \w+)? \d{3,4} ([^<>]*)', html, 'city')

    def finddeathdate(self, html: str):
        return self.findbyre(r'(?s)Todestag:(?:<[^<>]*>|\s)*((?:\d+\. \w+)? \d{3,4})', html)

    def finddeathplace(self, html: str):
        return self.findbyre(r'(?s)Todestag:(?:<[^<>]*>|\s)*(?:\d+\. \w+)? \d{3,4} ([^<>]*)', html, 'city')

    def findnationality(self, html: str):
        return self.findbyre(r'(?s)Nation:(?:<[^<>]*>|\s)*([^<>]*)', html, 'country')


class PeopleAustraliaAnalyzer(Analyzer):
    def setup(self):
        self.dbproperty = 'P1315'
        self.dbid = None
        self.dbname = 'National Library of Australia'
        self.urlbase = 'https://trove.nla.gov.au/people/{id}'
        self.hrtre = '(<h1.*?)<h2>(?:Resources|Related)'
        self.language = 'en'
        self.escapeurl = True
        self.escapehtml = True

    def finddescriptions(self, html: str):
        return [
            self.findbyre(r'(?s)<h2>Biographies</h2>.*?<p>(.*?)<', html),
            self.findbyre(r'(?s)<dd class="creator">(.*)</dd>', html),
        ]

    def findnames(self, html) -> List[str]:
        return [self.findbyre(r'(?s)<h1>(.*?)[\(<]', html)] \
            + self.findallbyre(r'(?s)othername">(.*?)[\<]', html)

    def findlongtext(self, html: str):
        return self.findbyre(r'(?s)<h2>Biographies</h2>(.*?)<h2', html)

    def findbirthdate(self, html: str):
        return self.findbyre(r'(?s)<h1>[^<>]+\(([^<>\)]*)-', html)

    def finddeathdate(self, html: str):
        return self.findbyre(r'(?s)<h1>[^<>]+\([^<>\)]*-([^<>\)]*)\)', html)

    def findfirstname(self, html: str):
        return self.findbyre(r'(?s)<h1>[^<>,\(\)]+,\s*([\w\-]+)', html, 'firstname')

    def findlastname(self, html: str):
        return self.findbyre(r'(?s)<h1>([^<>,\(\)]+),', html, 'lastname')

    def findoccupations(self, html: str):
        section = self.findbyre(r'(?s)<dt>Field of Activity</dt>(.*?)</dd>', html)
        if section:
            return self.findallbyre(r'>([^<>]+)</a>', section, 'occupation')

    def findmixedrefs(self, html: str):
        return [x for x in self.finddefaultmixedrefs(html, includesocial=False) if
                not (x[0] == 'P345' and not x[1].startswith('nm'))]

    def findschools(self, html: str):
        return self.findallbyre(r'(?s)\(student\)\s*<[^<>]*>(.*?)<', html, 'university')

    def findemployers(self, html: str):
        return self.findallbyre(r'(?s)\(employee\)\s*<[^<>]*>(.*?)<', html, 'employer', alt=['university'])

    def findworkfields(self, html: str):
        section = self.findbyre(r'(?s)<dt>Field of activity</dt>\s*<dd>(.*?)</dd>', html)
        if section:
            return self.findallbyre(r'(?s)>(.*?)<', section, 'subject')


class ArtUkAnalyzer(Analyzer):
    def setup(self):
        self.dbproperty = 'P1367'
        self.dbid = None
        self.dbname = 'Art UK'
        self.urlbase = 'https://artuk.org/discover/artists/{id}'
        self.hrtre = '<div class="page-header">(.*?)<main id="main">'
        self.language = 'en'

    def findnames(self, html) -> List[str]:
        return self.findallbyre(r'(?s)<h2>(.*?)<', html)

    def findbirthdate(self, html: str):
        return self.findbyre(r'(?s)</h2>\s*<p>([^<>]*)–', html)

    def finddeathdate(self, html: str):
        return self.findbyre(r'(?s)</h2>\s*<p>[^<>]*–([^<>]*)', html)

    def findnationalities(self, html: str):
        section = self.findbyre(r'(?s)>([^<>]+)</p>\s*</div>\s*<!-- END: skins/artuk/actor/v_page_title -->', html)
        if section:
            return self.findallbyre(r'([^,]+)', section, 'country')

    def findincollections(self, html: str):
        return self.findallbyre(r'(?s)<a href="https://artuk.org/visit/venues/[^"]*" title="(.*?)"', html, 'museum')


class LnbAnalyzer(Analyzer):
    def setup(self):
        self.dbproperty = 'P1368'
        self.dbid = None
        self.dbname = 'National Library of Latvia'
        self.urlbase = 'https://kopkatalogs.lv/F?func=direct&local_base=lnc10&doc_number={id}'
        self.hrtre = '<!-- filename: full-999-body -->(.*)<!-- filename: direct-tail  -->'
        self.escapehtml = True
        self.language = 'lv'

    def prepare(self, html: str):
        return html.replace('&nbsp;', ' ')

    def getvalue(self, field, html, dtype=None, alt=None):
        return self.findbyre(
            r'(?s)<td[^<>]*>[^<>]*{}[^<>]*</td>\s*<td[^<>]*>(.*?)</td>'
            .format(field), html, dtype, alt=alt)

    def getvalues(self, field, html, dtype=None, alt=None) -> List[str]:
        parts = re.findall('(?s)<td[^<>]*>(.*?)</td>', html)
        status = 'inactive'
        result = []
        for part in parts:
            if status == 'active':
                result.append(self.findbyre(r'(?s)(.*)', part.strip().rstrip('.'), dtype, alt=alt))
                status = 'waiting'
            elif field in part or status == 'waiting' and not part.strip():
                status = 'active'
            else:
                status = 'inactive'
        return result

    def instanceof(self, html: str):
        return self.getvalue('Entītes veids', html, 'instanceof')

    def findnames(self, html) -> List[str]:
        namecontainers = self.getvalues('Persona', html) \
            + self.getvalues('Norāde', html)
        namecontainers = [self.TAGRE.sub('', namecontainer)
                          for namecontainer in namecontainers]
        return [self.findbyre(r'([^\d]+),', namecontainer)
                for namecontainer in namecontainers] \
            + [self.findbyre(r'([^\d]+)', namecontainer)
               for namecontainer in namecontainers]

    def findbirthplace(self, html: str):
        return self.findbyre(r'Dzim\.:([^<>]*)\.', html, 'city')

    def finddeathplace(self, html: str):
        return self.findbyre(r'Mir\.:([^<>]*)\.', html, 'city')

    def findworkfields(self, html: str):
        return self.getvalues('Darbības joma', html, 'subject')

    def findoccupations(self, html: str):
        return self.getvalues('Nodarb', html, 'occupation')

    def findgender(self, html: str):
        return self.getvalue('Dzimums', html, 'gender')

    def findisni(self, html: str):
        return self.getvalue('ISNI', html)

    def findviaf(self, html: str):
        return self.findbyre(r'\(VIAF\)\s*(\d+)', html)

    def findemployers(self, html: str):
        return self.getvalues('Grupa saistīta ar', html, 'employer', alt=['university'])

    def findlanguagesspoken(self, html: str):
        if self.instanceof(html) == 'Q5':
            return self.getvalues('Valoda saistīta ar', html, 'language')


class OxfordAnalyzer(Analyzer):
    def setup(self):
        self.dbproperty = 'P1415'
        self.dbid = 'Q17565097'
        self.dbname = 'Oxford Dictionary of National Biography'
        self.urlbase = 'https://doi.org/10.1093/ref:odnb/{id}'
        self.hrtre = '<div class="abstract">(.*?)</div>'
        self.language = 'en'

    def findnames(self, html) -> List[str]:
        return [self.findbyre(r'"pf:contentName" : "(.*?)\(', html)]

    def findoccupations(self, html: str):
        section = self.findbyre(r'"pf:contentName".*?\)(.*?)"', html)
        if section:
            parts = section.split(' and ')
            results = []
            for part in parts:
                results += self.findbyre(r'([\w\s]+)', part, 'occupation')
            return results

    def findbirthdate(self, html: str):
        return self.findbyre(r'<title>[^<>]*\((\d+)-', html)

    def finddeathdate(self, html: str):
        return self.findbyre(r'<title>[^<>]*-(\d+)\)', html)

    def findlongtext(self, html: str):
        return self.findbyre(r'<div class="abstract">(.*?)</div>', html)


class SandrartAnalyzer(Analyzer):
    def setup(self):
        self.dbproperty = 'P1422'
        self.dbid = 'Q17298559'
        self.dbname = 'Sandrart'
        self.urlbase = 'http://ta.sandrart.net/en/person/view/{id}'
        self.hrtre = '<h2>Basic data</h2>(.*?)<h2>Occurrences'
        self.language = 'de'

    def findlongtext(self, html: str):
        return self.findbyre(r'(?s)<h2>Basic data</h2>.*?<p>(.*?)</p>', html)

    def findnames(self, html) -> List[str]:
        return [self.findbyre(r'<h1>(.*?)<', html)]

    def finddescription(self, html: str):
        return self.findbyre(r'(?s)<h2>Basic data</h2>.*?<p>(.*?)(?:, geb\. |, gest\.|;|<)', html)

    def findbirthdate(self, html: str):
        return self.findbyre(r'geb\. (\d+)', html)

    def findbirthplace(self, html: str):
        return self.findbyre(r'geb\.[^;,<>]* in (?:<[^<>]*>)?(.+?)[,<]', html, 'city')

    def finddeathdate(self, html: str):
        return self.findbyre(r'gest\. (\d+)', html)

    def finddeathplace(self, html: str):
        return self.findbyre(r'gest\.[^;,<>]* in (?:<[^<>]*>)?(.+?)[,<]', html, 'city')

    def findoccupations(self, html: str):
        section = self.finddescription(html)
        if section:
            result = []
            parts = section.split(' und ')
            for part in parts:
                result += self.findallbyre(r'[\w\s]+', part, 'occupation')
            return result

    def findmixedrefs(self, html: str):
        return self.finddefaultmixedrefs(html, includesocial=False)


class FideAnalyzer(Analyzer):
    def setup(self):
        self.dbproperty = 'P1440'
        self.dbid = 'Q27038151'
        self.dbname = 'FIDE'
        self.urlbase = 'https://ratings.fide.com/profile/{id}'
        self.hrtre = '(<table width=480.*?</table>)'
        self.language = 'en'
        self.escapehtml = True

    def findinstanceof(self, html: str):
        return 'Q5'

    def findnames(self, html) -> List[str]:
        return [self.findbyre(r'<title>(.*?)<', html)]

    def findnationality(self, html: str):
        return self.findbyre(r'(?s)Federation:</div>\s*<div[^<>]*>(.*?)<', html, 'country')

    def findsportcountries(self, html: str):
        return [self.findbyre(r'(?s)Federation:</div>\s*<div[^<>]*>(.*?)<', html, 'country')]

    def findchesstitle(self, html: str):
        return self.findbyre(r'(?s)FIDE title:</div>\s*<div[^<>]*>(.*?)<', html, 'chesstitle')

    def findgender(self, html: str):
        return self.findbyre(r'(?s)Sex:</div>\s*<div[^<>]*>(.*?)<', html, 'gender')

    def findbirthdate(self, html: str):
        return self.findbyre(r'(?s)B-Year:</div>\s*<div[^<>]*>(.*?)<', html)

    def findsports(self, html: str):
        return ['Q718']

    def findoccupations(self, html: str):
        return ['Q10873124']


class SportsReferenceAnalyzer(Analyzer):
    def setup(self):
        self.dbproperty = 'P1447'
        self.dbid = 'Q18002875'
        self.dbname = 'sports-reference.com'
        self.urlbase = 'https://www.sports-reference.com/olympics/athletes/{id}.html'
        self.hrtre = '(<h1.*?</div>)'
        self.language = 'en'

    def findnames(self, html) -> List[str]:
        return [
            self.findbyre(r'<h1.*?>(.*?)<', html),
            self.findbyre(r'Full name:</span>([^<>]*)', html),
        ]

    def findlongtext(self, html: str):
        return self.findbyre(r'(?s)<h2[^<>]*>Biography</h2>(.*?)<h2', html)

    def findinstanceof(self, html: str):
        return 'Q5'

    def findgender(self, html: str):
        return self.findbyre(r'Gender:</span>([^<>]*)', html, 'gender')

    def findheights(self, html: str):
        return [self.findbyre(r'Height:</span>[^<>]*\((.*?)\)', html)]

    def findweights(self, html: str):
        return [
            self.findbyre(r'Weight:</span>(.*?)\(', html),
            self.findbyre(r'Weight:</span>[^<>]*\((.*?)\)', html),
        ]

    def findbirthdate(self, html: str):
        return self.findbyre(r'data-birth="(.*?)"', html)

    def finddeathdate(self, html: str):
        return self.findbyre(r'data-death="(.*?)"', html)

    def findbirthplace(self, html: str):
        return self.findbyre(r'birthplaces\.cgi.*?">(.*?)<', html, 'city')

    def findsportteams(self, html: str):
        return [self.findbyre(r'Affiliations:</span>([^<>,]*)', html, 'club')]

    def findnationality(self, html: str):
        return self.findbyre(r'Country:</span>.*?>([^<>]*)</a>', html, 'country')

    def findsports(self, html: str):
        section = self.findbyre(r'(?s)Sport:</span>(.*?)(?:<p>|<br>|</div>)', html)
        if section:
            return self.findallbyre(r'>([^<>]*)</', section, 'sport')

    def findoccupations(self, html: str):
        section = self.findbyre(r'(?s)Sport:</span>(.*?)(?:<p>|<br>|</div>)', html)
        if section:
            return self.findallbyre(r'>([^<>]*)</', section, 'occupation')

        return ['Q2066131']

    def findparticipations(self, html: str):
        section = self.findbyre(r'(?s)(<tbody>.*</tbody>)', html)
        if section:
            return self.findallbyre(r'<a href="/olympics/\w+/\d+/">(.*?)<', section, 'olympics')


class PrdlAnalyzer(Analyzer):
    def setup(self):
        self.dbproperty = 'P1463'
        self.dbid = 'Q7233488'
        self.dbname = 'Post-Reformation Digital Library'
        self.urlbase = 'http://prdl.org/author_view.php?a_id={id}'
        self.hrtre = '(<span id="header_text">.*?</table>)'
        self.language = 'en'

    def findnames(self, html) -> List[str]:
        return self.findallbyre(r'&ldquo;([^<>]*?)&rdquo;', html)

    def finddescription(self, html: str):
        result = self.findbyre(r'Academic Title</span>(<span.*?</span>)', html)
        if result:
            return self.TAGRE.sub('', result)

    def findinstanceof(self, html: str):
        return 'Q5'

    def findbirthdate(self, html: str):
        result = self.findbyre(r'</b></span><span[^<>]*>\s*\((?:c\.)?([^<>\-\)]*)', html)
        if result and 'fl.' not in result and re.search(r'1\d{3}', result):
            return result
        return None

    def finddeathdate(self, html: str):
        section = self.findbyre(r'</b></span><span[^<>]*>\s*\(([^<>\)]*-[^<>]*?)\)', html)
        if section and 'fl.' not in section and re.search(r'-.*1\d{3}', section):
            return self.findbyre(r'\-(?:c\.)?(.*)', section)
        return None

    def findreligions(self, html: str):
        section = self.findbyre(r'>Tradition</span>(.*?)<span', html)
        if section:
            return self.findallbyre(r'<a[^<>]*>(.*?)<', section, 'religion')

    def findmixedrefs(self, html: str):
        return self.finddefaultmixedrefs(html, includesocial=False)


class FifaAnalyzer(Analyzer):
    def setup(self):
        self.dbproperty = 'P1469'
        self.dbid = None
        self.dbname = 'FIFA'
        self.urlbase = 'https://static.fifa.com/fifa-tournaments/players-coaches/people={id}/index.html'
        self.hrtre = '<div class="fdh-wrap contentheader">(.*?)</div>'
        self.language = 'en'

    def getvalue(self, field, html, dtype=None):
        return self.findbyre(r'<meta name="{}" content="(.*?)"'
                             .format(field), html, dtype)

    def findinstanceof(self, html: str):
        return 'Q5'

    def findnames(self, html) -> List[str]:
        return [
            self.findbyre(r' - ([^<>\-]+)</title>', html),
            self.getvalue('profile-webname', html),
            self.getvalue('profile-webnameALT', html),
            self.getvalue('profile-fullname', html),
            self.findbyre(r'<h1>(.*?)<', html)
        ]

    def findlastname(self, html: str):
        result = self.getvalue('profile-commonSurname', html)
        if result:
            return self.findbyre(r'([A-Z\s]*) ', result + ' ', 'lastname')

    def findnationality(self, html: str):
        return self.getvalue('profile-countryname', html, 'country') or \
               self.getvalue('profile-countrycode', html, 'country')

    def findgender(self, html: str):
        return self.getvalue('profile-gender', html, 'gender')

    def findbirthdate(self, html: str):
        result = self.getvalue('person-birthdate', html)
        if result:
            return result.split('T')[0]

    def findsports(self, html: str):
        return ['Q2736']


class ZbmathAnalyzer(Analyzer):
    def setup(self):
        self.dbproperty = 'P1556'
        self.dbid = None
        self.dbname = 'ZbMath'
        self.urlbase = 'https://zbmath.org/authors/?q=ai:{id}'
        self.hrtre = '</h2>(.*?)<div class="indexed">'
        self.language = 'en'
        self.escapehtml = True

    def findnames(self, html) -> List[str]:
        result = self.findallbyre(r'<h2>(.*?)<', html)
        section = self.findbyre(r'(?s)<td>Published as:</td>(.*?)</tr>', html)
        if section:
            result += self.findallbyre(r':([^<>"]+)"', section)
        return result

    def findlongtext(self, html: str):
        return self.findbyre(r'(?s)(<h2>.*?)<div class="indexed">', html)

    def findawards(self, html: str):
        section = self.findbyre(r'(?s)<td>Awards:</td>(.*?)</tr>', html)
        if section:
            return self.findallbyre(r'title="(.*?)"', section, 'award')

    def findmixedrefs(self, html: str):
        return [
                   ('P227', self.findbyre(r'title="([^"<>]+)">GND</a>', html)),
                   ('P549', self.findbyre(r'title="([^"<>]+)">MGP</a>', html)),
                   ('P1563', self.findbyre(r'title="([^"<>]+)">MacTutor</a>', html)),
                   ('P2456', self.findbyre(r'title="([^"<>]+)">dblp</a>', html)),
                   ('P4252', self.findbyre(r'title="([^"<>]+)">Math-Net.Ru</a>', html)),
               ] + \
               self.finddefaultmixedrefs(html, includesocial=False)

    def findworkfields(self, html: str):
        section = self.findbyre(r'(?s)<h4>Fields</h4>(.*?)</table>', html)
        if section:
            preresults = self.findallbyre(r'(?s)<tr>(.*?)</tr>', section.replace('&nbsp;', ' '))[:5]
            results = []
            for preresult in preresults:
                if int(self.findbyre(r'">(\d+)</a>', preresult) or 0) > 5:
                    results.append(
                        self.findbyre(r'(?s)"Mathematics Subject Classification">(.*?)<', preresult, 'subject'))
            return results

    def findwebsite(self, html: str):
        return self.findbyre(r'(?s)<td>Homepage:</td>\s*<td><a[^<>]*>(.*?)<', html)


class UBarcelonaAnalyzer(Analyzer):
    def setup(self):
        self.dbproperty = 'P1580'
        self.dbid = None
        self.dbname = 'University of Barcelona authority control'
        self.urlbase = 'https://crai.ub.edu/sites/default/files/autoritats/permanent/{id}'
        self.hrtre = '(<h2.*?</table>)'
        self.language = 'ca'
        self.escapehtml = True

    def finddescriptions(self, html: str):
        return [
            self.findbyre(r'<h2>(.*?)<', html),
            self.findbyre(r'(?s)Nota hist[^<>]*rica(.*?)</tr>', html)
        ]

    def findnames(self, html) -> List[str]:
        return [self.findbyre(r'(?s)<h2>([^<>]*)(?:, \d|<)', html)] \
            + self.findallbyre(r'(?s)Emprat per<.*?<i>(.*?)(?:, \d|<)', html)

    def findlongtext(self, html: str):
        return self.findbyre(r'(?s)(<h2.*?</table>)', html)

    def findinstanceof(self, html: str):
        return 'Q5'

    def findviaf(self, html: str):
        return self.findbyre(r'http://viaf.org/viaf/(\w+)', html)

    def findworkplaces(self, html: str):
        section = self.findbyre(r"(?s)Lloc d'activitat(.*?)</tr>", html)
        if section:
            return self.findallbyre(r'<td>([^<>,]*)', section, 'city')

    def findoccupations(self, html: str):
        section = self.findbyre(r'(?s)Ocupaci(.*?)</tr>', html) or \
                  self.findbyre(r'(?s)Nota hist[^<>]*rica(.*?)</tr>', html)
        if section:
            return self.findallbyre(r'<td>([^<>,]*)', section, 'occupation')

    def findgender(self, html: str):
        return self.findbyre(r'G&egrave;nere.*?<td>(.*?)</td>', html, 'gender')


class DialnetAnalyzer(Analyzer):
    def setup(self):
        self.dbproperty = 'P1607'
        self.dbid = 'Q3025975'
        self.dbname = 'Dialnet'
        self.urlbase = 'https://dialnet.unirioja.es/servlet/autor?codigo={id}'
        self.hrtre = '(<div id="paginaDeAutor" class="textos">.*?)<!-- Inicio de las secciones de la obra del autor -->'
        self.language = 'es'

    def findinstanceof(self, html: str):
        return 'Q5'

    def findnames(self, html) -> List[str]:
        return self.findallbyre(r'title" content="(.*?)"', html) \
            + self.findallbyre(r'<title>(.*?)(?: - |</)', html) \
            + self.findallbyre(r'(?s)<h2>(.*?)</h2>', html)

    def findfirstname(self, html: str):
        return self.findbyre(r'first_name" content="(.*?)"', html, 'firstname')

    def findlastname(self, html: str):
        return self.findbyre(r'last_name" content="(.*?)"', html, 'lastname')

    def findemployers(self, html: str):
        section = self.findbyre(r'(?s)<ul id="listaDeInstituciones">(.*?)</ul>', html)
        if section:
            return self.findallbyre(r'">(.*?)<', section, 'employer', alt=['university'])

    def findworkfields(self, html: str):
        section = self.findbyre(r'(?s)<ul id="listaDeAreasDeConocimiento">(.*?)</ul>', html)
        if section:
            return self.findallbyre(r'">(.*?)<', section, 'subject')

    def findmixedrefs(self, html: str):
        return self.finddefaultmixedrefs(html, includesocial=False)


class ClaraAnalyzer(Analyzer):
    def setup(self):
        self.dbproperty = 'P1615'
        self.dbid = 'Q18558540'
        self.dbname = 'CLARA'
        self.urlbase = 'http://clara.nmwa.org/index.php?g=entity_detail&entity_id={id}'
        self.hrtre = '<div id="pageArea">(.*?)<div style="width: 600px;'
        self.language = 'en'

    def findnames(self, html) -> List[str]:
        return [self.findbyre(r'(?s)<div class="title">(.*?)<', html)]

    def findlongtext(self, html: str):
        return self.findbyre(
            '(?s)(<div id="pageArea">.*?)<div style="width: 600px; border: 1px solid #000000; padding: 5px;">', html)

    def findinstanceof(self, html: str):
        return 'Q5'

    def findgender(self, html: str):
        return 'Q6581072'

    def findbirthdate(self, html: str):
        return self.findbyre(r'(?s)<div class="lifespan">([^<>]+?)-', html)

    def finddeathdate(self, html: str):
        result = self.findbyre(r'(?s)<div class="lifespan">[^<>]+-([^<>]+)</div>', html)
        if result.strip() != 'present':
            return result

    def findnationality(self, html: str):
        return self.findbyre(r'(?s)<div class="detail_label">Nationality:</div>\s*<div class="detail_text">(.*?)<', html,
                             'country')

    def findoccupations(self, html: str):
        result = []
        section = self.findbyre(
            r'(?s)<div class="detail_label">Artistic Role\(s\):</div>\s*<div class="detail_text">(.*?)<', html)
        if section:
            result += self.findallbyre(r'([^,]*)', section, 'occupation')
        section = self.findbyre(
            r'(?s)<div class="detail_label">Other Occupation\(s\):</div>\s*<div class="detail_text">(.*?)<', html)
        if section:
            result += self.findallbyre(r'([^,]*)', section, 'occupation')
        return result

    def findresidences(self, html: str):
        section = self.findbyre(
            r'(?s)<div class="detail_label">Place\(s\) of Residence:</div>\s*<div class="detail_text">(.*?)<', html)
        if section:
            return self.findallbyre(r'([^,]*)', section, 'city')
        return None


class WelshBioAnalyzer(Analyzer):
    def setup(self):
        self.dbproperty = 'P1648'
        self.dbid = 'Q5273977'
        self.dbname = 'Dictionary of Welsh Biography'
        self.urlbase = 'https://biography.wales/article/{id}'
        self.hrtre = '<div class="col-lg py-3 px-3">(.*?)</div>'
        self.language = 'en'
        self.escapehtml = True

    def findnames(self, html) -> List[str]:
        return [self.findbyre(r'<b>Name:</b>(.*?)<', html)]

    def finddescription(self, html: str):
        return self.findbyre(r'<h1>(.*?)<', html)

    def findlongtext(self, html: str):
        return self.findbyre(r'<div class="col-lg py-3 px-3">.*?</div>(.*?)<h2', html)

    def findlastname(self, html: str):
        return self.findbyre(r'<h1>([^<>\(\),]*),', html, 'lastname')

    def findfirstname(self, html: str):
        return self.findbyre(r'<h1>[^<>\(\)]*?([^<>\(\),]*)\(', html, 'firstname')

    def findinstanceof(self, html: str):
        return 'Q5'

    def findbirthdate(self, html: str):
        return self.findbyre(r'<b>Date of birth:</b>(.*?)<', html)

    def finddeathdate(self, html: str):
        return self.findbyre(r'<b>Date of death:</b>(.*?)<', html)

    def findspouses(self, html: str):
        return self.findallbyre(r'<b>Spouse:</b>(.*?)<', html, 'person')

    def findchildren(self, html: str):
        return self.findallbyre(r'<b>Child:</b>(.*?)<', html, 'person')

    def findgender(self, html: str):
        return self.findbyre(r'<b>Gender:</b>(.*?)<', html, 'gender')

    def findoccupations(self, html: str):
        return self.findallbyre(r'<b>Occupation:</b>(.*?)<', html, 'occupation')

    def findfather(self, html: str):
        for person in self.findallbyre(r'<b>Parent:</b>(.*?)<', html, 'male-person'):
            if person:
                return person

    def findmother(self, html: str):
        for person in self.findallbyre(r'<b>Parent:</b>(.*?)<', html, 'female-person'):
            if person:
                return person


class TgnAnalyzer(Analyzer):
    def setup(self):
        self.dbproperty = 'P1667'
        self.dbid = 'Q1520117'
        self.dbname = 'Getty Thesaurus of Geographic Names'
        self.urlbase = 'https://www.getty.edu/vow/TGNFullDisplay?find=&place=&nation=&subjectid={id}'
        self.hrtre = r'(<TR>\s*<TD VALIGN=TOP>.+?)<!-- END PRINT -->'
        self.language = 'en'

    def finddescriptions(self, html: str):
        return [
            self.findbyre(r'<SPAN CLASS=page>.*?<B>(.*?)</B>', html),
            self.findbyre(r'<B>Note:.*?</B>(.*?)<', html),
        ]

    def findnames(self, html) -> List[str]:
        section = self.findbyre(r'(?s)<B>Names:</B>(.*?)</TABLE>', html)
        if section:
            return self.findallbyre(r'<NOBR><B>(.*?)<', section)
        return []

    def findlongtext(self, html: str):
        return self.findbyre(r'(?s)<B>Note:\s*</B>(.*?)<', html)

    def findinstanceof(self, html: str):
        return self.findbyre(r'(?s)Place Types:.*?SPAN CLASS=page>(.*?)[<\(]', html, 'type')

    def findcountry(self, html: str):
        return self.findbyre(r'>([^<>]+)\s*</A>\s*\(nation\)', html, 'country')

    def findadminloc(self, html: str):
        county = self.findbyre(r'>([^<>]+)</A> \(county\)', html)
        state = self.findbyre(r'>([^<>]+)</A> \(state\)', html)
        if not state:
            return None

        if county:
            return self.getdata('county', '{} county, {}'
                                .format(county, state))
        return self.getdata('state', state)

    def findcoords(self, html: str):
        lat = self.findbyre(r'Lat:\s*(-?\d+\.\d+)', html)
        lon = self.findbyre(r'Long:\s*(-?\d+\.\d+)', html)
        if lat and lon:
            return f'{lat} {lon}'


class NlpAnalyzer(Analyzer):
    def setup(self):
        self.dbproperty = 'P1695'
        self.dbid = None
        self.dbname = 'National Library of Poland'
        self.urlbase = 'http://mak.bn.org.pl/cgi-bin/KHW/makwww.exe?BM=01&IM=04&NU=01&WI={id}'
        self.hrtre = '(<table.*?</table>)'
        self.language = 'pl'
        self.escapeunicode = True

    def finddescriptions(self, html: str):
        return self.findallbyre(r'>667.*?</I>(.*?)<', html)

    def findnames(self, html) -> List[str]:
        return self.findallbyre(r'>1\..*?</I>(.*?)<', html)

    def findlongtext(self, html: str):
        return '\n'.join(self.findallbyre(r'>667.*?</I>(.*?)<', html))

    def findoccupations(self, html: str):
        result = []
        sections = self.findallbyre(r'>667.*?</I>(.*?)<', html)
        for section in sections:
            result += self.findallbyre(r'([\s\w]+)', section, 'occupation')
        return result

    def findbirthdate(self, html: str):
        result = self.findbyre(r' d </TT></I>\(([^<>]*)-', html)
        if result and 'ca 'not in result:
            return result
        return None

    def finddeathdate(self, html: str):
        result = self.findbyre(r' d </TT></I>\([^<>]*-([^<>]*)\)', html)
        if result and 'ca' not in result:
            return result
        return None

    def findnationality(self, html: str):
        for result in self.findallbyre(r'>667.*?</I>\s*([^\s<>]*)', html, 'country'):
            if result:
                return result
        return None


class DaaoAnalyzer(Analyzer):
    def setup(self):
        self.dbproperty = 'P1707'
        self.dbid = 'Q5273961'
        self.dbname = 'DAAO'
        self.urlbase = 'https://www.daao.org.au/bio/{id}/'
        self.hrtre = '<div class="content_header research">(.*?)<!-- end content'
        self.language = 'en'
        self.escapehtml = True

    def getvalue(self, field, html, dtype=None):
        return self.findbyre(r'(?s)<dt>\s*{}\s*</dt>\s*<dd>(.*?)</dd>'
                             .format(field), html, dtype)

    def findinstanceof(self, html: str):
        return 'Q5'

    def findnames(self, html) -> List[str]:
        sections = self.findallbyre(r'(?s)<div class="aka">(.*?)<', html)
        result = []
        for section in sections:
            result += self.findallbyre(r'(?s)<li>(.*?)<', section)
        return (
            self.findallbyre(r'<span class="name">(.*?)<', html) + result
            + self.findallbyre(r'(/s)<dt>\s*Name\s*</dt>\s*<dd>(.*?)<', html)
        )

    def findlongtext(self, html: str):
        return self.findbyre(r'(?s)<div class="summary">(.*?)</div>', html)

    def finddescription(self, html: str):
        return self.findbyre(r'(?s)<div class="summary">(.*?)</div>', html)

    def findgender(self, html: str):
        return self.getvalue('Gender', html, 'gender')

    def findoccupations(self, html: str):
        result = []
        section = self.findbyre(r'(?s)<div class="roles">(.*?)</div>', html)
        if section:
            result += self.findallbyre(r'(?s)<li>(.*?),?\s*<', section, 'occupation')
        section = self.getvalue('Roles', html)
        if section:
            result += self.findallbyre(r'(?s)<li>(.*?)<', section, 'occupation')
        section = self.getvalue('Other Occupation', html)
        if section:
            result += self.findallbyre(r'(?s)<li>(.*?)[<\(]', section, 'occupation')
        return result

    def findbirthdate(self, html: str):
        return self.getvalue('Birth date', html)

    def findbirthplace(self, html: str):
        return self.getvalue('Birth place', html, 'city')

    def finddeathdate(self, html: str):
        return self.getvalue('Death date', html)

    def finddeathplace(self, html: str):
        return self.getvalue('Death place', html, 'city')

    def findresidences(self, html: str):
        section = self.getvalue('Residence', html)
        if section:
            return self.findallbyre(r'(?s)<li>[^<>]*?([^<>\d]+)</li>', section, 'city')

    def findlanguagesspoken(self, html: str):
        section = self.getvalue('Languages', html)
        if section:
            return self.findallbyre(r'(?s)<li>(.*?)<', section, 'language')
        return None


class BritishMuseumAnalyzer(Analyzer):
    def setup(self):
        self.dbproperty = 'P1711'
        self.dbid = 'Q18785969'
        self.dbname = 'British Museum'
        self.urlbase = 'https://www.britishmuseum.org/collection/term/BIOG{id}'
        self.hrtre = '<div class="section__inner">.*?<dl>(.*?)(?:Biography|</dl>)'
        self.language = 'en'

    def finddetails(self, html: str):
        return self.findbyre(r'(?s)Details</dt>\s*<dd[^<>]*>(.*?)</dd>', html) or ''

    def findnames(self, html) -> List[str]:
        return self.findallbyre('(?s)name:</span>(.*?)<', html)

    def findlongtext(self, html: str):
        return self.findbyre(r'(?s)Biography</dt>\s*<dd[^<>]*>(.*?)</dd>', html)

    def findinstanceof(self, html: str):
        return self.findbyre('([^;]+)', self.finddetails(html), 'instanceof')

    def findoccupations(self, html: str):
        return self.findallbyre('([^;/]+)', self.finddetails(html), 'occupation')

    def findnationalities(self, html: str):
        parts = self.findallbyre('([^;]+)', self.finddetails(html))
        return self.findallbyre('(.+)', parts[-2], 'country')

    def findgender(self, html: str):
        return self.findbyre('([^;]+)$', self.finddetails(html), 'gender')

    def findbirthdate(self, html: str):
        return self.findbyre(r'(?s) dates</dt>\s*<dd[^<>]*>([^<>]*)-', html)

    def finddeathdate(self, html: str):
        return self.findbyre(r'(?s) dates</dt>\s*<dd[^<>]*>[^<>]*-([^<>]*)', html)


class GtaaAnalyzer(Analyzer):
    def setup(self):
        self.dbproperty = 'P1741'
        self.dbid = 'Q19366588'
        self.dbname = 'GTAA'
        self.urlbase = 'http://data.beeldengeluid.nl/gtaa/{id}'
        self.hrtre = '<h3>DocumentationProperties</h3>(.*?)<h3'
        self.language = 'nl'

    def findlanguagenames(self, html: str):
        results = [
            ('nl', self.findbyre(r'<title>(.*?)<', html)),
            ('nl', self.findbyre(r'<h2>(.*?)<', html))
        ]
        section = self.findbyre(r'(?s)<h3>LexicalLabels</h3>(.*?)<h3', html)
        if section:
            results += re.findall(r'xml:lang="(\w+)">(.*?)<', section)
        return results

    def findlanguagedescriptions(self, html: str):
        section = self.findbyre(r'(?s)skos:scopeNote(.*?)<h3', html)
        if section:
            return re.findall(r'xml:lang="(\w+)">(.*?)<', section)
        return None

    def findlongtext(self, html: str):
        return self.findbyre(r'(?s)(<h3>DocumentationProperties</h3>.*?)<h3>Alternatieve formaten', html)

    def findoccupations(self, html: str):
        section = self.findbyre(r'(?s)skos:scopeNote(.*?)<h3', html)
        if section:
            results = []
            parts = self.findallbyre(r'(?s)">(.*?)<', section)
            for part in parts:
                results += self.findallbyre(r'([\w\s]+)', part, 'occupation')
            return results


class ParlementPolitiekAnalyzer(Analyzer):
    def setup(self):
        self.dbproperty = 'P1749'
        self.dbid = 'Q14042250'
        self.dbname = 'Parlement & Politiek'
        self.urlbase = 'https://www.parlement.com/id/{id}'
        self.hrtre = '<p class="mnone">(.*?)</p>'
        self.language = 'nl'

    def getsection(self, field, html, ntype=None):
        return self.findbyre(r'(?s){}</h2>\s*</div></div>(.*?)<[bp][>\s]'
                             .format(field), html, ntype)

    def findlongtext(self, html: str):
        return self.findbyre(r'(?s)<p class="m(?:none|top)">(.*?)</div>', html)

    def findnames(self, html) -> List[str]:
        return self.findallbyre(r'title" content="(.*?)"', html) \
            + self.findallbyre(r'<(?:title|h1)>(.*?)(?: - |<)', html)

    def finddescriptions(self, html: str):
        return self.findallbyre(r'[dD]escription" content="(.*?)"', html)

    def findfirstname(self, html: str):
        section = self.getsection('[vV]oorna[^<>]*', html)
        if section:
            return self.findbyre(r'\((.*?)\)', section, 'firstname') or \
                   self.findbyre(r'([\w\-]+)', section, 'firstname')

    def findbirthplace(self, html: str):
        return self.findbyre(r'(?s)geboorteplaats en -datum</b><br>([^<>]*),', html, 'city')

    def findbirthdate(self, html: str):
        return self.findbyre(r'(?s)geboorteplaats en -datum</b><br>[^<>]*,([^<>]*)', html)

    def finddeathplace(self, html: str):
        return self.findbyre(r'(?s)overlijdensplaats en -datum</b><br>([^<>]*),', html, 'city')

    def finddeathdate(self, html: str):
        return self.findbyre(r'(?s)overlijdensplaats en -datum</b><br>[^<>]*,([^<>]*)', html)

    def findparties(self, html: str):
        section = self.findbyre(r'(?s)partij\(en\)</b><br>(.*?<)/div>', html)
        if section:
            return self.findallbyre(r'([^<>]+)<', section, 'party')

    def findpolitical(self, html: str):
        section = self.findbyre(r'(?s)stroming\(en\)</b><br>(.*?<)/div>', html)
        if section:
            return self.findallbyre(r'([^<>]+)<', section, 'politicalmovement')

    def findoccupations(self, html: str):
        section = self.getsection('(?s)Hoofdfuncties/beroepen[^<>]*', html)
        if section:
            return self.findallbyre(r'(?s)"opsomtekst">(.*?)[,<]', section, 'occupation')

    def findpositions(self, html: str):
        section = self.getsection('(?s)Hoofdfuncties/beroepen[^<>]*', html)
        if section:
            return self.findallbyre(r'(?s)"opsomtekst">(.*?)[,<]', section, 'position')

    def findemployers(self, html: str):
        section = self.getsection('(?s)Hoofdfuncties/beroepen[^<>]*', html)
        if section:
            return self.findallbyre(r'(?s)"opsomtekst">(.*?)[,<]', section, 'employer', alt=['university'])


class AmericanArtAnalyzer(Analyzer):
    def setup(self):
        self.dbproperty = 'P1795'
        self.dbid = None
        self.dbname = 'Smithsonian American Art Museum'
        self.urlbase = 'https://americanart.si.edu/collections/search/artist/?id={id}'
        self.hrtre = '</h1>(.*?)<dt class="field--label visually-hidden">'
        self.language = 'en'

    def findnames(self, html) -> List[str]:
        section = self.findallbyre(r'(?s)>Name</dt>(.*?)</dd>', html) \
            + self.findallbyre(r'(?s)>Also Known as</dt>(.*?)</dd>', html)
        return self.findallbyre(r'(?s)>([^<>]+)<', '\n'.join(section))

    def findlongtext(self, html: str):
        return self.findbyre(r'(?s)<div class="body">(.*?)</div>', html)

    def findbirthplace(self, html: str):
        section = self.findbyre(r'(?s)Born</dt>.*?<span>(.*?)</span>', html)
        if section:
            return self.findbyre(r'(.*)', self.TAGRE.sub('', section).strip(), 'city')

    def finddeathplace(self, html: str):
        section = self.findbyre(r'(?s)Died</dt>.*?<span>(.*?)</span>', html)
        if section:
            return self.findbyre(r'(.*)', self.TAGRE.sub('', section).strip(), 'city')

    def findbirthdate(self, html: str):
        return self.findbyre(r'(?s)born[^<>\-]+?(\d+)\s*[\-<]', html)

    def finddeathdate(self, html: str):
        return self.findbyre(r'(?s)died[^<>]+?(\d+)\s*<', html)

    def findworkplaces(self, html: str):
        section = self.findbyre(r'(?s)Active in</dt>.*?<ul>(.*?)</ul>', html)
        if section:
            return self.findallbyre(r'(.*)', self.TAGRE.sub('', section), 'city')

    def findnationalities(self, html: str):
        section = self.findbyre(r'(?s)Nationalities</dt>(.*?)</dd>', html)
        if section:
            return self.findallbyre(r'>([^<>]+)<', section, 'country')

    def findincollections(self, html: str):
        return ['Q1192305']


class EmloAnalyzer(Analyzer):
    def setup(self):
        self.dbproperty = 'P1802'
        self.dbid = 'Q44526767'
        self.dbname = 'Early Modern Letters Online'
        self.urlbase = 'http://emlo.bodleian.ox.ac.uk/profile/person/{id}'
        self.hrtre = '(<div id="details">.*?>)Catalogue Statistics</h3>'
        self.language = 'en'

    def findnames(self, html) -> List[str]:
        result = self.findallbyre(r'<h2>([^<>]*),', html)
        section = self.findbyre(
            r'(?s)<dt>Alternative names</dt>\s*<dd>(.*?)</dd>', html)
        if section:
            result += self.findallbyre(r'([^<>;]+)', section)
        return result

    def finddescription(self, html: str):
        return self.findbyre(r'(?s)<dt>Titles or roles</dt>\s*<dd>(.*?)</dd>', html)

    def findlongtext(self, html: str):
        parts = [self.findbyre(r'(?s)<dt>Titles or roles</dt>\s*<dd>(.*?)</dd>', html) or ''] + \
                self.findallbyre(r'(?s)<div class="relations">(.*?)</div>', html)
        return '\n'.join(parts)

    def findoccupations(self, html: str):
        section = self.findbyre(r'(?s)<dt>Titles or roles</dt>\s*<dd>(.*?)</dd>', html)
        if section:
            return self.findallbyre(r'([^;<>,]*)', section.replace('and', ','), 'occupation')

    def findbirthdate(self, html: str):
        return self.findbyre(r'(?s)<dt>Date of birth</dt>\s*<dd>(\d+)', html)

    def finddeathdate(self, html: str):
        return self.findbyre(r'(?s)<dt>Date of death</dt>\s*<dd>(\d+)', html)

    def findmemberships(self, html: str):
        section = self.findbyre(r'(?s)<dt>Member of</dt>\s*<dd>(.*?)</dd>', html)
        if section:
            return self.findallbyre(r'(?s)>([^<>]*)<', section, 'organization')

    def findsiblings(self, html: str):
        section = self.findbyre(r'(?s)<dt>Sibling of</dt>\s*<dd>(.*?)</dd>', html)
        if section:
            return self.findallbyre(r'(?s)>([^<>]*)</a>', section, 'person')

    def findmixedrefs(self, html: str):
        return self.finddefaultmixedrefs(html, includesocial=False)


class NpgPersonAnalyzer(Analyzer):
    def setup(self):
        self.dbproperty = 'P1816'
        self.dbid = None
        self.dbname = 'National Portrait Gallery'
        self.urlbase = 'https://www.npg.org.uk/collections/search/person/{id}'
        self.hrtre = "(<h1.*)<div class='view-results-options'>"
        self.language = 'en'

    def finddescription(self, html: str):
        return self.findbyre(r"<span class='largistText'>(.*?)<", html)

    def findnames(self, html) -> List[str]:
        return [self.findbyre(r'<title>(.*?)[-<]', html)]

    def findinstanceof(self, html: str):
        return 'Q5'

    def findoccupations(self, html: str):
        return self.findallbyre(r'/collections/search/group/\d+/([^\'"\s]*)', html, 'occupation')

    def findbirthdate(self, html: str):
        return self.findbyre(r"<span class='largistText'>[^<>]*\((\d+)-", html)

    def finddeathdate(self, html: str):
        return self.findbyre(r"<span class='largistText'>[^<>]*-(\d+)\)", html)

    def findmixedrefs(self, html: str):
        return self.finddefaultmixedrefs(html)


class GenealogicsAnalyzer(Analyzer):
    def setup(self):
        self.dbproperty = 'P1819'
        self.dbid = 'Q19847326'
        self.dbname = 'genealogics.org'
        self.urlbase = 'http://www.genealogics.org/getperson.php?personID={id}&tree=LEO'
        self.hrtre = '(<ul class="nopad">.*?)<!-- end info -->'
        self.language = 'en'

    def prepare(self, html: str):
        return html.replace('&nbsp;', ' ').replace('&nbsp', ' ')

    def getvalue(self, field, html, dtype=None):
        return self.findbyre(
            r'(?s)"fieldname">\s*{}\s*</span></td>\s*<td[^<>]*>(?:<[^<>]*>)*(.+?)<'
            .format(field), html, dtype)

    def getallvalues(self, field, html, dtype=None):
        return self.findallbyre(
            r'(?s)"fieldname">\s*{}\s*</span></td>\s*<td[^<>]*>(?:<[^<>]*>)*(.+?)<'
            .format(field), html, dtype)

    def getfullvalue(self, field, html, dtype=None):
        return self.findbyre(
            r'(?s)"fieldname">\s*{}\s*</span></td>\s*<td[^<>]*>(.*?)</td>'
            .format(field), html, dtype)

    def getsecondvalue(self, field, html, dtype=None):
        section = self.findbyre(r'(?s)"fieldname">(\s*{}\s*</span>.*?)</tr>'
                                .format(field), html)
        if section:
            return self.findbyre(r'<td.*?</td>\s*<td[^<>]*>(?:<[^<>]*>)*([^<>]*?)<', section, dtype)

    def findnames(self, html) -> List[str]:
        return [
            self.findbyre(r'<title>([^<>]*):', html),
            self.findbyre(r'name="Keywords" content="(.*?)"', html),
            self.findbyre(r'name="Description" content="([^"]*):', html),
            self.findbyre(r'<h1[^<>]*>(.*?)<', html)
        ]

    def findlongtext(self, html: str):
        return self.findbyre(r'(?s)<ul class="nopad">(.*)<td class="databack">', html)

    def findinstanceof(self, html: str):
        return 'Q5'

    def findbirthdate(self, html: str):
        result = self.getvalue('Born', html)
        if result and 'abt' not in result.lower():
            return result

    def findbirthplace(self, html: str):
        return self.getsecondvalue('Born', html, 'city')

    def findbaptismdate(self, html: str):
        return self.getvalue('Christened', html)

    def findgender(self, html: str):
        return self.getvalue('Gender', html, 'gender')

    def findnationality(self, html: str):
        return self.getvalue('Lived In', html, 'country')

    def findoccupations(self, html: str):
        return [self.getvalue('Occupation', html, 'occupation')]

    def finddeathdate(self, html: str):
        result = self.getvalue('Died', html)
        if result and 'abt' not in result.lower():
            return result

    def finddeathplace(self, html: str):
        return self.getsecondvalue('Died', html, 'city')

    def findfather(self, html: str):
        return self.getvalue('Father', html, 'person')

    def findmother(self, html: str):
        return self.getvalue('Mother', html, 'person')

    def findchildren(self, html: str):
        sections = self.findallbyre(r'(?s)>Children[^<>]*<.*?(<table.*?</table>)', html)
        result = []
        for section in sections:
            result += self.findallbyre(r'>([^<>]*)</a>', section, 'person')
        return result

    def findsiblings(self, html: str):
        sections = self.findallbyre(r'(?s)>Siblings<.*?(<table.*?</table>)', html)
        result = []
        for section in sections:
            result += self.findallbyre(r'>([^<>]*)</a>', section, 'person')
        return result

    def findspouses(self, html: str):
        return self.getallvalues(r'Family(?: \d+)?', html, 'person')

    def findburialplace(self, html: str):
        return self.getsecondvalue('Buried', html, 'cemetary')

    def findsources(self, html: str):
        section = self.findbyre(r'(?s)(<span class="fieldname">Source.*?)</table>', html)
        if section:
            return self.findallbyre(r'~([^<>]*)\.', section, 'source')


class PssBuildingAnalyzer(Analyzer):
    def setup(self):
        self.dbproperty = 'P1838'
        self.dbid = None
        self.dbname = 'PSS-archi'
        self.urlbase = 'http://www.pss-archi.eu/immeubles/{id}.html'
        self.hrtre = '<table class="idtable">(.*?)</table>'
        self.language = 'fr'

    def finddescription(self, html: str):
        return self.findbyre(r'(?s)<div id="infos">.*?<p>(.*?)</?p>', html)

    def findnames(self, html) -> List[str]:
        return [self.findbyre(r'(?s)<h1 id="nom_immeuble">(.*?)<', html)]

    def findlongtext(self, html: str):
        return self.findbyre(r'(?s)<div id="infos">(.*?)</div>', html)

    def findinstanceof(self, html: str):
        return 'Q41176'

    def findcountry(self, html: str):
        return self.findbyre(r'<th>Pays</th>.*?>([^<>]+)</a>', html, 'country')

    def findadminloc(self, html: str):
        return self.findbyre(r'<th>Commune</th>.*?>([^<>]+)</a>', html, 'commune')

    def findaddress(self, html: str):
        result = self.findbyre(r'<th>Adresse[^<>]*?</th>.*?td>(.+?)</td>', html)
        if result:
            result = self.TAGRE.sub(' ', result)
            return result

    def findcoords(self, html: str):
        return self.findbyre(r'<th>Coordonn[^<>]+es</th>.*?>([^<>]+)</td>', html)

    def findinception(self, html: str):
        return self.findbyre(r'<th>Ann[^<>]*e</th>.*?td>(.*?)<', html)

    def findarchitects(self, html: str):
        archilist = self.findbyre(r'<th>Architecte\(s\).*?<ul(.*?)</ul>', html)
        if archilist:
            return self.findallbyre(r'<li>(?:<a[^<>]+>)?([^<>]+)</', archilist, 'architect')

    def findheights(self, html: str):
        return [self.findbyre(r'<th>Hauteur du toit</th>.*?span>([^<>]+)<', html)]


class CerlAnalyzer(Analyzer):
    def setup(self):
        self.dbproperty = 'P1871'
        self.dbid = None
        self.dbname = 'CERL Thesaurus'
        self.urlbase = 'https://data.cerl.org/thesaurus/{id}'
        self.hrtre = '(<h3.*?)<h3>Other Formats'
        self.language = 'en'

    def getvalue(self, field, html, dtype=None):
        return self.findbyre(
            r'(?s)>{}</span><span[^<>]*>(?:<[^<>]*>)?([^<>]*)</'
            .format(field), html, dtype)

    def getvalues(self, field, html, dtype=None, link=False) -> List[str]:
        section = self.findbyre(r'(?s)>{}</span>(.*?>)[^<>]+</span><span'
                                .format(field), html) or \
                  self.findbyre(fr'(?s)>{field}</span>(.*)', html)
        if section:
            return self.findallbyre(r'<{}[^<>]*>(.*?)[\(<]'
                                    .format('a ' if link else 'span'),
                                    section, dtype)
        return []

    def findnames(self, html) -> List[str]:
        return self.getvalues('Heading', html) \
            + self.getvalues('Variant Name', html)

    def findlongtext(self, html: str):
        return '{}\n{}\n{}'.format(
            self.findbyre(r'(?s)<h3>General Note</h3>(.*?)<h3', html) or '',
            self.findbyre(r'(?s)<h3>More Information</h3>(.*?)<h3', html) or '',
            self.findbyre(r'(?s)<h3>Related Entries</h3>(.*?)<h3', html) or ''
        )

    def findbirthdate(self, html: str):
        section = self.getvalue('Biographical Data', html)
        if section:
            return self.findbyre(r'(.*) -', section)

    def finddeathdate(self, html: str):
        section = self.getvalue('Biographical Data', html)
        if section:
            return self.findbyre(r'- (.*)', section)

    def findbirthplace(self, html: str):
        values = self.getvalues('Place of Birth', html, 'city', link=True)
        if values:
            return values[0]

        return self.getvalue('Place of Birth', html, 'city')

    def finddeathplace(self, html: str):
        values = self.getvalues('Place of Death', html, 'city', link=True)
        if values:
            return values[0]

        return self.getvalue('Place of Death', html, 'city')

    def findoccupations(self, html: str):
        sections = self.getvalues('Profession / Occupation', html) + \
                   self.getvalues('Activity', html) + \
                   self.getvalues('Intellectual Responsibility', html)
        result = []
        for section in sections:
            result += self.findallbyre(r'([^;,]*)', section, 'occupation')
        return result

    def findmixedrefs(self, html: str):
        return self.finddefaultmixedrefs(html)

    def findnationality(self, html: str):
        return self.getvalue('Country', html, 'country')

    def findworkplaces(self, html: str):
        return self.getvalues('Place of Activity', html, 'city', link=True)

    def findchildren(self, html: str):
        return self.getvalues('Child', html, 'person', link=True)


class MetallumAnalyzer(Analyzer):
    def setup(self):
        self.dbproperty = 'P1952'
        self.dbid = 'Q938726'
        self.dbname = 'Encyclopaedia Metallum'
        self.urlbase = 'https://www.metal-archives.com/bands//{id}'
        self.hrtre = '<h1 class="band_name">(.*?<dl.*?)</div>'
        self.language = 'en'

    def getvalue(self, field, html, dtype=None, alt=None):
        return self.findbyre(
            r'(?s)<dt>{}:</dt>\s*<dd[^<>]*>(?:<[^<>]*>)*(.+?)(?:<[^<>]*>)*</dd>'
            .format(field), html, dtype, alt=alt)

    def findinstanceof(self, html: str):
        return 'Q215380'

    def findnames(self, html) -> List[str]:
        return self.findallbyre('bandName = "(.*?)"', html) \
            + self.findallbyre('<h1[^<>]*>(?:<[^<>]*>)*(.*?)<', html)

    def findlongtext(self, html: str):
        return self.findbyre('(?s)<div class="band_comment[^<>]*>(.*?)</?div', html)

    def findorigcountry(self, html: str):
        return self.getvalue('Country of origin', html, 'country')

    def findformationlocation(self, html: str):
        return self.getvalue('Location', html, 'city')

    def findinception(self, html: str):
        return self.getvalue('Formed in', html)

    def findfloruit(self, html: str):
        return self.getvalue('Years active', html)

    def findgenre(self, html: str):
        return self.getvalue('Genre', html, 'music-genre', alt=['genre'])

    def findlabels(self, html: str):
        return [self.getvalue('Last label', html, 'label')]

    def findparts(self, html: str):
        section = self.findbyre('(?s)<div id="band_tab_members_all">(.*?)</table>', html)
        if section:
            return self.findallbyre('<a href=[^<>]*>(.*?)<', section, 'musician')


class DiscogsAnalyzer(Analyzer):
    def setup(self):
        self.dbproperty = 'P1953'
        self.dbid = 'Q504063'
        self.dbname = 'Discogs'
        self.urlbase = 'https://www.discogs.com/artist/{id}'
        self.hrtre = '<div class="profile">(.*?)<div class="right">'
        self.language = 'en'

    def finddescriptions(self, html: str):
        return [
            self.findbyre(r'(?s)"description": "(.*?)"', html),
            self.findbyre(r'(?s)"description": "(.*?)\.', html)
        ]

    def findnames(self, html) -> List[str]:
        result = [self.findbyre(r'<h1[^<>]*>(.*?)<', html)]
        section = self.findbyre(
            r'(?s)<div class="head">Variations:</div>(.*?)<!-- /content -->',
            html)
        if section:
            result += self.findallbyre(r'>([^<>]*)</a>', section)
        result.append(self.findbyre(r'(?s)<div class="head">Real Name:</div>.*?<div class="content">(.*?)</div>', html))
        section = self.findbyre(r'(?s)<div class="head">Aliases:</div>.*?<div class="content">(.*?)</div>', html)
        if section:
            result += self.findallbyre(r'>([^<>]*)</a>', section)
        return result

    def findlongtext(self, html: str):
        return self.findbyre(r'(?s)<div class="profile">(.*?)<!-- end profile -->', html)

    def findparts(self, html: str):
        section = self.findbyre(r'(?s)Members:</div>(.*?<a.*?)</div', html)
        if section:
            return self.findallbyre(r'>([^<>]+)</[sa]>', section, 'musician')
        return None

    def findmemberships(self, html: str):
        section = self.findbyre(r'(?s)In Groups:</div>(.*?<a.*?)</div', html)
        if section:
            return self.findallbyre(r'>([^<>]+)</[sa]>', section, 'group')
        return None

    def findoccupations(self, html: str):
        result = []
        section = self.findbyre(r'(?s)id="profile">(.*?)<', html)
        if section:
            parts = section.split(' and ')
            for part in parts[:5]:
                result += self.findallbyre(r'[\w\s\-]+', part, 'occupation', alt=['music-occupation'])
        return result

    def findinstruments(self, html: str):
        result = []
        section = self.findbyre(r'(?s)id="profile">(.*?)<', html)
        if section:
            parts = section.split(' and ')
            for part in parts[:5]:
                result += self.findallbyre(r'[\w\s\-]+', part, 'instrument')
        return result

    def findbirthdate(self, html: str):
        result = self.findbyre(r'born on (\d+\w{2} of \w+ \d{4})', html)
        if result:
            return self.findbyre(r'(\d+)', result) + self.findbyre(r'of( .*)',
                                                                   result)

        return (
            self.findbyre(r'born on (\w+ \w+ \w+)', html)
            or self.findbyre(r'Born\s*:?\s*(\d+ \w+ \d+)', html)
            or self.findbyre(r'Born\s*:?\s*(\w+ \d+, \d+)', html)
        )

    def findbirthplace(self, html: str):
        return self.findbyre(r'[bB]orn (?:on|:) .*? in ([\w\s]+)', html, 'city')

    def finddeathdate(self, html: str):
        return self.findbyre(r'died on (\w+ \w+ \w+)', html) or \
               self.findbyre(r'Died\s*:?\s*(\d+ \w+ \d+)', html) or \
               self.findbyre(r'Died\s*:?\s*(\w+ \d+, \d+)', html)

    def finddeathplace(self, html: str):
        return self.findbyre(r'[dD]ied (?:on|:) .*? in ([\w\s]+)', html, 'city')

    def findschools(self, html: str):
        return [self.findbyre(r'[eE]ducated at ([\w\s\']+)', html, 'university')]

    def findmixedrefs(self, html: str):
        section = self.findbyre(r'(?s)<div class="head">Sites:</div>\s*<div[^<>]*>(.*?)</div>', html) or \
                  self.findbyre(r'(?s)"sameAs": \[(.*?)\]', html)
        if section:
            return self.finddefaultmixedrefs(section)

    def findsiblings(self, html: str):
        section = self.findbyre(r'(?:[bB]rother|[sS]ister) of (<[^<>]*>(?:[^<>]|<[^<>]*>)*?)(?:\.|</div>)', html)
        if section:
            return self.findallbyre(r'>(.*?)<', section, 'person')


class ArchivesDuSpectacleAnalyzer(Analyzer):
    def setup(self):
        self.dbproperty = 'P1977'
        self.dbid = 'Q80911465'
        self.dbname = 'Les Archives du spectacle'
        self.urlbase = 'https://www.lesarchivesduspectacle.net/?IDX_Personne={id}'
        self.hrtre = '(<h1.*?)<script>'
        self.language = 'fr'

    def findinstanceof(self, html: str):
        return self.findbyre(r"itemtype='http://schema.org/(.*?)'", html, 'instanceof')

    def findnames(self, html) -> List[str]:
        return self.findallbyre(r'(?s)itemprop="\w*[nN]ame">(.*?)<', html)

    def finddescription(self, html: str):
        return self.findbyre(r"(?s)<div class='fiche__infos'>(.*?)</div>", html)

    def findgender(self, html: str):
        return self.findbyre(r"meta itemprop='gender' content='(.*?)'", html, 'gender')

    def findbirthdate(self, html: str):
        return self.findbyre(r'datetime="([\w-]*)" itemprop="birthDate"', html) or\
            self.findbyre(r'(?s)birthDate">(.*?)[<\(]', html)

    def finddeathdate(self, html: str):
        return self.findbyre(r'datetime="([\w-]*)" itemprop="deathDate"', html) or\
            self.findbyre(r'(?s)deathDate">(.*?)<', html)

    def findoccupations(self, html: str):
        return self.findallbyre(r'"metier-(.*?)"', html, 'theater-occupation', alt=['occupation']) +\
            self.findallbyre(r'(?s)-metier">(.*?)<', html, 'theater-occupation', alt=['occupation'])


class ItalianPeopleAnalyzer(Analyzer):
    def setup(self):
        self.dbproperty = 'P1986'
        self.dbid = 'Q1128537'
        self.dbname = 'Dizionario Biografico degli Italiani'
        self.urlbase = 'http://www.treccani.it/enciclopedia/{id}_(Dizionario-Biografico)'
        self.hrtre = '<!-- module article full content -->(.*?)<!-- end module -->'
        self.language = 'it'

    def finddescription(self, html: str):
        return self.findbyre(r'<meta name="description" content="(.*?)"', html)

    def findnames(self, html) -> List[str]:
        return [self.findbyre(r'(?s)<h1[^<>]*>(.*?)<', html)]

    def findlongtext(self, html: str):
        return self.findbyre(r'(?s)<!-- module article full content -->(.*?)<!-- end module -->', html)

    def findinstanceof(self, html: str):
        return 'Q5'

    def findlastname(self, html: str):
        return self.findbyre(r'<strong>(.*?)<', html, 'lastname')

    def findfirstname(self, html: str):
        return self.findbyre(r'<span class="sc">(.*?)<', html, 'firstname') or \
               self.findbyre(r'<span class="sc">\s*([\w\-]+)', html, 'firstname')

    def findbirthplace(self, html: str):
        return self.findbyre(r"[nN]acque (?:nell)?a (.*?)(?:,|\.| il| l'| l&#039;| nel)", html, 'city')

    def findbirthdate(self, html: str):
        return self.findbyre(r"[nN]acque.*? (?:il|l'|l&#039;)\s*(\d+ \w+\.? \d+)", html)

    def finddeathplace(self, html: str):
        return self.findbyre(r"[mM]or(?:ì|&igrave;) (?:nell)?a (.*?)(?:,|\.| il| l'| l&#039; |nel)", html, 'city')

    def finddeathdate(self, html: str):
        return self.findbyre(r"[mM]or(?:ì|&igrave;) .*? (?:il|l'|l&#039;)\s*(\d+ \w+\.? \d+)", html)


class DelargeAnalyzer(Analyzer):
    def setup(self):
        self.dbproperty = 'P1988'
        self.dbid = 'Q20056651'
        self.dbname = 'Le Delarge'
        self.urlbase = 'https://www.ledelarge.fr/{id}'
        self.hrtre = '(<h1.*?)</div>'
        self.language = 'fr'
        self.escapehtml = True

    def findlongtext(self, html: str):
        result = self.findbyre(r'(?s)Présentation[^<>]*</span>\s*<span[^<>]*>(.*?)</span>', html)
        if result:
            result = [result]
        else:
            result = []
        result += self.findallbyre(r'<p align="justify">(.*?)</p>', html)
        return '\n'.join(result)

    def findinstanceof(self, html: str):
        return 'Q5'

    def findbirthdate(self, html: str):
        return self.findbyre(r'née? le (\d+ \w+ \d+)', html) or \
               self.findbyre(r'née? en (\d+)', html)

    def findbirthplace(self, html: str):
        return self.findbyre(r'née? [\w\s]+ (?:à|en) (.*?)[;<>]', html, 'city')

    def finddeathdate(self, html: str):
        return self.findbyre(r'([^<>;,]*), meurte? ', html)

    def finddeathplace(self, html: str):
        return self.findbyre(r'meurte? (?:à|en) (.*?)\.?[;<]', html, 'city')

    def findoccupations(self, html: str):
        section = self.findbyre(r'(?s)Technique\(s\)\s*:\s*</span>(.*?)<', html)
        if not section:
            section = self.findbyre(r'(?s)Type\(s\)\s*:\s*</span>(.*?)<', html)
        if section:
            return self.findallbyre(r'(\w+)', section, 'occupation')


class HalensisAnalyzer(Analyzer):
    def setup(self):
        self.dbproperty = 'P2005'
        self.dbid = 'Q20680681'
        self.dbname = 'Catalogus Professorum Halensis'
        self.urlbase = 'http://www.catalogus-professorum-halensis.de/{id}.html'
        self.hrtre = '(<h1.*?)<!-- Ende -->'
        self.language = 'de'

    def findnames(self, html) -> List[str]:
        result = self.findallbyre(r'<title>(.*?)<', html) \
            + self.findallbyre(r'(?s)<h[12][^<>]*>(.*?)<', html)
        return [r.replace('\\n', ' ') for r in result]

    def findlongtext(self, html: str):
        return self.findbyre(r'(?s)<!-- custom html code -->(.*?)<!-- Ende -->', html)

    def findbirthdate(self, html: str):
        return self.findbyre(r'geboren:(?:<[^<>]*>)*([^<>]*\d{4})', html)

    def findbirthplace(self, html: str):
        return self.findbyre(r'gestorben:(?:<[^<>]*>)*[^<>]*\d{4}([^<>]*)', html, 'city')

    def finddeathdate(self, html: str):
        return self.findbyre(r'gestorben:(?:<[^<>]*>)*([^<>]*\d{4})', html)

    def finddeathplace(self, html: str):
        return self.findbyre(r'geboren:(?:<[^<>]*>)*[^<>]*\d{4}([^<>]*)', html, 'city')

    def findreligion(self, html: str):
        return self.findbyre(r'Konfession:(?:<[^<>]*>)*([^<>]+)', html, 'religion')

    def findemployers(self, html: str):
        return ['Q32120']


class AcademiaeGroninganaeAnalyzer(Analyzer):
    def setup(self):
        self.dbproperty = 'P2016'
        self.dbid = 'Q20730803'
        self.dbname = 'Catalogus Professorum Academiae Groninganae'
        self.urlbase = 'https://hoogleraren.ub.rug.nl/hoogleraren/{id}'
        self.hrtre = '(<h1.*?)<!-- OVERIGE -->'
        self.language = 'nl'

    def getentry(self, naam, html, dtype=None):
        return self.findbyre(fr'(?s){naam}<.*?>([^<>]*)</div>', html, dtype)

    def finddescription(self, html: str):
        return self.findbyre(r'<h1>(.*?)<', html)

    def findnames(self, html) -> List[str]:
        return [self.findbyre(r'<h1>(.*?)[,<]', html)]

    def findinstanceof(self, html: str):
        return 'Q5'

    def findlastname(self, html: str):
        return self.getentry('Achternaam', html, 'lastname')

    def findfirstname(self, html: str):
        return self.getdata('firstname', self.getentry('Voornamen en tussenvoegsel', html).split()[0].strip(','))

    def findgender(self, html: str):
        return self.getentry('Geslacht', html, 'gender')

    def findbirthdate(self, html: str):
        return self.getentry('Geboortedatum', html)

    def findbirthplace(self, html: str):
        return self.getentry('Geboorteplaats', html, 'city')

    def finddeathdate(self, html: str):
        return self.getentry('Overlijdensdatum', html)

    def finddeathplace(self, html: str):
        return self.getentry('Overlijdensplaats', html, 'city')

    def findmixedrefs(self, html: str):
        return self.finddefaultmixedrefs(html)

    def findoccupations(self, html: str):
        return [self.getentry('Functie', html, 'occupation')]

    def findemployers(self, html: str):
        return ['Q850730']

    def finddegrees(self, html: str):
        return [
            self.getentry('Graad', html, 'degree'),
            self.getentry('Titels', html, 'degree')
        ]

    def findschools(self, html: str):
        return [self.getentry('Universiteit promotie', html, 'university')]


class UlsterAnalyzer(Analyzer):
    def setup(self):
        self.dbproperty = 'P2029'
        self.dbid = None
        self.dbname = 'Dictionary of Ulster Biography ID'
        self.urlbase = 'http://www.newulsterbiography.co.uk/index.php/home/viewPerson/{id}'
        self.hrtre = '(<h1.*?)<form'
        self.language = 'en'

    def finddescription(self, html: str):
        return self.findbyre(r'(?s)<div id="person_details">.*?</table>(.*?)<', html)

    def findnames(self, html) -> List[str]:
        return [self.findbyre(r'<h1[^<>]*>(.*?)[<\(]', html)]

    def findlongtext(self, html: str):
        return self.findbyre(r'(?s)<div id="person_details">(.*?)</div>', html)

    def findinstanceof(self, html: str):
        return 'Q5'

    def findbirthdate(self, html: str):
        return self.findbyre(r'(?s)<strong>\s*Born:.*?<td>(.*?)</td>', html)

    def finddeathdate(self, html: str):
        return self.findbyre(r'(?s)<strong>\s*Died:.*?<td>(.*?)</td>', html)

    def findoccupations(self, html: str):
        section = self.findbyre(r'(?s)<span class="person_heading_profession">(.*?)</span>', html)
        if section:
            section = section.split('and')
            result = []
            for sectionpart in section:
                result += self.findallbyre(r'([\w\s]+)', sectionpart, 'occupation')
            return result


class ResearchGateAnalyzer(Analyzer):
    def setup(self):
        self.dbproperty = 'P2038'
        self.dbid = 'Q754454'
        self.dbname = 'ResearchGate'
        self.urlbase = 'https://www.researchgate.net/profile/{id}'
        self.hrtre = r'<h2[^<>]*>(?:<[^<>]*>|\s)*About(<.*?<h2'
        self.language = 'en'

    def findinstanceof(self, html: str):
        return self.findbyre(r'".type":\s*"(.*?)"', html, 'instanceof')

    def findnames(self, html) -> List[str]:
        return self.findallbyre(r'"name":\s*"(.*?)"', html)

    def finddescriptions(self, html: str):
        return self.findallbyre('content="(.*?)"', html)

    def findfirstname(self, html: str):
        return self.findbyre('first_name" content="(.*?)"', html, 'firstname')

    def findlastname(self, html: str):
        return self.findbyre('last_name" content="(.*?)"', html, 'lastname')

    def findgender(self, html: str):
        return self.findbyre('gender" content="(.*?)"', html, 'gender')

    def findworkfields(self, html: str):
        return self.findallbyre('href="topic/[^"]*>(.*?)<', html, 'subject')

    def findemployers(self, html: str):
        result = self.findallbyre(r'institution[^"<>]*">(?:<[^<>]*>|\s)*(.*?)<', html, 'employer', alt=['university'])
        section = self.findbyre('(?s)>(.*?>)Publications<', html)
        if section:
            result += self.findallbyre('<b>(.*?)<', section, 'employer', alt=['university'])
        return result

    def findoccupations(self, html: str):
        return self.findallbyre(r'"jobTitle":\s*"(.*?)"', html, 'occupation') +\
            self.findallbyre(r'[pP]osition(?:<[^<>]*>\s)*?([^<>]*?)</', html, 'occupation')


class NgvAnalyzer(Analyzer):
    def setup(self):
        self.dbproperty = 'P2041'
        self.dbid = None
        self.dbname = 'National Gallery of Victoria'
        self.urlbase = 'https://www.ngv.vic.gov.au/explore/collection/artist/{id}/'
        self.hrtre = '(<h1.*?)<h2'

    def findinstanceof(self, html: str):
        return 'Q5'

    def findnames(self, html) -> List[str]:
        return self.findallbyre(r'rd-card__info">(.*?)<', html)

    def findlongtext(self, html: str):
        return self.findbyre(r'(?s)<dt>Lived/worked</dt>\s*<dd>(.*?)</dd>', html)

    def findbirthdate(self, html: str):
        return self.findbyre(r'(?s)<dt>Born</dt>\s*<dd>((?:\d+ \w+ )?\d+)', html)

    def findbirthplace(self, html: str):
        return self.findbyre(r'(?s)<dt>Born</dt>\s*<dd>(?:\d+ \w+ )?\d+([^<>]*)', html, 'city')

    def finddeathdate(self, html: str):
        return self.findbyre(r'(?s)<dt>Died</dt>\s*<dd>((?:\d+ \w+ )?\d+)', html)

    def finddeathplace(self, html: str):
        return self.findbyre(r'(?s)<dt>Died</dt>\s*<dd>(?:\d+ \w+ )?\d+([^<>]*)', html, 'city')

    def findnationality(self, html: str):
        return self.findbyre(r'(?s)<dt>Nationality</dt>\s*<dd>(.*?)<', html, 'country')

    def findincollections(self, html: str):
        return ['Q1464509']


class JukeboxAnalyzer(Analyzer):
    def setup(self):
        self.dbproperty = 'P2089'
        self.dbid = 'Q1362143'
        self.dbname = 'National Jukebox'
        self.urlbase = 'https://www.loc.gov/jukebox/artists/detail/id/{id}'
        self.urlbase = None  # 503 forbidden
        self.hrtre = '<h1.*?</table>'
        self.language = 'en'

    def findnames(self, html) -> List[str]:
        return [self.findbyre(r'(?s)<h1[^<>]*>(.*?)<', html)]

    def findinstanceof(self, html: str):
        return 'Q5'

    def findoccupations(self, html: str):
        sections = self.findallbyre(r'(?s)<tr>(.*?)</tr>', html)
        result = []
        for section in sections:
            result += self.findbyre(r'(?s)<td>.*?<td>(.*?)<', section, 'occupation')
        return result

    def findmixedrefs(self, html: str):
        return self.finddefaultmixedrefs(html)


class FastAnalyzer(Analyzer):
    def setup(self):
        self.dbproperty = 'P2163'
        self.dbid = 'Q3294867'
        self.dbname = 'FAST'
        self.urlbase = 'https://experimental.worldcat.org/fast/{id}/'
        self.hrtre = '>Information about the Resource</h4>(.*?)<h4'
        self.language = 'en'
        self.escapehtml = True

    def findnames(self, html) -> List[str]:
        result = []
        section = self.findbyre(
            r'(?s)"skos:prefLabel".*?<ul>(.*?)</ul>', html)
        if section:
            result += self.findallbyre(r'(?s)<li>(.*?)[\(<]', section)

        section = self.findbyre(r'(?s)"skos:altLabel".*?<ul>(.*?)</ul>', html)
        if section:
            result += self.findallbyre(r'(?s)<li>(.*?)[\(<]', section)
        result = [x.split('--')[-1] for x in result]
        return [', '.join(x.split(',')[:2]) if ',' in x else x for x in result]

    def findinstanceof(self, html: str):
        return self.findbyre(r'(?s)Type:</a>.*?>([^<>]*)</a>', html, 'instanceof')

    def findfirstname(self, html: str):
        name = self.findbyre(r'(?s)SKOS Preferred Label:</a>.*?<li>(.*?)</li>', html)
        if name:
            return self.findbyre(r',\s*(\w+)', name, 'firstname')

    def findlastname(self, html: str):
        name = self.findbyre(r'(?s)SKOS Preferred Label:</a>.*?<li>(.*?)</li>', html)
        if name:
            return self.findbyre(r'(.*?),', name, 'lastname')


class SvenskFilmAnalyzer(Analyzer):
    def setup(self):
        self.dbproperty = 'P2168'
        self.dbid = 'Q1139587'
        self.dbname = 'Svensk Film Database'
        self.urlbase = 'http://www.svenskfilmdatabas.se/sv/item/?type=person&itemid={id}'
        self.hrtre = '(<table class="information-table">.*?)<h3>Relaterat</h3>'
        self.language = 'sv'

    def finddescriptions(self, html: str):
        description = self.findbyre(r'(?s)<h3>Beskrivning</h3>\s*<p>(.*?)<', html)
        if description:
            return [
                description,
                description.split('.')[0],
                '.'.join(description.split('.')[:2]),
                '.'.join(description.split('.')[:3]),
            ]

    def findnames(self, html) -> List[str]:
        result = [self.findbyre(r'<h1[^<>]*>(.*?)<', html)]
        section = self.findbyre(
            r'(?s)<th>Alternativnamn</th>\s*<td>(.*?)</td>', html)
        if section:
            return result + self.findallbyre(r'>([^<>]+)<', section)
        return result

    def findlongtext(self, html: str):
        return self.findbyre(r'(?s)<h3>Beskrivning</h3>(.*?)</div>', html)

    def findinstanceof(self, html: str):
        return 'Q5'

    def findoccupations(self, html: str):
        section = self.findbyre(r'(?s)<h3>Beskrivning</h3>\s*<p>\s*\w+\s*(.*?)[<\.]', html)
        if section:
            result = []
            parts = self.findallbyre(r'([\w\s]+)', section)
            for part in parts:
                result += [self.getdata('occupation', subpart) for subpart in part.split(' och ')]
            return ['Q2526255' if r == 'Q3455803' else r for r in result]

    def findnationality(self, html: str):
        return self.findbyre(r'(?s)<h3>Beskrivning</h3>\s*<p>\s*(\w+)', html, 'country')

    def findbirthdate(self, html: str):
        return self.findbyre(r'<time class="person__born" datetime="(.*?)"', html)


class NilfAnalyzer(Analyzer):
    def setup(self):
        self.dbproperty = 'P2191'
        self.dbid = 'Q23023088'
        self.dbname = 'NILF'
        self.urlbase = 'https://www.fantascienza.com/catalogo/autori/{id}'
        self.hrtre = '<p class="bio">(.*?)<br class="clear"/>'
        self.language = 'it'

    def prepare(self, html: str):
        return html.replace('&nbsp;', ' ')

    def findnames(self, html) -> List[str]:
        result = [self.TAGRE.sub('', self.findbyre(r'<h1>(.*?)</h1>', html)
                                 or '')]
        section = self.findbyre(r'(?s)Noto anche como:(.*?)</p>', html)
        if section:
            result += self.findallbyre(r'(\w[\w\s]+)',
                                       self.TAGRE.sub('', section))
        return result

    def findlongtext(self, html: str):
        return self.findbyre(r'(?s)<p class="bio">(.*?)<div id="right">', html)

    def findnationality(self, html: str):
        return self.findbyre(r'Nazionalit.agrave.:<[^<>]*>(.*?)<', html, 'country')

    def findlanguagesspoken(self, html: str):
        return [self.findbyre(r'Lingua:<[^<>]*>(.*?)<', html, 'language')]

    def findlastname(self, html: str):
        return self.findbyre(r'<span class="cognome">(.*?)<', html, 'lastname')

    def findbirthdate(self, html: str):
        return self.findbyre(r'nato il</span>(.*?)<', html)

    def findawards(self, html: str):
        section = self.findbyre(r'(?s)Riconoscimenti:</span>(.*?)</p>', html)
        if section:
            return self.findallbyre(r'(\w[\w\s]+)', self.TAGRE.sub('', section), 'award')


class NgaAnalyzer(Analyzer):
    def setup(self):
        self.dbproperty = 'P2252'
        self.dbid = None
        self.dbname = 'National Gallery of Art'
        self.urlbase = 'https://www.nga.gov/collection/artist-info.{id}.html'
        self.hrtre = '<div class="artist-intro detailheader">(.*?)</div>'
        self.language = 'en'

    def findnames(self, html) -> List[str]:
        section = self.findbyre(
            r'(?s)<dd class="description">(.*?)</dd>', html)
        if section:
            return [self.findbyre(r'<dt class="artist">(.*?)<', html)] \
                + self.findallbyre(r'(\w.+)', section)
        return [self.findbyre(r'<dt class="artist">(.*?)<', html)]

    def findnationality(self, html: str):
        return self.findbyre(r'(?s)<dd class="lifespan">([^<>]+?),', html, 'country')

    def findbirthdate(self, html: str):
        return self.findbyre(r'(?s)<dd class="lifespan">[^<>]+,([^<>]+)-', html)

    def finddeathdate(self, html: str):
        return self.findbyre(r'(?s)<dd class="lifespan">[^<>]+-([^<>\-]+)', html)

    def findincollections(self, html: str):
        return ['Q214867']


class OrsayAnalyzer(Analyzer):
    def setup(self):
        self.dbproperty = 'P2268'
        self.dbid = None
        self.dbname = "Musee d'Orsay"
        self.urlbase = 'http://www.musee-orsay.fr/fr/espace-professionnels/professionnels/' \
                       'chercheurs/rech-rec-art-home/notice-artiste.html?nnumid={id}'
        self.hrtre = '(<h2.*?)<div class="unTiers.notice">'
        self.language = 'fr'

    def finddescription(self, html: str):
        return self.findbyre(r'(?s)<h6>Documentation</h6>(.*?)</div>', html)

    def findlongtext(self, html: str):
        return self.findbyre(r'(?s)<h6>Commentaire</h6>(.*?)<(?:h\d|div)', html)

    def findnames(self, html) -> List[str]:
        section = self.findbyre(r'(?s)(<h2>.*?)</div>', html)
        if section:
            result = self.findallbyre(r'>(.*?)<', section)
            return [r for r in result if ':' not in r]

    def findisinstanceof(self, html: str):
        return 'Q5'

    def findgender(self, html: str):
        return self.findbyre(r'Sexe\s*:\s*(.*?)<', html, 'gender')

    def findbirthdate(self, html: str):
        return self.findbyre(r'Naissance</h6>([^<>,]*?\d{4}[^<>,]*?)[,<]', html)

    def findbirthplace(self, html: str):
        return self.findbyre(r'Naissance</h6>[^,<>]*?,([^<>]*)', html, 'city')

    def finddeathdate(self, html: str):
        return self.findbyre(r'D.c.s</h6>([^<>,]*?\d{4}[^<>,]*?)[,<]', html)

    def finddeathplace(self, html: str):
        return self.findbyre(r'D.c.s</h6>[^,<>]*?,([^<>]*)', html, 'city')

    def findnationality(self, html: str):
        return self.findbyre(r'Nationalit. pr.sum.e</h6>(.*?)<', html, 'country')

    def findoccupations(self, html: str):
        section = self.findbyre(r'(?s)Documentation(</h6>.*?<)[/h]', html)
        return self.findallbyre(r'(?s)>(.*?)<', section, 'occupation')


class ArtHistoriansAnalyzer(Analyzer):
    def setup(self):
        self.dbproperty = 'P2332'
        self.dbid = 'Q17166797'
        self.dbname = 'Dictionary of Art Historians'
        self.urlbase = 'http://arthistorians.info/{id}'
        self.hrtre = '(<h1.*?>)Citation</h2>'
        self.language = 'en'

    def finddescription(self, html: str):
        return self.findbyre(r'name="(?s)dcterms.description" content="(.*?)"', html)

    def findnames(self, html) -> List[str]:
        section = (
            self.findbyre(r'(?s)">Full Name:(.*?clearfix">)', html) or '') \
            + (self.findbyre(r'(?s)">Other Names:(.*?clearfix">)', html) or '')
        return self.findallbyre(r'"field-item .*?">(.*?)<', section)

    def findlongtext(self, html: str):
        return self.findbyre(r'(?s)<div class="field-label">Overview:(.*?)<div class="field-label">', html)

    def findinstanceof(self, html: str):
        return 'Q5'

    def findfirstname(self, html: str):
        return self.findbyre(r'dcterms.title" content="[^<>"]+,\s*([\w\-]+)', html, 'firstname')

    def findlastname(self, html: str):
        return self.findbyre(r'dcterms.title" content="([^<>"]+),', html, 'lastname')

    def findbirthdate(self, html: str):
        return self.findbyre(r'Date Born:.*?>([^<>]+)</span>', html)

    def findnationality(self, html: str):
        return self.findbyre(r'Home Country:.*?>([^<>]+)</', html, 'country')


class CesarAnalyzer(Analyzer):
    def setup(self):
        self.dbproperty = 'P2340'
        self.dbid = None
        self.dbname = 'César'
        self.urlbase = 'http://cesar.org.uk/cesar2/people/people.php?fct=edit&person_UOID={id}'
        self.hrtre = '</H1>(.*?)<H2>'
        self.language = 'en'

    def getvalue(self, field, html, dtype=None):
        return self.findbyre(
            '(?s)<TR><TD[^<>]*keyColumn[^<>]*>[^<>]*{}[^<>]*</TD>[^<>]*<TD[^<>]*valueColumn[^<>]*>(.*?)<'
            .format(field), html.replace('&nbsp;', ' '), dtype)

    def findnames(self, html) -> List[str]:
        return [
            self.findbyre(r"'objectSummary'>(.*?)</B>", html),
            self.findbyre(r"'objectSummary'>(.*?)</I>", html),
            self.getvalue('Pseudonym', html)
        ]

    def findfirstname(self, html: str):
        return self.getvalue('First name', html, 'firstname')

    def findlastname(self, html: str):
        return self.getvalue('Last name', html, 'lastname')

    def findbirthdate(self, html: str):
        return self.getvalue('Birth date', html)

    def finddeathdate(self, html: str):
        return self.getvalue('Death date', html)

    def findgender(self, html: str):
        return self.getvalue('Gender', html, 'gender')

    def findnationality(self, html: str):
        return self.getvalue('Nationality', html, 'country')

    def findoccupations(self, html: str):
        section = self.getvalue('Skills', html)
        if section:
            return self.findallbyre(r'(\w+)', section, 'occupation')


class AgorhaAnalyzer(Analyzer):
    def setup(self):
        self.dbproperty = 'P2342'
        self.dbid = 'Q21994367'
        self.dbname = 'AGORHA'
        self.urlbase = 'http://agorha.inha.fr/inhaprod/ark:/54721/002{id}'
        self.hrtre = '(<h2.*?)<!-- Vue de la notice -->'
        self.language = 'fr'

    def finddescription(self, html: str):
        return self.findbyre(r'name="dcterms.description" content="(.*?)"', html)

    def findnames(self, html) -> List[str]:
        return [self.findbyre(r'(?s)<h2[^<>]*>(.*?)[\(<]', html)]

    def findgender(self, html: str):
        return self.findbyre(r'(?s)>Sexe</th>.*?<td>(.*?)</', html, 'gender')

    def findnationality(self, html: str):
        return self.findbyre(r'(?s)>Nationalit.</th>.*?<td>(.*?)</', html, 'country')

    def findbirthdate(self, html: str):
        result = self.findbyre(r'(?s)>Naissance</th>.*?<td>(.*?)<', html)
        if result and '/' not in result:
            return result

    def finddeathdate(self, html: str):
        result = self.findbyre(r'(?s)>D.c.s</th>.*?<td>(.*?)<', html)
        if result and '/' not in result:
            return result


class StuttgartAnalyzer(Analyzer):
    def setup(self):
        self.dbproperty = 'P2349'
        self.dbid = 'Q21417186'
        self.dbname = 'Stuttgart Database of Scientific Illustrators'
        self.urlbase = 'https://dsi.hi.uni-stuttgart.de/index.php?table_name=dsi&function=details&where_field=id&where_value={id}'
        self.hrtre = 'Details of the item(<.*?</table>)'
        self.language = 'en'
        self.escapehtml = True

    def getvalue(self, field, html, dtype=None):
        return self.findbyre(
            r'<label[^<>]*>\s*{}\s*<.*?"form_input_element">(.*?)<'
            .format(field), html, dtype)

    def getvalues(self, field, html, dtype=None) -> List[str]:
        sections = self.findallbyre(
            r'<label[^<>]*>\s*{}\s*<.*?"form_input_element">(.*?)<'
            .format(field), html)
        result = []
        for section in sections:
            result += self.findallbyre('([^;]*)', section, dtype)
        return result

    def findnames(self, html) -> List[str]:
        return self.getvalues('alt. Names', html)

    def findlongtext(self, html: str):
        return self.getvalue('other', html)

    def findlastname(self, html: str):
        return self.getvalue('Last Name', html, 'lastname')

    def findfirstname(self, html: str):
        return self.getvalue('Given Name', html, 'firstname')

    def findspouse(self, html: str):
        return self.getvalue('Marriage', html, 'person')

    def findchildren(self, html: str):
        return self.getvalues('Children', html, 'person')

    def findfather(self, html: str):
        return self.getvalue("Father's occupation", html, 'person')

    def findbirthdate(self, html: str):
        result = self.getvalue('Year born', html)
        if result:
            return result.split(' in ')[0]
        return None

    def finddeathdate(self, html: str):
        result = self.getvalue('Year died', html)
        if result:
            return result.split(' in ')[0]
        return None

    def findbirthplace(self, html: str):
        result = self.getvalue('Year born', html)
        if result:
            return self.findbyre(' in (.*)', result, 'city')

    def finddeathplace(self, html: str):
        return self.getvalue('Place of death', html, 'city')

    def findschools(self, html: str):
        return self.getvalues('Education', html, 'university')

    def findnationalities(self, html: str):
        return self.getvalues('Country of Activity', html, 'country')

    def findemployers(self, html: str):
        return self.getvalues('Worked for', html, 'employer')

    def findmixedrefs(self, html: str):
        return [('P214', code) for code in self.getvalues(r'viaf\d*', html)]


class OdisAnalyzer(Analyzer):
    def setup(self):
        self.dbproperty = 'P2372'
        self.dbid = 'Q3956431'
        self.dbname = 'ODIS'
        if self.id.startswith('PS'):
            self.id = self.id[3:]
            self.urlbase = 'http://www.odis.be/lnk/PS_{id}'
            self.urlbase3 = 'https://www.odis.be/hercules/CRUDscripts/pers/identificatie/getPublicdata.script.php' \
                            '?persid={id}&websiteOutputIP=www.odis.be&taalcode=nl'
            self.skipfirst = True
        else:
            self.urlbase = None
        self.hrtre = '<h2>Identificatie</h2>(.*?)<h2>Varia</h2>'
        self.language = 'nl'

    def findinstanceof(self, html: str):
        return 'Q5'

    def findnames(self, html) -> List[str]:
        return self.findallbyre(r'<OMSCHRIJVING>(.*?)<', html)

    def finddescription(self, html: str):
        return self.findbyre(r'(?s)<b>Biografische schets</b>\s*</td>\s*</tr>\s*<tr>\s*<td>\s*<[pP]>([^<>\.]*)', html)

    def findlongtext(self, html: str):
        return self.findbyre(r'(?s)<b>Biografische schets</b>\s*</td>\s*</tr>\s*<tr>\s*<td>\s*<[pP]>(.*?)</td>', html)

    def findlastname(self, html: str):
        return self.findbyre(r'(?s)<td[^<>]*>familienaam</td>\s*<td[^<>]*>(.*?)<', html, 'lastname')

    def findfirstname(self, html: str):
        return self.findbyre(r'(?s)<td[^<>]*>roepnaam</td>\s*<td[^<>]*>(.*?)<', html, 'firstname') or \
               self.findbyre(r'(?s)<td[^<>]*>eerste voornaam</td>\s*<td[^<>]*>(.*?)<', html, 'firstname')

    def findpseudonyms(self, html: str):
        return self.findallbyre(r'(?s)<td[^<>]*>[^<>]*pseudoniem[^<>]*</td>\s*<td[^<>]*>(.*?)<', html)

    def findresidences(self, html: str):
        section = self.findbyre(r'(?s)<b>Woon- en verblijfplaatsen</b>\s*</td>\s*</tr>\s*<tr>(.*?)</tbody>', html)
        if section:
            result = []
            subsections = self.findallbyre(r'(?s)(<tr.*?</tr>)', section)
            for subsection in subsections:
                result.append(
                    self.findbyre(r'<td width="auto">([^<>]*)</td>', subsection, 'city')
                    or self.findbyre(r'<span[^<>]*>(.*?)<', subsection, 'city')
                )
            return result

    def findoccupations(self, html: str):
        section = self.findbyre(r'(?s)<b>Professionele loopbaan</b>\s*</td>\s*</tr>\s*<tr>(.*?)</tbody>', html)
        if section:
            return self.findallbyre(r'(?s)<tr[^<>]*>\s*<td[^<>]*>(.*?)</td>', section, 'occupation')

    def findemployers(self, html: str):
        section = self.findbyre(
            r'(?s)<b>Engagementen in organisaties en instellingen</b>\s*</td>\s*</tr>\s*<tr>(.*?)</tbody>', html)
        if section:
            return self.findallbyre(r'(?s)<tr[^<>]*>\s*<td[^<>]*>[^<>]*</td>\s*<td[^<>]*>([^<>]*)</td>', section,
                                    'employer', alt=['university'], skips=['organization']) + \
                   self.findallbyre(r'<a[^<>]*>(.*?)<', section, 'employer', alt=['university'], skips=['organization'])
        return None

    def findmemberships(self, html: str):
        section = self.findbyre(
            r'(?s)<b>Engagementen in organisaties en instellingen</b>\s*</td>\s*</tr>\s*<tr>(.*?)</tbody>', html)
        if section:
            return self.findallbyre(r'(?s)<tr[^<>]*>\s*<td[^<>]*>[^<>]*</td>\s*<td[^<>]*>([^<>]*)</td>', section,
                                    'organization', skips=['employer', 'university']) + \
                   self.findallbyre(r'<a[^<>]*>(.*?)<', section, 'organization', skips=['employer', 'university'])

    def findpositions(self, html: str):
        section = self.findbyre(r'(?s)<b>Politieke mandaten</b>\s*</td>\s*</tr>\s*<tr>(.*?)</tbody>', html)
        if section:
            result = []
            for subsection in self.findallbyre(r'(?s)<tr[^<>]*>(.*?)</tr>', section):
                parts = self.findallbyre(r'<span[^<>]*>(.*?)<', subsection)
                result += self.findallbyre(r'(.*)', ' '.join(parts), 'position')
        return result

    def findlanguagesspoken(self, html: str):
        section = self.findbyre(r'(?s)<b>Talen</b>\s*</td>\s*</tr>\s*<tr>(.*?)</tbody>', html)
        if section:
            return self.findallbyre(r'(?s)<tr[^<>]*>\s*<td[^<>]*>(.*?)[<\(]', section, 'language')

    def findwebpages(self, html: str):
        section = self.findbyre(r'(?s)<b>Online bijlagen</b>\s*</td>\s*</tr>\s*<tr>(.*?)</tbody>', html)
        if section:
            result = self.findallbyre(r'<a href="(.*?)[#"]', section)
            return [r for r in result if 'viaf' not in r]

    def findmixedrefs(self, html: str):
        return self.finddefaultmixedrefs(html)


class AcademicTreeAnalyzer(Analyzer):
    def setup(self):
        self.dbproperty = 'P2381'
        self.dbid = 'Q21585670'
        self.dbname = 'Academic Family Tree'
        self.urlbase = 'https://academictree.org/chemistry/peopleinfo.php?pid={id}'
        self.hrtre = '(<h1.*?)<div class="rightcol'
        self.language = 'en'

    def findinstanceof(self, html: str):
        return 'Q5'

    def findnames(self, html) -> List[str]:
        return [self.findbyre(r'(?s)<h1[^<>]*>(.*?)<', html)]

    def findlongtext(self, html: str):
        return self.findbyre(r'(?s)</h1>(\s*<table.*?)<table', html)

    def finddescription(self, html: str):
        return self.findbyre(r'(?s)Commentaire biographique</th>.*?<td>(.*?)</td>', html)

    def findemployers(self, html: str):
        section = self.findbyre(r'(?s)Affiliations:.*?(<.*?</table>)', html)
        if section:
            return self.findallbyre(r'>([^<>]*)</a>', section, 'university', alt=['employer'])

    def findadvisors(self, html: str):
        section = self.findbyre(r'(?s)Parents</h4>(.*?)<h\d', html)
        if section:
            return self.findallbyre(r'(?s)>([^<>]*)</a>', section.replace('&nbsp;', ' '), 'scientist',
                                    skips=['university', 'employer'])

    def finddocstudents(self, html: str):
        section = self.findbyre(r'(?s)Children</h4>(.*?)<h\d', html)
        if section:
            return self.findallbyre(r'(?s)>([^<>]*)</a>', section.replace('&nbsp;', ' '), 'scientist',
                                    skips=['university', 'employer'])

    def findbirthdate(self, html: str):
        return self.findbyre(r'Bio:(?:<[^<>]*>)*\(([^<>]*) -', html)

    def finddeathdate(self, html: str):
        return self.findbyre(r'Bio:(?:<[^<>]*>)*\([^<>]* - ([^<>]*?)\)', html)

    def findwebsite(self, html: str):
        return self.findbyre(r'(?s)>Site web</th>.*?>([^<>]*)</a>', html)

    def findmixedrefs(self, html: str):
        return self.finddefaultmixedrefs(html)

    def findworkfields(self, html: str):
        section = self.findbyre(r'(?s)Area:</[^<>]*>([^<>]*)<', html)
        if section:
            return self.findallbyre(r"([\w\s']+)", section, 'subject')


class CthsAnalyzer(Analyzer):
    def setup(self):
        self.dbproperty = 'P2383'
        self.dbid = None
        self.dbname = 'Comité des travaux historiques et scientifiques'
        self.urlbase = 'http://cths.fr/an/savant.php?id={id}'
        self.hrtre = r'<div class=\s*title>(.*?</div id =biographie>)'
        self.language = 'fr'

    def findnames(self, html) -> List[str]:
        return [self.findbyre(r'<title>[^<>]*?-(.*?)<', html),
                self.findbyre(r'id=proso_bio_detail>([^<>]*) est un', html)]

    def findfirstname(self, html: str):
        return self.findbyre(r'<h2>.*?<strong>(.*?)<', html, 'firstname')

    def findlastname(self, html: str):
        return self.findbyre(r'<h2>(.*?)<', html, 'lastname')

    def finddescription(self, html: str):
        return self.findbyre(r'proso_bio_detail>(.*?)<', html)

    def findlongtext(self, html: str):
        return self.findbyre(r'(?s)<div id =biographie>(.*?)</fieldset>', html)

    def findbirthdate(self, html: str):
        return self.findbyre(r'Naissance: ((?:\d+ )?(?:\w+ )?\d{4})', html)

    def findbirthplace(self, html: str):
        return self.findbyre(r'Naissance: [^<>\-]* à ([^<>\(]*)', html, 'city')

    def finddeathdate(self, html: str):
        return self.findbyre(r'Décès: ((?:\d+ )?(?:\w+ )?\d{4})', html)

    def finddeathplace(self, html: str):
        return self.findbyre(r'Décès: [^<>\-]* à ([^<>\(]*)', html, 'city')

    def findmemberships(self, html: str):
        section = self.findbyre(r'(?s)<fieldset id="fieldset_societes">(.*?)</fieldset>', html)
        if section:
            return self.findallbyre(r'>([^<>]+)</A>', html, 'organization')

    def findoccupations(self, html: str):
        result = []
        section = self.findbyre(r'id=proso_bio_detail>[^<>]* est une? ([^<>]*)', html)
        if section:
            subsections = section.split(' et ')
            for subsection in subsections:
                result += [self.getdata('occupation', part) for part in subsection.split(',')]
            return result


class TransfermarktAnalyzer(Analyzer):
    def setup(self):
        self.dbproperty = 'P2446'
        self.dbid = 'Q2449070'
        self.dbname = 'Transfermarkt'
        self.urlbase = 'https://www.transfermarkt.com/-/profil/spieler/{id}'
        self.hrtre = '<span>Player data</span>(.*?)<div class="box'
        self.language = 'en'

    def findnames(self, html) -> List[str]:
        return [
            self.findbyre(r'"keywords" content="([^"]+),', html),
            self.findbyre(r'<title>([^<>]*) - ', html),
            self.findbyre(r'(?s)Full Name:.*?<td>(.*?)<', html),
        ]

    def findlongtext(self, html: str):
        return self.findbyre(r'(?s)>Further information</span>(.*?)<div class="box', html)

    def findlastname(self, html: str):
        return self.findbyre(r'<h1 itemprop="name">[^<>]*<b>(.*?)<', html, 'lastname')

    def findfirstname(self, html: str):
        return self.findbyre(r'<h1 itemprop="name">([^<>]*)<b>', html, 'firstname')

    def findinstanceof(self, html: str):
        return 'Q5'

    def findoccupations(self, html: str):
        return ['Q937857']

    def findbirthdate(self, html: str):
        return self.findbyre(r'(?s)<span itemprop="birthDate" class="dataValue">(.*?)[\(<]', html)

    def finddeathdate(self, html: str):
        return self.findbyre(r'(?s)<span itemprop="deathDate" class="dataValue">(.*?)[\(<]', html)

    def findbirthplace(self, html: str):
        return self.findbyre(r'(?s)<span itemprop="birthPlace">(.*?)<', html)

    def finddeathplace(self, html: str):
        return self.findbyre(r'(?s)<span itemprop="deathPlace">(.*?)<', html)

    def findnationalities(self, html: str):
        return self.findallbyre(r'(?s)<span itemprop="nationality">(.*?)<', html)

    def findheight(self, html: str):
        return self.findbyre(r'(?s)<span itemprop="height" class="dataValue">(.*?)<', html)

    def findteampositions(self, html: str):
        result = []
        for section in [
            self.findbyre(r'(?s)<span>Main position\s*:</span(>.*?<)/div>', html),
            self.findbyre(r'(?s)<span>Other position\(s\)\s*:</span(>.*?<)/div>', html)
        ]:
            if section:
                result += self.findallbyre(r'>([^<>]*)<', section, 'footballposition')
        return result

    def findmixedrefs(self, html: str):
        return self.finddefaultmixedrefs(html)

    def findwebsite(self, html: str):
        return self.findbyre(r'(?s)<a href="([^"]*)"[^<>]*>\s*<img src="https://tmsi.akamaized.net/icons/.svg"', html)

    def findsportteams(self, html: str):
        section = self.findbyre(r'<div class="box transferhistorie">(.*?)<div class="box', html)
        if section:
            return self.findallbyre(
                r'(?s)<td class="hauptlink no-border-links hide-for-small vereinsname">\s*<[^<>]*>(.*?)<', html,
                'footballteam')
        return None


class KnawAnalyzer(Analyzer):
    def setup(self):
        self.dbproperty = 'P2454'
        self.dbid = 'Q21491701'
        self.dbname = 'KNAW'
        self.urlbase = 'http://www.dwc.knaw.nl/biografie/pmknaw/?pagetype=authorDetail&aId={id}'
        self.hrtre = '(<h1.*?)<div class="sidebar">'
        self.language = 'en'

    def finddescription(self, html: str):
        return self.findbyre(r'<h1>(.*?)</h1>', html)

    def findnames(self, html) -> List[str]:
        return [self.findbyre(r'<h1>(.*?)[\(<]', html)]

    def findinstanceof(self, html: str):
        return 'Q5'

    def findgender(self, html: str):
        return self.findbyre(r'<strong>Gender</strong>:?(.*?)<', html, 'gender')

    def findbirthplace(self, html: str):
        return self.findbyre(r'Born:([^<>]*),', html, 'city')

    def findbirthdate(self, html: str):
        return self.findbyre(r'Born:[^<>]*,([^<>]*)', html)

    def finddeathplace(self, html: str):
        return self.findbyre(r'Died:([^<>]*),', html, 'city')

    def finddeathdate(self, html: str):
        return self.findbyre(r'Died:[^<>]*,([^<>]*)', html)

    def findmemberships(self, html: str):
        result = ['Q253439']
        section = self.findbyre(r'(?s)Memberships(?:<[^<>]*>)?\s*:(.*?)</div>', html)
        if section:
            result += self.findallbyre(r'<em>(.*?)<', section, 'organization')
        return result


class DblpAnalyzer(Analyzer):
    def setup(self):
        self.dbproperty = 'P2456'
        self.dbid = 'Q1224715'
        self.dbname = 'DBLP'
        self.urlbase = 'https://dblp.org/pid/{id}'
        self.hrtre = '<h3>Person information</h3>(.*?)<h3>'
        self.language = 'en'

    def findlongtext(self, html: str):
        return self.findbyre(r'(?s)<h3>Person information</h3>(.*?)<h3>', html)

    def findnames(self, html) -> List[str]:
        return self.findallbyre(
            r'class="this-person" itemprop="name">(.*?)<', html)

    def findemployers(self, html: str):
        return self.findallbyre(r'(?s)>affiliation[^<>]*</em>.*?>([^<>]*)</span>', html, 'university')

    def findawards(self, html: str):
        return self.findallbyre(r'(?s)>award:</em>.*?>([^<>]*)</span>', html, 'award')

    def findbirthdate(self, html: str):
        return self.findallbyre(r'<li>\s*(\d+)\s*-\s*\d+\s*<', html)

    def finddeathdate(self, html: str):
        return self.findallbyre(r'<li>\s*\d+\s*-\s*(\d+)\s*<', html)


class TheatricaliaAnalyzer(Analyzer):
    def setup(self):
        self.dbproperty = 'P2469'
        self.dbid = 'Q24056151'
        self.dbname = 'Theatricalia'
        self.urlbase = 'http://theatricalia.com/person/{id}'
        self.hrtre = '(<h1.*?<h2 class="sm">Tools</h2>)'
        self.language = 'en'
        self.escapehtml = True

    def findlongtext(self, html: str):
        return self.findbyre(r'(?s)<div itemprop="description">(.*?)</div', html)

    def findinstanceof(self, html: str):
        return self.findbyre(r'itemtype="http://schema.org/(.*?)"', html, 'instanceof')

    def findnames(self, html) -> List[str]:
        return self.findallbyre(r'itemprop="name">(.*?)<', html)

    def findbirthdate(self, html: str):
        result = self.findbyre(r'itemprop="birthDate" datetime="(.*?)"', html)
        if result:
            return result.replace('-00', '')

    def finddeathdate(self, html: str):
        result = self.findbyre(r'itemprop="birthDate" datetime="(.*?)"', html)
        if result:
            return result.replace('-00', '')

    def findmixedrefs(self, html: str):
        return self.finddefaultmixedrefs(html, includesocial=False)

    def findoccupations(self, html: str):
        result = []
        if self.findbyre(r'(?s)itemprop="performerIn"[^<>]*>(\s*)<', html):
            result.append('Q2259451')
        sections = self.findallbyre(r'(?s)itemprop="performerIn"[^<>]*>(.*?)<', html, 'theater-occupation', alt=['occupation'])
        for section in sections:
            result += self.findallbyre(r'([^,/]+)', section, 'theater-occupation', alt=['occupation'])
        return result


class KinopoiskAnalyzer(Analyzer):
    def setup(self):
        self.dbproperty = 'P2604'
        self.dbid = 'Q2389071'
        self.dbname = 'KinoPoisk'
        self.urlbase = 'https://www.kinopoisk.ru/name/{id}/'
        self.hrtre = '(<h1.*?</table>)'
        self.language = 'ru'

    def findnames(self, html) -> List[str]:
        return [self.findbyre(r'<h1[^<>]*>(.*?)<', html)] \
            + self.findallbyre(r'"alternateName">(.*?)<', html) \
            + self.findallbyre(r'title" content="(.*?)"', html)

    def findinstanceof(self, html: str):
        return 'Q5'

    def findoccupations(self, html: str):
        return self.findallbyre(r'"jobTitle" content="(.*?)"', html, 'film-occupation', alt=['occupation'])

    def findbirthdate(self, html: str):
        return self.findbyre(r'"birthDate" content="(.*?)"', html) or \
               self.findbyre(r'birthDate="(.*?)"', html)

    def findheight(self, html: str):
        return self.findbyre(r'(?s)>рост</td>.*?>([^<>]*?)</span>', html)

    def findbirthplace(self, html: str):
        return self.findbyre(r'(?s)class="birth"[^<>]*>\s*<span><a[^<>]*>([^<>]*)</a>', html, 'city')


class CsfdAnalyzer(Analyzer):
    def setup(self):
        self.dbproperty = 'P2605'
        self.dbid = 'Q3561957'
        self.dbname = 'ČSFD'
        self.urlbase = 'https://www.csfd.cz/tvurce/{id}'
        # self.urlbase = None
        self.language = 'cs'
        self.hrtre = '(<div class="info">.*?</div>)'

    def findnames(self, html) -> List[str]:
        with codecs.open('result.html', 'w', 'utf-8') as f:
            f.write(html)
        return [self.findbyre(r'<h1.*?>(.*?)<', html)]

    def findlongtext(self, html: str):
        return self.findbyre(r'(?s)>\s*Biografie\s*<.*?<div class="content">(.*?)</div>', html)

    def findbirthdate(self, html: str):
        return self.findbyre(r'\snar\.(.*)', html)

    def findbirthplace(self, html: str):
        return self.findbyre(r'(?s)</h1>.*?<br>(.*?)<.*<div class="navigation">', html, 'city')

    def findoccupations(self, html: str):
        return self.findallbyre(r'>([^<>]*) filmografie<', html, 'film-occupation', alt=['occupation'])

    def findmixedrefs(self, html: str):
        return self.finddefaultmixedrefs(html, includesocial=False)


class FilmportalAnalyzer(Analyzer):
    def setup(self):
        self.dbproperty = 'P2639'
        self.dbid = 'Q15706812'
        self.dbname = 'Filmportal'
        self.urlbase = 'http://www.filmportal.de/film/{id}'
        self.urlbase2 = 'http://www.filmportal.de/person/{id}'
        self.hrtre = '<h1>(.*?)<div class="panel-panel sidebar">'
        self.language = 'de'

    def finddescription(self, html: str):
        return self.findbyre(r'(?s)<div class="intertitle">(.*?)</div>', html)

    def findnames(self, html) -> List[str]:
        result = [
            self.findbyre(r'Originaltitel \(\w+\)(.*?)<', html),
            self.findbyre(r'<meta name="title" content="(.*?)[\|<]', html),
            self.findbyre(r'(?s)<h1>(.*?)<', html),
        ]
        section = self.findbyre(r'(?s)Weitere Namen</div>(.*?)</div>', html)
        if section:
            result += self.findallbyre(r'(?s)>(.*?)[\(<]', section)
        return result

    def findlongtext(self, html: str):
        return self.findbyre(r'(?s)<h2[^<>*]>(?:Inhalt|Biografie)</h2>(.*?)<(?:div|section)\s*class=', html)

    def findinstanceof(self, html: str):
        if '/film/' in self.url:
            return 'Q11424'
        if '/person/' in self.url:
            return 'Q5'
        return None

    def findorigcountry(self, html: str):
        return self.findbyre(r'(?s)<span\s*class="movie-region-names"\s*>.*?<span\s*>(.*?)<', html, 'country')

    def findpubdate(self, html: str):
        return self.findbyre(r'(?s)<span\s*class="movie-year"\s*>\s*(\d+)', html)

    def findmoviedirectors(self, html: str):
        section = self.findbyre(r'(?s)<h3>Regie</h3>.*?(<ul.*?</ul>)', html)
        if section:
            return self.findallbyre(r'>([^<>]*)</a>', section, 'filmmaker')

    def findscreenwriters(self, html: str):
        section = self.findbyre(r'(?s)<h3>Drehbuch</h3>.*?(<ul.*?</ul>)', html)
        if section:
            return self.findallbyre(r'>([^<>]*)</a>', section, 'filmmaker')

    def finddirectorsphotography(self, html: str):
        section = self.findbyre(r'(?s)<h3>Kamera</h3>.*?(<ul.*?</ul>)', html)
        if section:
            return self.findallbyre(r'>([^<>]*)</a>', section, 'filmmaker')

    def findmovieeditors(self, html: str):
        section = self.findbyre(r'(?s)<h3>Schnitt</h3>.*?(<ul.*?</ul>)', html)
        if section:
            return self.findallbyre(r'>([^<>]*)</a>', section, 'filmmaker')

    def findcomposers(self, html: str):
        section = self.findbyre(r'(?s)<h3>Musik</h3>.*?(<ul.*?</ul>)', html)
        if section:
            return self.findallbyre(r'>([^<>]*)</a>', section, 'composer')

    def findcast(self, html: str):
        section = self.findbyre(r'(?s)<h3>Darsteller</h3>.*?(<ul.*?</ul>)', html)
        if section:
            return self.findallbyre(r'>([^<>]*)</a>', section, 'actor')

    def findprodcoms(self, html: str):
        section = self.findbyre(r'(?s)<h3>Produktionsfirma</h3>.*?(<ul.*?</ul>)', html)
        if section:
            return self.findallbyre(r'>([^<>]*)</a>', section, 'filmcompany')

    def findproducers(self, html: str):
        section = self.findbyre(r'(?s)<h3>Produzent</h3>.*?(<ul.*?</ul>)', html)
        if section:
            return self.findallbyre(r'>([^<>]*)</a>', section, 'filmmaker')

    def finddurations(self, html: str):
        return self.findallbyre(r'>Länge:.*?<div[^<>]*>[^<>]*?(\d+ min)[^<>]*<', html)

    def findoccupations(self, html: str):
        section = self.findbyre(r'<div class="[^"]*occupation field[^"]*">(.*?)<', html)
        if section:
            return self.findallbyre(r'([\w\s]+)', section, 'occupation')

    def findbirthplace(self, html: str):
        return self.findbyre(r'(?s)"field-birth-city">(.*?)<', html, 'city')

    def finddeathplace(self, html: str):
        return self.findbyre(r'(?s)"field-death-city">(.*?)<', html, 'city')

    def findbirthdate(self, html: str):
        return self.findbyre(r'(?s)"field-birth-date">.*?"datetime">(.*?)<', html)

    def finddeathdate(self, html: str):
        return self.findbyre(r'(?s)"field-death-date">.*?"datetime">(.*?)<', html)


class CageMatchAnalyzer(Analyzer):
    def setup(self):
        self.dbproperty = 'P2728'
        self.dbid = 'Q64902023'
        self.dbname = 'CageMatch'
        self.urlbase = 'https://www.cagematch.net//?id=2&nr={id}'
        self.hrtre = '<div class="LayoutContent">(.*?)<div class="LayoutRightPanel">'
        self.language = 'de'

    def getvalue(self, field, html, dtype=None):
        return self.findbyre(
            fr'(?s)<div class="InformationBoxTitle">{field}:</div>\s*<div class="InformationBoxContents">(.*?)</div>',
            html, dtype)

    def getvalues(self, field, html, dtype=None) -> List[str]:
        section = self.getvalue(field, html)
        if section:
            return self.findallbyre(r'>([^<>]*)<', '>' + section + '<', dtype)
        return []

    def findlanguagenames(self, html: str):
        result = []
        section = self.findbyre(r'Also known as(.*?)<', html)
        if section:
            result += section.split(',')
        result += self.getvalues('Alter egos', html)
        section = self.getvalue('Nicknames', html)
        if section:
            result += self.findallbyre(r'"([^,]+)"', section)
        return [('en', res) for res in result] + [('de', res) for res in result]

    def findlongtext(self, html: str):
        return self.findbyre(r'(?s)<div id="hiddenText1"[^<>]*>(.*?)</div>', html)

    def findbirthplace(self, html: str):
        return self.getvalue('Birthplace', html, 'city')

    def findgender(self, html: str):
        return self.getvalue('Gender', html, 'gender')

    def findheight(self, html: str):
        section = self.getvalue('Height', html)
        if section:
            return self.findbyre(r'\((.*?)\)', section)

        return None

    def findweights(self, html: str):
        section = self.getvalue('Weight', html)
        if section:
            return [
                self.findbyre(r'(\d+ lbs)', section),
                self.findbyre(r'(\d+ kg)', section)
            ]
        return None

    def findsports(self, html: str):
        return self.getvalues('Background in sports', html)

    def findmixedrefs(self, html: str):
        return self.finddefaultmixedrefs(self.getvalue('WWW', html) or '')

    def findoccupations(self, html: str):
        preoccs = self.getvalues('Roles', html)
        return [self.findbyre(r'([^\(\)]+)', preocc or '', 'occupation')
                for preocc in preoccs] + self.getvalues('Active Roles', html,
                                                        'occupation')


class PerseeAnalyzer(Analyzer):

    def setup(self):
        self.dbproperty = 'P2732'
        self.dbid = 'Q252430'
        self.dbname = 'Persée'
        self.urlbase = 'https://www.persee.fr/authority/{id}'
        self.hrtre = '(<h2 itemprop="name">.*?)</div>'
        self.language = 'fr'

    def findinstanceof(self, html: str):
        return 'Q5'

    def findlongtext(self, html: str):
        return self.findbyre(r'<p itemprop="description">(.*?)</p>', html)

    def findnames(self, html) -> List[str]:
        return [self.findbyre(r'<h2 itemprop="name">(.*?)[<\(]', html)]

    def findbirthdate(self, html: str):
        section = self.findbyre(r'<h2 itemprop="name">(.*?)</h2>', html)
        if section:
            return self.findbyre(r'\(([\s\w]+)-', section)

    def finddeathdate(self, html: str):
        section = self.findbyre(r'<h2 itemprop="name">(.*?)</h2>', html)
        if section:
            return self.findbyre(r'-([\w\s]+)\)', section)

    def findmixedrefs(self, html: str):
        return self.finddefaultmixedrefs(html, includesocial=False)


class PhotographersAnalyzer(Analyzer):
    def setup(self):
        self.dbproperty = 'P2750'
        self.dbid = 'Q23892012'
        self.dbname = "Photographers' Identity Catalog"
        self.urlbase = 'https://pic.nypl.org/constituents/{id}'
        self.hrtre = '(<div class="bio">.*</section>)'
        self.language = 'en'

    def findgender(self, html: str):
        return self.findbyre(r'<span class="gender">(.*?)<', html, 'gender')

    def findnames(self, html) -> List[str]:
        return [self.findbyre(r'<h1[^<>]*>(.*?)<', html)]

    def findoccupations(self, html: str):
        return self.findallbyre(r'role\.TermID=\d*">(.*?)<', html, 'occupation')

    def findnationality(self, html: str):
        return self.findbyre(r'<h2 class="subtitle">(.*?)[<,]', html, 'country')

    def findmixedrefs(self, html: str):
        return self.finddefaultmixedrefs(html)

    def findbirthdate(self, html: str):
        return self.findbyre(r'(?s)Birth\s*\((.*?)\)', html)

    def finddeathdate(self, html: str):
        return self.findbyre(r'(?s)Death\s*\((.*?)\)', html)

    def findbirthplace(self, html: str):
        return self.findbyre(r'(?s)Birth[^<>]*</h4>\s*<p>(.*?)<', html.replace('<br />', ' '), 'city')

    def finddeathplace(self, html: str):
        return self.findbyre(r'(?s)Death[^<>]*</h4>\s*<p>(.*?)<', html.replace('<br />', ' '), 'city')

    def findworkplaces(self, html: str):
        return self.findallbyre(r'(?s)Active in[^<>]*</h4>\s*<p>(.*?)<', html.replace('<br />', ' '), 'city') + \
               self.findallbyre(r'(?s)Studio or Business[^<>]*</h4>\s*<p>(.*?)<', html.replace('<br />', ' '), 'city')

    def findincollections(self, html: str):
        section = self.findbyre(r'(?s)<h3>Found in collections</h3>.*?<ul.*?>(.*?)</ul>', html)
        if section:
            return self.findallbyre(r'<a[^<>]*>(.*?)<', section, 'museum')


class CanadianBiographyAnalyzer(Analyzer):
    def setup(self):
        self.dbproperty = 'P2753'
        self.dbid = 'Q838302'
        self.dbname = 'Dictionary of Canadian Biography'
        self.urlbase = 'http://www.biographi.ca/en/bio/{id}E.html'
        self.hrtre = 'class="FirstParagraph">(.*?)</p>'
        self.language = 'en'

    def prepare(self, html: str):
        return html.replace('&amp;', '&').replace('&nbsp;', ' ')

    def findnames(self, html) -> List[str]:
        return [self.TAGRE.sub('', x)
                for x in self.findallbyre(r'<strong>(.*)</strong>', html)]

    def finddescription(self, html: str):
        return self.TAGRE.sub('', self.findbyre(r'(?s)class="FirstParagraph">(.*?)(?:;|</p>)', html))

    def findlongtext(self, html: str):
        return self.findbyre(r'(?s)(<p id="paragraph.*?)<!--END BIBLIOGRAPHY', html)

    def findbirthdate(self, html: str):
        return self.findbyre(r' b\. (\d+(?: \w+\.? \d+)?)', html)

    def findbirthplace(self, html: str):
        return self.findbyre(r' b\. [^<>,]* (?:in|at) ([^<>,\.]*)', html, 'city')

    def finddeathdate(self, html: str):
        return self.findbyre(r' d\. (\d+(?: \w+\.? \d+)?)', html)

    def finddeathplace(self, html: str):
        return self.findbyre(r' d\. [^<>,]* (?:in|at) ([^<>,\.]*)', html, 'city')

    def findfather(self, html: str):
        return self.findbyre(r'(?:son|daughter) of ([^,;<>]*)', html, 'person')

    def findmother(self, html: str):
        return self.findbyre(r'(?:son|daughter) of [^;<>]*? and ([^,;<>]*)', html, 'person')

    def findspouses(self, html: str):
        return [self.findbyre(r' m\. \d+(?: \w+ \d+)? ([^,;<>]+)', html, 'person')]


class IWDAnalyzer(Analyzer):
    def setup(self):
        self.dbproperty = 'P2829'
        self.dbid = 'Q24045324'
        self.dbname = 'Internet Wrestling Database'
        self.urlbase = 'http://www.profightdb.com/wrestlers/{id}.html'
        self.hrtre = '(<table.*?)</table>'
        self.language = 'en'

    def getvalue(self, field, html, dtype=None):
        return self.findbyre(r'<strong>{}:</strong>(.*?)</td>'
                             .format(field), html, dtype)

    def getvalues(self, field, html, dtype=None) -> List[str]:
        section = self.getvalue(field, html)
        if section:
            return self.findallbyre(r'([^,]+)', section, dtype)
        return []

    def findinstanceof(self, html: str):
        return 'Q5'

    def findnames(self, html) -> List[str]:
        return [
            self.getvalue('Name', html),
            self.getvalue('Preferred Name', html)
        ] + self.getvalues(r'Ring Name\(s\)', html)

    def findbirthdate(self, html: str):
        return self.getvalue('Date Of Birth', html)

    def findnationalities(self, html: str):
        return self.getvalues('Nationality', html, 'country')

    def findbirthplace(self, html: str):
        return self.getvalue('Place Of Birth', html, 'city')

    def findgender(self, html: str):
        return self.getvalue('Gender', html, 'gender')


class BenezitAnalyzer(Analyzer):
    def setup(self):
        self.dbproperty = 'P2843'
        self.dbid = 'Q24255573'
        self.dbname = 'Benezit'
        self.urlbase = 'https://doi.org/10.1093/benz/9780199773787.article.{id}'
        self.hrtre = '(<h1.*?"moreLikeLink">)'
        self.language = 'en'

    def finddescription(self, html: str):
        return self.findbyre(r'"pf:contentName"\s*:\s*"(.*?)"', html)

    def findnames(self, html) -> List[str]:
        return [self.findbyre(r'"pf:contentName"\s*:\s*"(.*?)[\("]', html)]

    def findlongtext(self, html: str):
        return self.findbyre(r'<abstract>(.*?)</abstract>', html)

    def findisntanceof(self, html: str):
        return 'Q5'

    def findbirthdate(self, html: str):
        return self.findbyre(r'(?s)[^\w][bB]orn\s*((\w+\s*){,2}\d{4})[,\.\)]', html)

    def finddeathdate(self, html: str):
        return self.findbyre(r'(?s)[^\w][dD]ied\s*((\w+\s*){,2}\d{4})[,\.\)]', html)

    def findbirthplace(self, html: str):
        return self.findbyre(r'[bB]orn(?: [^<>,\.;]*,)? in ([^<>,\.;]*)', html, 'city')

    def finddeathplace(self, html: str):
        return self.findbyre(r'[dD]ied(?: [^<>,\.]*,)? in ([^<>,\.;]*)', html, 'city')

    def findoccupations(self, html: str):
        result = []
        section = self.findbyre(r'"pf:contentName" : "[^"]+-(.*?)"', html)
        if section:
            result += self.findallbyre(r'([^,]+)', section, 'occupation')
        section = self.findbyre(r'"pf:contentName" : "[^"]*\)(.*?)"', html)
        if section:
            result += self.findallbyre(r'([\s\w]+)', section, 'occupation')
        return result

    def findlastname(self, html: str):
        return self.findbyre(r'"pf:contentName" : "([^"]+?),', html, 'lastname')

    def findfirstname(self, html: str):
        return self.findbyre(r'"pf:contentName" : "[^",]+,\s*(\w+)', html, 'firstname')

    def findnationality(self, html: str):
        return self.findbyre(r'<abstract><p>([^<>]*?),', html, 'country')

    def findgender(self, html: str):
        return self.findbyre(r'<abstract><p>[^<>]*,([^<>,]*)\.</p>', html, 'gender')


class EcarticoAnalyzer(Analyzer):
    def setup(self):
        self.dbproperty = 'P2915'
        self.dbid = 'Q24694883'
        self.dbname = 'ECARTICO'
        self.urlbase = 'http://www.vondel.humanities.uva.nl/ecartico/persons/{id}'
        self.hrtre = '(<h1.*?)<h2>References'
        self.language = 'en'

    def findnames(self, html) -> List[str]:
        return self.findallbyre(r'<(?:h1|title)[^<>]*>(.*?)[<,\(]', html) \
            + self.findallbyre(r'alias:(.*?)<', html)

    def findinstanceof(self, html: str):
        return 'Q5'

    def findgender(self, html: str):
        return self.findbyre(r'schema:gender"[^<>]+resource="schema:([^<>]+?)"', html, 'gender') or \
               self.findbyre(r'Gender:</td><td[^<>]*>([^<>]+)', html, 'gender')

    def findbirthplace(self, html: str):
        return self.findbyre(r'schema:birthPlace"[^<>]*>(.*?)<', html, 'city')

    def finddeathplace(self, html: str):
        return self.findbyre(r'schema:deathPlace"[^<>]*>(.*?)<', html, 'city')

    def findbirthdate(self, html: str):
        if 'baptized on' not in html:
            return self.findbyre(r'schema:birthDate"[^<>]*>(?:<[^<>]*>)*([^<>]*)</time>', html)
        return None

    def finddeathdate(self, html: str):
        return self.findbyre(r'schema:deathDate"[^<>]*>(?:<[^<>]*>)*([^<>]*)</time>', html)

    def findbaptismdate(self, html: str):
        return self.findbyre(r'baptized on (?:<[^<>]*>|\s)*([\d\-]+)', html)

    def findspouses(self, html: str):
        return self.findallbyre(r'schema:spouse"[^<>]*>(.*?)[<\(]', html, 'person')

    def findfather(self, html: str):
        return self.findbyre(r'Father:.+schema:parent"[^<>]*>(.*?)[<\(]', html, 'person')

    def findmother(self, html: str):
        return self.findbyre(r'Mother:.+schema:parent"[^<>]*>(.*?)[<\(]', html, 'person')

    def findchildren(self, html: str):
        section = self.findbyre(r'(?s)<h2>Children:</h2>(.*?)<h', html)
        if section:
            return self.findallbyre(r'>([^<>]*?)(?:\([^<>]*)?</a>', section, 'person')

    def findoccupations(self, html: str):
        return self.findallbyre(r'schema:(?:hasOccupation|jobTitle)"[^<>]*>([^<>]*)</a>', html, 'occupation')

    def findworkplaces(self, html: str):
        return self.findallbyre(r'schema:(?:work)?[lL]ocation"[^<>]*>(.*?)<', html, 'city')

    def findstudents(self, html: str):
        return self.findallbyre(r'"ecartico:masterOf".*?>([^<>]*)</a>', html, 'person')

    def findteachers(self, html: str):
        return self.findallbyre(r'"ecartico:pupilOf".*?>([^<>]*)</a>', html, 'person')

    def findmixedrefs(self, html: str):
        return self.finddefaultmixedrefs(html) + \
               [('P245', self.findbyre(r'page/ulan/(\w+)', html))]

    def findgenres(self, html: str):
        return self.findallbyre(r'<td>Subject of[^<>]*</td>\s*<td>(.*?)<', html, 'genre') + \
               self.findallbyre(r'<td>Subject of[^<>]*</td>\s*<td>[^<>]+</td>\s*<td>(.*?)<', html, 'genre', alt=['art-genre'])

    def findlanguagesspoken(self, html: str):
        return self.findallbyre(r'<td>Language</td>\s*<td>[^<>]*</td>\s*<td>(.*?)<', html, 'language')

    def findreligions(self, html: str):
        return self.findallbyre(r'<td></td>\s*<td>[^<>]*</td>\s*<td>(.*?)<', html, 'language')

    def findsources(self, html: str):
        section = '\n'.join(self.findallbyre(r'(?s)sources</h3>(.*?)</ol>', html))
        return self.findallbyre('<i>(.*?)<', section, 'source')


class RostochiensiumAnalyzer(Analyzer):

    def setup(self):
        self.dbproperty = 'P2940'
        self.dbid = 'Q1050232'
        self.dbname = 'Catalogus Professorum Rostochiensium'
        self.urlbase = 'http://cpr.uni-rostock.de/metadata/cpr_person_{id}'
        self.hrtre = '(<h2.*)<div class="docdetails-separator">.*?eingestellt'
        self.language = 'de'

    def finddescription(self, html: str):
        return self.findbyre(r'(?s)(<h2>.*?)<div class="docdetails-block">', html)

    def findlongtext(self, html: str):
        return self.findbyre(r'<div class="docdetails">(.*?)<div class="docdetails-label">eingestellt', html)

    def findnames(self, html) -> List[str]:
        return self.findbyre(r'(?s)<title>(.*?)(?: - |<)', html)

    def findinstanceof(self, html: str):
        return 'Q5'

    def findlastname(self, html: str):
        return self.findbyre(r'(?s)<h1>([^<>]*?),', html, 'lastname')

    def findfirstname(self, html: str):
        return self.findbyre(r'(?s)<h1>[^<>]*,\s*([\w\-]+)', html, 'firstname')

    def finddegrees(self, html: str):
        return [self.findbyre(r'(?s)</h2>\s*</div><div class="docdetails-values">(.*?)<', html, 'degree')]

    def findemployers(self, html: str):
        return ['Q159895']

    def findbirthdate(self, html: str):
        return self.findbyre(r'(?s)geboren\s*am\s*([\d\.]+)', html)

    def findbirthplace(self, html: str):
        return self.findbyre(r'(?s)geboren\s*am[^<>]*in(.*?)<', html, 'city')

    def finddeathdate(self, html: str):
        return self.findbyre(r'(?s)gestorben\s*am\s*([\d\.]+)', html)

    def finddeathplace(self, html: str):
        return self.findbyre(r'(?s)gestorben\s*am[^<>]*in(.*?)<', html, 'city')

    def findreligion(self, html: str):
        return self.findbyre(r'(?s)Konfession:.*?"docdetails-value">(.*?)<', html, 'religion')

    def findfather(self, html: str):
        return self.findbyre(r'(?s)>Vater</td>.*?<td[^<>]*>([^<>,\(]*)', html, 'person')

    def findmother(self, html: str):
        return self.findbyre(r'(?s)>Mutter</td>.*?<td[^<>]*>([^<>,\(]*)', html, 'person')

    def findschools(self, html: str):
        section = self.findbyre(r'(?s)>akademische  Abschlüsse:<.*?<tbody>(.*?)</tbody>', html)
        if section:
            return self.findallbyre(r',(.*)', section, 'university')

    def findmemberships(self, html: str):
        section = self.findbyre(r'(?s)>wissenschaftliche\s*Mitgliedschaften:<.*?<tbody>(.*?)</tbody>', html)
        if section:
            return self.findallbyre(r'(?s)>(?:Korrespondierendes Mitglied, )?([^<>]*)<?td>\s*</tr>', section,
                                    'organization')

    def findmixedrefs(self, html: str):
        return self.finddefaultmixedrefs(html)


class MunksRollAnalyzer(Analyzer):
    def setup(self):
        self.dbproperty = 'P2941'
        self.dbid = 'Q6936720'
        self.dbname = "Munk's Roll"
        self.urlbase = 'http://munksroll.rcplondon.ac.uk/Biography/Details/{id}'
        self.hrtre = '<h2 class="PageTitle">(.*?)</div>'
        self.language = 'en'

    def findnames(self, html) -> List[str]:
        return [self.findbyre(r'<h2 class="PageTitle">(.*?)<', html)]

    def finddescription(self, html: str):
        return self.findbyre(r'(?s)</h2>(.*?)<div', html)

    def findlongtext(self, html: str):
        return self.findbyre(r'(?s)<div id="prose">(.*?)</div>', html)

    def findbirthdate(self, html: str):
        return self.findbyre(r'<p><em>b\.(.*?)(?: d\.|<)', html)

    def finddeathdate(self, html: str):
        return self.findbyre(r'<em>[^<>]* d\.(.*?)<', html)


class PlarrAnalyzer(Analyzer):
    def setup(self):
        self.dbproperty = 'P2944'
        self.dbid = 'Q51726418'
        self.dbname = 'Royal College of Surgeons'
        self.urlbase = 'https://livesonline.rcseng.ac.uk/biogs/{id}.htm'
        self.language = 'en'
        self.hrtre = '(<div class="[^"]*asset_detail" .*?(?:LIVES_DETAILS|RIGHTS_MGMT)">)'

    def findnames(self, html) -> List[str]:
        return self.findallbyre(r'PERSON_NAME">(.*?)<', html)

    def finddescription(self, html: str):
        return self.findbyre(r'DESCRIPTION">(.*?)<', html)

    def findlongtext(self, html: str):
        return self.findbyre(r'(?s)LIVES_DETAILS">(.*?)</div>', html)

    def findbirthdate(self, html: str):
        return self.findbyre(r'LIVES_BIRTHDATE">(.*?)<', html)

    def finddeathdate(self, html: str):
        return self.findbyre(r'LIVES_DEATHDATE">(.*?)<', html)

    def findbirthplace(self, html: str):
        return self.findbyre(r'LIVES_BIRTHPLACE">(.*?)<', html, 'city')

    def finddeathplace(self, html: str):
        return self.findbyre(r'LIVES_DEATHPLACE">(.*?)<', html, 'city')

    def findoccupations(self, html: str):
        section = self.findbyre(r'(?s)LIVES_OCCUPATION">(.*?)</div>', html)
        if section:
            return self.findallbyre(r'(?:alt|title)="(.*?)"', section, 'occupation')

    def finddegrees(self, html: str):
        return self.findallbyre(r'LIVES_HONOURS">([^<>]*?)(?:(?: \d+ \w+)? \d{4}\s*)?<', html, 'degree')


class BookTradeAnalyzer(Analyzer):
    def setup(self):
        self.dbproperty = 'P2945'
        self.dbid = 'Q25713895'
        self.dbname = 'British Book Trade'
        self.urlbase = 'http://bbti.bodleian.ox.ac.uk/details/?traderid={id}'
        self.hrtre = '(<table.*?</table>)'
        self.language = 'en'

    def getvalue(self, field, html, dtype=None):
        return self.findbyre(r'(?s)<strong>{}:</strong></td>\s*<td>(.*?)</td>'
                             .format(field), html, dtype)

    def findnames(self, html) -> List[str]:
        return [self.getvalue('Name', html)]

    def findlongtext(self, html: str):
        return self.getvalue('Notes', html)

    def findoccupations(self, html: str):
        result = []
        for section in [
            self.getvalue('Book Trades', html),
            self.getvalue('Non-Book Trade', html)
        ]:
            if section:
                result += self.findallbyre(r'([^,]*)', section, 'occupation')
        return result

    def finddeathdate(self, html: str):
        return self.findbyre(r'(\d+)\s*\(date of death\)', html)

    def findfloruit(self, html: str):
        return self.getvalue('Trading Dates', html)

    def findworkplaces(self, html: str):
        return [self.getvalue('Town', html, 'city')]


class WikitreeAnalyzer(Analyzer):
    def setup(self):
        self.dbproperty = 'P2949'
        self.dbid = 'Q1074931'
        self.dbname = 'WikiTree'
        self.urlbase = 'https://www.wikitree.com/wiki/{id}'
        self.hrtre = '<div class="ten columns">(.*?)<div class="SMALL"'
        self.language = 'en'

    def findnames(self, html) -> List[str]:
        return [
            self.findbyre(r'<title>(.*?)[\(\|<]', html),
            self.findbyre(r'"keywords" content="([^"]+) genealogy', html),
            self.findbyre(r'<span itemprop="name">(.*?)<', html),
        ]

    def findlongtext(self, html: str):
        return self.findbyre(r'(?s)<a name="Biography">(.*?)<a name', html)

    def findfirstname(self, html: str):
        return self.findbyre(r'"givenName">(.*?)<', html, 'firstname')

    def findlastname(self, html: str):
        return self.findbyre(r'"familyName">(.*?)<', html, 'lastname')

    def findbirthdate(self, html: str):
        return self.findbyre(r'itemprop="birthDate" datetime="(\d{4})-00-00"', html) or \
               self.findbyre(r'itemprop="birthDate" datetime="(\d{4}-\d{2}-\d{2})"', html)

    def finddeathdate(self, html: str):
        return self.findbyre(r'itemprop="deathDate" datetime="(\d{4})-00-00"', html) or \
               self.findbyre(r'itemprop="deathDate" datetime="(\d{4}-\d{2}-\d{2})"', html)

    def findbirthplace(self, html: str):
        return self.findbyre(r'"birthPlace"[^<>]*>(?:<[^<>]*>)*([^<>]+)', html, 'city')

    def finddeathplace(self, html: str):
        return self.findbyre(r'"deathPlace"[^<>]*>(?:<[^<>]*>)*([^<>]+)', html, 'city')

    def findfather(self, html: str):
        return self.findbyre(r'(?s)"Father:[^"]+">(?:<[^<>]*>)*([^<>]+)', html, 'person')

    def findmother(self, html: str):
        return self.findbyre(r'(?s)"Mother:[^"]+">(?:<[^<>]*>)*([^<>]+)', html, 'person')

    def findchildren(self, html: str):
        return self.findallbyre(r'(?s)<span itemprop="children".*?><span itemprop="name">(.*?)<', html, 'person')

    def findspouses(self, html: str):
        return self.findallbyre(r'(?s)(?:Husband|Wife) of\s*(?:<[^<>]*>)*([^<>]+)', html, 'person')

    def findsiblings(self, html: str):
        section = self.findbyre(r'(?s)(?:Brother|Sister) of(.*?)</div>', html)
        if section:
            return self.findallbyre(r'>([^<>]*)</', section, 'person')

    def findmixedrefs(self, html: str):
        return self.finddefaultmixedrefs(html, includesocial=False)

    def findfamily(self, html: str):
        section = self.findbyre(r'(?s)<div class="VITALS"><span class="large">(.*?)</div>', html)
        if section:
            return self.findbyre(r'itemprop="familyName" content="(.*?)"', section, 'family')


class GoodreadsAnalyzer(Analyzer):
    def setup(self):
        self.dbproperty = 'P2963'
        self.dbid = None
        self.dbname = 'Goodreads author'
        self.urlbase = 'https://www.goodreads.com/author/show/{id}'
        self.hrtre = '(<h1.*?)<div class="aboutAuthorInfo">'
        self.language = 'en'
        self.escapehtml = True

    def findinstanceof(self, html: str):
        return 'Q5'

    def findnames(self, html) -> List[str]:
        return self.findallbyre(r"'([^']*)' property='[^']*title", html) \
            + self.findallbyre(r'"name">(.*?)<', html) \
            + [self.findbyre(r'<title>([^<>\(\)]*)', html)]

    def finddescriptions(self, html: str):
        return self.findallbyre(r'name="[^"]*description" content="(.*?)"', html) + \
               self.findallbyre(r"content='(.*?)' name='[^']*description", html)

    def findlongtext(self, html: str):
        return self.findbyre(r'(?s)<span id="freeTextauthor\d+"[^<>]*>(.*?)</span>', html) or \
               self.findbyre(r'(?s)<span id="freeTextContainerauthor\d+"[^<>]*>(.*?)</span>', html)

    def findbirthplace(self, html: str):
        return self.findbyre(r'(?s)Born</div>\s*(?:in )?(.*?)<', html, 'city')

    def findbirthdate(self, html: str):
        return self.findbyre(r"(?s)'birthDate'>(.*?)<", html)

    def finddeathdate(self, html: str):
        return self.findbyre(r"(?s)'deathDate'>(.*?)<", html)

    def findwebsite(self, html: str):
        section = self.findbyre(r'(?s)<div class="dataTitle">Website</div>(.*?)</div>', html)
        if section:
            result = self.findbyre(r'>([^<>]*)</a>', section) or ''
            if '://' not in result:
                result = '://'.join(result.split(':', 1))
            if '://' in result:
                return result
        return None

    def findgenres(self, html: str):
        return self.findallbyre(r'/genres/[^"\']*">(.*?)<', html, 'genre', alt=['literature-genre'])

    def findmixedrefs(self, html: str):
        result = self.finddefaultmixedrefs(html)
        return [r for r in result if r[0] != 'P2969' and 'goodreads' not in r[1].lower() and r[1].lower() != 'intent']


class LbtAnalyzer(Analyzer):
    def setup(self):
        self.dbproperty = 'P2977'
        self.dbid = 'Q25935022'
        self.dbname = 'Lord Byron and his Times'
        self.urlbase = 'https://www.lordbyron.org/persRec.php?&selectPerson={id}'
        self.hrtre = '</style>(.*?</tr>.*?)</tr>'
        self.language = 'en'

    def findinstanceof(self, html: str):
        return 'Q5'

    def findnames(self, html) -> List[str]:
        section = self.findbyre(
            r'(?s)<b>NAME AUTHORITIES:</b>(.*?)</td>', html)
        if section:
            return self.findallbyre(r'(?s)</b>([^<>]*)(?:, |\()\d', section)
        return []

    def finddescriptions(self, html: str):
        result = [self.findbyre(r'(?s)<div[^<>]*font-size:\s*18px[^<>*>(.*?)[<;]', html)]
        section = self.findbyre(r'(?s)<b>NAME AUTHORITIES:</b>(.*?)</td>', html)
        if section:
            result += self.findallbyre(r'(?s)</b>(.*?)<', section)
        return result

    def findlongtext(self, html: str):
        return self.findbyre(r'(?s)<div[^<>]*font-size:\s*18px[^<>]*>(.*?)</div>', html)

    def findbirthdate(self, html: str):
        return self.findbyre(r'<b>B/BAP:</b>(.*?)<', html)

    def finddeathdate(self, html: str):
        return self.findbyre(r'<b>DIED:</b>(.*?)<', html)

    def findmixedrefs(self, html: str):
        return self.finddefaultmixedrefs(html) + \
               [('P214', self.findbyre(r'<b>VIAF ID:</b>([^<>]*)', html)),
                ('P244', self.findbyre(r'<b>LOC ID:</b>([^<>]*)', html)),
                ]


class NationalArchivesAnalyzer(Analyzer):
    def setup(self):
        self.dbproperty = 'P3029'
        self.dbid = None
        self.dbname = 'The National Archives'
        self.urlbase = 'https://discovery.nationalarchives.gov.uk/details/c/{id}'
        self.hrtre = '(<h1.*?)<h2'
        self.language = 'en'

    def findnames(self, html) -> List[str]:
        return [self.findbyre(r'<title>([^<>]*)\(', html)]

    def finddescription(self, html: str):
        return self.findbyre(r'<title>(.*?)[\|<]', html)

    def findgender(self, html: str):
        return self.findbyre(r'(?s)Gender:</th>.*?<td[^<>]*>(.*?)<', html, 'gender')

    def findfirstname(self, html: str):
        return self.findbyre(r'(?s)Forenames:</th>.*?<td[^<>]*>\s*([\w\-]*)', html, 'firstname')

    def findlastname(self, html: str):
        return self.findbyre(r'(?s)Surname:</th>.*?<td[^<>]*>(.*?)<', html, 'lastname')

    def findbirthdate(self, html: str):
        return self.findbyre(r'(?s)Date:</th>.*?<td[^<>]*>([^<>-]*)-', html)

    def finddeathdate(self, html: str):
        return self.findbyre(r'(?s)Date:</th>.*?<td[^<>]*>[^<>]*-(.*?)<', html)

    def findoccupations(self, html: str):
        section = self.findbyre(r'\)([^<>]+)</h1>', html)
        if section:
            result = []
            parts = self.findallbyre(r'[\w\s]+', section)
            for part in parts:
                result += [self.getdata('occupation', p) for p in part.split(' and ')]
            return result

    def findmixedrefs(self, html: str):
        return self.finddefaultmixedrefs(html, includesocial=False)


class LdifAnalyzer(Analyzer):
    def setup(self):
        self.dbproperty = 'P3107'
        self.dbid = 'Q1822317'
        self.dbname = 'Lexicon of International Films'
        self.urlbase = 'https://www.zweitausendeins.de/filmlexikon/?sucheNach=titel&wert={id}'
        self.hrtre = "<div class='film-detail'>(.*?)<div class="
        self.language = 'de'

    def findnames(self, html) -> List[str]:
        return self.findallbyre(r"class='[^'<>]*-o?titel'>(.*?)<", html) \
            + self.findallbyre(r'<b>Originaltitel: </b>(.*?)<', html)

    def findlongtext(self, html: str):
        return self.findbyre(r"(?s)<div class='film-detail'>(.*?)</div>", html)

    def findgenres(self, html: str):
        sections = self.findallbyre(r"'film-angaben'>([^<>]+)</p>", html)
        result = []
        for section in sections:
            result += [self.getdata('film-genre', genre) for genre in section.split(',')]
        return result

    def findorigcountries(self, html: str):
        section = self.findbyre(r'<b>Produktionsland:\s*</b>(.*?)<', html)
        if section:
            return self.findallbyre(r'([^/]+)', section, 'country')

    def findpubdate(self, html: str):
        return self.findbyre(r'<b>Produktionsjahr:\s*</b>(.*?)<', html)

    def findprodcoms(self, html: str):
        return [self.findbyre(r'<b>Produktionsfirma:\s*</b>(.*?)<', html, 'filmcompany')]

    def finddurations(self, html: str):
        return [self.findbyre(r'<b>Länge:\s*</b>(.*?)<', html)]

    def findcast(self, html: str):
        section = self.findbyre(r'(?s)<b>Darsteller:\s*</b>(.*?)</p>', html)
        if section:
            return self.findallbyre(r'>([^<>]*)</a>', section, 'actor')

    def findproducers(self, html: str):
        section = self.findbyre(r'(?s)<b>Produzent:\s*</b>(.*?)</p>', html)
        if section:
            return self.findallbyre(r'>([^<>]*)</a>', section, 'filmmaker')

    def findmoviedirectors(self, html: str):
        section = self.findbyre(r'(?s)<b>Regie:\s*</b>(.*?)</p>', html)
        if section:
            return self.findallbyre(r'>([^<>]*)</a>', section, 'filmmaker')

    def findscreenwriters(self, html: str):
        section = self.findbyre(r'(?s)<b>Drehbuch:\s*</b>(.*?)</p>', html)
        if section:
            return self.findallbyre(r'>([^<>]*)</a>', section, 'filmmaker')

    def finddirectorsphotography(self, html: str):
        section = self.findbyre(r'(?s)<b>Kamera:\s*</b>(.*?)</p>', html)
        if section:
            return self.findallbyre(r'>([^<>]*)</a>', section, 'filmmaker')

    def findcomposers(self, html: str):
        section = self.findbyre(r'(?s)<b>Musik:\s*</b>(.*?)</p>', html)
        if section:
            return self.findallbyre(r'>([^<>]*)</a>', section, 'composer')

    def findmovieeditors(self, html: str):
        section = self.findbyre(r'(?s)<b>Schnitt:\s*</b>(.*?)</p>', html)
        if section:
            return self.findallbyre(r'>([^<>]*)</a>', section, 'filmmaker')


class PeakbaggerAnalyzer(Analyzer):
    def setup(self):
        self.dbproperty = 'P3109'
        self.dbid = 'Q28736250'
        self.dbname = 'Peakbagger'
        self.urlbase = 'http://www.peakbagger.com/peak.aspx?pid={id}'
        self.hrtre = '(<h1>.*?)<address>'
        self.language = 'en'

    def finddescriptions(self, html: str):
        return [
            self.findbyre(r'(?s)(<h1.*?</h2>)', html),
            self.findbyre(r'(?s)(<h1.*?</h1>)', html)
        ]

    def findnames(self, html) -> List[str]:
        return [self.findbyre(r'<title>([^<>]*) - ', html)]

    def findinstanceof(self, html: str):
        return 'Q8502'

    def findelevations(self, html: str):
        result = self.findbyre(r'Elevation:(.+?)<', html)
        if result:
            return [r for r in result.split(',') if '+' not in result]

    def findcoords(self, html: str):
        return self.findbyre(r'>([^<>]+) \(Dec Deg\)', html)

    def findcountry(self, html: str):
        return self.findbyre(r'Country</td><td>(.*?)</td>', html, 'country')

    def findadminloc(self, html: str):
        result = self.findbyre(r'County/Second Level Region</td><td>(.*?)</td>', html, 'county')
        return result or self.findbyre(r'State/Province</td><td>(.*?)</td>', html, 'state')

    def findprominences(self, html: str):
        result = self.findbyre(r'Prominence:(.*?)</td>', html)
        if result:
            return result.split(',')

    def findisolations(self, html: str):
        result = self.findbyre(r'True Isolation:(.*?)<', html)
        if result:
            return result.split(',')

    def findmountainrange(self, html: str):
        results = self.findallbyre(r'Range\d+:\s*(?:<.*?>)?([^<>]+)<', html)
        if results:
            return self.getdata('mountainrange', results[-1])


class OfdbAnalyzer(Analyzer):
    def setup(self):
        self.dbproperty = 'P3138'
        self.dbid = 'Q1669874'
        self.dbname = 'Online-Filmdatenbank'
        self.urlbase = 'https://ssl.ofdb.de/film/{id},'
        self.urlbase3 = 'https://ssl.ofdb.de/view.php?page=film_detail&fid={id}'
        self.hrtre = 'Filmangaben(.*?)<!-- Inhaltsangabe -->'
        self.language = 'de'
        self.escapehtml = True

    def finddescriptions(self, html: str):
        return [
            self.findbyre(r'(?s)<!-- Rechte Spalte -->(.*?<tr.*?<tr.*?<tr.*?<tr.*?)<tr', html),
            self.findbyre(r'(?s)<!-- Rechte Spalte -->(.*?<tr.*?<tr.*?<tr.*?)<tr', html),
            self.findbyre(r'(?s)<!-- Rechte Spalte -->(.*?<tr.*?<tr.*?)<tr', html),
        ]

    def findnames(self, html) -> List[str]:
        result = [self.findbyre(r'"og:title" content="(.*?)[\("]', html)]
        section = self.findbyre(r'(?s)Alternativtitel:(.*?)</table>', html)
        if section:
            result += self.findallbyre(r'<b>(.*?)<', section)
        return result

    def findinstanceof(self, html: str):
        return 'Q11424'

    def findpubdate(self, html: str):
        return self.findbyre(r'(?s)Erscheinungsjahr:.*?>(\d+)</a>', html)

    def findorigcountry(self, html: str):
        return self.findbyre(r'(?s)Herstellungsland:.*?>([^<>]+)</a>', html, 'country')

    def findmoviedirectors(self, html: str):
        directorlist = self.findbyre(r'(?s)(Regie:.*?)</tr>', html)
        if directorlist:
            return self.findallbyre(r'>([^<>]+)</span', directorlist, 'filmmaker')

    def findcast(self, html: str):
        castlist = self.findbyre(r'(?s)(Darsteller:.*?)</tr>', html)
        if castlist:
            return self.findallbyre(r'>([^<>]+)</span', castlist, 'actor')

    def findgenres(self, html: str):
        genrelist = self.findbyre(r'(?s)(Genre\(s\):.*?)</tr>', html)
        if genrelist:
            return self.findallbyre(r'>([^<>]+)</span', genrelist, 'film-genre', alt=['genre'])

    def findscreenwriters(self, html: str):
        section = self.findbyre(r'(?s)<i>Drehbuchautor\(in\)</i>.*?(<table>.*?</table>)', html)
        if section:
            return self.findallbyre(r'<b>([^<>]*)</b>', section, 'filmmaker')

    def findcomposers(self, html: str):
        section = self.findbyre(r'(?s)<i>Komponist\(in\)</i>.*?(<table>.*?</table>)', html)
        if section:
            return self.findallbyre(r'<b>([^<>]*)</b>', section, 'filmmaker')

    def finddirectorsphotography(self, html: str):
        section = self.findbyre(r'(?s)<i>Director of Photography \(Kamera\)</i>.*?(<table>.*?</table>)', html)
        if section:
            return self.findallbyre(r'<b>([^<>]*)</b>', section, 'filmmaker')

    def findmovieeditors(self, html: str):
        section = self.findbyre(r'(?s)<i>Cutter \(Schnitt\)</i>.*?(<table>.*?</table>)', html)
        if section:
            return self.findallbyre(r'<b>([^<>]*)</b>', section, 'filmmaker')


class RunebergAuthorAnalyzer(Analyzer):
    def setup(self):
        self.dbproperty = 'P3154'
        self.dbid = 'Q933290'
        self.dbname = 'Project Runeberg'
        self.urlbase = 'http://runeberg.org/authors/{id}.html'
        self.hrtre = '<br clear=all>(.*?)<p>Project'
        self.language = 'en'
        self.escapeunicode = True

    def finddescription(self, html: str):
        return self.findbyre(r'(?s)<br clear=all>(.*?)<p>', html)

    def findnames(self, html) -> List[str]:
        return [self.findbyre(r'<title>(.*?)</title>', html)]

    def findlongtext(self, html: str):
        return self.findbyre(r'(?s)</h1>(.*?)<a', html)

    def findinstanceof(self, html: str):
        return 'Q5'

    def findlastname(self, html: str):
        return self.findbyre(r'(?s)<b>([^<>]*),', html, 'lastname')

    def findfirstname(self, html: str):
        return self.findbyre(r'(?s)<b>[^<>]*,\s*([\w\-]+)', html, 'firstname')

    def findbirthdate(self, html: str):
        return self.findbyre(r'(?s)<b>[^<>]+\(([^<>\(\)]*?)-', html)

    def finddeathdate(self, html: str):
        return self.findbyre(r'(?s)<b>[^<>]+\([^<>\(\)]+-([^<>\(\)]*)', html)

    def findoccupations(self, html: str):
        return [self.findbyre(r'(?s)<br clear=all>.*?</b>\s*,([^<>]*?),', html, 'occupation')]

    def findnationality(self, html: str):
        return self.findbyre(r'(?s)<br clear=all>.*?</b>[^<>]*,([^<>]*?)\.', html, 'country')

    def findmixedrefs(self, html: str):
        return self.finddefaultmixedrefs(html, includesocial=False)


class UGentAnalyzer(Analyzer):
    def setup(self):
        self.dbproperty = 'P3159'
        self.dbid = 'Q26453893'
        self.dbname = 'UGent Memorialis'
        self.urlbase = 'http://www.ugentmemorialis.be/catalog/{id}'
        self.hrtre = '(<h3.*?</dl>)'
        self.language = 'nl'

    def finddescription(self, html: str):
        return self.findbyre(r'<title>(.*?)(?: - |\|<)', html)

    def findnames(self, html) -> List[str]:
        return [self.findbyre(r'<title>(.*?)\d{4}\s*-', html)]

    def findlongtext(self, html: str):
        return self.findbyre(r'(?s)(<h3.*?</dl>)', html)

    def findinstanceof(self, html: str):
        return 'Q5'

    def findbirthdate(self, html: str):
        return self.findbyre(r'<dd class="blacklight-birth_date_display">[^<>]*?([^<>,]*?)</dd>', html)

    def findbirthplace(self, html: str):
        return self.findbyre(r'<dd class="blacklight-birth_date_display">([^<>,]*),', html, 'city')

    def finddeathdate(self, html: str):
        return self.findbyre(r'<dd class="blacklight-death_date_display">[^<>]*?([^<>,]*?)</dd>', html)

    def finddeathplace(self, html: str):
        return self.findbyre(r'<dd class="blacklight-death_date_display">([^<>,]*),', html, 'city')

    def findemployers(self, html: str):
        return ['Q1137665']

    def findschools(self, html: str):
        section = self.findbyre(r'<dd class="blacklight-higher_education_display">(.*?)</dd>', html)
        if section:
            return self.findallbyre(r'([^<>]{3,})', section, 'university')

    def findfather(self, html: str):
        return self.findbyre(r'<dd class="blacklight-name_father_display">(.*?)<', html, 'person')

    def findmixedrefs(self, html: str):
        return self.finddefaultmixedrefs(html)


class BandcampAnalyzer(Analyzer):
    def setup(self):
        self.dbproperty = 'P3283'
        self.dbid = None
        self.dbname = 'Bandcamp'
        self.urlbase = 'https://{id}.bandcamp.com/'
        self.language = 'en'
        self.hrtre = '()'

    def findnames(self, html) -> List[str]:
        return [
            self.findbyre(r'<title>([^<>]+)\|', html),
            self.findbyre(r'"og_site_name" content="(.*?)"', html),
            self.findbyre(r'"og_title" content="(.*?)"', html)
        ]

    def findlongtext(self, html: str):
        return self.findbyre(r'(?s)<meta name="Description" content="(.*?)"', html)

    def findmixedrefs(self, html: str):
        section = self.findbyre(r'(?s)<ol id="band-links">(.*?)</ol>', html) \
                  or self.findbyre(r'(?s)(<head.*)', html)
        return self.finddefaultmixedrefs(section)


class Chess365Analyzer(Analyzer):
    def setup(self):
        self.dbproperty = 'P3314'
        self.dbid = 'Q27529905'
        self.dbname = '365Chess'
        self.urlbase = 'https://www.365chess.com/players/{id}'
        self.language = 'en'
        self.hrtre = '(<table.*?</table>)'

    def findnames(self, html) -> List[str]:
        return self.findallbyre('<h1>(.*?)</h1>', html)

    def findnationalities(self, html: str):
        return self.findallbyre('<span itemprop="nationality">(.*?)<', html, 'country')

    def findsportcountries(self, html: str):
        return self.findallbyre('<span itemprop="nationality">(.*?)<', html, 'country')

    def findgender(self, html: str):
        return self.findbyre('<span itemprop="gender">(.*?)<', html, 'gender')

    def findbirthdate(self, html: str):
        return self.findbyre('<span itemprop="birthDate">(.*?)<', html)

    def findchesstitle(self, html: str):
        return self.findbyre('<span itemprop="award">(.*?)<', html, 'chesstitle')

    def findmixedrefs(self, html: str):
        return [('P1440', self.findbyre(r'http://ratings.fide.com/card.phtml\?event=(\d+)', html))]

    def findparticipations(self, html: str):
        names = self.findallbyre('href="https://www.365chess.com/tournaments/[^"]*">(.*?)<', html)
        names = list(set(names))
        return [self.findbyre('(.+)', name, 'chess-tournament') for name in names]

    def findsports(self, html: str):
        return ['Q718']


class HkmdbAnalyzer(Analyzer):
    def setup(self):
        self.dbproperty = 'P3346'
        self.dbid = 'Q5369036'
        self.dbname = 'Hong Kong Movie Database'
        self.urlbase = 'http://www.hkmdb.com/db/people/view.mhtml?id={id}'
        self.language = 'en'
        self.hrtre = '(<TABLE WIDTH="90%".*?)<TABLE CELLPADDING="3"'

    def findlanguagenames(self, html: str):
        result = [('en', name) for name in self.findallbyre(r'(?s)<font size="[^"]+"><b>(.*?)[<\(]', html)] + \
                 [('zh', name) for name in self.findallbyre(r'(?s)<font size="[^"]+"><b>(.*?)[<\(]', html)]
        section = self.findbyre(r'(?s)Aliases:(.*?<TR>)', html)
        if section:
            section = section.replace('&nbsp;', ' ')
            result += [('en', name) for name in self.findallbyre(r'(?s)>(.*?)[,<]', section)]
        return result

    def findbirthdate(self, html: str):
        return self.findbyre(r'Born: (.*?)<', html)

    def findoccupations(self, html: str):
        return self.findallbyre(r'(?s)<TD COLSPAN="\d+">([^<>]+)<i>\([^<>]*\)</i></TD>', html, 'occupation')


class AdultFilmAnalyzer(Analyzer):
    def setup(self):
        self.dbproperty = 'P3351'
        self.dbid = 'Q732004'
        self.dbname = 'Adult Film Database'
        self.urlbase = 'http://www.adultfilmdatabase.com/actor.cfm?actorid={id}'
        self.hrtre = '(<div class="w3-panel.*?)<div class="w3-card'
        self.language = 'en'

    def getvalue(self, field, html, dtype=None):
        return self.findbyre(r'(?s)</i>{}.*?(<ul.*?)</ul>'
                             .format(field), html, dtype)

    def getvalues(self, field, html, dtype=None) -> List[str]:
        section = self.getvalue(field, html)
        if section:
            return self.findallbyre(r'>([^<>]*)</li>', section, dtype)
        return []

    def findnames(self, html) -> List[str]:
        return self.getvalues('Aliases', html)

    def findlongtext(self, html: str):
        return '\n'.join(self.getvalues('Trivia', html))

    def findeyecolor(self, html: str):
        section = self.getvalue('Appearance', html)
        if section:
            return self.findbyre('([^<>]*) eyes', section, 'eyecolor')

    def findhaircolor(self, html: str):
        section = self.getvalue('Appearance', html)
        if section:
            return self.findbyre('([^<>]*) hair', section, 'haircolor')

    def findethnicities(self, html: str):
        return self.getvalues('Origin', html, 'ethnicity')

    def findbirthdate(self, html: str):
        return self.findbyre(r'Date of Birth: ([\d/\-]+)', html)

    def findfloruitstart(self, html: str):
        return self.findbyre(r'Starting Year: (\d+)', html)

    def findmixedrefs(self, html: str):
        return self.finddefaultmixedrefs(html)


class NobelPrizeAnalyzer(Analyzer):
    def setup(self):
        self.dbproperty = 'P3360'
        self.dbid = None
        self.dbname = 'Nobel Prize Nominations'
        self.urlbase = 'https://www.nobelprize.org/nomination/archive/show_people.php?id={id}'
        self.hrtre = '(<div id="main">.*?)<b>'
        self.language = 'en'
        self.escapehtml = True

    def findnames(self, html) -> List[str]:
        return [self.findbyre(r'<h2>(.*?)</', html)]

    def findlastname(self, html: str):
        return self.findbyre(r'Lastname/org:(?:<[^<>]*>)*([^<>]+)', html, 'lastname')

    def findfirstname(self, html: str):
        return self.findbyre(r'Firstname:(?:<[^<>]*>)*([^<>]+)', html, 'firstname')

    def findgender(self, html: str):
        return self.findbyre(r'Gender:(?:<[^<>]*>)*([^<>]+)', html, 'gender')

    def findbirthdate(self, html: str):
        return self.findbyre(r'Year, Birth:(?:<[^<>]*>)*([^<>]+)', html)

    def finddeathdate(self, html: str):
        return self.findbyre(r'Year, Death:(?:<[^<>]*>)*([^<>]+)', html)


class SurmanAnalyzer(Analyzer):
    def setup(self):
        self.dbproperty = 'P3392'
        self.dbid = None
        self.dbname = 'Surman Index'
        self.urlbase = 'https://surman.english.qmul.ac.uk/main.php?personid={id}'
        self.hrtre = '"detailDisplay">.*?<br/>(.*?)<strong>Notes:'
        self.language = 'en'

    def findnames(self, html) -> List[str]:
        return [self.findbyre(r'(?s)<h2>(.*?)</', html)]

    def findlongtext(self, html: str):
        return self.findbyre(r'(?s)"detailDisplay">.*?<br/>(.*?<strong>Notes:.*?)<br', html)

    def findinstanceof(self, html: str):
        return 'Q5'

    def findbirthdate(self, html: str):
        return self.findbyre(r'(?s)<strong>Born:\s*</strong>([^<>]*?\d{4})', html)

    def findbirthplace(self, html: str):
        return self.findbyre(r'(?s)<strong>Born:\s*</strong>[^<>]*?\d{4}([^<>]*)', html, 'city')

    def finddeathdate(self, html: str):
        return self.findbyre(r'(?s)<strong>Died:\s*</strong>([^<>]*?\d{4})', html)

    def finddeathplace(self, html: str):
        return self.findbyre(r'(?s)<strong>Died:\s*</strong>[^<>]*?\d{4}([^<>]*)', html, 'city')

    def findschools(self, html: str):
        section = self.findbyre(r'(?s)<strong>Education:\s*</strong>(.*?)</table>', html)
        if section:
            return self.findallbyre(r'(?s)<a[^<>]*>(.*?)<', section, 'university')

    def findworkplaces(self, html: str):
        section = self.findbyre(r'(?s)<strong>Career:\s*</strong>(.*?)</table>', html)
        if section:
            return self.findallbyre(r'(?s)parishid=[^<>]*>(.*?)<', section, 'city')

    def findoccupations(self, html: str):
        return ['Q2259532']

    def findreligion(self, html: str):
        return 'Q1062789'


class CcedAnalyzer(Analyzer):
    def setup(self):
        self.dbproperty = 'P3410'
        self.dbid = None
        self.dbname = 'Clergy of the Church of England database'
        self.urlbase = 'http://db.theclergydatabase.org.uk/jsp/persons/DisplayPerson.jsp?PersonID={id}'
        self.hrtre = '<h2>Ordination Events</h2>()</body>'
        self.language = 'en'

    def findnames(self, html) -> List[str]:
        return self.findallbyre(r'(?s)<tr[^<>]*>\s*<td>[^<>]*</td>\s*<td>([^<>]*[a-z][^<>]*)', html)

    def findfirstname(self, html: str):
        return self.findbyre(r'(?s)<tr[^<>]*>\s*<td>[^<>]*</td>\s*<td>[^<>]+,([^<>]*)', html, 'firstname')

    def findlastname(self, html: str):
        return self.findbyre(r'(?s)<tr[^<>]*>\s*<td>[^<>]*</td>\s*<td>([^<>]+),', html, 'lastname')

    def findlongtext(self, html: str):
        return self.findbyre(r'(?s)<h3>Comments</h3>(.*?)<h\d', html)

    def findschools(self, html: str):
        section = self.findbyre(r'(?s)<h2>Education Events</h2>(.*?)<h2', html)
        if section:
            return self.findallbyre(
                r'(?s)<tr[^<>]*>\s*<td>[^<>]*</td>\s*<td>[^<>]*</td>\s*<td>[^<>]*</td>\s*<td>[^<>]</td>\s*<td>([^<>]*)',
                section, 'university')

    def finddegrees(self, html: str):
        section = self.findbyre(r'(?s)<h2>Education Events</h2>(.*?)<h2', html)
        if section:
            return self.findallbyre(
                r'(?s)<tr[^<>]*>\s*<td>[^<>]*</td>\s*<td>[^<>]*</td>\s*<td>[^<>]*</td>\s*<td>([^<>]*)', section,
                'degree')

    def findinstanceof(self, html: str):
        return 'Q5'

    def findoccupations(self, html: str):
        return ['Q2259532']

    def findreligion(self, html: str):
        return 'Q82708'

    def findpositions(self, html: str):
        section = self.findbyre(r'(?s)<h2>Appointment Events</h2>(.*?)<h2', html)
        if section:
            return self.findallbyre(
                r'(?s)<tr[^<>]*>\s*<td>[^<>]*</td>\s*<td>[^<>]*</td>\s*<td>[^<>]*</td>\s*<td>([^<>]*)', section,
                'position')

    def findbirthdate(self, html: str):
        section = self.findbyre(r'(?s)<h2>Birth Events</h2>(.*?)<h2', html)
        if section:
            return self.findbyre(r'(?s)<tr[^<>]*>\s*<td>\s*(\d*[1-9]\d*/\d+/\d+)\s*<', html)

    def findbirthplace(self, html: str):
        section = self.findbyre(r'(?s)<h2>Birth Events</h2>(.*?)<h2', html)
        if section:
            for city in self.findallbyre(r'(?s)<tr[^<>]*>\s*<td>[^<>]*</td>\s*<td>([^<>]*)</td>', section, 'city'):
                if city:
                    return city

    def findworkplaces(self, html: str):
        section = self.findbyre(r'(?s)<h2>Appointment Events</h2>(.*?)<h2', html)
        if section:
            return self.findallbyre(r'<a href="../locations[^<>]+>(.*?)<', html, 'city')


class LeopoldinaAnalyzer(Analyzer):
    def setup(self):
        self.dbproperty = 'P3413'
        self.dbid = None
        self.dbname = 'Leopoldina'
        self.urlbase = 'https://www.leopoldina.org/mitglieder/mitgliederverzeichnis/mitglieder/member/Member/show/{id}/'
        self.hrtre = '<table class="mitglied-single">(.*?)</table>'
        self.language = 'de'

    def findnames(self, html) -> List[str]:
        return self.findallbyre('<h1[^<>]*>(.*?)<', html)

    def findinstanceof(self, html: str):
        return 'Q5'

    def findlongtext(self, html: str):
        return self.findbyre('(?s)<div class="panel">(.*?)</div>', html)

    def findworkfields(self, html: str):
        return [self.findbyre('(?s)Sektion:.*?<span[^<>]*>(.*?)<', html, 'subject')]

    def findnationalities(self, html: str):
        return [self.findbyre('(?s)Land:.*?<span[^<>]*>(.*?)<', html, 'country')]

    def findworklocations(self, html: str):
        return [self.findbyre('(?s)Stadt:.*?<span[^<>]*>(.*?)<', html, 'city')]

    def findmemberships(self, html: str):
        return ['Q543804']


class EnlightenmentAnalyzer(Analyzer):
    def setup(self):
        self.dbproperty = 'P3429'
        self.dbid = 'Q1326050'
        self.dbname = 'Electronic Enlightenment'
        self.urlbase = 'http://www.e-enlightenment.com/person/{id}/'
        self.hrtre = '</h1>.*?</h2>(.*?)<h[3r]'
        self.language = 'en'

    def findnames(self, html) -> List[str]:
        return [self.findbyre(r'(?s)Name</span>\s*:?\s*(.*?)<', html)]

    def finddescription(self, html: str):
        result = self.findbyre(r'(?s)Occupation</span>(.*?)<p>', html)
        if result:
            return self.TAGRE.sub('', result).lstrip(':')

    def findlongtext(self, html: str):
        return self.findbyre(r'(?s)<div id="content">(.*?)</div>', html)

    def findinstanceof(self, html: str):
        return 'Q5'

    def findbirthdate(self, html: str):
        section = self.findbyre(r'(?s)Dates</span>(.*?)<p>', html)
        if section:
            return self.findbyre(r'born ([\w\s]+)', section)

    def finddeathdate(self, html: str):
        section = self.findbyre(r'(?s)Dates</span>(.*?)<p>', html)
        if section:
            return self.findbyre(r'died ([\w\s]+)', section)

    def findnationality(self, html: str):
        return self.findbyre(r'(?s)Nationality</span.*?>([^<>]*)</a>', html, 'country')

    def findoccupations(self, html: str):
        section = self.findbyre(r'(?s)Occupation</span>(.*?)<p>', html)
        if section:
            return self.findallbyre(r'>([^<>]*)</a>', section, 'occupation')

    def findinception(self, html: str):
        section = self.findbyre(r'(?s)Dates</span>(.*?)<p>', html)
        if section:
            return self.findbyre(r'founded ([\w\s]+)', section)

    def findmixedrefs(self, html: str):
        return self.finddefaultmixedrefs(html)


class SnacAnalyzer(Analyzer):
    def setup(self):
        self.dbproperty = 'P3430'
        self.dbid = 'Q29861311'
        self.dbname = 'SNAC'
        self.urlbase = 'http://snaccooperative.org/ark:/99166/{id}'
        self.hrtre = '(<div class="main_content">.*?)<div class="relations"'
        self.language = 'en'

    def findnames(self, html) -> List[str]:
        section = self.findbyre(
            r'(?s)extra-names[^<>]*"[^<>]*>(.*?)<div class="', html)
        if section:
            return self.findallbyre(r'<div>(.*?)<', section)
        return []

    def finddescriptions(self, html: str):
        description = self.findbyre(r'(?s)"og:description"[^<>]*content="(.*?)"', html)
        if description:
            description = re.sub(r'(?s)\s+', ' ', description)
            result = [description, description.split('.')[0]]
        else:
            result = []
        result += self.findallbyre(r'(?s)<p xmlns="[^<>"]*">(.*?)<', html)
        return result

    def findlongtext(self, html: str):
        return self.findbyre(r'(?s)<biogHist>(.*?)</biogHist>', html)

    def findbirthdate(self, html: str):
        return self.findbyre(r'>Birth(.*?)<', html)

    def finddeathdate(self, html: str):
        return self.findbyre(r'>Death(.*?)<', html)

    def findnationalities(self, html: str):
        section = self.findbyre(r'(?s)Nationality:\s*<[^<>]*>([^<>]*)<', html)
        if section:
            return self.findallbyre(r'([\w\s]+)', section, 'country')

    def findlanguagesspoken(self, html: str):
        section = self.findbyre(r'(?s)Language:\s*<[^<>]*>([^<>]*)<', html)
        if section:
            return self.findallbyre(r'([\w\s]+)', section, 'language')

    def findoccupations(self, html: str):
        section = self.findbyre(r'(?s)<h4>Occupations:</h4>(.*?)(?:</ul>|<h4>)', html)
        if section:
            return self.findallbyre(r'<li>([^<>]*)<', section, 'occupation')


class BabelioAnalyzer(Analyzer):
    def setup(self):
        self.dbproperty = 'P3630'
        self.dbid = 'Q2877812'
        self.dbname = 'Babelio'
        self.urlbase = 'https://www.babelio.com/auteur/-/{id}'
        self.hrtre = '(<div class="livre_bold">.*?>)Ajouter'
        self.language = 'fr'
        self.escapeunicode = True

    def finddescription(self, html: str):
        return self.findbyre(r'<meta name="description" content="(.*?)"', html)

    def findnames(self, html) -> List[str]:
        return [self.findbyre(r'<title>(.*?)(?:\(| - |<)', html)]

    def findlongtext(self, html: str):
        return self.findbyre(r'(?s)<div id="d_bio"[^<>]*>(.*?)</div>', html)

    def findinstanceof(self, html: str):
        return 'Q5'

    def findnationality(self, html: str):
        return self.findbyre(r'(?s)Nationalit[^<>]*:(.*?)<', html, 'country')

    def findbirthplace(self, html: str):
        return self.findbyre(r'N[^\s]*e\) [^\s]+ :([^<>]*),', html, 'city')

    def finddeathplace(self, html: str):
        return self.findbyre(r'Mort\(e\) [^\s]+ :([^<>]*),', html, 'city')

    def findbirthdate(self, html: str):
        return self.findbyre(r'itemprop="birthDate">(.*?)<', html)

    def finddeathdate(self, html: str):
        return self.findbyre(r'itemprop="deathDate">(.*?)<', html)

    def findwebsite(self, html: str):
        return self.findbyre(r'(?s)[Ss]ite(?: [\w\s\-]*)?:(?:<br />)?([^<>]*://[^<>]*)', html)

    def findmixedrefs(self, html: str):
        return [x for x in self.finddefaultmixedrefs(html) if x[0] != 'P4003']


class ArtnetAnalyzer(Analyzer):
    def setup(self):
        self.dbproperty = 'P3782'
        self.dbid = 'Q266566'
        self.dbname = 'Artnet'
        self.urlbase = 'http://www.artnet.com/artists/{id}/'
        self.urlbase3 = 'http://www.artnet.com/artists/{id}/biography'
        self.hrtre = '(<h1.*?</section>)'
        self.language = 'en'

    def finddescription(self, html: str):
        return self.findbyre(r'<div class="headline">(.*?)</div>', html)

    def findlongtext(self, html: str):
        parts = self.findallbyre(r'(?s)(<div class="bioSection.*?)</div>', html)
        return '\n'.join(parts)

    def findnames(self, html) -> List[str]:
        return [self.findbyre(r"'artistName'\s*:\s*'(.*?)'", html)]

    def findinstanceof(self, html: str):
        return 'Q5'

    def findnationalities(self, html: str):
        section = self.findbyre(r'"nationality":"(.*?)"', html)
        if section:
            return self.findallbyre(r'([^/,\.;]+)', section, 'country')

    def findbirthdate(self, html: str):
        return self.findbyre(r'"birthDate":"(.*?)"', html)

    def finddeathdate(self, html: str):
        return self.findbyre(r'"deathDate":"(.*?)"', html)

    def findincollections(self, html: str):
        result = []
        section = self.findbyre(r'(?s)Public Collections</h2>(.*?)</div>', html)
        result += self.findallbyre(r'>([^<>]*?)<', section or '', 'museum')
        section = self.findbyre(r'(?s)Collections:(.*?)</dl>', html)
        result += self.findallbyre(r'>([^<>]*?)<', section or '', 'museum')
        section = self.findbyre(r'(?s)Museums:(.*?)</dl>', html)
        result += self.findallbyre(r'>([^<>]*?)<', section or '', 'museum')
        return result

    def findmemberships(self, html: str):
        return self.findallbyre(r'(?s)>Member (.*?)<', html, 'organization')


class DanskefilmAnalyzer(Analyzer):
    def setup(self):
        self.dbproperty = 'P3786'
        self.dbid = 'Q5159753'
        self.dbname = 'Danskefilm'
        self.urlbase = 'https://danskefilm.dk/skuespiller.php?id={id}'
        self.hrtre = '(<div class="col-lg-4 col-md-4">.*?</div>)'
        self.language = 'da'
        self.escapeunicode = True

    def findnames(self, html) -> List[str]:
        return [
            self.findbyre(r'<title>(.*?)(?: - |<)', html),
            self.findbyre(r'<H4><B>(.*?)<', html)
        ]

    def findlongtext(self, html: str):
        return self.findbyre(r'(?s)<div class="biografi">(.*?)</div>', html)

    def finddescriptions(self, html: str):
        return [
            self.findbyre(r'"description" content="(.*?)"', html),
            self.findbyre(r'Biografi(?:<[^<>]*>)*(.*?)[<\.]', html)
        ]

    def findbirthdate(self, html: str):
        return self.findbyre(r'Født: ([\d\-]+)', html)

    def findbirthplace(self, html: str):
        return self.findbyre(r'Født:[^<>]* i (.*?)<', html, 'city')

    def finddeathdate(self, html: str):
        return self.findbyre(r'Død: ([\d\-]+)', html)

    def finddeathplace(self, html: str):
        return self.findbyre(r'Død:[^<>]* i (.*?)<', html, 'city')

    def findburialplace(self, html: str):
        return self.findbyre(r'Gravsted:(.*?)<', html, 'cemetery')

    def findawards(self, html: str):
        section = self.findbyre(r'(?s)(<B>Priser.*?</table>)', html)
        if section:
            return self.findallbyre(r'(?s)<td>(.*?)[\(<]', section, 'award')


class BnaAnalyzer(Analyzer):
    def setup(self):
        self.dbproperty = 'P3788'
        self.dbid = None
        self.dbname = 'National Library of the Argentine Republic'
        self.urlbase = 'https://catalogo.bn.gov.ar/F/?func=direct&doc_number={id}&local_base=BNA10'
        self.hrtre = '<!-- filename: full-999-body-bna10 -->(.*)<!-- filename: full-999-body-bna10 -->'
        self.language = 'es'

    def getvalue(self, field, html, dtype=None):
        return self.findbyre(
            r'(?s)<td class="td1"[^<>]*>\s*<strong>{}</strong>\s*</td>\s*<td[^<>]*>(.*?)</td>'
            .format(field), html, dtype)

    def getvalues(self, field, html, dtype=None) -> List[str]:
        section = self.getvalue(field, html)
        if section:
            return self.findallbyre(r'(?s)>(.*?)<', '>' + section + '<', dtype)
        return []

    def prepare(self, html: str):
        return html.replace('&nbsp;', ' ')

    def instanceof(self, html: str):
        return 'Q5'

    def findnames(self, html) -> List[str]:
        result = []
        section = self.getvalue('Nombre personal', html) or ''
        if section:
            result += self.findallbyre(r'>([^<>,]*,[^<>,]*),', section)
        section = (self.getvalue('Usado por', html) or '')
        if section:
            result += self.findallbyre(r'>([^<>,]*,[^<>,]*),', section)
        result += self.getvalues('Forma compl. nombre', html)
        return result

    def finddescription(self, html: str):
        return self.getvalue('Datos biogr./hist.', html)

    def findlongtext(self, html: str):
        return (self.getvalue('Datos biogr./hist.', html) or '') + ' ' + (self.getvalue('Fuente de info.', html) or '')

    def findbirthdate(self, html: str):
        section = self.getvalue('Nombre personal', html)
        if section:
            return self.findbyre(r',([^<>\-,]*)-[^<>\-,]*<', section)

    def finddeathdate(self, html: str):
        section = self.getvalue('Nombre personal', html)
        if section:
            return self.findbyre(r',[^<>]*-([^<>\-,]*)<', section)

    def findbirthplace(self, html: str):
        return self.findbyre(r'Nació en([^<>]*)', html, 'city')

    def finddeathplace(self, html: str):
        return self.findbyre(r'Murió en([^<>]*)', html, 'city')

    def findworkfields(self, html: str):
        return self.getvalues('Campo de actividad', html, 'subject')

    def findoccupations(self, html: str):
        return self.getvalues('Ocupación', html, 'occupation')

    def findmemberships(self, html: str):
        return self.getvalues('Grupos asociados', html, 'organization')

    def findgender(self, html: str):
        return self.getvalue('Sexo', html, 'gender')

    def findlanguagesspoken(self, html: str):
        return self.getvalues('Idiomas asociados', html, 'language')


class AnimeConsAnalyzer(Analyzer):
    def setup(self):
        self.dbproperty = 'P3790'
        self.dbid = 'Q74763172'
        self.dbname = 'AnimeCons'
        self.urlbase = 'https://animecons.com/guests/bio/{id}/'
        self.hrtre = '<p class="lead">(.*?)<p><b>'
        self.language = 'en'

    def finalscript(self, html: str):
        return self.findbyre(r'(?s).*<script type="application/ld\+json">(.*?)</script>', html)

    def findinstanceof(self, html: str):
        return self.findbyre(r'"@type": "(.*?)"', self.finalscript(html), 'instanceof')

    def findnames(self, html) -> List[str]:
        return [self.findbyre(r'"name": "(.*?)"', self.finalscript(html))]

    def finddescription(self, html: str):
        return self.findbyre(r'"jobTitle": "(.*?)"', self.finalscript(html))

    def findlongtext(self, html: str):
        return self.findbyre(r'(?s)<b>Biography:</b>(.*?)></div>', html)

    def findnationality(self, html: str):
        return self.findbyre(r'"addressCountry": "(.*?)"', self.finalscript(html), 'country')

    def findoccupations(self, html: str):
        section = self.findbyre(r'"jobTitle": "(.*?)"', self.finalscript(html))
        if section:
            return self.findallbyre(r'([\w\s]+)', section, 'occupation')

    def findwebsite(self, html: str):
        return self.findbyre(r'"url": "(.*?)"', self.finalscript(html))


class PublonsAnalyzer(Analyzer):
    def setup(self):
        self.dbproperty = 'P3829'
        self.dbid = 'Q18389628'
        self.dbname = 'Publons'
        self.urlbase = 'https://publons.com/researcher/{id}/'
        self.urlbase3 = 'https://publons.com/researcher/api/{id}/summary/'
        self.urlbase4 = 'https://publons.com/researcher/api/{id}/summary-publications/'
        self.hrtre = '()'
        self.language = 'en'

    def findnames(self, html) -> List[str]:
        return [self.findbyre(r'href="[^"]*/{}/[^"]*">(.*?)<'
                              .format(self.id), html),
                self.findbyre(r'<title>([^<>\|]*)', html)]

    def finddescription(self, html: str):
        return self.findbyre(r'"blurb":"(.*?)"', html)

    def findworkfields(self, html: str):
        return self.findallbyre(r'research_field=\d+","name":"(.*?)"', html, 'subject')

    def findemployers(self, html: str):
        results = self.findallbyre(r'institution/\d+/","name":"(.*?)"', html)
        results = [result for result in results if 'student' not in result.lower().strip().split('-')[0]]
        results = [result.split(',')[-1] for result in results]
        results = [result.split('from')[0].split('until')[0] for result in results]
        results = '@'.join(results)
        return self.findallbyre(r'([^@]+)', results, 'university')

    def findschools(self, html: str):
        results = self.findallbyre(r'institution/\d+/","name":"(.*?)"', html)
        results = [result for result in results if 'student' in result.lower().strip().split('-')[0]]
        results = [result.split(',')[-1] for result in results]
        results = [result.split('from')[0].split('until')[0] for result in results]
        results = '@'.join(results)
        return self.findallbyre(r'([^@]+)', results, 'university')

    def findwebpages(self, html: str):
        section = self.findbyre(r'"affiliations":\[(.*?)\]', html)
        if section:
            return self.findallbyre(r'"url":"(.*?)"', section)

    def findnotableworks(self, html: str):
        html = re.sub('("journal":{(.*?)})', '', html)
        preresults = self.findallbyre(r'"title":"(.*?)"', html)
        preresults = preresults[:3]
        return [self.findbyre(r'(.*)', preresult, 'work') for preresult in preresults]


class SynchronkarteiAnalyzer(Analyzer):
    def setup(self):
        self.dbproperty = 'P3844'
        self.dbid = 'Q1204237'
        self.dbname = 'Deutsche Synchronkartei'
        self.urlbase = 'https://www.synchronkartei.de/film/{id}'
        self.hrtre = '(<h1.*?)<div class="alert'
        self.language = 'de'

    def findnames(self, html) -> List[str]:
        return [
            self.findbyre(r'<h1>(.*?)<', html),
            self.findbyre(r'<h3>(.*?)<', html),
        ]

    def description(self, html: str):
        return self.findbyre(r'<div><p>(.*?)<', html)

    def findinstanceof(self, html: str):
        return 'Q11424'

    def findcast(self, html: str):
        return self.findallbyre(r'(?s)"/darsteller/[^"]*">(.*?)<', html, 'actor')

    def findpubdate(self, html: str):
        return self.findbyre(r'<h1>[^<>]*<small>\(([^<>]*)\)', html)


class TrackFieldAnalyzer(Analyzer):
    def setup(self):
        self.dbid = 'Q29384941'
        self.dbname = 'Track and Field Statistics'
        self.hrtre = '(<table align=center.*?</table>)'
        self.language = 'en'

    def findnames(self, html) -> List[str]:
        return [self.findbyre(r'valign=top><b>(.*?)</b>', html)]

    def findlongtext(self, html: str):
        return self.findbyre(r'(?s)(<table align=center.*</table>)', html)

    def instanceof(self, html: str):
        return 'Q5'

    def findoccupations(self, html: str):
        return ['Q11513337']

    def findsports(self, html: str):
        return ['Q542']

    def findbirthdate(self, html: str):
        return self.findbyre(r'Born:(.*?)<', html)

    def findnationality(self, html: str):
        section = self.findbyre(r'(?s)(<table align=center.*?</table>)', html)
        return self.findbyre(r'.*valign=top><b>(.*?)<', section, 'country')


class TrackFieldFemaleAnalyzer(TrackFieldAnalyzer):
    def setup(self):
        TrackFieldAnalyzer.setup(self)
        self.dbproperty = 'P3924'
        self.urlbase = 'http://trackfield.brinkster.net/Profile.asp?ID={id}&Gender=W'

    def findgender(self, html: str):
        return 'Q6581072'


class TrackFieldMaleAnalyzer(TrackFieldAnalyzer):
    def setup(self):
        TrackFieldAnalyzer.setup(self)
        self.dbproperty = 'P3925'
        self.urlbase = 'http://trackfield.brinkster.net/Profile.asp?ID={id}&Gender=M'

    def findgender(self, html: str):
        return 'Q6581097'


class WhosWhoFranceAnalyzer(Analyzer):
    def setup(self):
        self.dbproperty = 'P4124'
        self.dbid = 'Q5924723'
        self.dbname = "Who's Who in France"
        self.urlbase = 'https://www.whoswho.fr/bio/{id}'
        self.hrtre = '(<h1.*?<!-- profils proches -->)'
        self.language = 'fr'

    def findnames(self, html) -> List[str]:
        return [
            self.findbyre(r'(?s)<h1[^<>]*>(.*?)<', html),
            self.findbyre(r'(?s)>Nom<.*?<div[^<>]*>(.*?)<', html)
        ]

    def finddescription(self, html: str):
        return self.findbyre(r'(?s)"jobTitle">(.*?)<', html)

    def findlongtext(self, html: str):
        return self.findbyre(r'(?s)(<h1.*)<h2', html)

    def findinstanceof(self, html: str):
        return 'Q5'

    def findoccupations(self, html: str):
        section = self.findbyre(r'(?s)"jobTitle">(.*?)<', html)
        if section:
            parts = section.split(',')
            parts = [part.strip().rstrip('.') for part in parts]
            return [self.getdata('occupation', part) for part in parts]

    def findbirthplace(self, html: str):
        return self.findbyre(r'(?s)>Ville de naissance<.*?<div[^<>]*>(.*?)<', html, 'city')

    def findnationality(self, html: str):
        return self.findbyre(r'(?s)>Pays de naissance<.*?<div[^<>]*>(.*?)<', html, 'country')

    def findtwitter(self, html: str):
        return self.findbyre(r'"https://twitter.com/([^<>"])"[^<>]*>[^<>]*sur Twitter<', html)


class AthenaeumAnalyzer(Analyzer):
    def setup(self):
        self.dbproperty = 'P4145'
        self.dbid = 'Q32061534'
        self.dbname = 'Athenaeum'
        self.urlbase = 'http://www.the-athenaeum.org/people/detail.php?id={id}'
        self.hrtre = '(<div id="bio".*</table>'
        self.language = 'en'

    def finddescription(self, html: str):
        return self.findbyre(r'(?s)<td align="left">(?:\s|<[<>]*>)*([^<>\.]*)', html)

    def findlongtext(self, html: str):
        return self.findbyre(r'(?s)<td align="left">(.*?)</td>', html)

    def findnames(self, html) -> List[str]:
        return self.findallbyre(
            r'<strong>Name:</strong></td><td>(.*?)<', html)

    def findbirthdate(self, html: str):
        return self.findbyre(r'<strong>Dates:</strong></td><td>(.*?)[-<]', html)

    def finddeathdate(self, html: str):
        return self.findbyre(r'<strong>Dates:</strong></td><td>[^<>]*-(.*?)<', html)

    def findnationality(self, html: str):
        return self.findbyre(r'<strong>Nationality:</strong></td><td>(.*?)<', html, 'country')

    def findgender(self, html: str):
        return self.findbyre(r'<strong>Sex:</strong></td><td>(.*?)<', html, 'gender')

    def findincollections(self, html: str):
        section = self.findbyre(r'(?s)Top owners of works by this artist(.*?)</table>', html)
        if section:
            return self.findallbyre(r'<tr><td[^<>]*>(.*?)<', section, 'museum')


class AutoresArAnalyzer(Analyzer):
    def setup(self):
        self.dbproperty = 'P4158'
        self.dbid = None
        self.dbname = 'Autores.ar'
        self.urlbase = 'http://www.dominiopublico.org.ar/node/{id}'
        self.hrtre = '<div class="content clearfix">(.*?)<!--'
        self.language = 'es'

    def prepare(self, html: str):
        return html.replace('&nbsp;', ' ')

    def getvalue(self, field, html, dtype=None):
        return self.findbyre(r'>{}:\s*(?:<[^<>]*>)*([^<>]+)<'
                             .format(field), html, dtype)

    def findinstanceof(self, html: str):
        return 'Q5'

    def findnames(self, html) -> List[str]:
        return self.findallbyre(r'<title>(.*?)[\|<]', html) \
            + self.findallbyre('(?s)<h1[^<>]*>(.*?)</h1>', html)

    def finddescriptions(self, html: str):
        section = self.findbyre(r'<h3[^<>]*>Disciplina:\s*</h3>(.*?)<hr', html)
        if section:
            return self.findallbyre('>(.+?)<', section)
        return []

    def findlongtext(self, html: str):
        return ' - '.join(self.finddescriptions(html))

    def findlastname(self, html: str):
        return self.getvalue('Apellidos', html, 'lastname')

    def findfirstname(self, html: str):
        return self.getvalue('Nombres', html, 'firstname')

    def findbirthdate(self, html: str):
        return self.getvalue('Fecha de nacimiento', html) \
            or self.getvalue('Año de nacimiento', html)

    def finddeathdate(self, html: str):
        return self.getvalue('Fecha de muerte', html) \
            or self.getvalue('Año de muerte', html)

    def findgender(self, html: str):
        return self.getvalue('Sexo', html, 'gender')

    def findbirthplace(self, html: str):
        return self.getvalue('Lugar de nacimiento', html, 'city')

    def finddeathplace(self, html: str):
        return self.getvalue('Lugar de muerte', html, 'city')

    def findoccupations(self, html: str):
        section = self.findbyre(r'<h3[^<>]*>Disciplina:\s*</h3>(.*?)<hr', html)
        if section:
            return self.findallbyre('>(.+?)<', section, 'occupation')

    def findmixedrefs(self, html: str):
        return self.finddefaultmixedrefs(html, includesocial=False)


class FoihAnalyzer(Analyzer):
    def setup(self):
        self.dbproperty = 'P4206'
        self.dbid = None
        self.dbname = 'FOIH'
        self.urlbase = 'https://inventaris.onroerenderfgoed.be/dibe/persoon/{id}'
        self.hrtre = '<!-- persoon velden -->(.*?)<!-- einde persoon velden -->'
        self.language = 'nl'

    def findinstanceof(self, html: str):
        return 'Q5'

    def findnames(self, html) -> List[str]:
        return self.findallbyre(r'title" content="(.*?)"', html) \
            + self.findallbyre(r'<title>([^<>\|]+)', html) \
            + self.findallbyre(r'(?s)<h1>(.*?)<', html)

    def findlongtext(self, html: str):
        return self.findbyre(r'(?s)<h3>Beschrijving</h3>(.*?)<h', html)

    def findbirthdate(self, html: str):
        return self.findbyre(r'(?s)<dd>Geboortedatum</dd>\s*<dt>(.*?)</dt>', html)

    def findbirthplace(self, html: str):
        return self.findbyre(r'(?s)<dd>Geboorteplaats</dd>\s*<dt>(.*?)</dt>', html, 'city')

    def finddeathdate(self, html: str):
        return self.findbyre(r'(?s)<dd>Sterfdatum</dd>\s*<dt>(.*?)</dt>', html)

    def finddeathplace(self, html: str):
        return self.findbyre(r'(?s)<dd>Plaats van overlijden</dd>\s*<dt>(.*?)</dt>', html, 'city')

    def findoccupations(self, html: str):
        section = self.findbyre(r'(?s)<dd>Beroep[^<>]*</dd>\s*<dt>(.*?)</dt>', html)
        if section:
            return self.findallbyre(r'([\w\s]+)', section, 'occupation')


class EoasAnalyzer(Analyzer):
    def setup(self):
        self.dbproperty = 'P4228'
        self.dbid = 'Q19160682'
        self.dbname = 'Encyclopedia of Australian Science'
        self.urlbase = 'http://www.eoas.info/biogs/{id}'
        self.hrtre = '(?s)<div id="main">(.*?)<div'
        self.language = 'en'

    def isperson(self, html: str):
        return self.findinstanceof(html) == 'Q5'

    def findnames(self, html) -> List[str]:
        result = [
            self.findbyre(r'<title>(.*?)(?: - |<)', html),
            self.findbyre(r'(?s)>([^<>]*)</h1>', html),
            self.findbyre(r'(?s)>([^<>]*)\([^<>]*</h1>', html),
        ]
        section = self.findbyre(
            r'(?s)<ul class="entitynames">(.*?)</ul>', html)
        if section:
            result += self.findallbyre(r'(?s)<li>(.*?)<', section)
        return result

    def findlongtext(self, html: str):
        return self.findbyre(r'(?s)<h3>Summary</h3>(.*?)</div>', html)

    def findinstanceof(self, html: str):
        return self.findbyre(r'(?s)<h1>\s*<span>(.*?)<', html, 'instanceof')

    def findbirthdate(self, html: str):
        if self.isperson(html):
            return self.findbyre(r'<dd class="startdate">(.*?)<', html)

    def finddeathdate(self, html: str):
        if self.isperson(html):
            return self.findbyre(r'<dd class="enddate">(.*?)<', html)

    def findbirthplace(self, html: str):
        if self.isperson(html):
            return self.findbyre(r'<dd class="startdate">[^<>]*<br\s*/>(.*?)<', html, 'city')

    def finddeathplace(self, html: str):
        if self.isperson(html):
            return self.findbyre(r'<dd class="enddate">[^<>]*<br\s*/>(.*?)<', html, 'city')

    def findoccupations(self, html: str):
        if self.isperson(html):
            sections = self.findallbyre(r'<dd class="function">(.*?)<', html)
            occupations = []
            for section in sections:
                occupations += section.split(' and ')
            result = []
            for occupation in occupations:
                result += self.findallbyre(r'([\w\s]+)', occupation, 'occupation')
            return result

    def findschools(self, html: str):
        if self.isperson(html):
            return self.findallbyre(r'Education - [^<>]* at (?:the )?(.*?)<', html, 'university')

    def finddegrees(self, html: str):
        if self.isperson(html):
            return self.findallbyre(r'Education - ([^<>]*?)(?:\(| at )', html, 'degree')

    def findemployers(self, html: str):
        if self.isperson(html):
            return self.findallbyre(r'Career position - [^<>]* at (?:the )?(.*?)<', html, 'employer', alt=['university'])

    def findwebsite(self, html: str):
        section = self.findbyre(r'<dd class="url">(.*?)</dd>', html)
        if section:
            return self.findbyre(r'href="(.*?)"', section)


class ItauAnalyzer(Analyzer):
    def setup(self):
        self.dbproperty = 'P4399'
        self.dbid = 'Q41599984'
        self.dbname = 'Enciclopédia Itaú Cultural'
        if self.isperson:
            self.urlbase = 'https://enciclopedia.itaucultural.org.br/{id}'
        else:
            # Analyzer only created for persons,
            # for works and possible other it can be extended later
            self.urlbase = None
        self.hrtre = r'<h1[^<>]*>\s*Outras informações.*?<div class="section_content">(.*?)</section>'
        self.language = 'pt'
        self.escapehtml = True

    @property
    def isperson(self):
        return self.id.startswith('pessoa')

    def findinstanceof(self, html: str):
        if self.isperson:
            return 'Q5'

    def findnames(self, html) -> List[str]:
        section = self.findbyre(r'(?s)Outros nomes.*?<ul>(.*?)</ul>', html)
        if section:
            result = self.findallbyre(r'(?s)>(.*?)<', section)
        else:
            result = []
        return (
            result
            + self.findallbyre(r'title" content="(.*?)[\|"]', html)
            + self.findallbyre(r'(?s)<title>(.*?)[\|"]', html)
        )

    def findlongtext(self, html: str):
        return self.findbyre(
            r'(?s)<h2[^<>]*>\s*Biografia\s*</h2>(.*?)<h\d', html)

    def findoccupations(self, html: str):
        section = self.findbyre(
            r'(?s)>\s*Habilidades\s*<.*?<ul>(.*?)</ul>', html)
        if section:
            return self.findallbyre(r'(?s)>(.*?)<', section, 'occupation')

    def findchildren(self, html: str):
        return self.findallbyre(r'(?s)mãe de\s*<.*?>(.*?)<', html, 'person')

    def findbirthdate(self, html: str):
        return self.findbyre(
            r'(?s)>Data de nascimento[^<>]*</span>(.*?)<', html)

    def findbirthplace(self, html: str):
        return self.findbyre(
            r'(?s)>Local de nascimento[^<>]*</span>(.*?)<', html, 'city')

    def finddeathdate(self, html: str):
        return self.findbyre(r'(?s)>Data de morte[^<>]*</span>(.*?)<', html)

    def finddeathplace(self, html: str):
        return self.findbyre(
            r'(?s)>Local de morte[^<>]*</span>(.*?)<', html, 'city')


class AKLAnalyzer(Analyzer):
    def setup(self):
        self.dbproperty = 'P4432'
        self.dbid = 'Q41640909'
        self.dbname = 'Allgemeines Künstlerlexikon'
        self.urlbase = 'https://db.degruyter.com/view/AKL/_{id}?language=de'
        self.hrtre = '<h2>(.*?)<div class="contentRestrictedMessage">'
        self.language = 'en'

    def findinstanceof(self, html: str):
        return 'Q5'

    def findnames(self, html) -> List[str]:
        return [self.findbyre(r'"pf:contentName"\s*:\s*"(.*?)"', html)]

    def finddescription(self, html: str):
        return self.findbyre(
            '<b>Beruf</b>.*?<dd class="fieldValue">(.*?)<', html)

    def findoccupations(self, html: str):
        section = self.findbyre('<b>Beruf</b>.*?<dd class="fieldValue">(.*?)<', html)
        if section:
            return self.findallbyre('([^;]+)', section, 'occupation')

    def findfirstname(self, html: str):
        return self.findbyre(r'"pf:contentName"\s*:\s*"[^"]*?,\s*(\w+)', html)

    def findlastname(self, html: str):
        return self.findbyre(r'"pf:contentName"\s*:\s*"([^"]*?),', html)

    def findbirthdate(self, html: str):
        return self.findbyre(
            r'<b>Beruf</b>.*?<dd class="fieldValue">([\d\.]+)', html)


class SpanishBiographyAnalyzer(Analyzer):
    def setup(self):
        self.dbproperty = 'P4459'
        self.dbid = 'Q41705771'
        self.dbname = 'Spanish Biographical Dictionary'
        self.urlbase = 'http://dbe.rah.es/biografias/{id}'
        self.hrtre = '(<div class="field--item">.*?</article>)'
        self.language = 'es'

    def finddescription(self, html: str):
        return self.findbyre(
            r'(?:<span style="font-family:\'Times New Roman\';">|</b>)\.?(.*?)<', html)

    def findnames(self, html) -> List[str]:
        return [self.findbyre(r'"twitter:title" content="(.*?)"', html)]

    def findlongtext(self, html: str):
        return self.findbyre(
            r'(?s)<div class="field--label[^<>]*">Biograf.a</div>(.*?)</div>',
            html)

    def findinstanceof(self, html: str):
        return 'Q5'

    def findbirthdate(self, html: str):
        return (
            self.findbyre(r'"description" content="[^"]+\(([^"]*?)–', html)
            or self.findbyre(
                r'(?:<span style="font-family:\'Times New Roman\';">|</b>)[^<>]*?((?:\d+\.\w+\.)?\d+) –',
                html)
        )

    def finddeathdate(self, html: str):
        return (
            self.findbyre(r'"description" content="[^"]+–([^"]*?)\)', html)
            or self.findbyre(
                r'(?:<span style="font-family:\'Times New Roman\';">|</b>)[^<>]*? – [^<>]*?((?:\d+\.\w+\.)?\d+)',
                html)
        )

    def findbirthplace(self, html: str):
        return self.findbyre(
            r'(?:<span style="font-family:\'Times New Roman\';">|</b>)\.?([^<>–,]*),',
            html, 'city')

    def finddeathplace(self, html: str):
        return self.findbyre(
            r'(?:<span style="font-family:\'Times New Roman\';">|</b>)[^<>]*?– ([^<>]*?),',
            html, 'city')

    def findoccupations(self, html: str):
        section = self.findbyre(
            r'(?:<span style="font-family:\'Times New Roman\';">|</b>)[^<>]+\.([^<>]+)',
            html)
        if section:
            return self.findallbyre(r'([\s\w]+)', section, 'occupation')

        return None


class CommonwealthGamesAnalyzer(Analyzer):
    def setup(self):
        self.dbproperty = 'P4548'
        self.dbid = None
        self.dbname = 'Commonwealth Games Federation'
        self.urlbase = 'https://thecgf.com/results/athletes/{id}'
        self.hrtre = '(<h2 class="table-title">.*?)</section>'
        self.language = 'en'

    def findnames(self, html) -> List[str]:
        return (
            self.findallbyre(r'name" content="(.*?)"', html)
            + self.findallbyre(r'<title>(.*?)[\|<]', html)
            + self.findallbyre(r'<h\d[^<>]*>(.*?)<', html)
        )

    def findinstanceof(self, html: str):
        return 'Q5'

    def findnationalities(self, html: str):
        return self.findallbyre(r'"Country"><[^<>]*>(.*?)<', html, 'country')

    def findparticipations(self, html: str):
        return self.findallbyre(
            r'"Games"><[^<>]*>(.*?)<', html, 'commonwealth-games')

    def findsports(self, html: str):
        return self.findallbyre(r'"Event"><[^<>]*>([^<>]*?)-', html, 'sport')

    def findgender(self, html: str):
        return self.findbyre(r'"Event"><[^<>]*>[^<>]*-(.*?)<', html, 'gender')


class AccademiaCruscaAnalyzer(Analyzer):
    def setup(self):
        self.dbproperty = 'P4585'
        self.dbid = None
        self.dbname = 'Accademia della Crusca'
        self.urlbase = 'http://www.accademicidellacrusca.org/scheda?IDN={id}'
        self.hrtre = '<div class="riga">(.*?<div class="riga">.*?)<div class="riga">'
        self.language = 'it'

    def findinstanceof(self, html: str):
        return 'Q5'

    def findnames(self, html) -> List[str]:
        return self.findallbyre('<h2[^<>]*>(.*?)[&<]', html)

    def findlongtext(self, html: str):
        return self.findbyre('(?s)Nota biografica</span>(.*?)</span>', html)

    def finddescription(self, html: str):
        return self.findbyre('>([^<>]+)', self.findlongtext(html))

    def findbirthplace(self, html: str):
        return self.findbyre(
            r'(?s)<span class="etichetta">Esistenza</span>\s*<span class="campo">(.*?) [\d—]',
            html, 'city')

    def findbirthdate(self, html: str):
        return self.findbyre(
            r'(?s)<span class="etichetta">Esistenza</span>\s*<span class="campo">[^<>]*? (\d[\w\d\s]*)—',
            html)

    def finddeathplace(self, html: str):
        return self.findbyre(
            r'(?s)<span class="etichetta">Esistenza</span>\s*<span class="campo">[^<>]*—(.*?) [\d<]',
            html, 'city')

    def finddeathdate(self, html: str):
        return self.findbyre(r'(?s)<span class="etichetta">Esistenza</span>\s*<span class="campo">[^<>]*—[^<>]*? (\d[\w\d\s]*)<', html)

    def findoccupations(self, html: str):
        section = self.findbyre(
            r'(?s)<span class="etichetta">Nota biografica</span>\s*<span class="campo">(.*?)<',
            html)
        if section:
            result = []
            parts = section.split(' e ')
            for part in parts:
                result += self.findallbyre(r'([\w\s]+)', part, 'occupation')
            return result

        return None

    def findmemberships(self, html: str):
        return ['Q338489']


class OnlineBooksAnalyzer(Analyzer):
    def setup(self):
        self.dbproperty = 'P4629'
        self.dbid = None
        self.dbname = 'Online Books Page'
        self.urlbase = 'http://onlinebooks.library.upenn.edu/webbin/book/lookupname?key={id}'
        self.hrtre = '(<h2 .*?/h3>)'
        self.language = 'en'

    def finddescription(self, html: str):
        return self.findbyre(r'<title>(.*?)[\|<]', html)

    def findnames(self, html) -> List[str]:
        return [self.findbyre(r'<title>(.*?)[\(\|<]', html)]

    def findfirstname(self, html: str):
        return self.findbyre(
            r'<h3[^<>]*>[^<>]*\([^<>,]*?,\s*([\w\-]+)', html, 'firstname')

    def findlastname(self, html: str):
        return self.findbyre(
            r'<h3[^<>]*>[^<>]*\(([^<>,]*?),', html, 'lastname')

    def findbirthdate(self, html: str):
        return self.findbyre(r'<h3[^<>]*>[^<>]*\([^<>]*,([^<>]*)-', html)

    def finddeathdate(self, html: str):
        return self.findbyre(
            r'<h3[^<>]*>[^<>]*\([^<>]*,[^<>]*-([^<>]*)\)', html)


class NumbersAnalyzer(Analyzer):
    def setup(self):
        self.dbproperty = 'P4657'
        self.dbid = 'Q17072251'
        self.dbname = 'The Numbers'
        self.urlbase = 'https://www.the-numbers.com/person/{id}'
        # self.urlbase = None # temporarily?
        self.language = 'en'

    def findnames(self, html) -> List[str]:
        return [self.findbyre(r'<h1.*?>(.*?)<', html)]

    def findoccupations(self, html: str):
        return self.findallbyre(r'"jobTitle">(.*?)<', html, 'occupation')


class DacsAnalyzer(Analyzer):
    def setup(self):
        self.dbproperty = 'P4663'
        self.dbid = None
        self.dbname = 'DACS'
        self.urlbase = 'https://www.dacs.org.uk/licensing-works/artist-search/artist-details?ArtistId={id}'
        self.hrtre = '(<h1.*?)<h2'
        self.language = 'en'

    def findlongtext(self, html: str):
        return self.findbyre(r'(?s)(<h1.*?)<h2', html)

    def findnames(self, html) -> List[str]:
        with open('result.html', 'w') as f:
            f.write(html)

        section = self.findbyre('(?s)Pseudonyms">(.*?)<', html)
        if section:
            return self.findallbyre('([^;]+)', section)
        return []

    def findnationalities(self, html: str):
        return self.findallbyre(r'lbNationality">(.*?)<', html, 'country')

    def findfirstname(self, html: str):
        return self.findbyre(r'lbFirstName\d*">(.*?)<', html, 'firstname')

    def findlastname(self, html: str):
        return self.findbyre(
            r'lbLastName\d*">(.*?)(?:,\s*)?<', html, 'lastname')

    def findbirthdate(self, html: str):
        return self.findbyre(r'lblDate[oO]fBirth">(.*?)<', html)

    def finddeathdate(self, html: str):
        return self.findbyre(r'lblDate[oO]fDeath">-*(.*?)<', html)


class CinemagiaAnalyzer(Analyzer):
    def setup(self):
        self.dbproperty = 'P4666'
        self.dbid = 'Q15065727'
        self.dbname = 'CineMagia'
        self.urlbase = 'https://www.cinemagia.ro/actor.php?actor_id={id}'
        # self.urlbase = None
        self.hrtre = '(<div class="detalii.block info.actor">.*?after.actor.biography -->)'
        self.language = 'ro'
        self.escapeunicode = True

    def findnames(self, html) -> List[str]:
        return [self.findbyre(r'"og:title"[^<>]*content="(.*?)"', html)]

    def finddescription(self, html: str):
        return self.findbyre(r'"description"[^<>]*content="(.*?)"', html)

    def findlongtext(self, html: str):
        return self.findbyre(
            r'(?s)(<div class="detalii.block info.actor">.*?after.actor.biography -->)',
            html)

    def findbirthplace(self, html: str):
        return self.findbyre(
            r'(?s)<b>Locul naşterii</b>:([^<>]*)', html, 'city')

    def findbirthdate(self, html: str):
        return self.findbyre(r'(?s)<b>Data naşterii</b>.*?>([^<>]*)</a>', html)

    def findoccupations(self, html: str):
        with open('result.html', 'w') as f:
            f.write(html)

        result = self.findallbyre(r'(?s)Filmografie - (.*?)<',
                                  html, 'film-occupation', alt=['occupation'])
        section = self.findbyre(r'(?s)<b>Ocupaţie</b>:([^<>]*)', html)
        if section:
            result += self.findallbyre(r'([\w\s]+)',
                                       section, 'film-occupation',
                                       alt=['occupation'])
        if 'title="Filme cu' in html:
            result += ['Q33999']
        return result


class PeintresBelgesAnalyzer(Analyzer):
    def setup(self):
        self.dbproperty = 'P4687'
        self.dbid = None
        self.dbname = 'Dictionnaire des peintres belges'
        self.urlbase = 'http://balat.kikirpa.be/peintres/Detail_notice.php?id={id}'
        self.urlbase3 = 'http://balat.kikirpa.be/peintres/Detail_notice_comp.php?id={id}'
        self.hrtre = '(<h4.*?)<span class="moyen"'
        self.language = 'fr'
        self.escapeunicode = True

    def finddescription(self, html: str):
        return self.findbyre(r'<span class="moyen">([^<>]*?)\.', html)

    def findnames(self, html) -> List[str]:
        return [self.findbyre(r'<h4>(.*?)<', html)]

    def findlongtext(self, html: str):
        return self.findbyre(r'<span class="moyen">(.*?)</span>', html)

    def findbirthplace(self, html: str):
        return self.findbyre(r'"flash">([^<>]*?),', html, 'city')

    def findbirthdate(self, html: str):
        return self.findbyre(r'"flash">(?:[^<>]*,)?([^<>,\-]*?)[<-]', html)

    def finddeathplace(self, html: str):
        return self.findbyre(r'"flash">[^<>]*? - ([^<>]*?),', html, 'city')

    def finddeathdate(self, html: str):
        return self.findbyre(
            r'"flash">[^<>]*? - (?:[^<>]*,)?([^<>,\-])*<', html)

    def findincollections(self, html: str):
        section = self.findbyre(r'(?s)Collections</span>(.*?)</table>', html)
        if section:
            return self.findallbyre(r'<span[^<>]*>(.*?)<', section, 'museum')


class AuteursLuxembourgAnalyzer(Analyzer):
    def setup(self):
        self.dbproperty = 'P4749'
        self.dbid = 'Q47341245'
        self.dbname = 'Dictionnaire des auteurs luxembourgeois'
        self.urlbase = 'http://www.autorenlexikon.lu/page/author/{id}/DEU/index.html'
        self.hrtre = '(<h1.*<div style="clear:both">)'
        self.language = 'fr'

    def finddescription(self, html: str):
        return self.findbyre(r'itemprop="description">(.*?)</p>', html)

    def findnames(self, html) -> List[str]:
        return self.findallbyre(r'itemprop="[^<>"]*[nN]ame">(.*?)<', html)

    def findlongtext(self, html: str):
        return self.findbyre(r'itemprop="description">(.*?)</div>', html)

    def findbirthdate(self, html: str):
        return self.findbyre(r'itemprop="birthDate" datetime="(.*?)"', html)

    def findbirthplace(self, html: str):
        return self.findbyre(
            r'itemprop="birthPlace".*?>(.*?)[\(<]', html, 'city')

    def finddeathdate(self, html: str):
        return self.findbyre(r'itemprop="deathDate" datetime="(.*?)"', html)

    def finddeathplace(self, html: str):
        return self.findbyre(r'itemprop="deathPlace".*?>(.*?)[<\(]', html, 'city')


class LuminousAnalyzer(Analyzer):
    def setup(self):
        self.dbproperty = 'P4759'
        self.dbid = 'Q6703301'
        self.dbname = 'Luminous-Lint'
        self.urlbase = 'http://www.luminous-lint.com/app/photographer/{id}'
        self.hrtre = \
            '<table cellpadding="5" cellspacing="0" border="0" bgcolor="#E0E0E0" width="100%">(.*?)</table>&nbsp;'
        self.language = 'en'

    def findnames(self, html) -> List[str]:
        section = self.findbyre(
            r'<td[^<>]*>Names:</td>(?:<[^<>]*>)*<td>(.*?)</td>', html)
        if section:
            return self.findallbyre(r';(.+?)&', section)
        return []

    def findlongtext(self, html: str):
        return (self.findbyre(
            '(?s)<table cellpadding="5" cellspacing="0" border="0" bgcolor="#E0E0E0" width="100%">(.*?)<h1>',
            html) or '').replace('&nbsp;', ' ')

    def findbirthdate(self, html: str):
        return self.findbyre(r'Dates:\s*</td><td[^<>]*>(.*?)[\-<]', html.replace('&nbsp;', ' '))

    def finddeathdate(self, html: str):
        return self.findbyre(r'Dates:\s*</td><td[^<>]*>[^\-]+-([^\-<]+)<', html.replace('&nbsp;', ' '))

    def findbirthplace(self, html: str):
        return self.findbyre(r'Born:\s*</td><td[^<>]*>(.*?)<', html.replace('&nbsp;', ' '), 'city')

    def findworkplaces(self, html: str):
        return [self.findbyre(r'Active:\s*</td><td[^<>]*>(.*?)<', html.replace('&nbsp;', ' '), 'city')]

    def finddeathplace(self, html: str):
        return self.findbyre(r'Died:\s*</td><td[^<>]*>(.*?)<', html.replace('&nbsp;', ' '), 'city')


class GameFaqsAnalyzer(Analyzer):
    def setup(self):
        self.dbproperty = 'P4769'
        self.dbid = 'Q693757'
        self.dbname = 'GameFAQs'
        self.urlbase = 'https://gamefaqs.gamespot.com/-/{id}-'
        self.hrtre = '<h2 class="title">Game Detail</h2>(.*?)<h2'
        self.language = 'en'
        self.escapehtml = True

    def getvalue(self, field, html, dtype=None):
        return self.findbyre(r'(?s)<b>{}:</b>(?:\s|<[^<>]*>)*([^<>]+)'
                             .format(field), html, dtype)

    def findinstanceof(self, html: str):
        return 'Q7889'

    def findnames(self, html) -> List[str]:
        return self.findallbyre('<h1[^<>]*>(.*?)<', html)

    def findlongtext(self, html: str):
        return self.findbyre('(?s)<div class="body game_desc">(.*?)</div>', html)

    def findplatforms(self, html: str):
        result = [self.getvalue('Platform', html)]
        section = self.findbyre('(?s)<h3 class="platform-title">(.*?)</h3>', html)
        if section:
            result += self.findallbyre('>([^<>]*)<', section, 'platform')
        return result

    def findgenres(self, html: str):
        return self.findallbyre(r'/category/\d+ ([^"<>]+)', html.replace('-', ' '), 'gamegenre')

    def findfranchises(self, html: str):
        return self.findallbyre(r'/franchise/\d+ ([^"<>]+)', html.replace('-', ' '), 'franchise')

    def finddevelopers(self, html: str):
        return [self.getvalue('Developer[^<>]*', html, 'gamecompany')]

    def findpublishers(self, html: str):
        return [self.getvalue('[^<>]*Publisher', html, 'gamecompany')]

    def findpubdate(self, html: str):
        return self.findbyre('Release', html)


class AmericanBiographyAnalyzer(Analyzer):
    def setup(self):
        self.dbproperty = 'P4823'
        self.dbid = 'Q465854'
        self.dbname = 'American National Biography'
        self.urlbase = 'http://www.anb.org/view/10.1093/anb/9780198606697.001.0001/anb-9780198606697-e-{id}'
        self.hrtre = '(<h1.*?)<div class="contentRestrictedMessage">'
        self.language = 'en'

    def finddescription(self, html: str):
        return self.findbyre(r'(?s)<h3>Extract</h3>(.*?)</p>', html)

    def findnames(self, html) -> List[str]:
        return [self.findbyre(r'"pf:contentName" : "([^"]*)\(', html)]

    def findlongtext(self, html: str):
        return self.findbyre(r'(?s)<p class="ency">(.*?)<div class="chunkFoot">', html)

    def findinstanceof(self, html: str):
        return 'Q5'

    def findbirthdate(self, html: str):
        return self.findbyre(r'(<span class="date">([^<>]*)–', html)

    def finddeathdate(self, html: str):
        return self.findbyre(r'(<span class="date">[^<>]*–([^<>]+)', html)

    def findoccupations(self, html: str):
        section = re.compile(r'\)([^<>]*)was born', html)
        if section:
            return self.findallbyre(r'([\w\s]+)', section, 'occupation')
        return None

    def findbirthplace(self, html: str):
        return self.findbyre(r'was born \w+ ([\w\s]+)', html, 'city')

    def findfirstname(self, html: str):
        return self.findbyre(r'<span class="name">[^<>]*,([^<>]*)', html, 'firstname')

    def findlastname(self, html: str):
        return self.findbyre(r'<span class="name">([^<>]*),', html, 'lastname')


class GeprisAnalyzer(Analyzer):
    def setup(self):
        self.dbproperty = 'P4872'
        self.dbid = 'Q48879895'
        self.dbname = 'GEPRIS'
        self.urlbase = 'http://gepris.dfg.de/gepris/person/{id}'
        self.urlbase3 = 'http://gepris.dfg.de/gepris/person/{id}?context=person&task=showDetail&id=1256901&'
        self.skipfirst = True
        self.hrtre = '(<h3.*?)<div class="clear">'
        self.language = 'en'

    def finddescription(self, html: str):
        return self.findbyre(r'(?s)name="description"[^<>]*content="([^<>]*?)"', html)

    def findinstanceof(self, html: str):
        return 'Q5'

    def findemployers(self, html: str):
        return [self.findbyre(r'(?s)>Adresse</span>\s*<span[^<>]*>(.*?)<', html, 'university', alt=['employer'])]

    def findwebsite(self, html: str):
        return self.findbyre(r'(?s)Internet<.*?<a[^<>]+class="extern"[^<>]+href="([^<>]*?)"', html)

    def findgender(self, html: str):
        if 'Antragstellerin<' in html:
            return 'Q6581072'
        if 'Antragsteller<' in html:
            return 'Q6581097'

    def findresidences(self, html: str):
        return self.findbyre(r'(?s)Adresse</span>.*?>([^<>]*)(?:<[^<>]*>|\s)*</span>', html, 'city')


class WebumeniaAnalyzer(Analyzer):
    def setup(self):
        self.dbproperty = 'P4887'
        self.dbid = 'Q50828580'
        self.dbname = 'Web umenia'
        self.urlbase = 'https://www.webumenia.sk/autor/{id}'
        self.hrtre = '<div class="col-sm-8 popis">(.*?)<div class="container-fluid'
        self.language = 'sk'
        self.escapehtml = True

    def findnames(self, html) -> List[str]:
        return self.findallbyre(r'itemprop="name">(.*?)<', html)

    def findbirthdate(self, html: str):
        return self.findbyre(r'itemprop="birthDate">(.*?)<', html)

    def findbirthplace(self, html: str):
        return self.findbyre(r'itemprop="birthPlace">(.*?)<', html, 'city')

    def finddeathdate(self, html: str):
        return self.findbyre(r'itemprop="deathDate">(.*?)<', html)

    def finddeathplace(self, html: str):
        return self.findbyre(r'itemprop="deathPlace">(.*?)<', html, 'city')

    def findoccupations(self, html: str):
        return self.findallbyre(r'itemprop="jobTitle">(.*?)<', html, 'occupation')

    def findworkplaces(self, html: str):
        section = self.findbyre(r'(?s)Pôsobenie</h4>(.*?)</div>', html)
        if section:
            return self.findallbyre(r'\?place=([^"<>]*)">', section, 'city')

    def findmixedrefs(self, html: str):
        return self.finddefaultmixedrefs(html, includesocial=False)

    def findwebpages(self, html: str):
        section = self.findbyre(r'(?s)Externé odkazy</h4>(.*?)</div>', html)
        if section:
            return self.findallbyre(r'href="([^"]*)" target="_blank"', section)
        return None


class InvaluableAnalyzer(Analyzer):
    def setup(self):
        self.dbproperty = 'P4927'
        self.dbid = None
        self.dbname = 'Invaluable.com'
        self.urlbase = 'https://www.invaluable.com/artist/-{id}/'
        self.hrtre = '({"artist".*?})'
        self.language = 'en'

    def findinstanceof(self, html: str):
        return self.findbyre(r'".type":"(.*?)"', html, 'instanceof')

    def findnames(self, html) -> List[str]:
        result = []
        section = self.findallbyre(r'"alias":\[(.*?)\]', html)
        if section:
            result += self.findallbyre(r'"(.*?)"', section) \
                + [self.findbyre(r'"displayName":"(.*?)"', html)]
        result += (
            self.findallbyre(r'"displayName":"(.*?)"', html)
            + self.findallbyre(r'Alias(?:es)?:([^<>]*)', html)
            + self.findallbyre(r'"name":"(.*?)"', html)
        )
        return result

    def findoccupations(self, html: str):
        section = self.findbyre(r'"profession":\[(.*?)\]', html)
        if section:
            return self.findallbyre(r'"(.*?)"', section, 'occupation')

        section = self.findbyre(r'Professions?:([^<>]*)', html)
        if section:
            return self.findallbyre(r'([\w\s]+)', section, 'occupation')
        return None

    def findbirthdate(self, html: str):
        return self.findbyre(r'"dates":"(.*?)[\-"]', html)

    def finddeathdate(self, html: str):
        return self.findbyre(r'"data":"[^"]*-(.*?)"', html)

    def findfirstname(self, html: str):
        return self.findbyre(r'"foreName":"(.*?)"', html)

    def findlastname(self, html: str):
        return self.findbyre(r'"lastName":"(.*?)"', html)


class AinmAnalyzer(Analyzer):
    def setup(self):
        self.dbproperty = 'P4929'
        self.dbid = None
        self.dbname = 'AINM'
        self.urlbase = 'https://www.ainm.ie/Bio.aspx?ID={id}'
        self.hrtre = '<div id="sidebar" .*?>(.*?)<!-- #sidebar-->'
        self.language = 'ga'

    def getvalue(self, field, html, category=None):
        return self.findbyre(
            r'(?s)<td class="caption">{}</td>\s*<td class="value">(.*?)</td>'
            .format(field), html, category)

    def findlongtext(self, html: str):
        return self.findbyre(r'(?s)<div class="article">(.*?)<div id="machines"', html)

    def findinstanceof(self, html: str):
        return 'Q5'

    def findnames(self, html) -> List[str]:
        result = [self.findbyre(
            r'<meta name="title" content="(.*?)[\(\|"]', html)]
        section = self.getvalue('ainm eile', html)
        if section:
            return result + self.findallbyre(r'>([^<>]+)</', section)
        return result

    def findbirthdate(self, html: str):
        return self.getvalue('dáta breithe', html) or \
               self.findbyre(r'"article-title">(?:<[^<>]*>)*[^<>]*\(<[^<>]*>(\d+)</a>-', html)

    def finddeathdate(self, html: str):
        return self.getvalue('dáta báis', html) or \
               self.findbyre(r'"article-title">(?:<[^<>]*>)*[^<>]*\(.*?-<[^<>]*>(\d+)</a>', html)

    def findbirthplace(self, html: str):
        section = self.getvalue('áit bhreithe', html)
        if section:
            return self.findbyre(r'>([^<>]+)</', section, 'city')

    def findgender(self, html: str):
        return self.getvalue('inscne', html, 'gender')

    def findschools(self, html: str):
        return [self.getvalue('scoil', html, 'university')]

    def findoccupations(self, html: str):
        section = self.getvalue('slí bheatha', html)
        if section:
            return self.findallbyre(r'>([^<>]*)</a>', section, 'occupation')


class TmdbAnalyzer(Analyzer):
    def setup(self):
        self.dbproperty = 'P4985'
        self.dbid = 'Q20828898'
        self.dbname = 'The Movie Database'
        self.urlbase = 'https://www.themoviedb.org/person/{id}'
        self.hrtre = '(<div id="left_column".*?)</section>'
        self.language = 'en'

    def getvalue(self, field, html, dtype=None, alt=None):
        if alt is None:
            alt = []
        return self.findbyre(r'(?s)<bdi>{}</bdi></strong>(.*?)</p>'
                             .format(field), html, dtype, alt=alt)

    def findnames(self, html) -> List[str]:
        return self.findallbyre(r'title" content="(.*?)"', html) + \
               self.findallbyre(r'<h2>(.*?)</', html) + \
               self.findallbyre(r'itemprop="[^"]*[nN]ame">(.*?)<', html)

    def findlongtext(self, html: str):
        return self.findbyre(r'(?s)<h3 dir="auto">Biography</h3>.*?<div class="text">(.*?)</div>', html)

    def finddescription(self, html: str):
        longtext = self.findlongtext(html)
        if longtext:
            return longtext.split('.')[0]

    def findoccupations(self, html: str):
        return [self.getvalue('Known For', html, 'film-occupation', alt=['occupation'])]

    def findgender(self, html: str):
        return self.getvalue('Gender', html, 'gender')

    def findbirthdate(self, html: str):
        return self.getvalue('Birthday', html)

    def finddeathdate(self, html: str):
        return self.getvalue('Day of Death', html)

    def findbirthplace(self, html: str):
        return self.getvalue('Place of Birth', html, 'city')

    def findwebsite(self, html: str):
        site = self.getvalue('Official Site', html)
        if site and ':' in site:
            return site

    def findmixedrefs(self, html: str):
        return self.finddefaultmixedrefs(html[:html.find('<footer')])


class LibraryKoreaAnalyzer(Analyzer):
    def setup(self):
        self.dbproperty = 'P5034'
        self.dbid = 'Q56640487'
        self.dbname = 'National Library of Korea'
        self.urlbase = 'https://nl.go.kr/authorities/resource/{id}'
        self.hrtre = '<div class="kac_number_area">(.*?)</tbody>'
        self.language = 'ko'

    def getvalue(self, field, html, dtype=None):
        return self.findbyre(r'(?s)<td id="{}" title="([^"<>]+)">'
                             .format(field), html, dtype)

    def getvalues(self, field, html, dtype=None) -> List[str]:
        section = self.getvalue(field, html)
        if section:
            return self.findallbyre(r'([^;]*)', section, dtype)
        return []

    def findnames(self, html) -> List[str]:
        return self.getvalues('other_name', html)

    def findbirthdate(self, html: str):
        section = self.getvalue('birth_year', html)
        if section:
            return self.findbyre(r'(.*)-', section)

    def finddeathdate(self, html: str):
        section = self.getvalue('birth_year', html)
        if section:
            return self.findbyre(r'-(.*)', section)

    def findnationalities(self, html: str):
        return self.getvalues('nationality', html, 'country')

    def findoccupations(self, html: str):
        return self.getvalues('job', html, 'occupation')

    def findlanguagesspoken(self, html: str):
        return self.getvalues('f_language', html, 'language')

    def findworkfields(self, html: str):
        return self.getvalues('field_of_activity', html, 'subject')

    def findemployers(self, html: str):
        descriptions = self.getvalues('related_org', html)
        return [self.findbyre(r'([^\(\)]+)', desc, 'employer')
                for desc in descriptions]

    def findmixedrefs(self, html: str):
        return self.finddefaultmixedrefs(html)


class KunstenpuntAnalyzer(Analyzer):
    def setup(self):
        self.dbproperty = 'P5068'
        self.dbid = None
        self.dbname = 'Kunstenpunt'
        self.urlbase = 'http://data.kunsten.be/people/{id}'
        self.hrtre = '(<h3>Details.*?)<h3'
        self.language = 'nl'

    def getvalue(self, field, html, category=None):
        return self.findbyre(r'<dt>{}</dt><dd>(.*?)<'
                             .format(field), html, category)

    def findnames(self, html) -> List[str]:
        return [self.getvalue('Volledige naam', html)]

    def finddescription(self, html: str):
        return self.getvalue('Sleutelnaam', html)

    def findlongtext(self, html: str):
        return self.findbyre(r'(?s)(<h3>Details.*?)<h3', html)

    def findbirthdate(self, html: str):
        return self.getvalue('Geboren', html)

    def findgender(self, html: str):
        return self.getvalue('Geslacht', html, 'gender')

    def findlastname(self, html: str):
        return self.getvalue('Naam', html, 'lastname')

    def findfirstname(self, html: str):
        return self.getvalue('Voornaam', html, 'firstname')

    def findnationality(self, html: str):
        return self.getvalue('Land', html, 'country')


class ArtistsCanadaAnalyzer(Analyzer):
    def setup(self):
        self.dbproperty = 'P5239'
        self.dbid = None
        self.dbname = 'Artists in Canada'
        self.urlbase = 'https://app.pch.gc.ca/application/aac-aic/' \
                       'artiste_detailler_bas-artist_detail_bas.app?lang=en&rID={id}'
        self.hrtre = '(<section class="maincontentpart">.*?</section>)'
        self.language = 'en'

    def findinstanceof(self, html: str):
        return 'Q5'

    def findnames(self, html) -> List[str]:
        result = [self.findbyre(r'(?s)<dt>Artist/Maker.*?<dd>(.*?)</dd>', html)]
        section = self.findbyre(r'(?s)<dt>Artist other names.*?<dd>(.*?)</dd>', html)
        if section:
            result += self.findallbyre(r'(?s)<li>(.*?)<', html)
        return result

    def findfirstname(self, html: str):
        return self.findbyre(r'(?s)Artist/Maker\s*</dt>\s*<dd[^<>]*>[^<>]*,\s*([\w\-]+)', html, 'firstname')

    def findlastname(self, html: str):
        return self.findbyre(r'(?s)Artist/Maker\s*</dt>\s*<dd[^<>]*>([^<>]*?),', html, 'lastname')

    def findoccupations(self, html: str):
        section = self.findbyre(r'(?s)Technique\s*</dt>.*?<dd[^<>]*>(.*?)</dd>', html)
        if section:
            return self.findallbyre(r'(?s)>(.*?)<', section, 'occupation')

    def findgender(self, html: str):
        return self.findbyre(r'(?s)<dt>Gender.*?<dd[^<>]*>(.*?)</dd>', html, 'gender')

    def findbirthplace(self, html: str):
        section = self.findbyre(r'(?s)<dt>Birth.*?<dd[^<>]*>(.*?)</dd>', html)
        if section:
            return self.findbyre(r'(?s)>([^<>]*)</li>', section, 'city')
        return None

    def findbirthdate(self, html: str):
        section = self.findbyre(r'(?s)<dt>Birth.*?<dd[^<>]*>(.*?)</dd>', html)
        if section:
            return self.findbyre(r'(?s)<time>(.*?)</time>', section)

    def finddeathplace(self, html: str):
        section = self.findbyre(r'(?s)<dt>Death.*?<dd[^<>]*>(.*?)</dd>', html)
        if section:
            return self.findbyre(r'(?s)>([^<>]*)</li>', section, 'city')
        return None

    def finddeathdate(self, html: str):
        section = self.findbyre(r'(?s)<dt>Death.*?<dd[^<>]*>(.*?)</dd>', html)
        if section:
            return self.findbyre(r'(?s)<time>(.*?)</time>', section)

    def findresidences(self, html: str):
        section = self.findbyre(r'(?s)(<dt>Address.*?<dd[^<>]*>.*?</dd>)', html)
        if section:
            result = self.findbyre(r'(?s)>([^,<>]*),[^<>]*</li>', section, 'city') or \
                     self.findbyre(r'(?s)>([^,<>]*)</li>', section, 'city')
            return [result]

    def findnationality(self, html: str):
        return self.findbyre(r'(?s)<dt>Citizenship.*?<dd[^<>]*>(.*?)</dd>', html, 'country')


class RollDaBeatsAnalyzer(Analyzer):
    def setup(self):
        self.dbproperty = 'P5240'
        self.dbid = 'Q4048404'
        self.dbname = 'RollDaBeats'
        self.urlbase = 'http://www.rolldabeats.com/artist/{id}'
        self.hrtre = '(<h1.*?<div id="shopping">)'
        self.language = 'en'
        self.escapehtml = True

    def findnames(self, html) -> List[str]:
        section = self.findbyre('(?s)Artist aliases</a>(.*?)<p>', html) or ''
        return self.findallbyre('<h1[^<>]*>(.*?)</', html) \
            + self.findallbyre('>(.*?)</a>', section)

    def findgenres(self, html: str):
        section1 = self.findbyre(r'(?s)Genre:\s*</span>(.*?)<', html) or ''
        section2 = self.findbyre(r'(?s)Style:\s*</span>(.*?)<', html) or ''
        return self.findallbyre('([^,]+)', section1, 'muziekgenre', alt=['genre']) +\
            self.findallbyre('([^,]+)', section2, 'muziekgenre', alt=['genre'])

    def findparts(self, html: str):
        section = self.findbyre(r'(?s)>Member\(s\)</li>(.*?)</ul>', html) or ''
        members = self.findallbyre('>(.*?)</a>', section)
        if len(members) > 1:
            return [self.getdata('musician', member) for member in members]

    def findresidence(self, html: str):
        section = self.findbyre(r'(?s)>Member\(s\)</li>(.*?)</ul>', html) or ''
        members = self.findallbyre('>(.*?)</a>', section)
        if len(members) == 1:
            return self.findbyre(r'</a>\s*<span>\((.*?)\)', html, 'city')

    def findmixedrefs(self, html: str):
        section = self.findbyre('(?s)Links</span>(.*?)</div>', html)
        if section:
            return self.finddefaultmixedrefs(section)


class PornhubAnalyzer(Analyzer):
    def setup(self):
        self.dbproperty = 'P5246'
        self.dbid = 'Q936394'
        self.dbname = 'Pornhub'
        self.urlbase = 'https://nl.pornhub.com/pornstar/{id}'
        self.hrtre = '<div class="detailedInfo">(.*?)</section>'
        self.language = 'nl'
        self.showurl = False

    def getvalue(self, field, html, dtype=None):
        return self.findbyre(r'(?si)itemprop="{}"[^<>]*>(.*?)<'
                             .format(field), html, dtype) \
            or self.findbyre(
                r'(?si)"infoPiece"><span>{}:</span>(?:\s|<[^<>]*>)*([^<>]*)'
                .format(field), html, dtype)

    def findnames(self, html) -> List[str]:
        return [self.findbyre(r'(?s)<h1>(.*?)<', html)]

    def finddescriptions(self, html: str):
        result = []
        section = self.findbyre(r'(?s)class="aboutMeSection(.*?)</section>', html)
        if section:
            result += self.findallbyre(r'>([^<>]*)<', section)
        # this would also analyze self.findlongtext(html)
        # but the code was removed
        return result

    def findlongtext(self, html: str):
        return self.getvalue('description', html)

    def findbirthdate(self, html: str):
        return self.getvalue(r'birth\s*date', html) or self.getvalue('born', html)

    def findbirthplace(self, html: str):
        return self.getvalue(r'birth\s*place', html, 'city')

    def finddeathdate(self, html: str):
        return self.getvalue(r'death\s*date', html) or self.getvalue('died', html)

    def finddeathplace(self, html: str):
        return self.getvalue(r'death\s*place', html, 'city')

    def findheight(self, html: str):
        section = self.getvalue('height', html)
        if section:
            return self.findbyre(r'(\d+ cm)', section)
        return None

    def findweights(self, html: str):
        section = self.getvalue('weight', html)
        if section:
            return self.findallbyre(r'(\d+ \w+)', section)

    def findoccupations(self, html: str):
        return ['Q488111']

    def findnotableworks(self, html: str):
        section = self.findbyre(r'(?s)<div class="featuredIn">(.*?)<div class', html)
        if section:
            return self.findallbyre(r'(?s)>([^<>]*)</a>', section, 'film')

    def findresidence(self, html: str):
        return self.getvalue('city and country', html)

    def findfloruit(self, html: str):
        result = self.getvalue('career start and end', html)
        if result:
            return result.replace(' to ', ' - ')

    def findethnicities(self, html: str):
        return [
            self.getvalue('ethnicity', html, 'ethnicity'),
            self.getvalue('background', html, 'ethnicity')
        ]

    def findeyecolor(self, html: str):
        return self.getvalue(r'eye\s*color', html, 'eyecolor')

    def findhaircolor(self, html: str):
        return self.getvalue(r'hair\s*color', html, 'haircolor')

    def findgender(self, html: str):
        return self.getvalue('gender', html, 'gender')

    def findwebsite(self, html: str):
        result = self.findbyre(r'(?si)href="([^<>]*?)"[^<>]*>(?:\s|<[^<>]*>)*official site', html)
        if result and 'onlyfans' not in result:
            return result
        return None

    def findmixedrefs(self, html: str):
        section = self.findbyre(r'(?s)(<h1.*)<h2', html)
        return self.finddefaultmixedrefs(section)


class YoupornAnalyzer(Analyzer):
    def setup(self):
        self.dbproperty = 'P5267'
        self.dbid = None
        self.dbname = 'YouPorn'
        self.urlbase = 'https://www.youporn.com/pornstar/{id}/'
        self.hrtre = '<div class="porn-star-columns">(.*?)<div'
        self.language = 'en'
        self.showurl = False

    def findinstanceof(self, html: str):
        return 'Q5'

    def findnames(self, html) -> List[str]:
        section = self.findbyre(r'(?s)(<h1.*?<)/div>', html)
        if section:
            result = []
            subsections = self.findallbyre(r'(?s)>(.*?)<', section)
            for subsection in subsections:
                result += self.findallbyre(r'([^,]+)', subsection)
            return result
        return []

    def findbirthdate(self, html: str):
        return self.findbyre(r'<label>Born:</label><span>(.*?)<', html)

    def finddeathdate(self, html: str):
        return self.findbyre(r'<label>Died:</label><span>(.*?)<', html)

    def findheight(self, html: str):
        return self.findbyre(r'<label>Height:</label><span>[^<>]*?\((.*?)\)', html)

    def findweights(self, html: str):
        return [
            self.findbyre(r'<label>Weight:</label><span>([^<>]*?)\(', html),
            self.findbyre(r'<label>Weight:</label><span>[^<>]*?\((.*?)\)', html)
        ]

    def findethnicities(self, html: str):
        section = self.findbyre(r'<label>Ethnicity:</label>(.*?)</li>', html)
        if section:
            return self.findallbyre(r'>(.*?)<', section, 'ethnicity')

    def findhaircolor(self, html: str):
        return self.findbyre(r'<label>Hair:</label><span>(.*?)</span>', html, 'haircolor')

    def findoccupations(self, html: str):
        return ['Q488111']

    def findmixedrefs(self, html: str):
        return self.finddefaultmixedrefs(html)


class NelsonAtkinsAnalyzer(Analyzer):
    def setup(self):
        self.dbproperty = 'P5273'
        self.dbid = None
        self.dbname = 'Nelson-Atkins Museum'
        self.urlbase = 'https://art.nelson-atkins.org/people/{id}'
        self.hrtre = '(<h1>.*?)<div class="emuseum-detail-category'
        self.language = 'en'

    def findlongtext(self, html: str):
        return self.findbyre(r'(?s)(<h1>.*?)View All Works', html)

    def findnames(self, html) -> List[str]:
        return [self.findbyre(r'<h1>(.*?)<', html)]

    def findinstanceof(self, html: str):
        return 'Q5'

    def findnationality(self, html: str):
        return self.findbyre(r'filter=nationality.3A([^<>]*)"', html, 'country')

    def findbirthdate(self, html: str):
        return self.findbyre(r'born ([^<>]*)</', html) or self.findbyre(r'<h3>[^<>]*,([^<>]*)-', html)

    def finddeathdate(self, html: str):
        return self.findbyre(r'<h3>[^<>]*,[^<>]*-([^<>]*)', html)

    def findbirthplace(self, html: str):
        return self.findbyre(r'<div class="detailField biographyField">born:(.*?)<', html, 'city')

    def findgender(self, html: str):
        if '"/vocabularies/thesaurus/1547188"' in html:
            return 'Q6581072'

    def findincollections(self, html: str):
        return ['Q1976985']


class ArmbAnalyzer(Analyzer):
    def setup(self):
        self.dbproperty = 'P5329'
        self.dbid = None
        self.dbname = 'ARMB'
        self.urlbase = 'http://www.armb.be/index.php?id={id}'
        self.hrtre = r'<div id="before_content_block">(.*?)<!--  Text: \[end\] -->'
        self.language = 'fr'

    def findnames(self, html) -> List[str]:
        return [self.findbyre(r'"DC.title"[^<>]*content="(.*?)"', html)]

    def finddescription(self, html: str):
        return self.findbyre(r'"DC.description"[^<>]*content="(.*?)"', html)

    def findlongtext(self, html: str):
        parts = self.findallbyre(r'(?s)<p class="bodytext">(.*?)</p>', html)
        if parts:
            return '\n'.join(parts)

    def findbirthplace(self, html: str):
        return self.findbyre(r'Née? à (.*?),? (?:\(|le )', html, 'city')

    def findbirthdate(self, html: str):
        return self.findbyre(r'Née?[^<>,]*(?:le|en)\s([^<>\.\(\)]*)', html)

    def finddeathplace(self, html: str):
        return self.findbyre(r'écédée? à (.*?),? (?:\(|le )', html, 'city')

    def finddeathdate(self, html: str):
        return self.findbyre(r'écédée?[^<>]*(?:le|en)\s([^<>\.\(\)]*)', html)

    def findassociations(self, html: str):
        return self.findallbyre(r'Professeur à (.*?)\.', html, 'university')

    def findworkfields(self, html: str):
        section = self.findbyre(r'Spécialités\s*:\s*([^<>]*)', html)
        if section:
            parts = section.split(' et ')
            result = []
            for part in parts:
                result += self.findallbyre(r'([^,;\-\.]*\w)', part, 'subject')
            return result
        return self.findallbyre(
            r'Spécialité\s*:\s*([^<>]*\w)', html, 'subject')

    def findmemberships(self, html: str):
        return ['Q2124852']


class OperoneAnalyzer(Analyzer):
    def setup(self):
        self.dbproperty = 'P5359'
        self.dbid = 'Q55019828'
        self.dbname = 'Operone'
        self.urlbase = 'http://www.operone.de/komponist/{id}.html'
        self.hrtre = '<body>(.*?)<span class="vb">'
        self.language = 'de'
        self.escapehtml = True

    def findnames(self, html) -> List[str]:
        result = self.findbyre(r'<b>(.*?)<br>', html)
        if result:
            return [self.TAGRE.sub('', result)]
        return []

    def finddescription(self, html: str):
        return self.findbyre(r'<br>([^<>]*)</p>', html)

    def findinstanceof(self, html: str):
        return 'Q5'

    def findbirthdate(self, html: str):
        return self.findbyre(r'\* (.*?)(?: in |<)', html)

    def findbirthplace(self, html: str):
        return self.findbyre(r'\* [^<>]* in (.*?)<', html, 'city')

    def finddeathdate(self, html: str):
        return self.findbyre(r'\+ (.*?)(?: in |<)', html)

    def finddeathplace(self, html: str):
        return self.findbyre(r'\+ [^<>]* in (.*?)<', html, 'city')

    def findoccupations(self, html: str):
        section = self.findbyre(r'<br>([^<>]*)</p>', html)
        if section:
            result = []
            subsections = section.split(' und ')
            for subsection in subsections:
                result += [self.getdata('occupation', text) for text in subsection.split(',')]
            return result


class BnbAnalyzer(Analyzer):
    def setup(self):
        self.dbproperty = 'P5361'
        self.dbid = 'Q919757'
        self.dbname = 'British National Bibliography'
        self.urlbase = 'http://bnb.data.bl.uk/doc/person/{id}'
        self.hrtre = '(<table id="id.*?)</section>'
        self.language = 'en'

    def findnames(self, html) -> List[str]:
        return [self.findbyre(
            r'(?s)<th class="label">name</th>.*?"value">(.*?)<', html)]

    def finddescription(self, html: str):
        return self.findbyre(r'<h1>(.*?)</', html)

    def findfirstname(self, html: str):
        return self.findbyre(r'(?s)<th class="label">given name</th>.*?"value">(.*?)<', html, 'firstname')

    def findinstanceof(self, html: str):
        section = self.findbyre(r'(?s)th class="label">type</th>(.*?)>/table>', html)
        if section:
            for result in self.findallbyre(r'>(.*?)</a>', section, 'instanceof'):
                if result:
                    return result

    def findlastname(self, html: str):
        return self.findbyre(r'(?s)<th class="label">family name</th>.*?"value">(.*?)<', html, 'lastname')

    def findbirthdate(self, html: str):
        return self.findbyre(r'/birth">(.*?)<', html)

    def finddeathdate(self, html: str):
        return self.findbyre(r'/death">(.*?)<', html)

    def findisni(self, html: str):
        return self.findbyre(r'"http://isni.org/isni/(.*?)"', html)

    def findviaf(self, html: str):
        return self.findbyre(r'"http://viaf.org/viaf/(.*?)"', html)


class InternetBookAnalyzer(Analyzer):
    def setup(self):
        self.dbproperty = 'P5365'
        self.dbid = 'Q55071470'
        self.dbname = 'Internet Book Database'
        self.urlbase = 'http://www.ibdof.com/author_details.php?author={id}'
        self.hrtre = '<dl class="bio-details">(.*?)</dl>'
        self.language = 'en'

    def getvalue(self, field, html, dtype=None):
        return self.findbyre(r'<dt>{}:</dt><dd>(.*?)</dd>'
                             .format(field), html, dtype)

    def findnames(self, html) -> List[str]:
        return [self.getvalue('Full Name', html)]

    def findlongtext(self, html: str):
        return self.findbyre(r'(?s)<div class="col-right">(.*?)</div>', html)

    def findwebsite(self, html: str):
        section = self.getvalue('Website', html)
        if section:
            return self.findbyre(r'>([^<>]*)</a>', section)

    def findbirthplace(self, html: str):
        return self.getvalue('Birthplace', html, 'city')

    def findbirthdate(self, html: str):
        return self.getvalue('Birth date', html)

    def finddeathplace(self, html: str):
        return self.getvalue('Deathplace', html, 'city')

    def finddeathdate(self, html: str):
        return self.getvalue('Death date', html)

    def findresidences(self, html: str):
        return [self.getvalue('Place of Residence', html, 'city')]


class BiuSanteAnalyzer(Analyzer):
    def setup(self):
        self.dbproperty = 'P5375'
        self.dbid = None
        self.dbname = 'Bibliothèque interuniversitaire de Santé'
        self.urlbase = 'http://www.biusante.parisdescartes.fr/histoire/biographies/index.php?cle={id}'
        self.hrtre = '<h2.*?(<h2.*?</table>)'
        self.language = 'fr'
        self.escapehtml = True

    def findnames(self, html) -> List[str]:
        return self.findallbyre(r'(?s)<h2>(.*?)<', html)

    def finddescription(self, html: str):
        return self.findbyre(r'(?s)Détails biographiques<.*?<td[^<>]*>(.*?)\.?<', html)

    def findbirthdate(self, html: str):
        return self.findbyre(r'(?s)Naissance<.*?<td[^<>]*>\s*([\d/]+)', html)

    def findbirthplace(self, html: str):
        return self.findbyre(r'(?s)Naissance(?:<[^<>]*>|\s)*<td[^<>]*>[^<>]*?à(.*?)[\(<]', html, 'city')

    def finddeathdate(self, html: str):
        return self.findbyre(r'(?s)Décès<.*?<td[^<>]*>\s*([\d/]+)', html)

    def finddeathplace(self, html: str):
        return self.findbyre(r'(?s)Décès(?:<[^<>]*>|\s)*<td[^<>]*>[^<>]*?à(.*?)[\(<]', html, 'city')

    def findoccupations(self, html: str):
        section = self.findbyre(r'(?s)Détails biographiques<.*?<td[^<>]*>(.*?)\.?<', html)
        if section:
            return self.findallbyre(r'([\w\s]+)', section, 'occupation')

    def findmixedrefs(self, html: str):
        return self.finddefaultmixedrefs(html, includesocial=False)


class PoetsWritersAnalyzer(Analyzer):
    def setup(self):
        self.dbproperty = 'P5394'
        self.dbid = 'Q7207541'
        self.dbname = 'Poets & Writers'
        self.urlbase = 'https://www.pw.org/content/{id}'
        self.hrtre = '(<span property="schema:mainEntity">.*?</article>)'
        self.language = 'en'
        self.escapehtml = True

    def getvalue(self, field, html, stype=None):
        section = self.findbyre(
            r'(?s)"field-label">[^<>]*{}:[^<>]*</div>(.*?)</div><div>'
            .format(field), html)
        if section:
            return self.findbyre(r'>\s*(\w[^<>]+)<', section, stype)
        return None

    def findnames(self, html) -> List[str]:
        return [self.findbyre(r'"og:title"[^<>]*content="(.*?)"', html)]

    def finddescription(self, html: str):
        return self.getvalue('Listed as', html)

    def findlongtext(self, html: str):
        result = self.findbyre(
            '(?s)(?:<div id="field-group-authors-bio"[^<>]*>|<h3><span[^<>]*>Publications and Prizes)(.*?)</article>',
            html)
        if result:
            return result.replace('&nbsp;', ' ').replace('&lt;', '<').replace('&gt;', '>')

    def findinstanceof(self, html: str):
        return 'Q5'

    def findoccupations(self, html: str):
        section = self.getvalue('Listed as', html)
        if section:
            return [self.getdata('occupation', part) for part in section.split(',')]

    def findlanguagesspoken(self, html: str):
        section = self.getvalue('Fluent in', html)
        if section:
            return [self.getdata('language', part) for part in section.split(',')]

    def findbirthplace(self, html: str):
        return self.getvalue('Born in', html, 'city') or self.findbyre(r'born in ([\w\s]+)', html, 'city')

    def findethnicities(self, html: str):
        section = self.findbyre(r'Identifies as:[^<>]*(?:<[^<>]*>)*([^<>]*)</', html)
        if section:
            return self.findallbyre(r'([^,]+)', section, 'ethnicity (us)', skips=['religion'])

    def findreligions(self, html: str):
        section = self.findbyre(r'Identifies as:[^<>]*(?:<[^<>]*>)*([^<>]*)</', html)
        if section:
            return self.findallbyre(r'([^,]+)', section, 'religion', skips=['ethnicity', 'ethnicity (us)'])

    def findwebsite(self, html: str):
        return self.findbyre(r'Website:[^<>]*(?:<[^<>]*>)*<a[^<>]*href="([^<>]*?)"', html)


class ScottishArchitectsAnalyzer(Analyzer):
    def setup(self):
        self.dbproperty = 'P5308'
        self.dbid = 'Q16973743'
        self.dbname = 'Dictionary of Scottish Architects'
        self.urlbase = 'http://www.scottisharchitects.org.uk/architect_full.php?id={id}'
        self.hrtre = '</h1>(.*?)(?:<h1|<td[^<>]*>Bio Notes)'
        self.language = 'en'

    def findnames(self, html) -> List[str]:
        return [self.findbyre(r'<b>(.*?)<', html)]

    def findlongtext(self, html: str):
        return self.findbyre(r'Bio Notes:(.*?)</tr>', html)

    def findinstanceof(self, html: str):
        return 'Q5'

    def findoccupations(self, html: str):
        section = self.findbyre(r'Designation:(.*?)</tr>', html)
        if section:
            result = []
            for subsection in self.findallbyre(r'>([^<>]*)</td', section):
                result += self.findallbyre(r'([\w\s]+)', subsection, 'occupation')
            return result

    def findbirthdate(self, html: str):
        return self.findbyre(r'Born:</td>.*?>(?:c\.)?([^<>]*)</td>', html)

    def finddeathdate(self, html: str):
        return self.findbyre(r'Died:</td>.*?>(?:c\.)?([^<>]*)</td>', html)

    def findresidences(self, html: str):
        section = self.findbyre(r'Addresses</h2>(<table.*?</table>)', html)
        if section:
            return self.findallbyre(
                "<tr[^<>]*><td><img src='images/table_item.gif'[^<>]*></td><td>[^<>]*?([^<>,]*(?:,[^<>,]*)?)<", section,
                'city')


class SFAnalyzer(Analyzer):
    def setup(self):
        self.dbproperty = 'P5357'
        self.dbid = 'Q5099499'
        self.dbname = 'Encyclopedia of Science Fiction'
        self.urlbase = 'http://www.sf-encyclopedia.com/entry/{id}'
        self.hrtre = '(<p>.*?)<h2'
        self.language = 'en'

    def findlongtext(self, html: str):
        return self.findbyre(r'(?s)(<p>.*?)<h\d', html)

    def findbirthdate(self, html: str):
        return self.findbyre(r'<b>born</b>[^<>]*?([^<>:]*)<', html)

    def finddeathdate(self, html: str):
        return self.findbyre(r'<b>died</b>[^<>]*?([^<>:]*)<', html)

    def findbirthplace(self, html: str):
        return self.findbyre(r'<b>born</b>([^<>]*):', html, 'city')

    def finddeathplace(self, html: str):
        return self.findbyre(r'<b>died</b>([^<>]*):', html, 'city')

    def findnationality(self, html: str):
        return self.findbyre(r'<p>\([\s\d\-]+\)\s*(\w+)', html, 'country')

    def findoccupations(self, html: str):
        section = self.findbyre(r'<p>\([\s\d\-]+\)([\w\s]+)', html)
        if section:
            return self.findallbyre(r'(\w+)', section, 'occupation')

    def findmixedrefs(self, html: str):
        return [
            ('P1233', self.findbyre(r'http://www.isfdb.org/cgi-bin/ea.cgi\?(\d+)', html))
        ]


class NatGeoCanadaAnalyzer(Analyzer):
    def setup(self):
        self.dbproperty = 'P5368'
        self.dbid = None
        self.dbname = 'National Gallery of Canada'
        self.urlbase = 'https://www.gallery.ca/collection/artist/{id}'
        self.hrtre = '(<div[^<>]* group-right .*?clearfix">)'
        self.language = 'en'

    def findnames(self, html) -> List[str]:
        return self.findallbyre(r'>Name(?:<[^<>]*>|\s)*(.*?)<', html)

    def findlongtext(self, html: str):
        return self.findbyre(r'(?s)(<div class="wrapper-max-width.*?)<div class="col-xs-12', html)

    def finddescription(self, html: str):
        return self.findbyre(r'<meta name="description" content="(.*?)"', html)

    def findbirthplace(self, html: str):
        return self.findbyre(r'Born</div>(.*?)<', html, 'city')

    def findbirthdate(self, html: str):
        return self.findbyre(r'Born</div>[^<>]*(?:<[^<>]*>)*([\d\-]+)<', html)

    def finddeathplace(self, html: str):
        return self.findbyre(r'Died</div>(.*?)<', html, 'city')

    def finddeathdate(self, html: str):
        return self.findbyre(r'Died</div>[^<>]*(?:<[^<>]*>)*([\d\-]+)<', html)

    def findnationalities(self, html: str):
        section = self.findbyre(r'>Nationality(?:<[^<>]*>|\s)*(.*?)<', html)
        if section:
            return self.findallbyre(r'([^,]+)', re.sub(r'\(.*?\)', ',', section), 'country')

    def findethnicity(self, html: str):
        section = self.findbyre(r'>Nationality(?:<[^<>]*>|\s)*(.*?)<', html)
        if '(' in section:
            return self.findbyre(r'(.*)', section, 'ethnicity')

    def findresidences(self, html: str):
        return self.findallbyre(r'lives ([^"<>]+)', html, 'city')


class EntomologistAnalyzer(Analyzer):
    def setup(self):
        self.dbproperty = 'P5370'
        self.dbid = 'Q57831640'
        self.dbname = 'Entomologists of the World'
        self.urlbase = 'http://sdei.senckenberg.de/biographies/information.php?id={id}'
        self.hrtre = '<SPAN[^<>]*>(Name:.*?)<SPAN[^<>]*>Updated:'
        self.language = 'en'

    def getvalue(self, field, html, dtype=None):
        return self.findbyre(
            r'<SPAN[^<>]*>{}:\s*</SPAN>(?:\s|<[^<>]*>)*([^<>]*)'
            .format(field), html, dtype)

    def getvalues(self, field, html, dtype=None) -> List[str]:
        section = self.getvalue(field, html)
        if section:
            return self.findallbyre('([^,;]*)', section, dtype)
        return []

    def findnames(self, html) -> List[str]:
        return [self.getvalue('Name', html)]

    def findlongtext(self, html: str):
        return self.getvalue('Remark', html)

    def findbirthdate(self, html: str):
        return self.getvalue('Date of birth', html)

    def findbirthplace(self, html: str):
        section = self.getvalue('Place of birth', html)
        if section:
            return self.findbyre(r'^\s*(?:in ?)(.*)', section, 'city')
        return None

    def finddeathdate(self, html: str):
        return self.getvalue('Da(?:te|ys) of death', html)

    def finddeathplace(self, html: str):
        section = self.getvalue('Place of death', html)
        if section:
            return self.findbyre(r'^\s*(?:in ?)(.*)', section, 'city')
        return None

    def findgender(self, html: str):
        return self.getvalue('Gender', html, 'gender')

    def findoccupations(self, html: str):
        return self.getvalues('Professions', html, 'occupation')

    def findworkfields(self, html: str):
        return self.getvalues('Specialisms', html, 'subject')

    def findmixedrefs(self, html: str):
        return [('P835', self.getvalue('Akronyms', html))]


class FantasticFictionAnalyzer(Analyzer):
    def setup(self):
        self.dbproperty = 'P5408'
        self.dbid = 'Q21777935'
        self.dbname = 'Fantastic Fiction'
        self.urlbase = 'https://www.fantasticfiction.com/{id}/'
        self.hrtre = '<div class="authorheading">(.*?)</div>'
        self.language = 'en'
        self.escapehtml = True

    def findinstanceof(self, html: str):
        return 'Q5'

    def findnames(self, html) -> List[str]:
        result = [self.findbyre(r'<title>(.*?)</title>', html)]
        result += self.findallbyre(r'<h1[^<>]*>(.*?)</h1>', html)
        result += self.findallbyre(r'<b>(.*?)</b>', html)
        result += self.findallbyre(r'>aka\s*<a[^<>]*>(.*?)<', html)
        return result

    def findlongtext(self, html: str):
        return self.findbyre(r'(?s)<div class="authorheading">.*?</div>(.*?)<div', html)

    def finddescription(self, html: str):
        prepart = self.findbyre(r'(?s)<div class="authorheading">.*?</div>(.*?)\.', html)
        return self.findbyre(r'(.*)', prepart)

    def findbirthdate(self, html: str):
        return self.findbyre(r'>b\.(?:<[^<>]*>)*(.+?)<', html)

    def findnationality(self, html: str):
        return self.findbyre(r'</h1><br><a[^<>]*>(.*?)<', html, 'country') or \
               self.findbyre(r'</h1><br><img alt="([^"]+)\s', html, 'country')

    def findsiblings(self, html: str):
        return self.findallbyre(r'(?:Brother|Sister) of <a[^<>]*>(.*?)<', html, 'person')

    def findfather(self, html: str):
        for person in self.findallbyre(r'(?:Son|Daughter) of <a[^<>]*>(.*?)<', html, 'male-person'):
            if person:
                return person

    def findmother(self, html: str):
        for person in self.findallbyre(r'(?:Son|Daughter) of <a[^<>]*>(.*?)<', html, 'female-person'):
            if person:
                return person

    def findchildren(self, html: str):
        return self.findallbyre(r'(?:Father|Mother) of <a[^<>]*>(.*?)<', html, 'person')

    def findgenres(self, html: str):
        section = self.findbyre(r'Genres: (.*)', html)
        if section:
            return self.findallbyre(r'<a[^<>]*>(.*?)<', section, 'literature-genre', alt=['genre'])

    def findawards(self, html: str):
        section = self.findbyre(r'(?s)>Awards<.*?<table[^<>]*>(.*?)</table>', html)
        if section:
            return self.findallbyre(r'<a[^<>]*>(?:<[^<>]*>)*([^<>]*)(?:<[^<>]*>)*</a>[^<>]*winner', html, 'award')

    def findnominations(self, html: str):
        section = self.findbyre(r'(?s)>Awards<.*?<table[^<>]*>(.*?)</table>', html)
        if section:
            return self.findallbyre(r'<a[^<>]*>(?:<[^<>]*>)*([^<>]*)(?:<[^<>]*>)*</a>[^<>]*nominee', html, 'award')


class WhonameditAnalyzer(Analyzer):
    def setup(self):
        self.dbproperty = 'P5415'
        self.dbid = 'Q66683'
        self.dbname = 'Who named it?'
        self.urlbase = 'http://www.whonamedit.com/doctor.cfm/{id}.html'
        self.hrtre = '(<h1.*?<div id="description">.*?</div>)'
        self.language = 'en'

    def findnames(self, html) -> List[str]:
        return [
            self.findbyre(r'<h1[^<>]*>(.*?)<', html),
            self.findbyre(r'(?s)</h2>\s*<p><strong>(.*?)<', html)
        ]

    def findlongtext(self, html: str):
        return self.findbyre(r'(?s)(<div id="description">.*?</div>)', html)

    def findinstanceof(self, html: str):
        return 'Q5'

    def findbirthdate(self, html: str):
        return self.findbyre(r'born (\w+ \d+, \d+)', html) or \
               self.findbyre(r'(?s)Born</td>\s*<td>(.*?)<', html)

    def finddeathdate(self, html: str):
        return self.findbyre(r'died (\w+ \d+, \d+)', html) or \
               self.findbyre(r'(?s)Died</td>\s*<td>(.*?)<', html)

    def findbirthplace(self, html: str):
        return self.findbyre(r'born [^<>]*?\d, ([A-Za-z][^<>]*?);', html, 'city')

    def finddeathplace(self, html: str):
        return self.findbyre(r'died [^<>]*?\d, ([A-Za-z][^<>]*?)\.', html, 'city')

    def findnationality(self, html: str):
        return self.findbyre(r'(?s)<div id="short-description">\s*(\w+)', html, 'country')

    def findoccupations(self, html: str):
        section = self.findbyre(r'(?s)<div id="short-description">\s*\w+([^<>]*?), born', html)
        if section:
            return self.findallbyre(r'(\w{4,})', section, 'occupation')


class TradingCardAnalyzer(Analyzer):
    def setup(self):
        self.dbproperty = 'P5421'
        self.dbid = None
        self.dbname = 'Trading Card Database'
        self.urlbase = 'https://www.tradingcarddb.com/Person.cfm/pid/{id}/'
        self.hrtre = '(<h4.*?)</div>'
        self.language = 'en'

    def findnames(self, html) -> List[str]:
        return self.findallbyre(r'<h4>(.*?)<', html) \
            + self.findallbyre(r'(?s)</h4>\s*<strong>(.*?)<', html)

    def findlongtext(self, html: str):
        return self.findbyre(r'(?s)(<h4.*?)</div>', html)

    def findbirthdate(self, html: str):
        return self.findbyre(r'Born:</strong>\s*(\w+ \d+, \d+)', html)

    def finddeathdate(self, html: str):
        return self.findbyre(r'Died:</strong>\s*(\w+ \d+, \d+)', html)

    def findbirthplace(self, html: str):
        return self.findbyre(r'Born:</strong>[^<>]* in ([^<>]*)', html)

    def finddeathplace(self, html: str):
        return self.findbyre(r'Died:</strong>[^<>]* in ([^<>]*)', html)

    def findschools(self, html: str):
        return self.findallbyre(r'<strong>College:</strong>(.*?)<', html)

    def findsportteams(self, html: str):
        return self.findallbyre(r'"/Team\.cfm/[^<>"]+">(.*?)</a>', html)

    def findsports(self, html: str):
        section = self.findbyre(r'<ol class="breadcrumb">(.*?)</ol>', html)
        if section:
            return self.findallbyre(r'"/ViewAll\.cfm/[^<>"]*">(.*?)<', section, 'sport (US)')


class BedethequeAnalyzer(Analyzer):
    def setup(self):
        self.dbproperty = 'P5491'
        self.dbid = 'Q2876969'
        self.dbname = 'Bedetheque'
        self.urlbase = 'https://www.bedetheque.com/auteur-{id}-BD-.html'
        self.hrtre = '<ul class="auteur-info">(.*?)</ul>'
        self.language = 'fr'

    def findinstanceof(self, html: str):
        return 'Q5'

    def findnames(self, html) -> List[str]:
        return self.findallbyre(r'<h2>(.*?)<', html) \
            + [self.findbyre(r'<label>Pseudo :</label>(.*?)</li>', html)]

    def findfirstname(self, html: str):
        return self.findbyre(r'<label>Prénom :</label>(?:<span>)?(.*?)</', html, 'firstname')

    def findlastname(self, html: str):
        return self.findbyre(r'<label>Nom :</label>(?:<span>)?(.*?)</', html, 'lastname')

    def findlongtext(self, html: str):
        return self.findbyre(r'(?s)<h3>Sa biographie</h3>.*?<div class="block-big block-big-last">(.*?)</div>', html)

    def findpseudonyms(self, html: str):
        return [self.findbyre(r'<label>Pseudo :</label>(.*?)</li>', html)]

    def findbirthdate(self, html: str):
        return self.findbyre(r'<label>Naissance :</label>le ([\d/]+)', html)

    def finddeathdate(self, html: str):
        return self.findbyre(r'<li><label>Décès :</label>le ([\d/]+)', html)

    def findnationality(self, html: str):
        return self.findbyre(r'<span class="pays-auteur">\(?(.*?)\)?<', html, 'country')

    def findwebsite(self, html: str):
        return self.findbyre(r'Site internet :.*?"(.*?)"', html)


class Edit16Analyzer(Analyzer):
    def setup(self):
        self.dbproperty = 'P5492'
        self.dbid = 'Q1053428'
        self.dbname = 'Edit16'
        self.urlbase = 'http://edit16.iccu.sbn.it/scripts/iccu_ext.dll?fn=11&res={id}'
        self.hrtre = '<TABLE width="100%">(.*?)</TABLE>'
        self.language = 'it'

    def getvalue(self, field, html, dtype=None):
        return self.findbyre('<B>{}:(?:<[^<>]*>)*([^<>]+)<'
                             .format(field), html, dtype)

    def findnames(self, html) -> List[str]:
        result = []
        section = self.getvalue('Nome', html)
        if section:
            result.append(self.findbyre(r'([^&]+)', section).replace(':', ''))
        pywikibot.info(f'section: {section}, result: {result}')
        section = self.getvalue('Nome su edizioni', html)
        if section:
            result += self.findallbyre(r'([^;]+)', section)
        pywikibot.info(f'section: {section}, result: {result}')
        section = self.getvalue('Fonti', html)
        if section:
            result += self.findallbyre(r'\((.*?)\)', section)
        pywikibot.info(f'section: {section}, result: {result}')
        return result

    def finddescriptions(self, html: str):
        result = []
        section = self.getvalue('Nome', html)
        if section:
            result.append(self.findbyre(r'&lt;(.*?)&', section))
        section = self.getvalue('Notizie', html)
        if section:
            result += self.findallbyre(r'([^\.]*)', section)
        return result

    def findbirthplace(self, html: str):
        return self.findbyre(r' nato a (\w+)', html, 'city')

    def finddeathplace(self, html: str):
        return self.findbyre(r' morto a (\w+)', html, 'city')

    def findbirthdate(self, html: str):
        return self.findbyre(r' nato a[\w\s]* (?:nel|il) ([\w\s]*)', html)

    def finddeathdate(self, html: str):
        return self.findbyre(r' nato a[\w\s]* (?:nel|il) ([\w\s]*)', html)

    def findoccupation(self, html: str):
        return self.getvalue('Notizie', html, 'occupation')


class RismAnalyzer(Analyzer):
    def setup(self):
        self.dbproperty = 'P5504'
        self.dbid = 'Q2178828'
        self.dbname = 'RISM'
        self.urlbase = 'https://opac.rism.info/LDBrowser/risma:{id}'
        self.hrtre = '<body>(.*?)(?:<div class="searchIdLink">|</body>)'
        self.language = 'de'

    def getvalue(self, field, html, dtype=None):
        return self.findbyre(
            '<span class="label">{}</span>: <span class="value">(.*?)</span>'
            .format(field), html, dtype)

    def getvalues(self, field, html, dtype=None, splitter=',') -> List[str]:
        field = self.getvalue(field, html)
        if field:
            if splitter == '<':
                return self.findallbyre('>(.*?)<', '>' + field + '<', dtype)
            return self.findallbyre(f'[^{splitter}]+', field, dtype)
        return []

    def findnames(self, html) -> List[str]:
        return [self.getvalues('Name', html, splitter='<')[0]] \
            + self.getvalues('Namensvarianten', html, splitter='<')

    def finddescription(self, html: str):
        return self.getvalue('Beruf', html)

    def findnationalities(self, html: str):
        return self.getvalues('Nationalität', html, 'country')

    def findworkplaces(self, html: str):
        return self.getvalues('Ort', html, 'city')

    def findoccupations(self, html: str):
        return self.getvalues('Beruf', html, 'occupation')

    def findmixedrefs(self, html: str):
        return self.finddefaultmixedrefs(html)

    def findbirthdate(self, html: str):
        if 'fl.' not in (self.getvalue('Schaffensjahre', html) or ''):
            return (self.getvalue('Schaffensjahre', html) or '').split('-')[0]

    def finddeathdate(self, html: str):
        if 'fl.' not in (self.getvalue('Schaffensjahre', html) or ''):
            return (self.getvalue('Schaffensjahre', html) or '').split('-')[-1]

    def findfloruit(self, html: str):
        if 'fl.' in (self.getvalue('Schaffensjahre', html) or ''):
            return self.getvalue('Schaffensjahre', html).replace('fl.', '')


class OmdbAnalyzer(Analyzer):
    def setup(self):
        self.dbproperty = 'P5534'
        self.dbid = 'Q27653527'
        self.dbname = 'Open Media Database'
        self.urlbase = 'https://www.omdb.org/person/{id}'
        self.hrtre = '<h3>Daten</h3>(.*?)<div class="headline-box">'
        self.language = 'de'

    def findinstanceof(self, html: str):
        return 'Q5'

    def findnames(self, html) -> List[str]:
        result = self.findallbyre(r'<h2>(.*?)</h2>', html)
        section = self.findbyre(
            r'(?s)<h3>auch bekannt als</h3>(.*?)<div class="headline-box">',
            html)
        if section:
            result += self.findallbyre(r'(?s)>([^<>]*)<', section)
        return result

    def finddescriptions(self, html: str):
        return self.findallbyre(r'<meta content="(.*?)"', html) + \
               [self.findbyre(r'(?s)<div class="parent-breadcrumb">.*?</div>\s*<h2>[^<>]*</h2>\s*<h3>(.*?)</h3>', html)]

    def findlongtext(self, html: str):
        return self.findbyre(r'(?s)<p id="abstract">(.*?)</div>', html)

    def findoccupations(self, html: str):
        section = self.findbyre(r'(?s)<div class="parent-breadcrumb">.*?</div>\s*<h2>[^<>]*</h2>\s*<h3>(.*?)</h3>', html)
        if section:
            return self.findallbyre(r'">([^<>]*)</a>', section, 'occupation')

    def findgender(self, html: str):
        return self.findbyre(r'(?s)<div class="title">Geschlecht:</div>\s*<div class="value">(.*?)<', html, 'gender')

    def findbirthdate(self, html: str):
        return self.findbyre(r'(?s)<div class="title">Geburtstag:</div>\s*<div class="value">(.*?)<', html)

    def findbirthplace(self, html: str):
        return self.findbyre(r'(?s)<div class="title">Geburtsort:</div>\s*<div class="value">(.*?)<', html, 'city')

    def finddeathdate(self, html: str):
        return self.findbyre(r'(?s)<div class="title">Todestag:</div>\s*<div class="value">(.*?)<', html)

    def finddeathplace(self, html: str):
        return self.findbyre(r'(?s)<div class="title">Todesort:</div>\s*<div class="value">(.*?)<', html, 'city')

    def findmixedrefs(self, html: str):
        return self.finddefaultmixedrefs(html)


class RedTubeAnalyzer(Analyzer):
    def setup(self):
        self.dbproperty = 'P5540'
        self.dbid = 'Q1264738'
        self.dbname = 'RedTube'
        self.urlbase = 'https://www.redtube.com/pornstar/{id}'
        self.hrtre = '<div class="pornstar_info_big_left">(.*?)<div class="pornstar_buttons">'
        self.language = 'en'
        self.escapehtml = True
        self.showurl = False

    def getvalue(self, field, html, dtype=None):
        return self.findbyre(
            r'(?is)<span class="pornstar_more_details_label">{}</span>\s*<span class="pornstar_more_details_data">(.*?)<'
            .format(field), html, dtype)

    def findnames(self, html) -> List[str]:
        result = self.findallbyre('<h1[^<>]*>(.*?)<', html)
        section = self.getvalue('Performer AKA', html)
        if section:
            result += section.split(',')
        return result

    def findlongtext(self, html: str):
        return self.findbyre(r'(?s)<div class="pornstar_info_bio[^<>]*long_description">(?:\s|<[^<>]*>)*(.*?)<', html) or\
            self.findbyre(r'(?s)<div class="pornstar_info_bio[^<>]*description">(?:\s|<[^<>]*>)*(.*?)<', html)

    def findheight(self, html: str):
        section = self.getvalue('Height', html)
        if section:
            return self.findbyre(r'(\d+ cm)', section)

    def findhaircolor(self, html: str):
        return self.getvalue('Hair Color', html, 'haircolor')

    def findbirthdate(self, html: str):
        return self.getvalue('Date Of Birth', html)

    def findbirthplace(self, html: str):
        return self.getvalue('Birth Place', html, 'city')

    def findfloruit(self, html: str):
        section = self.getvalue('Years Active', html)
        if section:
            return section.replace(' to ', ' - ')

    def findweights(self, html: str):
        section = self.getvalue('Weight', html)
        if section:
            return self.findallbyre(r'(\d+ \w+)', section)

    def findethnicities(self, html: str):
        return [
            self.getvalue('Ethnicity', html, 'ethnicity'),
            self.getvalue('Background', html, 'ethnicity')
        ]

    def findwebsite(self, html: str):
        return self.findbyre(r'(?s)href="([^<>"]*)"[^<>]*>(?:\s|<[^<>]*>)*Official Site', html)

    def findoccupations(self, html: str):
        return ['Q488111']


class NoosfereAnalyzer(Analyzer):
    def setup(self):
        self.dbproperty = 'P5570'
        self.dbid = None
        self.dbname = 'NooSFere'
        self.urlbase = 'https://www.noosfere.org/livres/auteur.asp?numauteur={id}&Niveau=bio'
        self.hrtre = '<td[^<>]*>[^<>]*Bio/Infos.*?(<.*?</TABLE>.*?</tr>)'
        self.language = 'fr'
        self.escapeunicode = True

    def prepare(self, html: str):
        return html.replace('\\n', '\n').replace('\\t', ' ').replace('\\r', '').replace("\\'", "'").\
            replace('\\xe9', 'é').replace('\\xe8', 'è').replace('\\xea', 'ê').replace('&nbsp;', ' ')

    def findinstanceof(self, html: str):
        return 'Q5'

    def findnames(self, html) -> List[str]:
        section = self.findbyre(r'Pseudonyme\(s\)(.*?)</DIV>', html)
        if section:
            result = self.findallbyre(r'>([^<>]*)<', section)
            return [name.title() for name in result]
        return []

    def findlongtext(self, html: str):
        return self.findbyre(r'<!-- Corps de la page -->(.*?)</TABLE>', html)

    def findbirthdate(self, html: str):
        return self.findbyre(r'Naissance\s?:[^<>]*?([^<>,]*?)\.?<', html)

    def findbirthplace(self, html: str):
        return self.findbyre(r'Naissance\s?:([^<>]*),', html, 'city')

    def finddeathdate(self, html: str):
        return self.findbyre(r'D.c.s :[^<>]*?([^<>,]*?)\.?<', html)

    def finddeathplace(self, html: str):
        return self.findbyre(r'D.c.s :([^<>]*),', html, 'city')

    def findnationality(self, html: str):
        return self.findbyre(r"'Auteurs du m.me pays'>(.*?)<", html, 'country')

    def findawards(self, html: str):
        return self.findallbyre(r'&numprix=\d+">(.*?)<', html, 'award')

    def findwebsite(self, html: str):
        return self.findbyre(r"'([^<>']*)'>Site officiel", html)

    def findmixedrefs(self, html: str):
        return self.finddefaultmixedrefs(html)


class ArtcyclopediaAnalyzer(Analyzer):
    def setup(self):
        self.dbproperty = 'P5597'
        self.dbid = 'Q3177776'
        self.dbname = 'Artcyclopedia'
        self.urlbase = 'http://www.artcyclopedia.com/artists/{id}.html'
        self.hrtre = '(<H1.*?)<TABLE WIDTH="100%"'
        self.language = 'en'
        self.escapehtml = True

    def prepare(self, html: str):
        return html.replace('&nbsp;', ' ')

    def findinstanceof(self, html: str):
        return 'Q5'

    def findnames(self, html) -> List[str]:
        return self.findallbyre(r'<H1[^<>]*>(.*?)<', html) \
            + self.findallbyre(
                r'Also known as:[^<>]*(?:<[^<>]*>)*([^<>]+)</', html)

    def finddescription(self, html: str):
        result = self.findbyre(r'<B>(.*?)</B>', html)
        if result:
            return self.TAGRE.sub(' ', result).strip('[]')

    def findlongtext(self, html: str):
        return self.findbyre(r'(?s)(<H1.*?)<TABLE WIDTH="100%"', html)

    def findmovements(self, html: str):
        section = self.findbyre(r'<B>(.*?)</B>', html)
        if section:
            return self.findallbyre(r'<A[^<>]*>(.*?)<', section, 'movement')

    def findnationality(self, html: str):
        return self.findbyre(r'<B>\[(\w+)', html, 'country')

    def findbirthdate(self, html: str):
        return self.findbyre(r'(\d+)-\d*\]<B>', html)

    def finddeathdate(self, html: str):
        return self.findbyre(r'-(\d+)\]<B>', html)

    def findincollections(self, html: str):
        section = self.findbyre(r'(?s)><A NAME="museums">(.*?)<A NAME', html)
        if section:
            return self.findallbyre(r'>([^<>]*)</A>', section, 'museum')


class AcademieFrancaiseAnalyzer(Analyzer):
    def setup(self):
        self.dbproperty = 'P5645'
        self.dbid = None
        self.dbname = 'Académie française'
        self.urlbase = 'http://www.academie-francaise.fr/{id}'
        self.hrtre = '(<h1>.*?)<div id="footer"'
        self.language = 'fr'

    def findnames(self, html) -> List[str]:
        return [
            self.findbyre(r'<title>(.*?)[\|<]', html),
            self.findbyre(r'(?s)<h1>(.*?)<', html)
        ]

    def findlongtext(self, html: str):
        return self.findbyre(r'(?s)(<h2>\s*Prix.*?)<div id="footer"', html)

    def findawards(self, html: str):
        section = self.findbyre(r'(?s)(<h2>\s*Prix.*?)<div id="footer"', html)
        if section:
            return self.findallbyre(r'">(.*?)</a>', section, 'award')


class AngelicumAnalyzer(Analyzer):
    def setup(self):
        self.dbproperty = 'P5731'
        self.dbid = None
        self.dbname = 'Angelicum'
        self.urlbase = 'https://pust.urbe.it/cgi-bin/koha/opac-authoritiesdetail.pl?marc=1&authid={id}'
        self.hrtre = '<h1>Entry[^<>]*</h1>(.*?)</div>'
        self.language = 'it'

    def instanceof(self, html: str):
        return self.findbyre(r' di ([^<>]*)</title>', html, 'instanceof')

    def findnames(self, html) -> List[str]:
        return self.findallbyre(r'(?s)<b>Nome d[^<>]*</b>(.*?)</', html)

    def findbirthdate(self, html: str):
        return self.findbyre(r'(?s)<b>Data di nascita:</b>(.*?)</', html)

    def finddeathdate(self, html: str):
        return self.findbyre(r'(?s)<b>Data di morte:</b>(.*?)</', html)

    def findlanguagesspoken(self, html: str):
        return self.findallbyre(r'(?s)<b>Codice di lingua:</b>(.*?)</', html, 'language')

    def findnationalities(self, html: str):
        return self.findallbyre(r'(?s)<b>Luogo di nascita:</b>(.*?)</', html, 'country')

    def findgender(self, html: str):
        return self.findbyre(r'(?s)<b>Sesso:</b>(.*?)</', html, 'gender')

    def findmixedrefs(self, html: str):
        return self.finddefaultmixedrefs(html, includesocial=False)


class PuscAnalyzer(Analyzer):
    def setup(self):
        self.dbproperty = 'P5739'
        self.dbid = None
        self.dbname = 'PUSC'
        self.urlbase = 'http://catalogo.pusc.it/cgi-bin/koha/opac-authoritiesdetail.pl?authid={id}&marc=1'
        self.hrtre = '</h1>(.*?)</div>'
        self.language = 'it'

    def findnames(self, html) -> List[str]:
        return self.findallbyre(r'(?s) name[^<>]*:</b>(.*?)[<\(]', html)

    def findlongtext(self, html: str):
        return '\n'.join(self.findallbyre(r'(?s)Source citation:</b>(.*?)<', html))

    def findbirthdate(self, html: str):
        return self.findbyre(r'(?s)Birth date:</b>(.*?)<', html)

    def finddeathdate(self, html: str):
        return self.findbyre(r'(?s)Death date:</b>(.*?)<', html)

    def findgender(self, html: str):
        return self.findbyre(r'(?s)Gender:</b>(.*?)<', html, 'gender')

    def getcode(self, code, html):
        return self.findbyre(
            r'(?s)<b>Source of number or code:</b>\s*{}</p>\s*<p><b>Standard number or code:</b>\s*(.*?)</p>'
            .format(code), html)

    def findmixedrefs(self, html: str):
        return [
                   ('P214', self.getcode('viaf', html)),
                   ('P269', self.getcode('idref', html)),
                   ('P244', self.getcode('lccn', html)),
               ] + \
               self.finddefaultmixedrefs(html, includesocial=False)

    def findisni(self, html: str):
        return self.getcode('isni', html)


class CwaAnalyzer(Analyzer):
    def setup(self):
        self.dbproperty = 'P5747'
        self.dbid = None
        self.dbname = 'CWA'
        self.urlbase = 'https://thecwa.co.uk/find-an-author/{id}/'
        self.hrtre = '(<h1.*?)<h3>Books'
        self.language = 'en'

    def findnames(self, html) -> List[str]:
        return self.findbyre(r'>([^<>]*)</h1>', html)

    def findinstanceof(self, html: str):
        return 'Q5'

    def findoccupations(self, html: str):
        return ['Q36180']

    def findwebsite(self, html: str):
        return self.findbyre(r'"([^"<>]*)">Website<', html)

    def findmixedrefs(self, html: str):
        return self.finddefaultmixedrefs(html)

    def findawards(self, html: str):
        section = self.findbyre(r'(?s)<h3>Other Awards</h3>(.*?)<h\d', html)
        if section:
            parts = self.findallbyre(r'>([^<>]*)</p>', section)
            result = []
            for part in parts:
                result += self.findallbyre(r'([^,]+)', part, 'award')
            return result


class IgdbAnalyzer(Analyzer):
    def setup(self):
        self.dbproperty = 'P5794'
        self.dbid = 'Q20056333'
        self.dbname = 'Internet Game Database'
        self.urlbase = 'https://www.igdb.com/games/{id}'
        self.hrtre = r'<h3 class="underscratch[^<>]*>(?:<[^<>]*>|\s)*Information(<.*?)<h3 class="underscratch'
        self.language = 'en'

    def getvalue(self, field, html, dtype=None):
        return self.findbyre(
            '<label>{}:</label>(.*?)<(?:label|<h3 class="underscratch)'
            .format(field), html, dtype)

    def getvalues(self, field, html, dtype=None, alt=None) -> List[str]:
        section = self.getvalue(field, html)
        if section:
            return self.findallbyre('>([^<>]+)<', section,
                                    dtype=dtype, alt=alt)
        return []

    def findinstanceof(self, html: str):
        return ['Q7889']

    def findnames(self, html) -> List[str]:
        result = self.findallbyre('<title>(.*?)<', html) \
            + self.findallbyre('Alternative names', html)
        return [self.findbyre(r'([^\(\)]+)', res) for res in result]

    def finddescriptions(self, html: str):
        return self.findallbyre('(?s)content="(.*?)"', html)

    def findmixedrefs(self, html: str):
        return self.finddefaultmixedrefs(html)

    def findpubdates(self, html: str):
        section = self.getvalue('Release Dates', html)
        if section:
            return self.findallbyre(r'datetime="([\d\-]+)', section)
        return None

    def finddevelopers(self, html: str):
        return self.getvalues('Developers', html, 'gamecompany')

    def findpublishers(self, html: str):
        return self.getvalues('Publishers', html, 'gamecompany')

    def findgamemodes(self, html: str):
        return self.getvalues('Game Modes', html, 'gamemode')

    def findgenres(self, html: str):
        return self.getvalues('Genres', html, 'gamegenre')

    def findfranchises(self, html: str):
        return self.getvalues('Series', html, 'franchise', alt=['series']) \
            + self.getvalue('Franchises', html, 'franchise')

    def findengines(self, html: str):
        return self.getvalues('Game engine', html, 'engine')


class MathOlympAnalyzer(Analyzer):
    def setup(self):
        self.dbproperty = 'P5819'
        self.dbid = None
        self.dbname = 'International Mathematical Olympiad'
        self.urlbase = 'http://www.imo-official.org/participant_r.aspx?id={id}'
        self.hrtre = '<table>(.*?)</table>'
        self.language = 'en'

    def findnames(self, html) -> List[str]:
        return self.findallbyre(r'<h\d*>(.*?)<', html)

    def findparticipations(self, html: str):
        return ['Q7983']

    def findnationalities(self, html: str):
        return self.findallbyre('"country_team[^"]*">(.*?)<', html, 'country')


class MuziekwebAnalyzer(Analyzer):
    def setup(self):
        self.dbproperty = 'P5882'
        self.dbid = 'Q18088607'
        self.dbname = 'Muziekweb'
        self.urlbase = 'https://www.muziekweb.nl/Link/{id}/'
        self.hrtre = r'(<h4 class="subheader">.*?<div class="widget-area">)'
        self.language = 'nl'
        self.escapehtml = True
        self._name = None

    @property
    def name(self):
        if self._name is None:
            self._name = self.findbyre('<title>(.*?)(?: - |<)', self.html)
        return self._name

    def findnames(self, html) -> List[str]:
        return [self.name] + self.findallbyre(
            r'itemprop="\w*[nN]ame">(.*?)<', html)

    def findlongtext(self, html: str):
        return self.findbyre(r'(?s)(<p class="cat-article-text">.*?</p>)', html)

    def finddescription(self, html: str):
        return self.findbyre(r'(?s)<p class="cat-article-text">(.*?)[\.<]', html)

    def findmixedrefs(self, html: str):
        section = self.findbyre(r'(?s)<h3>Externe links</h3>(.*?)<script>', html)
        if section:
            return self.finddefaultmixedrefs(section)

    def findisni(self, html: str):
        return self.findbyre(r'href="(\d{16})"', html)

    def findinstruments(self, html: str):
        sections = self.findallbyre(self.name + r'\s*<span class="cat-role">\((.*?)\)', html)
        result = []
        for section in sections:
            result += self.findallbyre('([^,]+)', section, 'instrument')
        return result


class LetterboxdAnalyzer(Analyzer):
    def setup(self):
        self.dbproperty = 'P6127'
        self.dbid = 'Q18709181'
        self.dbname = 'Letterboxd'
        self.urlbase = 'view-source:https://letterboxd.com/film/{id}/'
        self.hrtre = '(<div id="tabbed-content".*?)<p class="text-link '
        self.language = 'en'
        self.escapehtml = True

    def findinstanceof(self, html: str):
        return 'Q11424'

    def findlongtext(self, html: str):
        return self.findbyre(r'<meta name="description" content="(.*?)"', html)

    def finddescriptions(self, html: str):
        result = [
            self.findbyre(r'<meta property="og:title" content="(.*?)"', html),
            self.findbyre(r'<title>&\w+;([^<>]*). Reviews, film', html)
        ]
        section = self.findbyre(r'(?s)<h3><span>Alternative Titles</span></h3>.*?<p>(.*?)</p>', html)
        if section:
            result += section.split(' - ')
        return result

    def findnames(self, html) -> List[str]:
        return [self.findbyre(
            r'<meta property="og:title" content="([^<>\(\)"]+)', html)]

    def findcast(self, html: str):
        section = self.findbyre(r'(?s)(<div class="cast-list.*?</div>)', html)
        if section:
            return self.findallbyre(r'">([^<>]*)</a>', section, 'actor')

    def findmoviedirectors(self, html: str):
        section = self.findbyre(r'(?s)<h3><span>Director</span></h3>(.*?)</div>', html)
        if section:
            return self.findallbyre(r'">([^<>]*)</a>', section, 'filmmaker')

    def findscreenwriters(self, html: str):
        section = self.findbyre(r'(?s)<h3><span>Writers</span></h3>(.*?)</div>', html)
        if section:
            return self.findallbyre(r'">([^<>]*)</a>', section, 'filmmaker')

    def findmovieeditors(self, html: str):
        section = self.findbyre(r'(?s)<h3><span>Editors</span></h3>(.*?)</div>', html)
        if section:
            return self.findallbyre(r'">([^<>]*)</a>', section, 'filmmaker')

    def findproducers(self, html: str):
        section = self.findbyre(r'(?s)<h3><span>Producers</span></h3>(.*?)</div>', html)
        if section:
            return self.findallbyre(r'">([^<>]*)</a>', section, 'filmmaker')

    def finddirectorsphotography(self, html: str):
        section = self.findbyre(r'(?s)<h3><span>Cinematography</span></h3>(.*?)</div>', html)
        if section:
            return self.findallbyre(r'">([^<>]*)</a>', section, 'filmmaker')

    def findproductiondesigners(self, html: str):
        section = self.findbyre(r'(?s)<h3><span>Production Design</span></h3>(.*?)</div>', html)
        if section:
            return self.findallbyre(r'">([^<>]*)</a>', section, 'filmmaker')

    def findcomposers(self, html: str):
        section = self.findbyre(r'(?s)<h3><span>Composer</span></h3>(.*?)</div>', html)
        if section:
            return self.findallbyre(r'">([^<>]*)</a>', section, 'composer')

    def findsounddesigners(self, html: str):
        section = self.findbyre(r'(?s)<h3><span>Sound</span></h3>(.*?)</div>', html)
        if section:
            return self.findallbyre(r'">([^<>]*)</a>', section, 'filmmaker')

    def findcostumedesigners(self, html: str):
        section = self.findbyre(r'(?s)<h3><span>Costume</span></h3>(.*?)</div>', html)
        if section:
            return self.findallbyre(r'">([^<>]*)</a>', section, 'costumer')

    def findmakeupartists(self, html: str):
        section = self.findbyre(r'(?s)<h3><span>Make-Up</span></h3>(.*?)</div>', html)
        if section:
            return self.findallbyre(r'">([^<>]*)</a>', section, 'costumer')

    def findprodcoms(self, html: str):
        section = self.findbyre(r'(?s)<h3><span>Studios</span></h3>(.*?)</div>', html)
        if section:
            return self.findallbyre(r'">([^<>]*)</a>', section, 'filmcompany')

    def findorigcountries(self, html: str):
        section = self.findbyre(r'(?s)<h3><span>Country</span></h3>(.*?)</div>', html)
        if section:
            return self.findallbyre(r'">([^<>]*)</a>', section, 'country')

    def findoriglanguages(self, html: str):
        section = self.findbyre(r'(?s)<h3><span>Language</span></h3>(.*?)</div>', html)
        if section:
            return self.findallbyre(r'">([^<>]*)</a>', section, 'language')

    def findgenres(self, html: str):
        section = self.findbyre(r'(?s)<h3><span>Language</span></h3>(.*?)</div>', html)
        if section:
            return self.findallbyre(r'">([^<>]*)</a>', section, 'film-genre', alt=['genre'])

    def finddurations(self, html: str):
        result = self.findbyre(r'(\d+)(?:&nbsp;|\s+)mins', html)
        if result:
            return [result.replace('&nbsp;', ' ')]


class BritishExecutionsAnalyzer(Analyzer):
    def setup(self):
        self.dbproperty = 'P6167'
        self.dbid = None
        self.dbname = 'British Executions'
        self.urlbase = 'http://www.britishexecutions.co.uk/execution-content.php?key={id}'
        self.hrtre = '(<h1>.*?)<div'
        self.language = 'en'
        self.escapehtml = True

    def findinstanceof(self, html: str):
        return 'Q5'

    def findlongtext(self, html: str):
        return self.findbyre(r'(?s)<h1>.*?<div class="">(.*?)</div>', html)

    def findnames(self, html) -> List[str]:
        return [self.findbyre(r'<h1[^<>]*>(?:<[^<>]*>)*([^<>]+)<', html)]

    def findgender(self, html: str):
        return self.findbyre(r'<strong>Sex:</strong>(.*?)<', html, 'gender')

    def finddeathdate(self, html: str):
        return self.findbyre(r'<strong>Date Of Execution:</strong>(.*?)<', html)

    def findcrimes(self, html: str):
        return [self.findbyre(r'<strong>Crime:</strong>(.*?)<', html, 'crime')]

    def findmannerdeath(self, html: str):
        return 'Q8454'

    def findcausedeath(self, html: str):
        return self.findbyre(r'<strong>Method:</strong>(.*?)<', html, 'execution-method')

    def finddeathplace(self, html: str):
        return self.findbyre(r'<strong>Execution Place:</strong>(.*?)<', html, 'city')


class BdfaAnalyzer(Analyzer):
    def setup(self):
        self.dbproperty = 'P6188'
        self.dbid = 'Q19368470'
        self.dbname = 'Base de Datos del Futbol Argentino'
        self.urlbase = 'https://www.bdfa.com.ar/jugador.asp?codigo={id}'
        self.hrtre = '<!-- DATOS JUGADOR -->(.*?)<!-- FIN DATOS JUGADOR -->'
        self.language = 'es'
        self.escapehtml = True

    def findnames(self, html) -> List[str]:
        return self.findallbyre(r'<strong>(.*?)<', html)

    def findlongtext(self, html: str):
        return self.findbyre(r'(?s)Resumen</h4>(.*?)</div>', html)

    def findteampositions(self, html: str):
        return self.findbyre(r'(?s)<strong>Posición:</strong>(.*?)<', html, 'footballposition')

    def findweight(self, html: str):
        return self.findbyre(r'(?s)<strong>Peso:</strong>\s*(\d+\s*kg)\.', html)

    def findheight(self, html: str):
        return self.findbyre(r'(?s)<strong>Altura:</strong>\s*(\d+\s*m)ts', html)

    def findnationality(self, html: str):
        return self.findbyre(r'(?s)<strong>Nacionalidad:</strong>(.*?)<', html, 'country')

    def findbirthdate(self, html: str):
        return self.findbyre(r'(?s)<strong>Fecha de nacimiento:</strong>(.*?)[<\(]', html)

    def findbirthplace(self, html: str):
        return self.findbyre(r'(?s)<strong>Lugar de Nacimiento:</strong>(.*?)<', html, 'city')

    def findsportteams(self, html: str):
        return self.findallbyre(r'<a href="lista_jugadores[^<>]*>(.*?)<', html, 'footballteam')


class AustrianBiographicalAnalyzer(Analyzer):
    def setup(self):
        self.dbproperty = 'P6194'
        self.dbid = 'Q25666'
        self.dbname = 'Österreichisches Biographisches Lexikon'
        self.urlbase = 'http://www.biographien.ac.at/oebl/oebl_{id}.xml'
        self.hrtre = '<div id="Langtext">(.*?<span class="lemmatext">.*?</span>)'
        self.language = 'de'

    def findnames(self, html) -> List[str]:
        return [self.findbyre(
            r'<meta name="DC.Title" content="(.*?)[";]', html)]

    def finddescriptions(self, html: str):
        return [
            self.findbyre(r'<meta name="DC.Description" content="(.*?)"', html),
            self.findbyre(r'(?s)<span id="Schlagwort"[^<>]*>(.*?)<p>', html),
            self.findbyre(r'<span class="lemmatext">(.*?)</span>', html)
        ]

    def findlongtext(self, html: str):
        return self.findbyre(r'(?s)<div id="Langtext">(.*?)</div>', html)

    def findbirthplace(self, html: str):
        return self.findbyre(r' \* (.*?),', html, 'city')

    def findbirthdate(self, html: str):
        return self.findbyre(r' \* .*?,([^,;<>]*);', html)

    def finddeathplace(self, html: str):
        return self.findbyre(r' † (.*?),', html, 'city')

    def finddeathdate(self, html: str):
        return self.findbyre(r' † .*?,([^,;<>]*)\.', html)

    def findoccupations(self, html: str):
        section = self.findbyre(r'<span id="Schlagwort" class="lemma2">[^<>,]*,(.*?)<', html)
        if section:
            result = []
            parts = section.split(' und ')
            for part in parts:
                result += self.findallbyre(r'([\w\s]+)', part, 'occupation')
            return result

    def findmixedrefs(self, html: str):
        return self.finddefaultmixedrefs(html)


class BdelAnalyzer(Analyzer):
    def setup(self):
        self.dbproperty = 'P6231'
        self.dbid = None
        self.dbname = 'Base de données des élites suisses'
        self.urlbase = 'https://www2.unil.ch/elitessuisses/index.php?page=detailPerso&idIdentite={id}'
        self.hrtre = '<H1>(.*?)<h1'
        self.language = 'fr'
        self.escapehtml = True

    def getvalue(self, field, html, dtype=None):
        return self.findbyre(
            r'(?s)<td[^<>]*>\s*{}\s*:\s*</td>\s*<td[^<>]*>(.*?)</td>'
            .fomat(field), html, dtype)

    def findnames(self, html) -> List[str]:
        return self.findallbyre(r'<H1>(.*?)[\(<]', html)

    def finddescription(self, html: str):
        return self.getvalue('Principales professions', html)

    def findfirstname(self, html: str):
        return self.getvalue('Prénom', html, 'firstname')

    def findlastname(self, html: str):
        return self.getvalue('Nom', html, 'lastname')

    def findgender(self, html: str):
        return self.getvalue('Sexe', html, 'gender')

    def findbirthdate(self, html: str):
        return self.findbyre(r'Naissance:\s*([\d\.]+)', html)

    def finddeathdate(self, html: str):
        return self.findbyre(r'Décès:\s*([\d\.]+)', html)

    def findbirthplace(self, html: str):
        return self.getvalue('Lieu naissance', html, 'city')

    def findnationality(self, html: str):
        return self.getvalue('Nationalité', html, 'country')

    def findoccupations(self, html: str):
        section = self.getvalue('Principales professions', html)
        if section:
            return self.findallbyre(r'([^,]+)', section, 'occupation')

    def findranks(self, html: str):
        section = self.getvalue(r'Officier\s*\?', html)
        if section:
            return self.findallbyre(r'([^,/]+)', section, 'rank')

    def findparties(self, html: str):
        section = self.findbyre(r'(?s)<b>parti</b>(.*?)</table>', html)
        if section:
            return self.findallbyre(r'(?s)<td>([^<>]*)</td>\s*<td[^<>]*>[^<>]*</td>\s*</tr>', section, 'party')

    def findmixedrefs(self, html: str):
        return self.finddefaultmixedrefs(html)


class ArticArtistAnalyzer(Analyzer):
    def setup(self):
        self.dbproperty = 'P6295'
        self.dbid = 'Q64732761'
        self.dbname = 'ARTIC'
        self.urlbase = 'https://www.artic.edu/artists/{id}'
        self.hrtre = '(<dl>.*?</dl>)'
        self.language = 'en'

    def findinstanceof(self, html: str):
        return self.findbyre(r'<meta name="description"\s*content="(.*?)"', html, 'instanceof')

    def findnames(self, html) -> List[str]:
        return (
            self.findbyre('<dd itemprop="additionalName">(.*?)</dd>', html)
            or '').split(',') + self.findallbyre(
                r'title"\d*content="(.*?)["|]', html)

    def findlongtext(self, html: str):
        return self.findbyre('(?s)itemprop="description">(.*?)</div>', html)

    def finddescriptions(self, html: str):
        return self.findallbyre(r'<meta name="description"\s*content="(.*?)"', html)

    def findbirthdate(self, html: str):
        return self.findbyre('"birthDate">(.*?)<', html)

    def finddeathdate(self, html: str):
        return self.findbyre('"deathDate">(.*?)<', html)

    def findincollections(self, html: str):
        if 'See all' in html:
            return ['Q239303']


class WhoSampledAnalyzer(Analyzer):
    def setup(self):
        self.dbproperty = 'P6517'
        self.dbid = 'Q7997133'
        self.dbname = 'whosampled.com'
        self.urlbase = 'https://www.whosampled.com/{id}/'
        self.hrtre = '(<h1.*?)<script>'
        self.language = 'en'

    def findnames(self, html) -> List[str]:
        section = self.findbyre(
            r'(?s)(<h1.*?)<script>', html) or self.findbyre(
                r'(?s)(.*?)<script>', html) or html
        return (
            self.findallbyre(r'itemprop="\w*[nN]ame"[^<>]*>(.*?)<', section)
            + self.findallbyre(r'itemprop="sameAs"[^<>]*>(.*?)<', section)
        )

    def findlongtext(self, html: str):
        return self.findbyre(r'(?s)(<h1.*?)<script>', html)

    def findmemberships(self, html: str):
        return self.findallbyre(r'itemprop="memberOf"[^<>]*>(?:<[^<>]*>)*(.*?)<', html, 'group')

    def findparts(self, html: str):
        return self.findallbyre(r'itemprop="member"[^<>]*>(?:<[^<>]*>)*(.*?)<', html, 'musician')

    def findmixedrefs(self, html: str):
        return self.finddefaultmixedrefs(html, includesocial=False)

    def findwebsite(self, html: str):
        return self.findbyre(r'href="([^"<>]+)"[^<>]*>Official Site<', html)


class AcademieRouenAnalyzer(Analyzer):
    def setup(self):
        self.dbproperty = 'P6575'
        self.dbid = None
        self.dbname = 'Académie de Rouen'
        self.urlbase = 'http://www.rouen-histoire.com/Academie/Acad_Fich.php?id={id}'
        self.hrtre = ">Fiche(.*?)(?:</table>|Liste d'articles)"
        self.language = 'fr'
        self.escapehtml = True
        self.escapeunicode = True

    def getvalue(self, field, html, dtype=None):
        return self.findbyre(
            r'(?s){}.\s*:\s*</strong>.*?<td[^<>]*>(?:<[^<>]*>)*([^<>]+)<'
            .format(field), html, dtype)

    def findinstanceof(self, html: str):
        return 'Q5'

    def finddescription(self, html: str):
        return self.getvalue('Biographie', html)

    def findlongtext(self, html: str):
        return self.getvalue('Biographie', html)

    def findlastname(self, html: str):
        return self.getvalue('Nom', html, 'lastname')

    def findfirstname(self, html: str):
        with open('result.html', 'w') as f:
            f.write(html)
        return self.getvalue('Prénoms', html, 'firstname')

    def findbirthdate(self, html: str):
        return self.getvalue('Naissance', html)

    def findmemberships(self, html: str):
        return ['Q2822391']

    def findoccupations(self, html: str):
        section = self.getvalue('Biographie', html)
        if section:
            return self.findallbyre(r'([^,\.]*)', section, 'occupation')

    def findresidences(self, html: str):
        section = self.getvalue('Adresse', html)
        if section:
            return self.findallbyre('(.*)', section, 'city')


class MutualAnalyzer(Analyzer):
    def setup(self):
        self.dbproperty = 'P6578'
        self.dbid = 'Q22907130'
        self.dbname = 'MutualArt'
        self.urlbase = 'https://www.mutualart.com/Artist/wd/{id}'
        self.hrtre = r'(<h1.*?)<div\s*preferences'
        self.language = 'en'

    def findnames(self, html) -> List[str]:
        result = [self.findbyre(r'(?s)<h1[^<>]*>(.*?)<', html)]
        section = self.findbyre(r'names:(.*?)<', html)
        if section:
            result += self.findallbyre(r'([\w\s]+)', section)
        return result

    def findlongtext(self, html: str):
        return self.findbyre(r'(?s)<p class="bio"[^<>]*>(.*?)</div>', html)

    def findnationality(self, html: str):
        return self.findbyre(r'(?s)>([^<>]*)<span class="separator">', html, 'country')

    def findbirthdate(self, html: str):
        return self.findbyre(r'(?s)<span class="separator">.</span>(.*?)[\-<]', html)

    def finddeathdate(self, html: str):
        return self.findbyre(r'(?s)<span class="separator">.</span>[^<>]*-(.*?)<', html)


class GuggenheimAnalyzer(Analyzer):
    def setup(self):
        self.dbproperty = 'P6594'
        self.dbid = None
        self.dbname = 'Guggenheim Fellowship'
        self.urlbase = 'https://www.gf.org/fellows/all-fellows/{id}/'
        self.hrtre = '(<h1.*?)<div class="wpb_row'
        self.language = 'en'

    def findinstanceof(self, html: str):
        return 'Q5'

    def findnames(self, html) -> List[str]:
        return self.findallbyre('<h1[^<>]*>(.*?)<', html)

    def findwebsite(self, html: str):
        return self.findbyre('Website: <a[^<>]*>(.*?)<', html)

    def findawards(self, html: str):
        return ['Q1316544']

    def findworkfields(self, html: str):
        return self.findallbyre('Field of Study: ([^<>]+)', html, 'subject')

    def findbirthdate(self, html: str):
        return self.findbyre(r'Born: ([\d\-]+)', html)

    def finddeathdate(self, html: str):
        return self.findbyre(r'Died: ([\d\-]+)', html)


class SnsaAnalyzer(Analyzer):
    def setup(self):
        self.dbproperty = 'P6770'
        self.dbid = None
        self.dbname = 'Swiss National Sound Archives'
        self.urlbase = 'https://www.fonoteca.ch/cgi-bin/oecgi4.exe/inet_fnbasenamedetail?NAME_ID={id}&LNG_ID=ENU'
        self.hrtre = '<h2>(.*?)<br class="clearfix">'
        self.language = 'it'

    def getvalue(self, field, html, dtype=None, alt=None):
        return self.findbyre('(?s)<strong>{}</strong><br>(.*?)</p>'
                             .format(field), html, dtype, alt=alt)

    def getvalues(self, field, html, dtype=None, alt=None) -> List[str]:
        section = self.getvalue(field, html)
        if section:
            return self.findallbyre('([^;]*)', section, dtype, alt=alt)
        return []

    def findinstanceof(self, html: str):
        return self.getvalue('Formation', html, 'instanceof')

    def findnames(self, html) -> List[str]:
        return self.findallbyre('<h2>(.*?)<', html) \
            + self.getvalues('Same person[^<>]*', html)

    def findbirthplace(self, html: str):
        return self.getvalue('Place of birth', html, 'city')

    def findbirthdate(self, html: str):
        return self.getvalue('Date of birth', html)

    def finddeathplace(self, html: str):
        return self.getvalue('Place of death', html, 'city')

    def finddeathdate(self, html: str):
        return self.getvalue('Date of death', html)

    def findnationalities(self, html: str):
        return self.getvalues('Citizenship', html, 'country')

    def findoccupations(self, html: str):
        return self.getvalues('Activity', html, 'occupation')

    def findgenres(self, html: str):
        return self.getvalues('Musical genre', html, 'music-genre', alt=['genre'])

    def findinstruments(self, html: str):
        return self.getvalues('Musical instrument', html, 'instrument')

    def findvoices(self, html: str):
        return self.getvalues('Voice', html, 'voice')

    def findmemberships(self, html: str):
        return self.getvalues('Member of the group', html, 'group')

    def findworkfields(self, html: str):
        return self.getvalues('Work genre', html, 'subject')

    def findlastname(self, html: str):
        return self.findbyre('<h2>([^<>]*),', html, 'lastname')

    def findfirstname(self, html: str):
        return self.findbyre('<h2>[^<>]*,([^<>]*)', html, 'firstname')


class UvaAlbumAnalyzer(Analyzer):
    def setup(self):
        self.dbproperty = 'P6815'
        self.dbid = 'Q63962284'
        self.dbname = 'Album Academicum UvA'
        self.urlbase = 'http://albumacademicum.uva.nl/id/{id}'
        self.hrtre = 'nextPrevLinks -->(.*?)<table id="profdata">'
        self.language = 'nl'

    def prepare(self, html: str):
        return html.replace('&nbsp;', ' ')

    def getvalue(self, field, html, dtype=None, alt=None):
        return self.findbyre('(?s)<th>{}</th><td>(?:<a[^<>]*>)?(.*?)<'
                             .format(field), html, dtype, alt=alt)

    def getvalues(self, field, html, dtype=None, alt=None) -> List[str]:
        return self.findallbyre('(?s)<th>{}</th><td>(?:<a[^<>]*>)?(.*?)<'
                                .format(field), html, dtype, alt=alt)

    def findinstanceof(self, html: str):
        return 'Q5'

    def findnames(self, html) -> List[str]:
        name = self.getvalue('Naam', html)
        fullname = self.getvalue('Voornamen', html)
        if name and fullname and '. ' in name:
            return [name, fullname + name[name.find('. ') + 1:]]
        return [name]

    def findfirstname(self, html: str):
        section = self.getvalue('Voornamen', html)
        return self.findbyre(r'([\w\-]+)', section, 'firstname')

    def findgender(self, html: str):
        return self.getvalue('Geslacht', html, 'gender')

    def findbirthdate(self, html: str):
        birthdata = self.getvalue('Geboren', html)
        if birthdata:
            return self.findbyre(r'(.*\d),', birthdata)

    def findbirthplace(self, html: str):
        birthdata = self.getvalue('Geboren', html)
        if birthdata:
            return self.findbyre(r'.*\d,(.*)', birthdata, 'city')

    def finddeathdate(self, html: str):
        deathdata = self.getvalue('Overleden', html)
        if deathdata:
            return self.findbyre(r'(.*\d),', deathdata)

    def finddeathplace(self, html: str):
        deathdata = self.getvalue('Overleden', html)
        if deathdata:
            return self.findbyre(r'.*\d,(.*)', deathdata, 'city')

    def finddegrees(self, html: str):
        return [self.getvalue('Titels', html, 'degree')] +\
            self.getvalues('Examentype', html, 'degree') +\
            self.findallbyre('<h2 class="recordCodes">(.*?)<', html, 'degree')

    def findnationalities(self, html: str):
        return [self.getvalue('Nationaliteit', html, 'country')]

    def findschools(self, html: str):
        return self.getvalues(r'Instelling \(opleiding\)', html, 'university')

    def findadvisors(self, html: str):
        return self.getvalues(r'Promotor\(en\)', html, 'scientist')

    def findoccupations(self, html: str):
        return self.getvalues('Aanstelling', html, 'occupation')

    def findpositions(self, html: str):
        return self.getvalues('Aanstelling', html, 'position')

    def findemployers(self, html: str):
        return self.getvalues(r'Instelling \(aanstelling\)', html, 'employer', alt=['university'])

    def findworkfields(self, html: str):
        return self.getvalues('Discipline', html, 'subject')

    def findmajors(self, html: str):
        return self.getvalues('Opleiding', html, 'subject')


class AlvinAnalyzer(Analyzer):
    def setup(self):
        self.dbproperty = 'P6821'
        self.dbid = 'Q59341385'
        self.dbname = 'Alvin'
        self.urlbase = 'http://www.alvin-portal.org/alvin/view.jsf?pid={id}'
        self.hrtre = '(<div id="alvinForm:contentArkad".*?)<table>'
        self.language = 'sv'

    def findinstanceof(self, html: str):
        return self.findbyre('alvin-(.*?):', self.id, 'instanceof')

    def findnames(self, html) -> List[str]:
        result = self.findallbyre('(?s)<title>[^<>]* - (.*?)</title>', html)
        section = self.findbyre('(?s)<h2>Alternative names</h2>(.*?)<h2', html)
        if section:
            result += self.findallbyre(r'(?s)>([^<>\(\)]*)<', section)
        return result

    def findlongtext(self, html: str):
        return self.findbyre('(?s)<h2>Biography</h2>(.*?)<h2', html)

    def finddescription(self, html: str):
        return self.findbyre('(?s)<h2>Occupation</h2>(.*?)<h2', html)

    def findoccupations(self, html: str):
        section = self.findbyre('(?s)<h2>Occupation</h2>(.*?)<h2', html)
        if section:
            return self.findallbyre('([^,]*)', section, 'occupation')

    def findbirthdate(self, html: str):
        return self.findbyre(r'Born (\d+)', html)

    def finddeathdate(self, html: str):
        return self.findbyre(r'Death (\d+)', html)

    def findbirthplace(self, html: str):
        return self.findbyre('Born [^<>]*<a[^<>]*>(.*?)<', html, 'city')

    def finddeathplace(self, html: str):
        return self.findbyre('Death [^<>]*<a[^<>]*>(.*?)<', html, 'city')

    def findgender(self, html: str):
        return self.findbyre(r'\(Person\)(?:\s|<[^<>]*>)*<div class="singleRow">(.*?)<', html, 'gender')

    def findnationalities(self, html: str):
        section = self.findbyre('(?s)<h2>Nationality</h2>(.*?)<h2', html)
        if section:
            return self.findallbyre('([^,]*)', section, 'occupation')

    def findmixedrefs(self, html: str):
        return self.finddefaultmixedrefs(html)


class AbartAnalyzer(Analyzer):
    def setup(self):
        self.dbproperty = 'P6844'
        self.dbid = 'Q10855166'
        self.dbname = 'AbART'
        self.urlbase = 'https://en.isabart.org/person/{id}'
        self.hrtre = r'(<h2.*?)(?:<strong>word:|<strong>notes:|end \.detail-content)'
        self.language = 'cs'

    def findnames(self, html) -> List[str]:
        return [self.findbyre(r'<h2>(.*?)</h2>', html)]

    def findlanguagedescriptions(self, html: str):
        return [('en', self.findbyre(r'<br>([^<>]*)</p>', html))]

    def findlongtext(self, html: str):
        return self.findbyre(r'(?s)<strong>notes:</strong>(.*?)</p>', html)

    def findbirthdate(self, html: str):
        return self.findbyre(r'\*\s*<span>(.*?)</span>', html)

    def findbirthplace(self, html: str):
        return self.findbyre(r'\*\s*<span>[^<>]*</span>,\s*<span>(.*?)</span>', html, 'city')

    def finddeathdate(self, html: str):
        return self.findbyre(r'&dagger;\s*<span>(.*?)</span>', html)

    def finddeathplace(self, html: str):
        return self.findbyre(r'&dagger;\s*<span>[^<>]*</span>,\s*<span>(.*?)</span>', html, 'city')

    def findoccupations(self, html: str):
        section = self.findbyre(r'<br>([^<>]*)</p>', html)
        if section:
            return self.findallbyre(r'([^,]*)', section, 'occupation')

    def findnationality(self, html: str):
        return self.findbyre(r'<strong>nationality:</strong>([^<>]*)', html, 'country')

    def findgender(self, html: str):
        return self.findbyre(r'<strong>sex:</strong>([^<>]*)', html, 'gender')


class IntraTextAnalyzer(Analyzer):
    def setup(self):
        self.dbproperty = 'P6873'
        self.dbid = 'Q3800762'
        self.dbname = 'IntraText'
        self.urlbase = 'http://www.intratext.com/Catalogo/Autori/AUT{id}.HTM'
        self.hrtre = '()'
        self.language = 'en'
        self.escapehtml = True

    def findnames(self, html) -> List[str]:
        return [self.findbyre(r'<b>(.*?)<', html)] \
            + self.findallbyre(r'<FONT[^<>]*>(.*?)<', html)

    def findmixedrefs(self, html: str):
        return self.finddefaultmixedrefs(html, includesocial=False)


class RepertoriumAnalyzer(Analyzer):
    def setup(self):
        self.dbproperty = 'P7032'
        self.dbid = 'Q65032487'
        self.dbname = 'Repertorium van ambtsdragers en ambtenaren'
        self.urlbase = 'http://resources.huygens.knaw.nl/repertoriumambtsdragersambtenaren1428-1861/app/personen/{id}'
        self.hrtre = '(<h1 class="naam">)<h2'
        self.language = 'nl'

    def findinstanceof(self, html: str):
        return 'Q5'

    def findnames(self, html) -> List[str]:
        return [self.findbyre(r'(?s)<h1 class="naam">(.*?)<', html)]

    def findlongtext(self, html: str):
        return self.findbyre(r'(?s)(<h1 class="naam">.*?)<h2>bron', html)

    def findbirthdate(self, html: str):
        return self.findbyre(r'(?s)geboren:\s*([\d\-]+)', html)

    def finddeathdate(self, html: str):
        return self.findbyre(r'(?s)overleden:\s*([\d\-]+)', html)

    def findbirthplace(self, html: str):
        return self.findbyre(r'(?s)geboren:[^<>]*te ([^<>]*)', html, 'city')

    def finddeathplace(self, html: str):
        return self.findbyre(r'(?s)overleden:[^<>]*te ([^<>]*)', html, 'city')

    def findsources(self, html: str):
        return self.findallbyre(r'(?s)<p class="bronnen">(.*?)<', html, 'source')

    def findtitles(self, html: str):
        section = self.findbyre(r'(?s)Adelstitel:(.*?)<', html)
        if section:
            return self.findallbyre(r'([a-zA-Z][\w\s]*)', section, 'title')

    def findpositions(self, html: str):
        result = []
        section = self.findbyre(r'(?s)Overige:(.*?)<', html)
        if section:
            result += self.findallbyre(r'([a-zA-Z][\w\s]*)', section, 'position')
        section = self.findbyre(r'(?s)<h2>functies.*?</h2>(.*?)<!-- End Body -->', html)
        if section:
            parts = self.findallbyre(r'(?s)functie:(.*?<br.*?)<br', section)
            parts = [self.TAGRE.sub(' ', part) for part in parts]
            parts = [part.replace('instelling:', '') for part in parts]
            result += [self.findbyre(r'(?s)(.*)', part, 'position') for part in parts]
        result += self.findallbyre(r'(?s)<span class="functie">(.*?)[\(<]', html, 'position')
        return result

    def findoccupations(self, html: str):
        result = []
        section = self.findbyre(r'(?s)Overige:(.*?)<', html)
        if section:
            result += self.findallbyre(r'([a-zA-Z][\w\s]*)', section, 'occupation')
        section = self.findbyre(r'(?s)<h2>functies.*?</h2>(.*?)<!-- End Body -->', html)
        if section:
            parts = self.findallbyre(r'(?s)functie:(.*?<br.*?)<br', section)
            parts = [self.TAGRE.sub(' ', part) for part in parts]
            parts = [part.replace('instelling:', '') for part in parts]
            result += [self.findbyre(r'(?s)(.*)', part, 'occupation') for part in parts]
        result += self.findallbyre(r'(?s)<span class="functie">(.*?)[\(<]', html, 'occupation')
        return result


class PlwabnAnalyzer(Analyzer):
    def setup(self):
        self.dbproperty = 'P7293'
        self.dbid = None
        self.dbname = 'PLWABN'
        self.urlbase = 'http://mak.bn.org.pl/cgi-bin/KHW/makwww.exe?BM=1&NU=1&IM=4&WI={id}'
        self.hrtre = '(<table.*?</table>)'
        self.language = 'pl'

    def getvalue(self, field, letter, html, dtype=None):
        row = self.findbyre(r'(<tr><td[^<>]*>{}\s*<.*?</tr>)'
                            .format(field), html)
        if row:
            return self.findbyre(r'<I>\s*{}\s*</TT></I>(.*?)<'
                                 .fomat(letter), row, dtype)
        return None

    def getvalues(self, field, letter, html, dtype=None) -> List[str]:
        result = []
        rows = self.findallbyre(r'(<tr><td[^<>]*>{}\s*<.*?</tr>)'
                                .format(field), html)
        for row in rows:
            result += self.findallbyre(r'<I>\s*{}\s*</TT></I>(.*?)<'
                                       .format(letter), row, dtype)
        return result

    def findinstanceof(self, html: str):
        return self.getvalue('667', 'a', html, 'instanceof')

    def findnames(self, html) -> List[str]:
        return self.getvalues('100', 'a', html) + self.getvalues(
            '400', 'a', html)

    def finddescriptions(self, html: str):
        return self.getvalues('667', 'a', html)

    def findlongtext(self, html: str):
        return '\n'.join(self.finddescriptions(html))

    def findbirthdate(self, html: str):
        life = self.getvalue('100', 'd', html)
        if life:
            return self.findbyre(r'\((.*?)-', life)
        return None

    def finddeathdate(self, html: str):
        life = self.getvalue('100', 'd', html)
        if life:
            return self.findbyre(r'-(.*?)\)', life)
        return None

    def findnationalities(self, html: str):
        return self.getvalues('370', 'c', html, 'country')

    def findsources(self, html: str):
        sources = self.getvalues('670', 'a', html)
        result = []
        for source in sources:
            if source and ' by ' not in source and ' / ' not in source:
                result.append(self.findbyre('(.*)', source, 'source'))
        return result


class BewebAnalyzer(Analyzer):
    def setup(self):
        self.dbproperty = 'P7796'
        self.dbid = 'Q77541206'
        self.dbname = 'BeWeb'
        self.urlbase = 'https://www.beweb.chiesacattolica.it/persone/persona/{id}/'
        self.hrtre = 'Elementi descrittivi</h3>(.*?)<h3'
        self.language = 'it'
        self.languagetranslate = {'ita': 'it', 'lat': 'la', 'deu': 'de',
                                  'spa': 'es', 'fra': 'fr', 'eng': 'en'}
        self.escapehtml = True

    def getvalue(self, field, html, dtype=None):
        return self.findbyre(r'(?s)<b>{}</b>\s*:\s*([^<>]*)'
                             .format(field), html, dtype)

    def getvalues(self, field, html, dtype=None) -> List[str]:
        result = self.getvalue(field, html)
        if result:
            return self.findallbyre('([^;]*)', result, dtype)
        return []

    def findinstanceof(self, html: str):
        return self.getvalue('Categoria entità', html, 'instanceof')

    def findlanguagenames(self, html: str):
        result = [('it', name) for name in self.findallbyre('<h1>(.*?)<', html)]
        section = self.findbyre('(?s)Intestazioni</h3>(.*?)</ul>', html)
        if section:
            result += [('it', name) for name in self.findallbyre(r'(?s)<li>\s*(.*?)[&<]', section)]
        section = self.findbyre('(?s)Forme varianti</h3>(.*?</ul>)', html)
        if section:
            result += [(self.languagetranslate.get(lang, lang[:2]), name) for (name, lang) in re.findall(r'([^<>\(\)&]*)\(([^<>\(\)&]*)\)', section)]
            result += [('it', name) for name in self.findallbyre(r'([^<>\(\)&]*?)[<&]', section)]
        else:
            pywikibot.info('section not found')
        return result

    def finddescriptions(self, html: str):
        return self.findallbyre('description" content="(.*?)"', html) + [self.getvalue('Qualifiche', html)]

    def findlongtext(self, html: str):
        return self.findbyre('(?s)<div id="note"[^<>]*>(.*?)</div>', html)

    def findgender(self, html: str):
        return self.getvalue('Sesso', html, 'gender')

    def findnationalities(self, html: str):
        return self.getvalues('Nazionalità', html, 'country')

    def findbirthdate(self, html: str):
        return self.getvalue('Data nascita', html)

    def findbirthplace(self, html: str):
        return self.getvalue('Luogo nascita', html, 'city')

    def finddeathdate(self, html: str):
        return self.getvalue('Data morte', html)

    def finddeathplace(self, html: str):
        return self.getvalue('Luogo morte', html, 'city')

    def findoccupations(self, html: str):
        return self.getvalues('Qualifiche', html, 'occupation')

    def findpositions(self, html: str):
        return self.getvalues('Qualifiche', html, 'position')

    def findmixedrefs(self, html: str):
        result = self.finddefaultmixedrefs(self.findbyre('(?s)<section id="otherInfoAF">(.*?)</section>', html))
        sbn = self.findbyre(r'<span id="codSBN">[^<>]*</span>[^<>]*?([^\s]*)<', html)
        if sbn:
            result += [('P396', sbn)]
        return result

    def findviaf(self, html: str):
        return self.findbyre(r'Codice VIAF[^<>]*?(\d+)<', html)

    def findisni(self, html: str):
        return self.findbyre(r'Codice ISNI[^<>]*?(\d\w*)<', html)

    def findwebpages(self, html: str):
        section = self.findbyre('(?s)<section id="otherInfoAF">(.*?)</section>', html)
        links = self.findallbyre('"(http[^<>]*?)"', section)
        for text in ['wikipedia', 'id.loc.gov', 'd-nb.info', 'bnf.fr',
                     'getty.edu', 'viaf.org', 'cerl.org', 'catholic-hierarchy',
                     'wikidata', 'treccani']:
            links = [link for link in links if text not in link]
        return links


class DeutscheBiographieAnalyzer(Analyzer):
    def setup(self):
        self.dbproperty = 'P7902'
        self.dbid = 'Q1202222'
        self.dbname = 'Deutsche Biographie'
        self.urlbase = 'https://www.deutsche-biographie.de/pnd{id}.html'
        self.hrtre = r'<!-- Content -->(.*?)<h\d'
        self.language = 'de'

    def getvalue(self, field, html, dtype=None):
        return self.findbyre(
            r'(?s)<dt class="indexlabel">{}</dt>\s*<dd class="indexvalue">(.*?)</dd>'
            .format(field), html, dtype)

    def findnames(self, html) -> List[str]:
        section = self.getvalue('Namensvarianten', html) or ''
        return (
            self.findallbyre(r'<h1[^<>]*>(.*?)<', html)
            + self.findallbyre(r'<li[^<>]*>(.*?)<', section)
        )

    def findlongtext(self, html: str):
        return self.findbyre(r'(?s)<h4[^<>]*>Leben(<.*?)</li>', html)

    def findmixedrefs(self, html: str):
        return self.finddefaultmixedrefs(html, includesocial=False)

    def findbirthdate(self, html: str):
        section = self.getvalue('Lebensdaten', html)
        if section:
            return self.findbyre(r'(.*?\d+)', section)
        return None

    def findbirthplace(self, html: str):
        section = self.getvalue('Geburtsort', html)
        if section:
            return self.findbyre(r'>(.*?)<', section, 'city')
        return None

    def finddeathdate(self, html: str):
        section = self.getvalue('Lebensdaten', html)
        if section:
            return self.findbyre(r'bis (.*)', section)
        return None

    def finddeathplace(self, html: str):
        section = self.getvalue('Sterbeort', html)
        if section:
            return self.findbyre(r'>(.*?)<', section, 'city')
        return None

    def findoccupations(self, html: str):
        section = self.getvalue('Beruf/Funktion', html)
        if section:
            subsections = self.findallbyre(r'>([^<>]*)</a>', section)
            result = []
            for subsection in subsections:
                result += self.findallbyre(r'([^,]*)', subsection, 'occupation')
            return result
        return None

    def findreligions(self, html: str):
        section = self.getvalue('Konfession', html)
        if section:
            return self.findallbyre(r'([^,]+)', section, 'religion')
        return None

    def findwebpages(self, html: str):
        section = self.findbyre(r'(?s)<h4[^<>]*>\s*Quellen\s*\(nachweise\).*?<ul>(.*?)</ul>', html)
        if section:
            return self.findallbyre(r'href="(.*?)"', section)
        return None

    def findfloruit(self, html: str):
        return self.findbyre('Wirkungsdaten ([^<>]*)', html)


class WorldsWithoutEndAnalyzer(Analyzer):
    def setup(self):
        self.dbproperty = 'P8287'
        self.dbid = 'Q94576039'
        self.dbname = 'Worlds Without End'
        self.urlbase = 'https://www.worldswithoutend.com/author.asp?ID={id}'
        self.hrtre = '<!-- AUTHOR DETAILS -->(.*?)</table>'
        self.language = 'en'

    def getvalue(self, field, html, dtype=None):
        return self.findbyre(r'(?s)>{}:</td>\s*<td[^<>]*>(.*?)</td>'
                             .format(field), html, dtype)

    def findinstanceof(self, html: str):
        return 'Q5'

    def findnames(self, html) -> List[str]:
        return self.findallbyre('title" content="(.*?)"', html) \
            + [self.getvalue('Full Name', html)]

    def finddescriptions(self, html: str):
        return self.findallbyre('description" content="(.*?)"', html)

    def findlongtext(self, html: str):
        return self.findbyre('(?s)<!-- BIOGRAPHY -->(.*?)<!-- WORKS', html)

    def findbirthdate(self, html: str):
        section = self.getvalue('Born', html)
        if section:
            return self.findbyre('([^<>]*)', section)
        return None

    def findbirthplace(self, html: str):
        section = self.getvalue('Born', html)
        if section:
            return self.findbyre('>([^<>]*)', section, 'city')
        return None

    def finddeathdate(self, html: str):
        section = self.getvalue('Died', html)
        if section:
            return self.findbyre('([^<>]*)', section)
        return None

    def finddeathplace(self, html: str):
        section = self.getvalue('Died', html)
        if section:
            return self.findbyre('>([^<>]*)', section, 'city')
        return None

    def findoccupations(self, html: str):
        section = self.getvalue('Occupation', html)
        if section:
            result = []
            subsections = section.split(' and ')
            for subsection in subsections:
                result += self.findallbyre('([^,]*)', subsection, 'occupation')
            return result
        return None

    def findnationalities(self, html: str):
        section = self.getvalue('Nationality', html)
        if section:
            result = []
            subsections = section.split(' and ')
            for subsection in subsections:
                result += self.findallbyre('([^,]*)', subsection, 'country')
            return result
        return None

    def findwebpages(self, html: str):
        section = self.getvalue('Links', html)
        if section:
            return self.findallbyre('"([^<>"]*://[^<>"]*)"', section)
        return None


class BelgianPhotographerAnalyzer(Analyzer):
    def setup(self):
        self.dbproperty = 'P8696'
        self.dbid = 'Q99863977'
        self.dbname = 'Directory of Begian Photographers'
        self.urlbase = 'https://fomu.atomis.be/index.php/{id}'
        self.hrtre = '<h2>Identity</h2>(.*?)<h2>Affiliations</h2>'
        self.language = 'en'

    def getvalue(self, field, html, dtype=None, alt=None):
        if alt is None:
            alt = []
        return self.findbyre(r'(?s)<h3>\s*{}\s*</h3>\s*<div[^<>]*>(.*?)</div>'
                             .format(field), html, dtype, alt=alt)

    def getvalues(self, field, html, dtype=None, alt=None) -> List[str]:
        if alt is None:
            alt = []
        section = self.getvalue(field, html, alt=alt)
        if section:
            return self.findallbyre('>(.*?)<', '>' + section + '<', dtype)
        return []

    def findinstanceof(self, html: str):
        return self.getvalue('Category', html, 'instanceof')

    def findnames(self, html) -> List[str]:
        return self.findallbyre('<title>([^<>]*) - ', html) \
            + self.getvalues('Alternative name or descriptor', html) \
            + self.getvalues(
                r'Standardized form\(s\) of name according to other rules',
                html)

    def findlongtext(self, html: str):
        return self.TAGRE.sub(' ', self.getvalue('Activity', html) or '')

    def findgender(self, html: str):
        return self.findbyre(r'Person \((.*?)\)', html, 'gender')

    def findbirthdate(self, html: str):
        section = self.getvalue('Life dates', html)
        if section:
            return self.findbyre(r', (\d+) - ', section)
        return None

    def finddeathdate(self, html: str):
        section = self.getvalue('Life dates', html)
        if section:
            return self.findbyre(r', \d+ - [\w\s]+, (\d{4})', section)
        return None

    def findbirthplace(self, html: str):
        section = self.getvalue('Life dates', html)
        if section:
            return self.findbyre(r'(.*), \d+ - ', section, 'city')
        return None

    def finddeathplace(self, html: str):
        section = self.getvalue('Life dates', html)
        if section:
            return self.findbyre(r', \d+ - ([^<>]+), \d{4}', section, 'city')
        return None

    def findworkplaces(self, html: str):
        return [self.findbyre(r'[\d\s\-\+]+(.*)', section) for section in self.getvalues('Locations', html)]

    def findgenres(self, html: str):
        return self.getvalues('Genres / subject matter', html, 'photography-genre', alt=['art-genre', 'genre'])

    def findmemberships(self, html: str):
        section = self.getvalue('Affiliated entity', html)
        if section:
            return self.findallbyre('<a[^<>]+title="(.*?)"', section, 'organization')
        return None

    def findoccupations(self, html: str):
        return ['Q33231']


class AlkindiAnalyzer(Analyzer):
    def setup(self):
        self.dbproperty = 'P8795'
        self.dbid = 'Q101207543'
        self.dbname = 'AlKindi'
        self.urlbase = 'https://alkindi.ideo-cairo.org/agent/{id}'
        self.hrtre = '//// main ////(.*?)<tr class="blank_row">'
        self.language = 'ar'
        self.escapehtml = True

    def getvalue(self, field, html, dtype=None):
        return self.findbyre(
            r'(?s)<p class="ltr (?:notice-label|text-muted)">\s*{}.*?<[^<>]* class="ltr"\s*>(.*?)<'
            .format(field), html, dtype)

    def getvalues(self, field, html, dtype=None) -> List[str]:
        return self.findallbyre(r'(?s)<p class="ltr (?:notice-label|text-muted)">\s*{}.*?<[^<>]* class="ltr"\s*>(.*?)<'
                                .format(field), html, dtype)

    def instanceof(self, html: str):
        return 'Q5'

    def findnames(self, html) -> List[str]:
        return self.findallbyre(
            r'(?s)data-original-title="[^"]*ccess point">(.*?)(?:,[\s\d‒]*)?<',
            html.replace('،', ','))

    def finddescription(self, html: str):
        return self.getvalue('Profession', html)

    def findgender(self, html: str):
        return self.getvalue('Gender', html, 'gender')

    def findbirthdate(self, html: str):
        return self.getvalue('Date of birth', html)

    def finddeathdate(self, html: str):
        return self.getvalue('Date of death', html)

    def findlanguagesspoken(self, html: str):
        section = self.getvalue('Language', html)
        if section:
            return self.findallbyre(r'([\w\s]+)', section, 'language')
        return None

    def findbirthplace(self, html: str):
        return self.getvalue('Place of birth', html, 'city')

    def finddeathplace(self, html: str):
        return self.getvalue('Place of death', html, 'city')

    def findnationality(self, html: str):
        return self.getvalue('Nationality', html, 'country')

    def findmixedrefs(self, html: str):
        return self.finddefaultmixedrefs(html, includesocial=False)

    def findfirstnames(self, html: str):
        return self.getvalues('Part of the name other than the entry element', html, 'firstname')

    def findlastname(self, html: str):
        return self.getvalue('Entry element', html, 'lastname')


class ZobodatAnalyzer(Analyzer):
    def setup(self):
        self.dbproperty = 'P8914'
        self.dbid = 'Q55153845'
        self.dbname = 'ZOBODAT'
        self.urlbase = 'https://www.zobodat.at/personen.php?id={id}'
        self.urlbase3 = 'https://www.zobodat.at/personen.php?id={id}&bio=full'
        self.skipfirst = True
        self.hrtre = r"<div class='detail-container clearfix content-box\s*'>(.*?)<div id='footer'>"
        self.language = 'de'

    def findnames(self, html) -> List[str]:
        return self.findallbyre('<strong>(.*?)<', html) \
            + self.findallbyre('<h1>(.*?)<', html)

    def finddescription(self, html: str):
        return self.findbyre(r'(?s)</h1>(?:\s|<[^<>]*>)*([^<>]+)', html)

    def findlongtext(self, html: str):
        result = self.findbyre(r'(?s)</h1>\s*<p>(.*?)</p>', html)
        if result:
            return self.TAGRE.sub(' ', result)
        return None

    def findbirthdate(self, html: str):
        return self.findbyre(r'>\*\s*([^\s<>]+)', html)

    def findbirthplace(self, html: str):
        return self.findbyre(r'>\*\s*[^\s<>]+\s([^<>]+)', html, 'city')

    def finddeathdate(self, html: str):
        return self.findbyre(r'>†\s*([^\s<>]+)', html)

    def finddeathplace(self, html: str):
        return self.findbyre(r'>†\s*[^\s<>]+\s([^<>]+)', html, 'city')

    def findmixedrefs(self, html: str):
        return self.finddefaultmixedrefs(html, includesocial=False)

    def findwebpages(self, html: str):
        section = self.findbyre(r'</h1>\s*<p>(.*?)</p>', html)
        if section:
            return self.findallbyre('href="(.*?)"', section)
        return None


class OxfordMedievalAnalyzer(Analyzer):
    def setup(self):
        self.dbproperty = 'P9017'
        self.dbid = 'Q84825958'
        self.dbname = 'Medieval Manuscripts in Oxford Libraries'
        self.urlbase = 'https://medieval.bodleian.ox.ac.uk/catalog/person_{id}'
        self.hrtre = '(<h1.*?)<p class="coveragewarning">'
        self.language = 'en'

    def findnames(self, html) -> List[str]:
        fullname = self.findbyre('<h1[^<>]*>(.*?)</h1', html)
        if not fullname:
            return []

        parts = fullname.split(',')
        return [','.join(parts[:n]) for n in range(len(parts))]

    def findmixedrefs(self, html: str):
        return self.finddefaultmixedrefs(html, includesocial=False)


class PatrinumAnalyzer(Analyzer):
    def setup(self):
        self.dbproperty = 'P9113'
        self.dbid = 'Q105005338'
        self.dbname = 'Patrinum'
        self.urlbase = 'https://www.patrinum.ch/record/{id}'
        self.hrtre = r'Notice détaillée\s*</h3>(.*?)(?:<h3|<!--)'
        self.language = 'fr'

    def getvalue(self, field, html, dtype=None):
        return self.findbyre(r"(?s)<div class='metadata-row'><span [^<>]*>\s*%s\s*</span>\s*<span [^<>]*>(.*?)</span>" % field, html, dtype)

    def getvalues(self, field, html, dtype=None) -> List[str]:
        section = self.getvalue(field, html)
        if section:
            return self.findallbyre('(?s)>([^<>]*)<', '>' + section + '<', dtype)
        return []

    def findnames(self, html) -> List[str]:
        return [self.getvalue('Nom', html)] \
            + self.getvalues('Variations du nom', html) \
            + self.findallbyre('(?s)"description" content="(.*?)"', html) \
            + self.findallbyre('meta content="(.*?)"', html)

    def finddescriptions(self, html: str):
        return [
            self.getvalue('Nom', html),
            self.getvalue('Parcours de vie', html)
        ]

    def findlongtext(self, html: str):
        return self.findbyre(r'(?s)Historique\s*</h3>(.*?)(?:<h3|<!--)', html)

    def findbirthdate(self, html: str):
        return self.getvalue('Date de naissance', html)

    def findbirthplace(self, html: str):
        return self.getvalue('Lieu de naissance', html, 'city')

    def finddeathdate(self, html: str):
        return self.getvalue('Date de décès', html)

    def finddeathplace(self, html: str):
        return self.getvalue('Lieu de décès', html, 'city')

    def findgender(self, html: str):
        return self.getvalue('Sexe', html, 'gender')

    def findoccupations(self, html: str):
        return self.getvalues('Profession', html, 'occupation')

    def findworkfields(self, html: str):
        return self.getvalues('Domaine professionel', html, 'subject')

    def findmixedrefs(self, html: str):
        return self.finddefaultmixedrefs(html)

    def findwebpages(self, html: str):
        section = self.getvalue('Autre site web', html)
        if section:
            return self.findallbyre(r'"(\w+://[^"<>]*)"', section)
        return None


class JwaAnalyzer(Analyzer):
    def setup(self):
        self.dbproperty = 'P9430'
        self.dbid = 'Q6615646'
        self.dbname = "Jewish Women's Archive"
        self.urlbase = 'https://jwa.org/people/{id}'
        self.hrtre = '<div class="quick-facts">(.*?)<div id="block-citation">'
        self.language = 'en'

    def getvalue(self, field, html, dtype=None):
        result = self.findbyre(
            r'(?s)<div class="field-label">\s*{}\s*<.*?<div class=[^<>]*field-item[^<>]*>(.*?)</div>'
            .format(field), html)
        if result:
            result = self.TAGRE.sub('', result)
            if dtype:
                return self.findbyre('(.*)', result, dtype)
        return result

    def findinstanceof(self, html: str):
        return 'Q5'

    def findnames(self, html) -> List[str]:
        return [self.findbyre(r'<title>(.*?)[\|<]', html),
                self.findbyre('<h1[^<>]*>(.*?)</h1', html)]

    def finddescription(self, html: str):
        return self.findbyre('"description" content="(.*?)"', html)

    def findlongtext(self, html: str):
        return self.findbyre('(?s)<h1.*?<p>(.*?)</div>', html)

    def findbirthdate(self, html: str):
        return self.getvalue('Date of Birth', html)

    def findbirthplace(self, html: str):
        return self.getvalue('Birthplace', html, 'city')

    def finddeathdate(self, html: str):
        return self.getvalue('Date of Death', html)

    def findoccupations(self, html: str):
        section = self.findbyre('(?s)<div class="field-label">Occupations</div(>.*?<)/div>', html)
        if section:
            return self.findallbyre('>([^<>]*)<', section, 'occupation')
        return None


class WikiAnalyzer(Analyzer):
    def setup(self):
        site = 'wikipedia'
        self.language, self.id = self.id.split(':', 1)
        if self.language in ['wikiquote', 'wikisource', 'wiktionary']:
            site = self.language
            self.language, self.id = self.id.split(':', 1)
        self.dbproperty = None
        if self.language == 'be-tarask':
            self.language = 'be-x-old'
        if self.language == 'nb':
            self.language = 'no'
        if site == 'wikipedia':
            self.dbid = {
                'nl': 'Q10000', 'bs': 'Q1047829', 'nap': 'Q1047851', 'vec': 'Q1055841', 'sc': 'Q1058430',
                'ur': 'Q1067878', 'fo': 'Q8042979',
                'ast': 'Q1071918', 'bg': 'Q11913', 'it': 'Q11920', 'pt': 'Q11921', 'sl': 'Q14380', 'pl': 'Q1551807',
                'id': 'Q155214', 'sv': 'Q169514', 'fi': 'Q175482', 'ja': 'Q177837', 'ko': 'Q17985', 'da': 'Q181163',
                'eo': 'Q190551', 'cs': 'Q191168', 'no': 'Q58691283', 'sk': 'Q192582', 'ca': 'Q199693', 'uk': 'Q199698',
                'ar': 'Q199700', 'ro': 'Q199864', 'he': 'Q199913', 'et': 'Q200060', 'vi': 'Q200180', 'sr': 'Q200386',
                'lt': 'Q202472', 'hr': 'Q203488', 'ru': 'Q206855', 'sq': 'Q208533', 'nn': 'Q2349453', 'zh': 'Q30239',
                'en': 'Q328', 'jv': 'Q3477935', 'km': 'Q3568044', 'mr': 'Q3486726', 'ps': 'Q3568054', 'bn': 'Q427715',
                'de': 'Q48183', 'fa': 'Q48952', 'hu': 'Q53464', 'th': 'Q565074', 'tr': 'Q58255', 'hi': 'Q722040',
                'lv': 'Q728945', 'ceb': 'Q837615', 'fr': 'Q8447', 'es': 'Q8449', 'te': 'Q848046', 'sh': 'Q58679',
                'af': 'Q766705', 'als': 'Q1211233', 'eu': 'Q207620', 'commons': 'Q565', 'species': 'Q13679',
                'fy': 'Q2602203', 'el': 'Q11918', 'mai': 'Q18508969', 'hy': 'Q1975217', 'ka': 'Q848974',
                'li': 'Q2328409', 'be': 'Q877583', 'be-x-old': 'Q8937989', 'gl': 'Q841208', 'xmf': 'Q2029239',
                'bpy': 'Q1287192', 'ta': 'Q844491', 'ml': 'Q874555', 'br': 'Q846871', 'zh-min-nan': 'Q3239456',
                'oc': 'Q595628', 'simple': 'Q200183', 'az': 'Q58251', 'sco': 'Q1444686', 'nah': 'Q2744155',
                'pms': 'Q3046353', 'la': 'Q12237', 'azb': 'Q20789766', 'zh-classical': 'Q37041',
                'av': 'Q562665', 'ba': 'Q58209', 'ce': 'Q4783991', 'ms': 'Q845993', 'so': 'Q8572132',
                'vls': 'Q3568038', 'ckb': 'Q4115463', 'tl': 'Q877685', 'am': 'Q3025527', 'bo': 'Q2091593',
                'io': 'Q1154766', 'is': 'Q718394', 'sd': 'Q8571840', 'dv': 'Q928808', 'uz': 'Q2081526',
                'ug': 'Q60856', 'lb': 'Q950058', 'cy': 'Q848525', 'ky': 'Q60799', 'ku': 'Q1154741', 'kk': 'Q58172',
                'ga': 'Q875631', 'nds': 'Q4925786', 'ilo': 'Q8563685', 'mg': 'Q3123304', 'mk': 'Q842341',
                'pa': 'Q1754193', 'war': 'Q1648786', 'vo': 'Q714826', 'an': 'Q1147071', 'arz': 'Q2374285',
                'bcl': 'Q8561870', 'ht': 'Q1066461', 'qu': 'Q1377618', 'zh_min_nan': 'Q3239456', 'sw': 'Q722243',
                'nds-nl': 'Q1574617', 'gn': 'Q3807895', 'mzn': 'Q3568048', 'nrm': 'Q3568051', 'mad': 'Q104115350',
                'pnb': 'Q3696028', 'yo': 'Q1148240',
            }[self.language]
        elif site == 'wikisource':
            self.dbid = {
                'en': 'Q15156406', 'pl': 'Q15298974', 'ru': 'Q15634506', 'de': 'Q15522295', 'fr': 'Q15156541',
                'zh': 'Q19822573', 'he': 'Q22004676', 'it': 'Q15281537', 'es': 'Q15618752', 'ar': 'Q24577645',
                'nl': 'Q24577681', 'cs': 'Q16735590', 'la': 'Q21205461',
            }[self.language]
        else:
            self.dbid = {'wikiquote': 'Q369', 'wiktionary': 'Q151'}[site]
        self.iswiki = True
        self.skipfirst = True
        self.id = self.id.replace(' ', '_')
        if self.language in ['commons', 'species']:
            site = 'wikimedia'
        self.dbname = f'{site.title()} {self.language.upper()}'
        self.urlbase = 'https://{}.{}.org/wiki/{{id}}'.format(
            self.language, site)
        self.urlbase3 = 'https://{}.{}.org/w/index.php?title={{id}}&veswitched=1&action=edit'.format(
            self.language, site)
        self.hrtre = '{{(.*?)}}'
        self.mainRE = '(?s)<textarea[^<>]*name="wpTextbox1">(.*?)</textarea>'
        self.escapehtml = True
        if self.language in ['commons', 'species', 'simple']:
            self.language = 'en'

    def prepare(self, html: str):
        def reworkwikilink(wikipart):
            parts = wikipart[1].split('|')
            return '[[{}]]'.format(parts[0] if ':' in parts[0] else parts[-1])

        if not html:
            return None

        f = codecs.open('result.html', 'w', 'utf-8')
        f.write(html)
        f.close()
        html = re.search(self.mainRE, html)[1]
        html = re.sub(r'{{nowrap\|([^{}]*)}}', r'\1', html)
        return re.sub(r'\[\[([^\[\]]*)\]\]', reworkwikilink, html)

    @staticmethod
    def excludetemplatelight(text):
        templatetype = re.search('([^{|]*)', text)[0].lower().strip()
        firstword = templatetype.split()[0]
        lastword = templatetype.split()[-1]
        return (
            templatetype in ['sourcetext', 'ref-llibre', 'article', 'lien web',
                             'مرجع ويب', 'écrit', 'reflist']
            or firstword in ['citeer', 'cite', 'link', 'cita', 'cytuj',
                             'книга', 'citar', 'ouvrage', 'grafikus',
                             'citation', 'citácia', 'erreferentzia', 'citace',
                             'lien']
            or lastword in ['source', 'स्रोत', '인용']
        )

    def getinfos(self, names, html, dtype=None, splitters='<>,;/،・{}|*',
                 alt=None) -> List[str]:
        if not alt:
            alt = []
        if not splitters:
            splitters = None
        result = []
        for name in names:
            boxes = self.findallbyre(r'(?s){{((?:{{[^}]*}}|[^{}])*)}}',
                                     html.replace('[[', '').replace(']]', '').replace("'''", ''))
            for box in boxes:
                if self.excludetemplatelight(box):
                    continue
                if not splitters:
                    result += self.findallbyre(r'(?is)[\b\|_\s]%s\s*=((?:[^\|、\{\}]|\{\{[^\{\}]*\}\})+)' % name, box, dtype, alt=alt)
                else:
                    sections = self.findallbyre(r'(?is)[\b\|_\s]%s\s*=((?:[^\|、\{\}]|\{\{[^\{\}]*\}\})+)' % name, box, alt=alt)
                    for section in sections:
                        result += self.findallbyre(
                            fr'([^{splitters}]+)', section, dtype)
        return result

    def getinfo(self, names, html, dtype=None, splitters=None, alt=None) -> str:
        if not alt:
            alt = []
        for name in names:
            boxes = self.findallbyre(r'(?s){{((?:{{[^}]*}}|[^{}])*)}}',
                                     html.replace('[[', '').replace(']]', '').replace("'''", ''))
            for box in boxes:
                if self.excludetemplatelight(box):
                    continue
                if not splitters:
                    result = self.findallbyre(r'(?is)[\b\|_\s]%s\s*=((?:[^\|\{\}]|\{\{[^\{\}]*\}\})+)' % name, box, dtype, alt=alt)
                else:
                    result = []
                    preresult = self.findallbyre(r'(?is)[\b\|_\s]%s\s*=((?:[^\|\{\}]|\{\{[^\{\}]*\}\})+)' % name, box, alt=alt)
                    for section in preresult:
                        result += self.findallbyre(
                            fr'([^{splitters}]+)', section, dtype)
                if result:
                    return result[0]
        return None

    def findinstanceof(self, html: str):
        return self.getinfo([
            'background', 'färg', 'farve', 'fondo', 'culoare', '背景色', 'barva pozadí',
        ], html, 'instanceof')

    def findnames(self, html) -> List[str]:
        result = self.findallbyre(
            r"'''([^']+)'''",
            html.replace('[[', '').replace(']]', '').replace(
                '{{nbsp}}', ' ').replace("'''", '').replace("''", ''))
        result += self.findallbyre(r'{{voir homonymes\|(.*?)}', html)
        sections = self.getinfos([
            r'n[aou]me[\w\s_]*', r'naam\d*', 'name[ns]', r'imię[\w\s]*',
            'nimi', 'անուն', 'pseudonie?m', 'imiona', r'имя(?:[\s_][\w\s_])*',
            r'под именем(?:_\d+)?', r'име(?:-[\w\s]+)?', '人名', '全名',
            r"ім'я(?:[\s_][\w\s_]*)?", r'tên[\w\s]*', '名称', 'імен[аі]',
            'псевдонім', 'beter-bekend-als', r'nombre[\w\s]*', 'الاسم',
            r'[\w\s]*jméno', 'ime', r'nom(?:[\s_][\w\s_]+)?', 'vardas',
            'ook bekend als', 'alias', 'otros nombres', r'שם[\w\s]*', 'név',
            'ふりがな', '別名義', r"ім'я[\w\s\_]*", 'псевдонім', 'прізвисько',
            'pseudônimos?', 'όνομα', 'есімі', 'isim', 'isimleri', 'adı',
            'نام', 'لقب', r'imię[\w\s]*', 'alcume', '芸名', '本名', '이름',
            '본명', 'anarana', r'jina[\w\s]*', 'nom de naissance', '姓名',
            '原名', 'navn', 'nazwa', 'títol original', 'přezdívka',
            'pseŭdonomo', 'nomo', 'alias', 'namn', r'pseudonym(?:\(er\))?',
            r'názov[\w\s]*', 'názvy', '名前', 'jinak zvaný', 'есімі',
            'doğum_adı',
        ], html)
        for section in sections:
            result += self.findallbyre(r'([^,;]*)', section)
        return [
            self.id.replace('_', ' ').split('(')[0].split(':', 1)[-1]] + result

    def findlanguagenames(self, html: str):
        values = self.findallbyre(r'{{lang[-\|](\w+\|.*?)}}', html.replace("'''", ''))
        result = [value.split('|', 1) for value in values]
        values = self.findallbyre(r'\[\[([a-z]{2}:.+?)\]\]', html)
        result += [value.split(':', 1) for value in values]
        return result

    @staticmethod
    def excludetemplate(text):
        templatetype = re.search('([^{|]+)', text)[0].lower().strip()
        firstword = templatetype.split()[0]
        lastword = templatetype.split()[-1]
        return (
            templatetype in ['sourcetext', 's-bef', 's-ttl', 's-aft',
                             'appendix', 'familytree', 'ref-llibre', 'sfn',
                             'obra citada', 'arbre généalogique',
                             'infobox chinese namen',
                             'infobox tibetaanse namen', 'reflist',
                             'navedi splet', 'article', 'הערה', 'مرجع ويب',
                             'écrit']
            or firstword in ['citeer', 'cite', 'ouvrage', 'link', 'grafikus',
                             'cita', 'cytuj', 'книга', 'citar', 'ouvrage',
                             'citation', 'erreferentzia', 'lien', 'citace',
                             'citácia']
            or lastword in ['source', 'स्रोत', '인용']
            or templatetype.startswith('ahnentafel')
        )

    def findlongtext(self, html: str):
        changedhtml = html.strip()
        while changedhtml.startswith('{{'):
            changedhtml = changedhtml[changedhtml.find('}}') + 2:].strip()
        return changedhtml[:2000] + '\n---\n' + '\n'.join(
            [x for x in self.findallbyre(r'(?s){{((?:[^{}]|{{[^}]*}})*=(?:[^{}]|{{[^}]*}})*)}}', html)
             if not self.excludetemplate(x)]) + '\n' + ' - '.join(self.findallbyre(r'\[\[(\w+:.*?)\]\]', html))

    def removewiki(self, text):
        if not text:
            return None
        return text.replace('[[', '').replace(']]', '').replace("'''", '').replace("''", '')

    def finddescriptions(self, html: str):
        return self.getinfos([
                'fineincipit', 'commentaire', 'kurzbeschreibung', 'fets_destacables', 'описание', 'bekendvan',
                'postcognome', 'postnazionalità', 'known_for', 'description', 'başlık', 'известен как',
        ], html) \
            + [self.removewiki(
                self.findbyre(r" %s(?: stato)? (?:e[eiu]?n |an? |u[nm][ea]? |eine[nr]? |'n |ne |e |unha |ett? |o |một )?(.+?)[\.;]" % word, html)) for
               word in [
                   'is', 'w[aio]s', 'ist', 'wao?r', 'este?', 'était', 'fu', 'fou', '—', '-', 'era', 'е', 'היה', 'by[łl]',
                   'foi', 'был', 'fue', 'oli', 'bio', 'wie', 'var', 'je', 'იყო', 'adalah', 'é', 'ήταν', 'هو', 'стала',
                   '[eé]s', 'er', 'est[ia]s', 'एक', 'یک', 'كان', 'è', 'бил', 'là', 'on', ',', 'on', 'egy', 'sono',
                   'är', 'are', 'fuit', 'وهو', 'esas', 'は、', 'ni', 'là']] \
                   + self.findallbyre(r'{{short description\|(.*?)}', html) \
                   + self.findallbyre(r'\[\[[^\[\]\|]+?:([^\[\]\|]+)\]\]', html) \
                   + [x.replace('_', ' ') for x in self.findallbyre(r'\((.*?)\)', self.id)]

    def findoccupations(self, html: str):
        return self.getinfos([
            'charte', r'attività\s*(?:altre)?\d*', 'occupation', 'zawód', 'functie', 'spfunc', 'beroep',
            'рід_діяльності', 'المهنة', 'ocupación', 'עיסוק', '職業', 'ocupação', 'ιδιότητα', 'мамандығы',
            'zanimanje', 'meslek', 'mesleği', 'activités?', 'پیشه', 'профессия', 'profesión', '직업',
            'asa', 'kazi yake', r'(?:antaŭ|aliaj)?okupoj?\d*', 'работил', 'ocupacio', 'aktywność zawodowa',
            'funkcja', 'profesio', 'ocupație', 'povolání', 'töökoht', 'szakma', 'profession',
        ], html, 'occupation') + \
            self.findallbyre(r'(?i)info(?:box|boks|taula|kast)(?:\s*-\s*)?([\w\s]+)', html, 'occupation') \
            + self.findallbyre(
                r'基礎情報([\w\s]+)', html, 'occupation') \
                + self.findallbyre(r'{([\w\s]+)infobox', html, 'occupation') + self.findallbyre(
                    r'Categorie:\s*(\w+) (?:van|der) ', html, 'occupation') \
                    + self.findallbyre(r'(?i)inligtingskas([\w\s]+)', html, 'occupation')

    def findpositions(self, html: str):
        return self.getinfos([
            r'functie\d?', r'titre\d', r'stanowisko\d*', r'(?:\d+\. )?funkcja', r'должность(?:_\d+)?', r'títulos?\d*',
            'tytuł', 'titles', 'chức vị', r'amt\d*', 'jabatan', 'carica', '(?:altri)?titol[oi]', r'титул_?\d*',
            'anderwerk', 'titels', 'autres fonctions', 'апісанне выявы', r'titul(?:y|as)?\d*', 'title',
            r'\w*ambt(?:en)?', 'carica', 'other_post', 'посада', '事務所', '最高職務',
        ], html, 'position') \
            + self.findallbyre(r'S-ttl\|title\s*=(.*?)\|', html, 'position') + self.findallbyre(
                r"Categor[ií]a:((?:Re[iy]e?|Conde)s d['e].*?)(?:\]|del siglo)", html, 'position') \
                + self.findallbyre(r'Kategorie:\s*(König \([^\[\]]*\))', html, 'position') + self.findallbyre(
                    r'Category:([^\[\]]+ king)', html, 'position') \
                    + self.findallbyre(r'Catégorie:\s*(Roi .*?)\]', html, 'position') + self.findallbyre(
                        r'Kategoria:(Królowie .*?)\]', html, 'position') \
                        + self.findallbyre(r'Kategori:(Raja .*?)\]', html, 'position') + self.findallbyre(
                            r'[cC]ategorie:\s*((?:Heerser|Bisschop|Grootmeester|Abdis|Koning|Drost) .*?)\]', html, 'position')

    def findtitles(self, html: str):
        return self.getinfos(
            [r'titre\d*', r'титул_?\d*', r'tước vị[\w\s]*', '爵位', 'titels', 'titles', 'títuloas', r'titul(?:y|as|ai)?\d*',
             '(?:altri)?titol[oi]', ], html, 'title') + \
               self.findallbyre(r'Categorie:\s*((?:Heer|Vorst|Graaf) van.*?)\]', html, 'title') + self.findallbyre(
            r'Kategorie:\s*((?:Herzog|Herr|Graf|Vizegraf) \([^\[\]]*\))\s*\]', html, 'title') + \
               self.findallbyre(r'Catégorie:\s*((?:Duc|Prince|Comte) de.*?)\]', html, 'title') + \
               self.findallbyre(r'Category:'
                                '((?:Du(?:k|chess)e|Princ(?:ess)?e|Lord|Margrav(?:in)?e|Grand Master|Count|Viscount)s'
                                r' of.*?)\]', html, 'title') \
               + self.findallbyre(r'Categoría:((?:Prínciple|Señore|Conde|Duque)s de .*?)\]', html,
                                  'title') + self.findallbyre(r'Kategória:([^\[\]]+ királyai)', html, 'title')

    def findspouses(self, html: str):
        return self.getinfos(
            ['spouse', 'consorte', 'conjoint', 'małżeństwo', 'mąż', 'супруга', 'съпруга на', r'[\w\s]*брак',
             'echtgenoot', 'echtgenote', r'配偶者\d*', r'(?:\d+\. )?związek(?: z)?', 'чоловік', 'phối ngẫu',
             'vợ', 'chồng', 'الزوج', 'жонка', 'královna', 'sutuoktin(?:ė|is)', 'partners?', 'supružnik',
             'gade', 'cónyuge', 'conjoint', 'házastárs', 'дружина', 'cônjuge', 'σύζυγος', 'همسر',
             'współmałżonek', 'c[ôo]njuge', 'cónxuxe', '배우자', 'ndoa', 'supruga?', '配偶', 'abikaasa',
             'maire',
             ], html, 'person', splitters='<>,;)') + \
               self.findallbyre(r'{(?:marriage|matrimonio)\|(.*?)[\|}]', html, 'person')

    def findpartners(self, html: str):
        return self.getinfos(['liaisons', r'partner\d*', 'partnerka', 'relacja', 'cónyuge', 'فرزندان', 'lewensmaat',
                              'élettárs', 'conjunt',
                              ], html, 'person')

    def findfather(self, html: str):
        return self.getinfo(['father', 'padre', 'vader', 'père', 'far', 'ojciec', 'отец', 'баща', '父親', 'батько',
                             'cha', 'الأب', 'per', 'бацька', 'pai', 'otec', 'tėvas', 'батько', 'nome_pai',
                             ], html, 'person') or \
               self.getinfo(['rodzice', 'parents', 'roditelji', 'γονείς', 'والدین', 'parella', '부모', 'wazazi', 'ouers',
                             ], html, 'male-person') or \
               self.findbyre(r'\|otec\|([^|{}]*)}', html, 'person')

    def findmother(self, html: str):
        return self.getinfo(['mother', 'madre', 'moeder', 'mère', 'mor', 'matka', 'мать', 'майка', '母親', 'матір', 'mẹ',
                             'الأم', 'mer', 'маці', 'mãe', 'motina', 'мати', 'nome_mãe', ], html, 'person') or \
               self.getinfo(['rodzice', 'parents', 'roditelji', 'γονείς', 'والدین', 'parella', '부모', 'wazazi', 'ouers',
                             ], html, 'female-person') or \
               self.findbyre(r'\|matka\|([^|{}]*)}', html, 'person')

    def findchildren(self, html: str):
        return self.getinfos(
            ['issue', 'figli', 'enfants', 'children', 'kinder(?:en|s)', r'(?:\d+\. )?dzieci', 'дети', 'потомство',
             '子女', 'діти', 'con cái', 'descendencia', 'الأولاد', 'potostvo', 'vaikai', 'hijos', 'enfants?',
             'fil[hl]os', 'τέκνα', 'deca', 'çocukları', 'والدین', '자녀', 'watoto', 'деца', 'lapsed',
             ], html, 'person')

    def findsiblings(self, html: str):
        return self.getinfos(['broerzus', 'rodzeństwo', 'rodbina', 'broer', 'zuster', 'αδέλφια', '형제자매',
                              ], html, 'person') + \
               self.findallbyre(r'\|(?:bratr|sestra)\|([^\|{}]*)}', html, 'person') + \
               self.findallbyre(r'\[\[([^\[\]]*)\]\] \(brat\)', html, 'person')

    def findkins(self, html: str):
        return self.getinfos(['родичі', 'famille', '著名な家族', '친척'], html, 'person')

    def findfamily(self, html: str):
        return self.getinfo(['house', 'd[iy]nast[iyí]j?[ae]?', 'famille', 'noble family', 'rodzina', 'род', 'династия',
                             '王家', '王朝', 'hoàng tộc', 'casa', '家名・爵位', 'рід'], html, 'family') or \
               self.findbyre(r'Categorie:\s*Huis(.*?)\]\]', html, 'family') or self.findbyre(
            r'Catégorie:\s*Maison (.*?)\]\]', html, 'family') or \
               self.findbyre(r'Category:([^\[\]]*)(?:dynasty|family)', html, 'family') or self.findbyre(
            r'Kategorie:\s*Haus(.*?)\]', html, 'family') or \
               self.findbyre(r'Categor[ií]a:Casa(?:to)? d[ei](.*?)\]', html, 'family') or self.findbyre(
            r'Kategory:Hûs(.*?)\]', html, 'family') or \
               self.findbyre(r'Categorie:\s*([^\[\]]*)dynastie\]', html, 'family') or self.findbyre(
            r'Category:House of(.*?)\]', html, 'family')

    def findgens(self, html: str):
        return self.findbyre(r'Categorie:\s*Gens(.*?)\]\]', html, 'gens')

    def findbirthdate(self, html: str):
        return self.findbyre(
            r'{{(?:[bB]irth[\-\s]date(?: and age)?|dni|[dD]oğum tarihi ve yaşı|출생일(?:과 나이)?|[gG]eboortedatum(?: en ouderdom)?|'
            'Data naixement|[dD]atum narození a věk|Naskiĝdato|[dD]atum rođenja|生年月日と年齢|死亡年月日と没年齢|'
            'роден на|[dD]ate de naissance|'
            r')\s*(?:\|df=\w+)?\|(\d+\|\d+\|\d+)', html) or \
            self.findbyre(r'{{[dD]ate de naissance\|([\w\s]+)\}\}', html) or\
            self.findbyre(r'{{(?:[bB]irth year and age)\|(\d+)', html) or\
            self.getinfo(['geburtsdatum', 'birth[_ ]?date', 'data di nascita', 'annonascita', 'geboren?', 'født',
                          'data urodzenia', 'data_naixement', 'gbdat', 'data_nascimento', 'дата рождения', '出生日',
                          'дата_народження', 'geboortedatum', 'sinh', 'fecha de nacimiento', 'تاريخ الولادة',
                          'date de naissance', 'дата нараджэння', 'data de nascimento', 'datum narození', 'gimė',
                          'תאריך לידה', 'születési dátum', 'дата народження', 'jaiotza data', 'nascimento_data',
                          'ημερομηνία γέννησης', 'туған күні', 'datum_rođenja', 'تاریخ تولد', 'teraka', 'alizaliwa',
                          'naskiĝjaro', 'rođenje', '出生日期', 'dato de naskiĝo', 'sünnlaeg', 'syntymäaika',
                          'туған күні', '태어난 날', 'datadenaissença', 'doğum_tarihi'],
                         html) \
            or self.findbyre(r'Category:\s*(\d+) births', html) or self.findbyre(r'Kategorie:\s*Geboren (\d+)', html) or \
               self.findbyre(r'Catégorie:\s*Naissance en ([^\[\]]*)\]', html) or self.findbyre(
            r'Categorie:\s*Nașteri în (.*?)\]', html) or \
               self.findbyre(r'(.*)-', self.getinfo(['leven'], html) or '') or self.findbyre(
            r'Kategory:Persoan berne yn(.*?)\]', html) or \
               self.findbyre(r'{{bd\|([^{}]*?)\|', html) or self.findbyre(r'(\d+)年生', html)

    def finddeathdate(self, html: str):
        return self.findbyre(r'{{(?:[dD]eath (?:date|year)[\w\s]*|morte|사망일과 나이|Data defunció i edat|[dD]atum smrti i godine|'
                             '[dD]atum úmrtí a věk|[dD]ate de décès|починал на|[sS]terfdatum(?: en ouderdom)?|'
                             r')\|(\d+\|\d+\|\d+)[}|]', html) or \
               self.findbyre(r'{{(?:死亡年月日と没年齢)\|\d+\|\d+\|\d+\|(\d+\|\d+\|\d+)[}|]', html) or\
               self.getinfo(
                   ['sterbedatum', 'death[_ ]?date', 'data di morte', 'annomorte', 'date de décès', 'gestorven', 'død',
                    'data śmierci', 'data_defuncio', r'sterf(?:te)?dat\w*', 'data_morte', 'дата смерти', '死亡日',
                    'дата_смерті', 'mất', 'overlijdensdatum', 'overleden', 'fecha de defunción', 'تاريخ الوفاة',
                    'datum_smrti', 'дата смерці', 'dta da morte', 'datum úmrtí', 'mirė', 'oorlede',
                    'fecha de fallecimiento', 'תאריך פטירה', 'halál dátuma', 'дата смерті', 'heriotza data',
                    'morte_data', 'ημερομηνία θανάτου', 'қайтыс болған күн7і', 'datum_smrti', 'ölüm_tarihi',
                    'تاریخ مرگ', 'falecimento', 'maty', 'alikufa', 'mortjaro', 'smrt', '逝世日期', 'surmaaeg',
                    'kuolinaika', 'қайтыс болған күні', '죽은 날', 'datadedecès', 'ölüm_tarihi',
                    ], html) or \
               self.findbyre(r'Category:\s*(\d+) deaths', html) or \
               self.findbyre(r'Catégorie:\s*Décès en ([^\[\]]*)\]', html) or \
               self.findbyre(r'Kategorie:\s*Gestorben (\d+)', html) or \
               self.findbyre(r'{{death year and age\|(.*?)\|', html) or \
               self.findbyre(r'Categoria:Mortos em (.*?)\]', html) or self.findbyre(r'Category:(\d+)年没\]', html) or \
               self.findbyre(r'Categorie:\s*Decese în (.*?)\]', html) or\
               self.findbyre(r'Kategori:Kematian(.*?)\]', html) or \
               self.findbyre(r'Kategory:Persoan stoarn yn (.*?)\]', html) or \
               self.findbyre(r'-(.*)', self.getinfo(['leven'], html) or '') or self.findbyre(r'(\d+)年没', html) or \
               self.findbyre(r'{{bd\|[^[\|{}]*\|[^[\|{}]*\|([^[\|{}]*)\|', html)

    def findburialdate(self, html: str):
        return self.getinfo(['埋葬日', 'datum pohřbení'], html)

    def findbirthplace(self, html: str):
        return self.getinfo(
            ['birth[_ ]?place', 'luogo di nascita', r'luogonascita\w*', 'geboren_in', 'geburtsort', 'fødested',
             'geboorteplaats', 'miejsce urodzenia', 'lloc_naixement', 'gbplaats', 'место рождения', 'място на раждане',
             '生地', 'місце_народження', r'lugar\s*de\s*nac[ei]mi?ento', 'مكان الولادة', 'lieu de naissance',
             'месца нараджэння', 'local de nascimento', 'místo narození', 'gimimo vieta', 'geboortestad',
             'geboorteplek', 'תאריך לידה', 'születési hely', '出生地點?', 'місце народження', 'nascimento_local',
             'τόπος γέννησης', 'туған жері', r'mj?esto[\s_]rođenja', 'doğum_yeri', 'محل تولد', 'local_nascimento',
             'роден-място', '출생지', 'naskiĝloko', 'loko de naskiĝo', 'sünnikoht', 'syntymäpaikka', 'туған жері',
             '태어난 곳', 'luòcdenaissença', 'doğum_yeri',
             ], html, 'city') or \
               self.findbyre(r'Category:Births in(.*?)\]', html, 'city') or \
               self.findbyre(r'Categoria:Naturais de(.*?)\]', html, 'city')

    def finddeathplace(self, html: str):
        return self.getinfo(
            ['death[_ ]?place', 'luogo di morte', 'luogomorte', 'lieu de décès', 'gestorven_in', 'sterbeort',
             'dødested', 'miejsce śmierci', 'lloc_defuncio', 'sterfplaats', 'место смерти', 'място на смърт(?:та)?',
             '没地', 'місце_смерті', 'nơi mất', 'overlijdensplaats', 'lugar de defunción', 'مكان الوفاة',
             'месца смерці', 'local da morte', 'místo úmrtí', 'mirties vieta', 'stadvanoverlijden', 'מקום פטירה',
             'sterfteplek', 'lugar de fallecimiento', 'halál helye', '死没地', 'місце смерті', 'morte_local',
             'τόπος θανάτου', 'қайтыс болған жері', r'mj?esto_[\s_]mrti', 'ölüm_yeri', 'محل مرگ', 'починал-място',
             'lugardefalecemento', '사망지', 'mortloko', '逝世地點', 'surmakoht', 'kuolinpaikka', 'қайтыс болған жері',
             '죽은 곳', 'plaatsvanoverlijden', 'luòcdedecès', 'ölüm_sebebi',
             ], html, 'city') or \
               self.findbyre(r'{{МестоСмерти\|([^{}\|]*)', html, 'city') or \
               self.findbyre(r'Category:Deaths in(.*?)\]', html, 'city')

    def findburialplace(self, html: str):
        return self.getinfo(
            ['place of burial', 'sepoltura', 'begraven', 'gravsted', 'resting_place', 'miejsce spoczynku', 'sepultura',
             'похоронен', 'погребан', '埋葬地', '陵墓', 'burial_place', 'lugar de entierro', 'مكان الدفن',
             'local de enterro', 'místo pohřbení', 'palaidotas', 'поховання', 'مدفن', '墓葬'],
            html, 'cemetery',
            alt=['city']) \
            or self.findbyre(r'Category:Burials at (.*?)\]', html, 'cemetery')

    def findreligions(self, html: str):
        return self.getinfos(['religione?', '宗教', 'wyznanie', 'religij?[ea]', 'الديانة', r'церковь_?\d*', 'church',
                              'конфесія', 'religião', '종교', 'uskonto', 'dini',
                              ], html, 'religion') + \
               self.findallbyre(r'Catégorie:Religieux(.*?)\]', html, 'religion')

    def findnationalities(self, html: str):
        return self.getinfos(
            [r'nazionalità[\w\s_]*', 'allégeance', 'land', 'nationality', 'narodowość', 'państwo', 'громадянство',
             'нац[іи]ональ?н[іо]сть?', 'الجنسية', 'nacionalnost', 'nationalité', 'na[ts]ionaliteit', 'citizenship',
             'geboorteland', 'nacionalidade?', 'מדינה', '国籍', 'підданство', 'εθνικότητα', 'υπηκοότητα',
             R'nazione\d*', 'азаматтығы', 'ملیت', 'гражданство', 'nacionalitat', 'firenena', 'nchi',
             r'nationalteam\d*', 'ŝtato', '國家', 'občanství', 'kodakondsus', 'rahvus', 'kansalaisuus',
             'nationalité', 'állampolgárság', 'азаматтығы', '국적', 'paísdorigina', 'milliyeti',
             ], html, 'country') or \
               self.findallbyre(r'Category:\d+th-century people of (.*?)\]\]', html, 'country') or \
               self.findallbyre(r'Categorie:\s*Persoon in([^\[\]]+)in de \d+e eeuw', html, 'country') or \
               self.findallbyre(r'Category:\d+th-century ([^\[\]]+) people\]\]', html, 'country') or \
               self.findallbyre(r'Category:([^\[\]]+) do século [IVX]+\]\]', html, 'country') or \
               self.findallbyre(r'Kategorie:\s*Person \(([^\[\]]*)\)\]', html, 'country') or \
               self.findallbyre(r'Kategori:Tokoh(.*?)\]', html, 'country') or \
               self.findallbyre(r'Categoria:([^\[\]]+) del Segle [IVX]+', html, 'country') or \
               self.findallbyre(r'Categorie:\s*([^\[\]]*) persoon\]', html, 'country')

    def findorigcountries(self, html: str):
        return self.getinfos(['país', "pays d'origine", 'nazione', 'pochodzenie'], html, 'country')

    def findlastname(self, html: str):
        return self.getinfo(['cognome', 'surnom', 'familinomo', 'priezvisko', 'lastname'], html, 'lastname') or \
               self.findbyre(r'(?:DEFAULTSORT|SORTIERUNG):([^{},]+),', html, 'lastname')

    def findfirstname(self, html: str):
        return self.getinfo(['antaŭnomo', 'nome', 'meno', 'firstname'], html, 'firstname') \
               or self.findbyre(r'(?:DEFAULTSORT|SORTIERUNG|ORDENA):[^{},]+,\s*([\w\-]+)', html, 'firstname')

    def findgender(self, html: str):
        return self.getinfo(['sesso'], html, 'gender') or \
               self.findbyre(r'Kategorie:\s*(Mann|Frau|Kvinnor)\]', html, 'gender')

    def findmemberships(self, html: str):
        return self.getinfos(['org', 'groep'], html, 'organization') + \
               self.getinfos(['associated_acts', 'artistas_relacionados'], html, 'group') + \
               self.findallbyre(r'Categor(?:ie|y):\s*(?:Lid van|Members of)(.*?)\]\]', html, 'organization')

    def findmixedrefs(self, html: str):
        imdb = self.findbyre(r'IMDb name\|([^{}]*)\|', html) or self.getinfo(['imdb', 'imdb_id'], html)
        if imdb and imdb.strip() and imdb.strip()[0] in '0123456789':
            imdb = 'nm' + imdb.strip()
        if not imdb or not imdb.strip() or imdb.startswith('tt'):
            imdb = None
        return self.finddefaultmixedrefs(html) + [
            ('P214', self.getinfo(['viaf'], html)),
            ('P227', self.getinfo(['gnd'], html)),
            ('P345', imdb),
            ('P349', self.getinfo(['ndl'], html)),
            ('P428', self.getinfo(['botaaniline_nimelühend'], html)),
            ('P650', self.getinfo(['rkd'], html)),
            ('P723', self.getinfo(['dbnl'], html)),
            ('P835', self.getinfo(['zooloogiline_nimelühend'], html)),
            ('P1220', self.getinfo(['ibdb'], html)),
            ('P1969', self.getinfo(['moviemeter'], html)),
            ('P2002', self.getinfo(['twitter'], html)),
            ('P2013', self.getinfo(['facebook'], html)),
        ]

    def findschools(self, html: str):
        return self.getinfos(['education', 'alma[ _]?m[aá]ter', 'edukacja', r'[\w\s]*uczelnia', 'formation', 'skool',
                              'universiteit', 'educacio', 'альма-матер', 'diplôme', 'iskolái', '출신 대학',
                              ], html, 'university') + \
               self.findallbyre(r'Kategorie:\s*Absolvent de[rs] (.*?)\]', html, 'university') + \
               self.findallbyre(r'Category:\s*Alumni of(?: the)?(.*?)\]', html, 'university') + \
               self.findallbyre(r'Category:People educated at(.*?)\]', html, 'university') + \
               self.findallbyre(r'Category:([^\[\]]+) alumni\]', html, 'university') +\
               self.findallbyre(r'Categoria:Alunos do (.*?)\]', html, 'university')

    def findemployers(self, html: str):
        return self.getinfos(
            ['employer', 'pracodawca', 'institutions', 'empleador', r'jednostka podrz\d* nazwa',
             'workplaces', 'instituutti', 'жұмыс орны', '소속', 'çalıştığı_yerler'],
            html, 'employer', alt=['university']) \
            + self.findallbyre(r'Category:([^\[\]]+) faculty', html, 'university')

    def findteachers(self, html: str):
        return self.getinfos(['maîtres?', 'leraren', 'ohjaaja'], html, 'artist')

    def findwebsite(self, html: str):
        result = self.getinfo(['website', 'www', 'site internet', 'אתר אינטרנט', 'honlap', '公式サイト', 'сайты?',
                               'ιστοσελίδα', 'sitio web', 'وب‌گاه', 'web', '웹사이트', 'tovuti rasmi', 'webwerf',
                               'kotisivu', 'internettside', 'hemsida', 'hjemmeside', 'site', 'webstránka',
                               'veebileht', 'weboldal',
                               ], html)
        if result:
            return self.findbyre(r'(\w+://[\w/\.\-_]+)', result)
        return None

    def findwebpages(self, html: str):
        return self.getinfos(['קישור'], html)

    def findmannerdeath(self, html: str):
        return self.getinfo(['przyczyna śmierci', 'причина_смерті', 'سبب الوفاة', 'doodsoorzaak', 'death_cause',
                             'причина смерті'], html, 'mannerdeath') or \
               self.findbyre(r'Categoría:Fallecidos por(.*?)\]', html, 'mannerdeath')

    def findcausedeath(self, html: str):
        return self.getinfo(['przyczyna śmierci', 'причина_смерті', 'سبب الوفاة', 'doodsoorzaak', 'death_cause',
                             'причина смерті', 'vatandaşlığı'], html, 'causedeath') \
                             or self.findbyre(r'Categoría:Fallecidos por(.*?)\]', html, 'causedeath')

    def findresidences(self, html: str):
        return self.getinfos(['miejsce zamieszkania', 'місце_проживання', 'الإقامة', 'residence', 'residência',
                              'місце проживання', 'loĝloko', 'elukoht', 'asuinpaikat', 'domicile', '거주지'],
                             html, 'city')

    def findworkplaces(self, html: str):
        return self.getinfos(['место работы'], html, 'city')

    def finddegrees(self, html: str):
        return self.getinfos(['tytuł naukowy', 'education', 'учёная степень'], html, 'degree')

    def findheight(self, html: str):
        return self.getinfo(['зріст', 'estatura', '身長', 'зріст', '身長', 'height', 'výška'], html)

    def findweights(self, html: str):
        return self.getinfos(['masa', 'вага', 'вага', 'váha'], html)

    def findparties(self, html: str):
        return self.getinfos(['partia', 'партія'], html, 'party')

    def findawards(self, html: str):
        result = self.getinfos(['odznaczenia', 'onderscheidingen', 'الجوائز', 'distinctions', 'prizes',
                                r'pr[eé]mios[\w\s]*', 'ou?tros premios', 'awards', 'нагороди', 'марапаттары',
                                'apdovanojimai', 'جوایز', 'nagrody', '수상', 'toekennings', 'premis',
                                'oscar', 'emmy', 'tony', 'zlatni globus', 'bafta', 'cesar', 'goya', 'afi',
                                'olivier', 'saturn', 'nagrade', 'награды и премии', 'tunnustus',
                                'palkinnot', 'prix', 'kitüntetései', 'марапаттары', 'prijs', 'distincions',
                                'ödüller'], html)
        return [self.findbyre(r'([^\(\)]+)', r, 'award') for r in result]

    def findranks(self, html: str):
        return self.getinfos(['rang', 'grade militaire', 'військове звання'], html, 'rank')

    def findimage(self, html: str):
        result = self.getinfo(['imat?ge[nm]?', 'immagine', 'изображение(?: за личността)?', '画像', 'grafika?',
                               'afbeelding', 'hình', '圖像', 'зображення', 'afbeelding', 'صورة', 'выява',
                               'obráz[eo]k', 'vaizdas', 'slika', 'beeld', 'kép', '画像ファイル', 'зображення',
                               'εικόνα', 'суреті?', 'foto', 'slika', 'resim', 'تصویر', 'награды', 'портрет',
                               'imaxe', '사진', 'sary', 'picha', 'dosiero', 'imatge', '圖片名稱', 'portreto',
                               'kuva', 'պատկեր', 'bilde?', 'zdjęcie', 'img', 'фото', 'pilt', '그림',
                               'resim_adı',
                               ], html)
        if result and '.' in result:
            return result.split(':')[-1]
        return None

    def findcoatarms(self, html: str):
        return self.getinfo(['герб', 'herb', 'escudo', 'icone', 'пасада', 'герб'], html)

    def findsignature(self, html: str):
        return self.getinfo(['п[оі]дпис', 'faksymile', 'توقيع', 'po[dt]pis', 'handtekening', 'автограф',
                             'imza', 'sinatura', 'namnteckning', 'allkiri', 'allekirjoitus', 'signature',
                             'aláirás', 'imza',
                             ], html)

    def findlogo(self, html: str):
        return self.getinfo(['logo', 'logotypbild'], html)

    def findbranches(self, html: str):
        return self.getinfos(['onderdeel', 'eenheid', 'arme'], html, 'militarybranch')

    def findconflicts(self, html: str):
        return self.getinfos(['veldslagen(?:-naam)?', 'conflic?ts'], html, 'conflict')

    def findinworks(self, html: str):
        return self.findallbyre(r'Category:Characters in(.*?)\]', html, 'work') + \
               self.findallbyre(r'Categor[ií]a:Persona[tg]?[jg][ei]n?s? d[eo][li]?(.*?)\]', html, 'work') + \
               self.findallbyre(r'Kategorie:\s*Person i[nm](.*?)\]', html, 'work') + \
               self.findallbyre(r'Category:People in(.*?)\]', html, 'work') + \
               self.findallbyre(r'Catégorie:\s*Personnage d[ue]s?(.*?)\]', html, 'work') + \
               self.findallbyre(r'Categorie:\s*Persoon uit(.*?)\]', html, 'work')

    def findethnicities(self, html: str):
        return self.getinfos(['عرقية', 'ethnicity', '族裔'], html, 'ethnicity')

    def findbloodtype(self, html: str):
        return self.getinfo(['血液型'], html, 'bloodtype')

    def findfeastday(self, html: str):
        return self.getinfo(['fête', 'feestdag', 'feast_day', 'festivi[dt]ad'], html, 'date')

    def findpatronof(self, html: str):
        return self.getinfos(['beschermheilige_voor', 'patronat?ge', 'patrono'], html, 'subject')

    def findrelorder(self, html: str):
        return self.getinfo(['ordre'], html, 'religious order')

    def findgenres(self, html: str):
        return self.getinfos(['stijl', r'g[eè]ne?re\d*', 'estilo', 'ジャンル', 'жанр(?:ове)?', 'tyylilajit',
                              'ժանրեր', 'sjanger', 'xénero', r'genre\(r\)', 'gatunek', 'žáne?r'],
                             html, 'genre', alt=['art-genre', 'music-genre', 'literature-genre', 'film-genre'])

    def findmovements(self, html: str):
        return self.getinfos(['stroming', 'mou?vement', 'style', 'school_tradition', 'movimi?ento', 'stijl',
                              ], html, 'movement')

    def findnotableworks(self, html: str):
        return self.getinfos([r'notable[\s_]?works?', 'bekende-werken', R'\w+ notables', '主な作品',
                              'œuvres principales', 'principais_trabalhos', 'bitna uloga', 'obra-prima',
                              '著作', 'belangrijke_projecten', 'known_for', 'tuntumad_tööd', 'tunnetut työt',
                              'munkái',
                              ], html, 'work') + \
               self.getinfos(['films notables', 'значими филми', 'millors_films', 'znameniti_filmovi',
                              'noemenswaardige rolprente', 'važniji filmovi',
                              ], html, 'film', alt=['work']) +\
               self.getinfos(['belangrijke_gebouwen'], html, 'building')

    def findworkfields(self, html: str):
        return self.getinfos(['field', '(?:main_)?interests', 'known_for', 'زمینه فعالیت', 'specjalność',
                              r'[\w\s_]*dyscyplina', 'área', 'научная сфера', 'domaine', 'known_for',
                              'tegevusala', 'tutkimusalue', 'champs', 'ғылыми аясы', 'несімен белгілі',
                              '분야', '주요 업적', 'dalı', 'önemli_başarıları'],
                             html, 'subject')

    def finddocstudents(self, html: str):
        return self.getinfos(['doctoral_students', 'знаменитые ученики', 'étudiants thèse', 'doktora_öğrencileri'],
                             html, 'scientist')

    def findadvisors(self, html: str):
        return self.getinfos(['doctoral_advisor', 'научный руководитель', 'academic advisors',
                              'doktoritöö_juhendaja', 'directeur thèse', 'ғылыми жетекші'],
                             html, 'scientist')

    def findheights(self, html: str):
        return self.getinfos(['lengte', 'height'], html, splitters=None)

    def findsports(self, html: str):
        return self.getinfos(['sport'], html, 'sport')

    def findsportteams(self, html: str):
        return self.getinfos([r'clubs?\d*', r'[\w\s]*kluby', r'klub aktuální\s*\w?', 'tým'], html, 'club')

    def findteampositions(self, html: str):
        return self.getinfos(['positie', 'pozice'], html, 'sportposition')

    def findlanguagesspoken(self, html: str):
        return self.getinfos(['שפה מועדפת', 'langue', 'laulukieli', 'язык'], html, 'language')

    def findlanguages(self, html: str):
        return self.getinfos(['idioma'], html, 'language')

    def findinfluences(self, html: str):
        return self.getinfos(['influences', 'influências', 'influence de', 'invloeden', 'influenciadopor',
                              'influenced by'], html, 'person')

    def findpseudonyms(self, html: str):
        return self.getinfos(['псевдонім', r'pseudon[iy]e?m(?:\(er\))?', 'psudônimos?', 'pseŭdonomo'], html)

    def findinstruments(self, html: str):
        return self.getinfos(['instrumento?', 'strumento', 'instrumentarium', 'nástroj'],
                             html, 'instrument')

    def findvoice(self, html: str):
        return self.getinfo(['hlasový obor'], html, 'voice')

    def findlabels(self, html: str):
        return self.getinfos(['label', 'etichetta', 'discográfica', 'levy-yhtiö' 'լեյբլեր',
                              'gravadora', 'pla[dt]eselska[bp]', 'selo', 'skivbolag',
                              'wytwórnia płytowa', 'casă de discuri', 'лейблы', 'vydavatel',
                              'レーベル'], html, 'label')

    def findstudents(self, html: str):
        return self.getinfos(['leerlingen', 'tuntud_õpilased', 'oppilaat', 'атақты шәкірттері'],
                             html, 'person')

    def findformationlocation(self, html: str):
        return self.getinfo(['orig[ie]ne?', 'opphav', 'orixe', 'oprindelse', 'herkunft', 'krajina pôvodu'],
                            html, 'city')

    def findparts(self, html: str):
        return self.getinfos(['members', 'miembros', 'jäsenet', 'անդամներ', 'integrantes', 'medlemm[ae]r',
                              'membros', r'gründer\d*a?', r'besetzung\d*a?', r'ehemalige\d*a?',
                              'membres(?: actuels)?', 'członkowie', 'membri', 'состав', r'členovia[\w\s]*',
                              'メンバー'], html, 'musician')

    def findpremiere(self, html: str):
        return self.getinfo(['estrena'], html)

    def findmoviedirectors(self, html: str):
        return self.getinfos(['direcció'], html, 'filmmaker')

    def findartdirectors(self, html: str):
        return self.getinfos(['direcció artística'], html, 'filmmaker')

    def findscreenwriters(self, html: str):
        return self.getinfos(['guió'], html, 'filmmaker')

    def finddirectorsphotography(self, html: str):
        return self.getinfos(['fotografia'], html, 'filmmaker')

    def findcast(self, html: str):
        return self.getinfos(['repartiment'], html, 'actor')

    def findprodcoms(self, html: str):
        return self.getinfos(['productora'], html, 'filmcompany')

    def finddistcoms(self, html: str):
        return self.getinfos(['distribució'], html, 'filmcompany')

    def findinception(self, html: str):
        return self.getinfo(['gründung', 'rok założenia'], html)

    def finddissolution(self, html: str):
        return self.getinfo(['auflösung', 'rok rozwiązania'], html)

    def findfloruitstart(self, html: str):
        return self.getinfo(['anno inizio attività'], html)

    def findfloruitend(self, html: str):
        return self.getinfo(['anno fine attività'], html)

    def findfloruit(self, html: str):
        return self.getinfo([
            'aktiva_år', 'år aktiv', 'aktywność', 'ani activi', 'годы', 'roky pôsobenia',
            '活動期間', 'years_active', "période d'activité", 'aktivní roky',
        ], html)


class UrlAnalyzer(Analyzer):
    def __init__(self, id, data=None, item=None, bot=None):
        """Initializer."""
        if data is None:
            data = defaultdict(dict)
        super().__init__(id.split('/', 3)[-1], data, item, bot)
        self.urlbase = id
        self.dbproperty = None
        self.isurl = True


class BibliotecaNacionalAnalyzer(UrlAnalyzer):
    def setup(self):
        self.dbid = None
        self.dbname = 'Biblioteca Nacional Mariano Moreno'
        self.hrtre = '<table[^<>]*class="tabla-datos"[^<>]*>(.*?)</table>'
        self.language = 'es'

    def prepare(self, html: str):
        return html.replace('&nbsp;', ' ')

    def getvalue(self, field, html, dtype=None):
        return self.findbyre('(?s)<strong>{}</strong>.*?<td[^<>]*>(.*?)</td>'
                             .format(field), html, dtype)

    def getvalues(self, field, html, dtype=None) -> List[str]:
        section = self.getvalue(field, html)
        if section:
            return self.findallbyre('>(.*?)<', '>' + section + '<', dtype)
        return []

    def findnames(self, html) -> List[str]:
        section = self.getvalue('Nombre personal', html)
        if section:
            section = self.findbyre(r'(?s)>([^<>]*\w[^<>]*)<', section)
            return [','.join(section.split(',')[:1])]
        return []

    def findworkfields(self, html: str):
        return self.getvalues('Campo de actividad', html, 'subject')

    def findbirthplace(self, html: str):
        return self.findbyre('Nació en (.*?)<', html, 'city')

    def finddeathplace(self, html: str):
        return self.findbyre('Murió en (.*?)<', html, 'city')

    def findoccupations(self, html: str):
        return self.getvalues('Ocupación', html, 'occupation')

    def findgender(self, html: str):
        return self.getvalue('Sexo', html, 'gender')

    def findlanguagesspoken(self, html: str):
        return self.getvalues('Idiomas asociados', html, 'language')


class BrooklynMuseumAnalyzer(UrlAnalyzer):
    def setup(self):
        self.dbid = None
        self.dbname = 'Brooklyn Museum'
        self.hrtre = '<div class="container artist oc-search-results">(.*?)<div class="container '
        self.language = 'en'

    def findnames(self, html) -> List[str]:
        return self.findallbyre(r'<strong>(.*?)</strong>', html)

    def findlongtext(self, html: str):
        return self.findbyre(r'(?s)<div class="container artist oc-search-results">(.*?)<div class="container ', html)

    def findnationality(self, html: str):
        return self.findbyre(r'(?s)</strong>[^<>]*&ndash;([^<>]*?),', html, 'country')

    def findbirthdate(self, html: str):
        return self.findbyre(r'(?s)</strong>[^<>]*,([^<>,]*)-', html)

    def finddeathdate(self, html: str):
        return self.findbyre(r'(?s)</strong>[^<>]*-([^<>,\-]*)</div>', html)

    def findincollections(self, html: str):
        return ['Q632682']


class OnstageAnalyzer(UrlAnalyzer):
    def setup(self):
        self.dbid = 'Q66361136'
        self.dbname = 'OnStage'
        self.hrtre = '(<h1.*?)<div class="footer">'
        self.language = 'nl'
        self.escapehtml = True

    def findnames(self, html) -> List[str]:
        return [self.findbyre(r'<h1[^<>]*>(?:<[^<>]*>|\s)*(.*?)</', html)]

    def findbirthdate(self, html: str):
        return self.findbyre(r'\(([^<>\(\)]*)-[^<>\(\)]*\)\s*</h1>', html)

    def finddeathdate(self, html: str):
        return self.findbyre(r'\((?!\s*fl\.)[^<>\(\)]-([^<>\(\)]*)\)\s*</h1>', html)

    def findmixedrefs(self, html: str):
        return self.finddefaultmixedrefs(html)

    def findfloruit(self, html: str):
        return self.findbyre(r'\(fl\.([^<>\(\)]*)\)\s*</h1>', html)


class IasAnalyzer(UrlAnalyzer):
    def setup(self):
        self.dbid = None
        self.dbname = 'IAS'
        self.hrtre = '<div  class="scholar__header-bottom">(.*?)<div class="scholar__'
        self.language = 'en'

    def getvalue(self, field, html, dtype=None, alt=None):
        if alt is None:
            alt = []
        prevalue = self.findbyre(
            r'(?s)<h3[^<>]*>\s*{}\s*</h3>(.*?)(?:<h3|<div class="scholar__)'
            .format(field), html)
        if prevalue:
            return self.findbyre(r'(?s)^(?:<[^<>]*>|\s)*(.*?)(?:<[^<>]*>|\s)*$', prevalue, dtype, alt=alt)
        return None

    def getvalues(self, field, html, dtype=None, alt=None) -> List[str]:
        if alt is None:
            alt = []
        section = self.findbyre(
            r'(?s)<h3[^<>]*>\s*{}\s*</h3>(.*?)(?:<h3|<div class="scholar__)'
            .format(field), html)
        if section:
            return self.findallbyre(r'(?s)>([^<>]*)<', section, dtype, alt=alt) or []
        return []

    def getsubvalues(self, field, secondfield, html, dtype=None, alt=None):
        if alt is None:
            alt = []
        section = self.findbyre(
            r'(?s)<h3[^<>]*>\s*{}\s*</h3>(.*?)(?:<h3|<div class="scholar__)'
            .format(field), html)
        if section:
            return self.findallbyre(
                r'(?s)<div class="[^"]*{}[^"]*"><div class="field__item">(.*?)</div>'
                .format(secondfield), section, dtype, alt=alt) or []
        return []

    def findinstanceof(self, html: str):
        return 'Q5'

    def findnames(self, html) -> List[str]:
        return self.findallbyre(r'title" content="(.*?)"', html) \
            + self.findallbyre(r'(?s)<li>([^<>]*)</li>', html)

    def finddescription(self, html: str):
        return self.getvalue('Affiliation', html)

    def findlongtext(self, html: str):
        return self.findbyre(r'(?s)<div\s+class="[^"]*(?:bio|latest-description)*[^"]">(.*?)<div\s+class="scholar__bottom">', html)

    def findschools(self, html: str):
        results = self.getsubvalues('Degrees', 'institution', html)
        return [self.findbyre(r'(.*[^\.\s])', result, 'university') for result in results]

    def finddegrees(self, html: str):
        return self.getsubvalues('Degrees', 'degree-type', html, 'degree')

    def findawards(self, html: str):
        return self.getsubvalues('Honors', 'honor-description', html, 'award')

    def findemployers(self, html: str):
        return self.getvalues('Home Institution', html, 'employer', alt=['university']) +\
            self.getsubvalues('Appointments', 'organization', html, 'employer', alt=['university'])

    def findworkfields(self, html: str):
        return self.getvalues('Field of Study', html, 'subject')

    def findwebsite(self, html: str):
        return self.findbyre('<a [^<>]*href="([^"]*)"[^<>]*>Individual Website', html)


class KunstaspekteAnalyzer(UrlAnalyzer):
    def setup(self):
        self.dbid = None
        self.dbname = 'KunstAspekte'
        self.hrtre = '<div class="artist-profile">(.*?)<div class="artist-data">'
        if not self.id.startswith('person/'):
            self.urlbase = None
        self.language = 'de'

    def description(self, html: str):
        return (self.findbyre(r'(?s)"description": "(.*?)"', html)
                or self.findbyre(r'(?s)<h3>short biography</h3>(.*?)</div>',
                                 html))

    def findlongtext(self, html: str):
        return self.description(html)

    def findnames(self, html) -> List[str]:
        return [self.findbyre(r'(?s)"name": "(.*?)"', html)]

    def finddescriptions(self, html: str):
        section = self.description(html)
        if section:
            return section.split('\n')
        return None

    def findbirthdate(self, html: str):
        section = self.description(html)
        if section:
            return self.findbyre(r'\*\s*(\d+)', section)
        return None

    def findbirthplace(self, html: str):
        section = self.description(html)
        if section:
            return self.findbyre(r'\*\s*\d+(?: in)? ([^-!]*)', section.replace('\n', '!'), 'city')
        return None

    def findincollections(self, html: str):
        section = self.findbyre(r'(?s)<h3>collection/s</h3>(.*?)</div>', html)
        if section:
            return self.findallbyre(r'">(.*?)<', section, 'museum')
        return None


class FotomuseumAnalyzer(UrlAnalyzer):
    def setup(self):
        self.dbid = 'Q99863977'
        self.dbname = 'Directory of Belgian Photographers'
        self.hrtre = '<h2>Details</h2>(.*?)<h2>'
        self.language = 'en'

    def getvalue(self, field, html, dtype=None):
        return self.findbyre(r'(?s)<h3>{}</h3>\s*<div>(.*?)</div>'
                             .format(field), html, dtype)

    def instanceof(self, html: str):
        return self.findbyre('Category', html, 'instanceof')

    def findnames(self, html) -> List[str]:
        result = self.findallbyre('<title>(.*?)[-<]', html)
        result.append(self.getvalue('Authorized form of name', html))
        result.append(self.getvalue(
            r'Standardized form\(s\) of name according to other rules', html))
        section = self.getvalue('Activity', html)
        if section:
            result += self.findallbyre('<br/>(.*?),', section)
        section = self.getvalue('Alternative name or descriptor', html)
        if section:
            result += self.findallbyre('>(.*?)<', section)
        return result

    def findlongtext(self, html: str):
        return self.getvalue('Activity', html)

    def findgender(self, html: str):
        return self.findbyre(r'Person \((.*?)\)', html, 'gender')

    def findbirthdate(self, html: str):
        section = self.getvalue('Life dates', html)
        if section:
            return self.findbyre(r'(\d{4}) - ', section)
        return None

    def finddeathdate(self, html: str):
        section = self.getvalue('Life dates', html)
        if section:
            return self.findbyre(r'(\d{4})\s*$', section)
        return None

    def findbirthplace(self, html: str):
        section = self.getvalue('Life dates', html)
        if section:
            return self.findbyre(r'(.*?), \d{4} - ', section, 'city')
        return None

    def finddeathplace(self, html: str):
        section = self.getvalue('Life dates', html)
        if section:
            return self.findbyre(r', \d{4} - (.*), \d{4}', section, 'city')
        return None

    def findworkplaces(self, html: str):
        section = self.getvalue('Locations', html)
        if section:
            return self.findallbyre('([A-Z][^<>]*)', section, 'city')
        return None

    def findgenres(self, html: str):
        section = self.getvalue('Genres / subject matter', html)
        if section:
            return self.findallbyre('[^<>]+', section, 'art-genre', alt=['genre'])
        return None

    def findmixedrefs(self, html: str):
        return self.finddefaultmixedrefs(html, includesocial=False)

    def findoccupations(self, html: str):
        return ['Q33231']

    def findmemberships(self, html: str):
        section = self.getvalue('Affiliated entity', html)
        if section:
            return self.findallbyre('<a [^<>]*>(.*?)<', section, 'organization')
        return None


class NationalTrustAnalyzer(UrlAnalyzer):
    def setup(self):
        self.dbid = None
        self.dbname = 'National Trust Collections'
        self.hrtre = '<div class="sortable-header">(.*?)<h3'
        self.language = 'en'
        self.escapehtml = True

    def finddatesection(self, html: str):
        return self.findbyre(r'<b>[^<>]*\(([^<>]*\))', html)

    def findnames(self, html) -> List[str]:
        return self.findallbyre(r'<b>(.*?)[<\(]', html)

    def finddescriptions(self, html: str):
        return self.findallbyre(r'<b>([^<>]*)</b>', html)

    def findbirthplace(self, html: str):
        section = self.finddatesection(html)
        if section:
            return self.findbyre(r'^([\w\s]*?) [\-\d]', section, 'city')
        return None

    def findbirthdate(self, html: str):
        section = self.finddatesection(html)
        if section:
            return self.findbyre(r' (\d*) -', section)
        return None

    def finddeathplace(self, html: str):
        section = self.finddatesection(html)
        if section:
            return self.findbyre(r' - ([\w\s]*?)(?: \d|\))', section, 'city')
        return None

    def finddeathdate(self, html: str):
        section = self.finddatesection(html)
        if section:
            return self.findbyre(r' (\d*)\s*\)', section)
        return None

    def findincollections(self, html: str):
        return self.findallbyre(r'(?s)<label for="[^<>"]+">([^<>]*)</label>\s*<span class="item-bubble">[1-9]', html,
                                'museum')


class BenezitUrlAnalyzer(UrlAnalyzer):
    def setup(self):
        self.dbid = 'Q2929945'
        self.dbname = 'Benezit (url)'
        self.hrtre = '<h3>Extract</h3>(.*?)</div>'
        self.language = 'en'

    def indinstanceof(self, html: str):
        return 'Q5'

    def finddescription(self, html: str):
        return self.findbyre(r'"pf:contentName"\s*:\s*"(.*?)"', html)

    def findnames(self, html) -> List[str]:
        return [self.findbyre(r'"pf:contentName"\s*:\s*"(.*?)[\("]', html)]

    def findlongtext(self, html: str):
        return self.findbyre(r'<abstract>(.*?)</abstract>', html)

    def findisntanceof(self, html: str):
        return 'Q5'

    def findbirthdate(self, html: str):
        return self.findbyre(r'(?s)[^\w][bB]orn\s*((\w+\s*){,2}\d{4})[,\.\)]', html)

    def finddeathdate(self, html: str):
        return self.findbyre(r'(?s)[^\w][dD]ied\s*((\w+\s*){,2}\d{4})[,\.\)]', html)

    def findbirthplace(self, html: str):
        return self.findbyre(r'[bB]orn(?: [^<>,\.;]*,)? in ([^<>,\.;]*)', html, 'city')

    def finddeathplace(self, html: str):
        return self.findbyre(r'[dD]ied(?: [^<>,\.]*,)? in ([^<>,\.;]*)', html, 'city')

    def findoccupations(self, html: str):
        result = []
        section = self.findbyre(r'"pf:contentName" : "[^"]+-(.*?)"', html)
        if section:
            result += self.findallbyre(r'([^,]+)', section, 'occupation')
        section = self.findbyre(r'"pf:contentName" : "[^"]*\)(.*?)"', html)
        if section:
            result += self.findallbyre(r'([\s\w]+)', section, 'occupation')
        return result

    def findlastname(self, html: str):
        return self.findbyre(r'"pf:contentName" : "([^"]+?),', html, 'lastname')

    def findfirstname(self, html: str):
        return self.findbyre(r'"pf:contentName" : "[^",]+,\s*([\w\-]+)', html, 'firstname')

    def findnationality(self, html: str):
        return self.findbyre(r'<abstract><p>([^<>]*?),', html, 'country')

    def findgender(self, html: str):
        return self.findbyre(r'<abstract><p>[^<>]*,([^<>,]*)\.</p>', html, 'gender')


class UnivieAnalyzer(UrlAnalyzer):
    def setup(self):
        self.dbid = 'Q85217215'
        self.dbname = 'Database of Modern Exhibitions'
        self.hrtre = '<div class="lefthalf">(.*?)<div class="maphalf">'
        self.language = 'en'

    def getvalue(self, field, html, dtype=None):
        return self.findbyre(r'<meta property=(?:\w+:)?{}" content="(.*?)"'
                             .format(field), html, dtype)

    def findinstanceof(self, html: str):
        return self.findbyre(r'"@type":"(.*?)"', html, 'instanceof')

    def finddescriptions(self, html: str):
        return [
            self.getvalue('description', html),
            self.findbyre(r'"description":"(.*?)"', html)
        ]

    def findnames(self, html) -> List[str]:
        return [self.getvalue('title', html),
                self.findbyre(r'"name":"(.*?)"', html)]

    def findfirstname(self, html: str):
        return self.getvalue('first_name', html, 'firstname')

    def findlastname(self, html: str):
        return self.getvalue('last_name', html, 'lastname')

    def findgender(self, html: str):
        return self.getvalue('gender', html, 'gender')

    def findbirthdate(self, html: str):
        return self.findbyre(r'"birthDate":"(.*?)"', html)

    def findbirthplace(self, html: str):
        section = self.findbyre(r'"birthPlace":{(.*?)}', html)
        if section:
            return self.findbyre(r'"name":"(.*?)"', section, 'city')
        return None

    def finddeathdate(self, html: str):
        return self.findbyre(r'"deathDate":"(.*?)"', html)

    def finddeathplace(self, html: str):
        section = self.findbyre(r'"deathPlace":{(.*?)}', html)
        if section:
            return self.findbyre(r'"name":"(.*?)"', section, 'city')
        return None

    def findnationalities(self, html: str):
        section = self.findbyre(r'(?s)<div class="artist-information-label">Nationality:</div>'
                                r'\s*<div class="artist-information-text">(.*?)</div>', html)
        if section:
            return self.findallbyre(r'([\w\s\-]+)', section, 'country')
        return None

    def findworkplaces(self, html: str):
        section = self.findbyre(
            '(?s)<div class="artist-information-label">Places of Activity:</div>'
            r'\s*<div class="artist-information-text">(.*?)</div>', html)
        if section:
            return self.findallbyre(r'>([^<>]*)</a>', section, 'city')
        return None

    def findmixedrefs(self, html: str):
        return [('P245', self.findbyre(r'/ulan/(\d+)', html))] + self.finddefaultmixedrefs(html, includesocial=False)


class WeberAnalyzer(UrlAnalyzer):
    def setup(self):
        self.dbid = None
        self.dbname = 'Weber Gesamtausgabe'
        self.hrtre = '<h2>Basisdaten</h2>(.*?)</ol>'
        self.language = 'de'

    def findinstanceof(self, html: str):
        return self.findbyre(r'"dc:subject" content="(.*?)"', html, 'instanceof')

    def findnames(self, html) -> List[str]:
        return [self.findbyre(r'title" content="(.*?)(?: – |")', html)]

    def finddescriptions(self, html: str):
        return [
            self.findbyre(r'description" content="(.*?)"', html),
            self.findbyre(r'description" content="[^"]+?\.(.*?)"', html)
        ]

    def findbirthdate(self, html: str):
        return self.findbyre(r'(?s)<i class="fa fa-asterisk\s*"></i>\s*</div>\s*<div[^<>]*>\s*<span>(.*?)<', html)

    def findbirthplace(self, html: str):
        return self.findbyre(r'(?s)<i class="fa fa-asterisk\s*"></i>\s*</div>\s*<div[^<>]*>'
                             r'\s*<span>[^<>]*</span>\s*<span>\s*(?:in )([^<>]*)<',
                             html, 'city')

    def findxsdeathdate(self, html: str):
        return self.findbyre(r'(?s)<strong>†</strong>\s*</div>\s*<div[^<>]*>\s*<span>(.*?)<', html)

    def finddeathplace(self, html: str):
        return self.findbyre(
            r'(?s)<strong>†</strong>\s*</div>\s*<div[^<>]*>\s*<span>[^<>]*</span>\s*<span>\s*(?:in )([^<>]*)<',
            html, 'city')

    def findoccupations(self, html: str):
        section = self.findbyre(r'(?s)<li class="media occupations">(.*?)</li>', html)
        if section:
            subsection = self.findbyre(r'(?s)<div class="media-body">(.*?)<', section)
            if subsection:
                return self.findallbyre(r'([^,]*)', subsection, 'occupation')
        return None

    def findresidences(self, html: str):
        section = self.findbyre(r'(?s)<li class="media residences">(.*?)</li>', html)
        if section:
            subsection = self.findbyre(r'(?s)<div class="media-body">(.*?)<', section)
            if subsection:
                return self.findallbyre(r'([^,]*)', subsection, 'city')
        return None


class BacklinkAnalyzer(Analyzer):
    def setup(self):
        self.iswiki = True
        self.dbname = 'Wikidata Backlinks'
        self.dbproperty = None
        self.dbid = 'Q2013'
        self.urlbase = None
        self.sparqlquery = f'SELECT ?a ?b WHERE {{ ?a ?b wd:{self.id} }}'
        self.skipfirst = True
        self.hrtre = '()'
        self.language = 'en'

    def getrelations(self, relation, html):
        return [x.upper()
                for x in self.findallbyre(
                    r'statement/([qQ]\d+)[^{{}}]+statement/{}[^\d]'
                    .format(relation), html)]

    def findlongtext(self, html: str):
        matches = re.findall(r'statement/([qQ]\d+)[^{}]+statement/([pP]\d+)', html)
        return '\n'.join(f'{self.bot.label(m[1])} of: {self.bot.label(m[0])}' for m in matches)

    def findspouses(self, html: str):
        return self.getrelations('P26', html)

    def findpartners(self, html: str):
        return self.getrelations('P451', html)

    def findpositions(self, html: str):
        return self.getrelations('P1308', html)

    def findpartofs(self, html: str):
        return self.getrelations('P527', html)

    def findparts(self, html: str):
        return self.getrelations('P361', html)

    def findstudents(self, html: str):
        return self.getrelations('P1066', html)

    def findteachers(self, html: str):
        return self.getrelations('P802', html)

    def finddocstudents(self, html: str):
        with open('result.html', 'w') as f:
            f.write(html)
        return self.getrelations('P184', html)

    def findadvisors(self, html: str):
        return self.getrelations('P185', html)

    def findchildren(self, html: str):
        return self.getrelations('P2[25]', html)

    def findsiblings(self, html: str):
        return self.getrelations('P3373', html)

    def findkins(self, html: str):
        return self.getrelations('P1038', html)

    def findparticipantins(self, html: str):
        return self.getrelations('P(?:710|1923)', html)

    def findsources(self, html: str):
        return self.getrelations('P921', html)

    def findawards(self, html: str):
        return self.getrelations('P1346', html)

    def findmixedrefs(self, html: str):
        return [('P1889', result) for result in self.getrelations('P1889', html)]


def main(*args: Tuple[str, ...]) -> None:
    """
    Process command line arguments and invoke bot.

    If args is an empty list, sys.argv is used.

    :param args: command line arguments
    """
    item = None
    options = {}
    unknown_parameters = []
    local_args = pywikibot.handle_args(args)
    for arg in local_args:
        if arg.startswith('Q'):
            item = arg
        elif arg.startswith('P') or arg in ('Data', 'Wiki'):
            options['restrict'] = arg
        elif arg in ('-always', '-showonly'):
            options[arg[1:]] = True
        else:
            unknown_parameters.append(arg)

    if suggest_help(unknown_parameters=unknown_parameters,
                    additional_text='No item page specified'
                    if item is None else ''):
        return

    repo = pywikibot.Site().data_repository()
    try:
        item = pywikibot.ItemPage(repo, item)
    except InvalidTitleError as e:
        pywikibot.error(e)
    else:
        bot = DataExtendBot(site=repo, generator=[item], **options)
        bot.run()


if __name__ == '__main__':
    main()
