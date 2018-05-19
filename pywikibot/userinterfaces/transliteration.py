# -*- coding: utf-8 -*-
"""Module to transliterate text."""
#
# (C) Pywikibot team, 2006-2018
#
# Distributed under the terms of the MIT license.
#
from __future__ import absolute_import, unicode_literals


class transliterator(object):

    """Class to transliterating text."""

    def __init__(self, encoding):
        """
        Initialize the transliteration mapping.

        @param encoding: the encoding available. Any transliterated character
            which can't be mapped, will be removed from the mapping.
        @type encoding: str
        """
        self.trans = {}
        for char in 'ÀÁÂẦẤẪẨẬÃĀĂẰẮẴẶẲȦǠẠḀȂĄǍẢ':
            self.trans[char] = 'A'
        for char in 'ȀǞ':
            self.trans[char] = 'Ä'
        self.trans['Ǻ'] = 'Å'
        self.trans['Ä'] = 'Ae'
        self.trans['Å'] = 'Aa'
        for char in 'àáâầấẫẩậãāăằắẵặẳȧǡạḁȃąǎảẚ':
            self.trans[char] = 'a'
        for char in 'ȁǟ':
            self.trans[char] = 'ä'
        self.trans['ǻ'] = 'å'
        self.trans['ä'] = 'ae'
        self.trans['å'] = 'aa'
        for char in 'ḂḄḆƁƂ':
            self.trans[char] = 'B'
        for char in 'ḃḅḇƀɓƃ':
            self.trans[char] = 'b'
        for char in 'ĆĈĊÇČƇ':
            self.trans[char] = 'C'
        for char in 'ćĉċçčƈȼ':
            self.trans[char] = 'c'
        self.trans['Ḉ'] = 'Ç'
        self.trans['ḉ'] = 'ç'
        self.trans['Ð'] = 'Dh'
        self.trans['ð'] = 'dh'
        for char in 'ĎḊḌḎḐḒĐƉƊƋ':
            self.trans[char] = 'D'
        for char in 'ďḋḍḏḑḓđɖɗƌ':
            self.trans[char] = 'd'
        for char in 'ÈȄÉÊḚËĒḔḖĔĖẸE̩ȆȨḜĘĚẼḘẺ':
            self.trans[char] = 'E'
        for char in 'ỀẾỄỆỂ':
            self.trans[char] = 'Ê'
        for char in 'èȅéêḛëēḕḗĕėẹe̩ȇȩḝęěẽḙẻ':
            self.trans[char] = 'e'
        for char in 'ềếễệể':
            self.trans[char] = 'ê'
        for char in 'ḞƑ':
            self.trans[char] = 'F'
        for char in 'ḟƒ':
            self.trans[char] = 'f'
        for char in 'ǴḠĞĠĢǦǤƓ':
            self.trans[char] = 'G'
        for char in 'ǵḡğġģǧǥɠ':
            self.trans[char] = 'g'
        self.trans['Ĝ'] = 'Gx'
        self.trans['ĝ'] = 'gx'
        for char in 'ḢḤḦȞḨḪH̱ĦǶ':
            self.trans[char] = 'H'
        for char in 'ḣḥḧȟḩḫ̱ẖħƕ':
            self.trans[char] = 'h'
        for char in 'IÌȈÍÎĨḬÏḮĪĬȊĮǏİỊỈƗ':
            self.trans[char] = 'I'
        for char in 'ıìȉíîĩḭïḯīĭȋįǐiịỉɨ':
            self.trans[char] = 'i'
        for char in 'ĴJ':
            self.trans[char] = 'J'
        for char in 'ɟĵ̌ǰ':
            self.trans[char] = 'j'
        for char in 'ḰǨĶḲḴƘ':
            self.trans[char] = 'K'
        for char in 'ḱǩķḳḵƙ':
            self.trans[char] = 'k'
        for char in 'ĹĻĽḶḸḺḼȽŁ':
            self.trans[char] = 'L'
        for char in 'ĺļľḷḹḻḽƚłɫ':
            self.trans[char] = 'l'
        for char in 'ḾṀṂ':
            self.trans[char] = 'M'
        for char in 'ḿṁṃɱ':
            self.trans[char] = 'm'
        for char in 'ǸŃÑŅŇṄṆṈṊŊƝɲȠ':
            self.trans[char] = 'N'
        for char in 'ǹńñņňṅṇṉṋŋɲƞ':
            self.trans[char] = 'n'
        for char in 'ÒÓÔÕṌṎȬÖŌṐṒŎǑȮȰỌǪǬƠỜỚỠỢỞỎƟØǾ':
            self.trans[char] = 'O'
        for char in 'òóôõṍṏȭöōṑṓŏǒȯȱọǫǭơờớỡợởỏɵøǿ':
            self.trans[char] = 'o'
        for char in 'ȌŐȪ':
            self.trans[char] = 'Ö'
        for char in 'ȍőȫ':
            self.trans[char] = 'ö'
        for char in 'ỒỐỖỘỔȎ':
            self.trans[char] = 'Ô'
        for char in 'ồốỗộổȏ':
            self.trans[char] = 'ô'
        for char in 'ṔṖƤ':
            self.trans[char] = 'P'
        for char in 'ṕṗƥ':
            self.trans[char] = 'p'
        self.trans['ᵽ'] = 'q'
        for char in 'ȐŔŖŘȒṘṚṜṞ':
            self.trans[char] = 'R'
        for char in 'ȑŕŗřȓṙṛṝṟɽ':
            self.trans[char] = 'r'
        for char in 'ŚṤŞȘŠṦṠṢṨ':
            self.trans[char] = 'S'
        for char in 'śṥşșšṧṡṣṩȿ':
            self.trans[char] = 's'
        self.trans['Ŝ'] = 'Sx'
        self.trans['ŝ'] = 'sx'
        for char in 'ŢȚŤṪṬṮṰŦƬƮ':
            self.trans[char] = 'T'
        for char in 'ţțťṫṭṯṱŧȾƭʈ':
            self.trans[char] = 't'
        for char in 'ÙÚŨṸṴÜṲŪṺŬỤŮŲǓṶỦƯỮỰỬ':
            self.trans[char] = 'U'
        for char in 'ùúũṹṵüṳūṻŭụůųǔṷủưữựửʉ':
            self.trans[char] = 'u'
        for char in 'ȔŰǛǗǕǙ':
            self.trans[char] = 'Ü'
        for char in 'ȕűǜǘǖǚ':
            self.trans[char] = 'ü'
        self.trans['Û'] = 'Ux'
        self.trans['û'] = 'ux'
        self.trans['Ȗ'] = 'Û'
        self.trans['ȗ'] = 'û'
        self.trans['Ừ'] = 'Ù'
        self.trans['ừ'] = 'ù'
        self.trans['Ứ'] = 'Ú'
        self.trans['ứ'] = 'ú'
        for char in 'ṼṾ':
            self.trans[char] = 'V'
        for char in 'ṽṿ':
            self.trans[char] = 'v'
        for char in 'ẀẂŴẄẆẈ':
            self.trans[char] = 'W'
        for char in 'ẁẃŵẅẇẉ':
            self.trans[char] = 'w'
        for char in 'ẊẌ':
            self.trans[char] = 'X'
        for char in 'ẋẍ':
            self.trans[char] = 'x'
        for char in 'ỲÝŶŸỸȲẎỴỶƳ':
            self.trans[char] = 'Y'
        for char in 'ỳýŷÿỹȳẏỵỷƴ':
            self.trans[char] = 'y'
        for char in 'ŹẐŻẒŽẔƵȤ':
            self.trans[char] = 'Z'
        for char in 'źẑżẓžẕƶȥ':
            self.trans[char] = 'z'
        self.trans['ɀ'] = 'zv'

        # Latin: extended Latin alphabet
        self.trans['ɑ'] = 'a'
        for char in 'ÆǼǢ':
            self.trans[char] = 'AE'
        for char in 'æǽǣ':
            self.trans[char] = 'ae'
        self.trans['Ð'] = 'Dh'
        self.trans['ð'] = 'dh'
        for char in 'ƎƏƐ':
            self.trans[char] = 'E'
        for char in 'ǝəɛ':
            self.trans[char] = 'e'
        for char in 'ƔƢ':
            self.trans[char] = 'G'
        for char in 'ᵷɣƣᵹ':
            self.trans[char] = 'g'
        self.trans['Ƅ'] = 'H'
        self.trans['ƅ'] = 'h'
        self.trans['Ƕ'] = 'Wh'
        self.trans['ƕ'] = 'wh'
        self.trans['Ɩ'] = 'I'
        self.trans['ɩ'] = 'i'
        self.trans['Ŋ'] = 'Ng'
        self.trans['ŋ'] = 'ng'
        self.trans['Œ'] = 'OE'
        self.trans['œ'] = 'oe'
        self.trans['Ɔ'] = 'O'
        self.trans['ɔ'] = 'o'
        self.trans['Ȣ'] = 'Ou'
        self.trans['ȣ'] = 'ou'
        self.trans['Ƽ'] = 'Q'
        for char in 'ĸƽ':
            self.trans[char] = 'q'
        self.trans['ȹ'] = 'qp'
        self.trans[''] = 'r'
        self.trans['ſ'] = 's'
        self.trans['ß'] = 'ss'
        self.trans['Ʃ'] = 'Sh'
        for char in 'ʃᶋ':
            self.trans[char] = 'sh'
        self.trans['Ʉ'] = 'U'
        self.trans['ʉ'] = 'u'
        self.trans['Ʌ'] = 'V'
        self.trans['ʌ'] = 'v'
        for char in 'ƜǷ':
            self.trans[char] = 'W'
        for char in 'ɯƿ':
            self.trans[char] = 'w'
        self.trans['Ȝ'] = 'Y'
        self.trans['ȝ'] = 'y'
        self.trans['Ĳ'] = 'IJ'
        self.trans['ĳ'] = 'ij'
        self.trans['Ƨ'] = 'Z'
        for char in 'ʮƨ':
            self.trans[char] = 'z'
        self.trans['Ʒ'] = 'Zh'
        self.trans['ʒ'] = 'zh'
        self.trans['Ǯ'] = 'Dzh'
        self.trans['ǯ'] = 'dzh'
        for char in 'ƸƹʔˀɁɂ':
            self.trans[char] = u"'"
        self.trans['Þ'] = 'Th'
        self.trans['þ'] = 'th'
        for char in 'Cʗǃ':
            self.trans[char] = '!'

        # Punctuation and typography
        for char in '«»“”„¨':
            self.trans[char] = u'"'
        for char in '‘’′':
            self.trans[char] = u"'"
        self.trans['•'] = '*'
        self.trans['@'] = '(at)'
        self.trans['¤'] = '$'
        self.trans['¢'] = 'c'
        self.trans['€'] = 'E'
        self.trans['£'] = 'L'
        self.trans['¥'] = 'yen'
        self.trans['†'] = '+'
        self.trans['‡'] = '++'
        self.trans['°'] = ':'
        self.trans['¡'] = '!'
        self.trans['¿'] = '?'
        self.trans['‰'] = 'o/oo'
        self.trans['‱'] = 'o/ooo'
        for char in '¶§':
            self.trans[char] = '>'
        self.trans['…'] = '...'
        for char in '‒–—―':
            self.trans[char] = '-'
        self.trans['·'] = ' '
        self.trans['¦'] = '|'
        self.trans['⁂'] = '***'
        self.trans['◊'] = '<>'
        self.trans['‽'] = '?!'
        self.trans['؟'] = ';-)'
        self.trans['¹'] = '1'
        self.trans['²'] = '2'
        self.trans['³'] = '3'

        # Cyrillic
        self.trans.update({'А': 'A', 'а': 'a', 'Б': 'B', 'б': 'b',
                           'В': 'V', 'в': 'v', 'Г': 'G', 'г': 'g',
                           'Д': 'D', 'д': 'd', 'Е': 'E', 'е': 'e',
                           'Ж': 'Zh', 'ж': 'zh', 'З': 'Z', 'з': 'z',
                           'И': 'I', 'и': 'i', 'Й': 'J', 'й': 'j',
                           'К': 'K', 'к': 'k', 'Л': 'L', 'л': 'l',
                           'М': 'M', 'м': 'm', 'Н': 'N', 'н': 'n',
                           'О': 'O', 'о': 'o', 'П': 'P', 'п': 'p',
                           'Р': 'R', 'р': 'r', 'С': 'S', 'с': 's',
                           'Т': 'T', 'т': 't', 'У': 'U', 'у': 'u',
                           'Ф': 'F', 'ф': 'f', 'х': 'kh', 'Ц': 'C',
                           'ц': 'c', 'Ч': 'Ch', 'ч': 'ch', 'Ш': 'Sh',
                           'ш': 'sh', 'Щ': 'Shch', 'щ': 'shch', 'Ь': "'",
                           'ь': "'", 'Ъ': '"', 'ъ': '"', 'Ю': 'Yu',
                           'ю': 'yu', 'Я': 'Ya', 'я': 'ya', 'Х': 'Kh',
                           'Χ': 'Kh'})

        # Additional Cyrillic letters, most occuring in only a few languages
        self.trans.update({
            'Ы': 'Y', 'ы': 'y', 'Ё': 'Ë', 'ё': 'ë',
            'Э': 'È', 'Ѐ': 'È', 'э': 'è', 'ѐ': 'è',
            'І': 'I', 'і': 'i', 'Ї': 'Ji', 'ї': 'ji',
            'Є': 'Je', 'є': 'je', 'Ґ': 'G', 'Ҝ': 'G',
            'ґ': 'g', 'ҝ': 'g', 'Ђ': 'Dj', 'ђ': 'dj',
            'Љ': 'Lj', 'љ': 'lj',
            'Њ': 'Nj', 'њ': 'nj', 'Ћ': 'Cj', 'ћ': 'cj',
            'Җ': 'Zhj', 'Ѓ': 'Gj', 'ѓ': 'gj',
            'Ќ': 'Kj', 'ќ': 'kj', 'Ӣ': 'Ii', 'ӣ': 'ii',
            'Ҳ': 'H', 'ҳ': 'h',
            'Ҷ': 'Dz', 'ҷ': 'dz', 'Ө': 'Ô', 'Ӫ': 'Ô',
            'ө': 'ô', 'ӫ': 'ô', 'Ү': 'Y', 'ү': 'y', 'Һ': 'H',
            'һ': 'h', 'Ә': 'AE', 'Ӕ': 'AE', 'ә': 'ae',
            'Ӛ': 'Ë', 'Ӭ': 'Ë', 'ӛ': 'ë', 'ӭ': 'ë',
            'җ': 'zhj', 'Ұ': 'U', 'ў': 'ù', 'Ў': 'Ù',
            'ѝ': 'ì', 'Ѝ': 'Ì', 'Ӑ': 'A', 'ă': 'a', 'Ӓ': 'Ä',
            'Ҽ': 'Ts', 'Ҿ': 'Ts', 'ҽ': 'ts', 'ҿ': 'ts',
            'Ҙ': 'Dh', 'ҙ': 'dh', 'Ӏ': '', 'ӏ': '', 'Ӆ': 'L',
            'ӆ': 'l', 'Ӎ': 'M', 'ӎ': 'm', 'Ӧ': 'Ö', 'ӧ': 'ö',
            'Ҩ': 'u', 'ҩ': 'u', 'Ҧ': 'Ph', 'ҧ': 'ph', 'Ҏ': 'R',
            'ҏ': 'r', 'Ҫ': 'Th', 'ҫ': 'th', 'Ҭ': 'T', 'ҭ': 't',
            'Ӯ': 'Û', 'ӯ': 'û', 'Ӹ': 'U', 'ұ': 'u',
            'ӹ': 'u', 'Ҵ': 'Tts', 'ҵ': 'tts', 'Ӵ': 'Ch', 'ӵ': 'ch'})

        for char in 'ЈӤҊ':
            self.trans[char] = 'J'
        for char in 'јӥҋ':
            self.trans[char] = 'j'
        for char in 'ЏӁӜҶ':
            self.trans[char] = 'Dzh'
        for char in 'џӂӝҷ':
            self.trans[char] = 'dzh'
        for char in 'ЅӞӠӋҸ':
            self.trans[char] = 'Dz'
        for char in 'ѕӟӡӌҹ':
            self.trans[char] = 'dz'
        for char in 'ҒӶҔ':
            self.trans[char] = 'G'
        for char in 'ғӷҕ':
            self.trans[char] = 'g'
        for char in 'ҚҞҠӃ':
            self.trans[char] = 'Q'
        for char in 'қҟҡӄ':
            self.trans[char] = 'q'
        for char in 'ҢҤӉӇ':
            self.trans[char] = 'Ng'
        for char in 'ңҥӊӈ':
            self.trans[char] = 'ng'
        for char in 'ӖѢҌ':
            self.trans[char] = 'E'
        for char in 'ӗѣҍ':
            self.trans[char] = 'e'
        for char in 'ӲӰҮ':
            self.trans[char] = 'Ü'
        for char in 'ӳӱү':
            self.trans[char] = 'ü'

        # Archaic Cyrillic letters
        self.trans.update({
            'Ѹ': 'Ou', 'ѹ': 'ou', 'Ѡ': 'O', 'Ѻ': 'O', 'ѡ': 'o',
            'ѻ': 'o', 'Ѿ': 'Ot', 'ѿ': 'ot', 'Ѣ': 'E', 'ѣ': 'e',
            'Ѥ': 'Ei', 'Ѧ': 'Ei', 'ѥ': 'ei', 'ѧ': 'ei', 'Ѫ': 'Ai',
            'ѫ': 'ai', 'Ѯ': 'X', 'ѯ': 'x', 'Ѱ': 'Ps', 'ѱ': 'ps',
            'Ѳ': 'Th', 'ѳ': 'th', 'Ѵ': 'Ü', 'Ѷ': 'Ü', 'ѵ': 'ü'})

        # Hebrew alphabet
        for char in 'אע':
            self.trans[char] = u"'"
        self.trans['ב'] = 'b'
        self.trans['ג'] = 'g'
        self.trans['ד'] = 'd'
        self.trans['ה'] = 'h'
        self.trans['ו'] = 'v'
        self.trans['ז'] = 'z'
        self.trans['ח'] = 'kh'
        self.trans['ט'] = 't'
        self.trans['י'] = 'y'
        for char in 'ךכ':
            self.trans[char] = 'k'
        self.trans['ל'] = 'l'
        for char in 'םמ':
            self.trans[char] = 'm'
        for char in 'ןנ':
            self.trans[char] = 'n'
        self.trans['ס'] = 's'
        for char in 'ףפ':
            self.trans[char] = 'ph'
        for char in 'ץצ':
            self.trans[char] = 'ts'
        self.trans['ק'] = 'q'
        self.trans['ר'] = 'r'
        self.trans['ש'] = 'sh'
        self.trans['ת'] = 'th'

        # Arab alphabet
        for char in 'اﺍﺎ':
            self.trans[char] = 'a'
        for char in 'بﺏﺐﺒﺑ':
            self.trans[char] = 'b'
        for char in 'تﺕﺖﺘﺗ':
            self.trans[char] = 't'
        for char in 'ثﺙﺚﺜﺛ':
            self.trans[char] = 'th'
        for char in 'جﺝﺞﺠﺟ':
            self.trans[char] = 'g'
        for char in 'حﺡﺢﺤﺣ':
            self.trans[char] = 'h'
        for char in 'خﺥﺦﺨﺧ':
            self.trans[char] = 'kh'
        for char in 'دﺩﺪ':
            self.trans[char] = 'd'
        for char in 'ذﺫﺬ':
            self.trans[char] = 'dh'
        for char in 'رﺭﺮ':
            self.trans[char] = 'r'
        for char in 'زﺯﺰ':
            self.trans[char] = 'z'
        for char in 'سﺱﺲﺴﺳ':
            self.trans[char] = 's'
        for char in 'شﺵﺶﺸﺷ':
            self.trans[char] = 'sh'
        for char in 'صﺹﺺﺼﺻ':
            self.trans[char] = 's'
        for char in 'ضﺽﺾﻀﺿ':
            self.trans[char] = 'd'
        for char in 'طﻁﻂﻄﻃ':
            self.trans[char] = 't'
        for char in 'ظﻅﻆﻈﻇ':
            self.trans[char] = 'z'
        for char in 'عﻉﻊﻌﻋ':
            self.trans[char] = u"'"
        for char in 'غﻍﻎﻐﻏ':
            self.trans[char] = 'gh'
        for char in 'فﻑﻒﻔﻓ':
            self.trans[char] = 'f'
        for char in 'قﻕﻖﻘﻗ':
            self.trans[char] = 'q'
        for char in 'كﻙﻚﻜﻛک':
            self.trans[char] = 'k'
        for char in 'لﻝﻞﻠﻟ':
            self.trans[char] = 'l'
        for char in 'مﻡﻢﻤﻣ':
            self.trans[char] = 'm'
        for char in 'نﻥﻦﻨﻧ':
            self.trans[char] = 'n'
        for char in 'هﻩﻪﻬﻫ':
            self.trans[char] = 'h'
        for char in 'وﻭﻮ':
            self.trans[char] = 'w'
        for char in 'یيﻱﻲﻴﻳ':
            self.trans[char] = 'y'
        # Arabic - additional letters, modified letters and ligatures
        self.trans['ﺀ'] = "'"
        for char in 'آﺁﺂ':
            self.trans[char] = u"'a"
        for char in 'ةﺓﺔ':
            self.trans[char] = 'th'
        for char in 'ىﻯﻰ':
            self.trans[char] = 'á'
        for char in 'یﯼﯽﯿﯾ':
            self.trans[char] = 'y'
        self.trans['؟'] = '?'
        # Arabic - ligatures
        for char in 'ﻻﻼ':
            self.trans[char] = 'la'
        self.trans['ﷲ'] = 'llah'
        for char in 'إأ':
            self.trans[char] = u"a'"
        self.trans['ؤ'] = "w'"
        self.trans['ئ'] = "y'"
        for char in '◌◌':
            self.trans[char] = ""  # indicates absence of vowels
        # Arabic vowels
        self.trans['◌'] = 'a'
        self.trans['◌'] = 'u'
        self.trans['◌'] = 'i'
        self.trans['◌'] = 'a'
        self.trans['◌'] = 'ay'
        self.trans['◌'] = 'ay'
        self.trans['◌'] = 'u'
        self.trans['◌'] = 'iy'
        # Arab numerals
        for char in '٠۰':
            self.trans[char] = '0'
        for char in '١۱':
            self.trans[char] = '1'
        for char in '٢۲':
            self.trans[char] = '2'
        for char in '٣۳':
            self.trans[char] = '3'
        for char in '٤۴':
            self.trans[char] = '4'
        for char in '٥۵':
            self.trans[char] = '5'
        for char in '٦۶':
            self.trans[char] = '6'
        for char in '٧۷':
            self.trans[char] = '7'
        for char in '٨۸':
            self.trans[char] = '8'
        for char in '٩۹':
            self.trans[char] = '9'
        # Perso-Arabic
        for char in 'پﭙﭙپ':
            self.trans[char] = 'p'
        for char in 'چچچچ':
            self.trans[char] = 'ch'
        for char in 'ژژ':
            self.trans[char] = 'zh'
        for char in 'گﮔﮕﮓ':
            self.trans[char] = 'g'

        # Greek
        self.trans.update({
            'Α': 'A', 'α': 'a', 'Β': 'B', 'β': 'b', 'Γ': 'G',
            'γ': 'g', 'Δ': 'D', 'δ': 'd', 'Ε': 'E', 'ε': 'e',
            'Ζ': 'Z', 'ζ': 'z', 'Η': 'I', 'η': 'i', 'θ': 'th',
            'Θ': 'Th', 'Ι': 'I', 'ι': 'i', 'Κ': 'K', 'κ': 'k',
            'Λ': 'L', 'λ': 'l', 'Μ': 'M', 'μ': 'm', 'Ν': 'N',
            'ν': 'n', 'Ξ': 'X', 'ξ': 'x', 'Ο': 'O', 'ο': 'o',
            'Π': 'P', 'π': 'p', 'Ρ': 'R', 'ρ': 'r', 'Σ': 'S',
            'σ': 's', 'ς': 's', 'Τ': 'T', 'τ': 't', 'Υ': 'Y',
            'υ': 'y', 'Φ': 'F', 'φ': 'f', 'Ψ': 'Ps', 'ψ': 'ps',
            'Ω': 'O', 'ω': 'o', 'ϗ': '&', 'Ϛ': 'St', 'ϛ': 'st',
            'Ϙ': 'Q', 'Ϟ': 'Q', 'ϙ': 'q', 'ϟ': 'q', 'Ϻ': 'S',
            'ϻ': 's', 'Ϡ': 'Ss', 'ϡ': 'ss', 'Ϸ': 'Sh', 'ϸ': 'sh',
            '·': ':', 'Ά': 'Á', 'ά': 'á', 'Έ': 'É', 'Ή': 'É',
            'έ': 'é', 'ή': 'é', 'Ί': 'Í', 'ί': 'í', 'Ϊ': 'Ï',
            'ϊ': 'ï', 'ΐ': 'ï', 'Ό': 'Ó', 'ό': 'ó', 'Ύ': 'Ý',
            'ύ': 'ý', 'Ϋ': 'Y', 'ϋ': 'ÿ', 'ΰ': 'ÿ', 'Ώ': 'Ó',
            'ώ': 'ó'})

        # Japanese (katakana and hiragana)
        for char in 'アァあ':
            self.trans[char] = 'a'
        for char in 'イィい':
            self.trans[char] = 'i'
        for char in 'ウう':
            self.trans[char] = 'u'
        for char in 'エェえ':
            self.trans[char] = 'e'
        for char in 'オォお':
            self.trans[char] = 'o'
        for char in 'ャや':
            self.trans[char] = 'ya'
        for char in 'ュゆ':
            self.trans[char] = 'yu'
        for char in 'ョよ':
            self.trans[char] = 'yo'
        for char in 'カか':
            self.trans[char] = 'ka'
        for char in 'キき':
            self.trans[char] = 'ki'
        for char in 'クく':
            self.trans[char] = 'ku'
        for char in 'ケけ':
            self.trans[char] = 'ke'
        for char in 'コこ':
            self.trans[char] = 'ko'
        for char in 'サさ':
            self.trans[char] = 'sa'
        for char in 'シし':
            self.trans[char] = 'shi'
        for char in 'スす':
            self.trans[char] = 'su'
        for char in 'セせ':
            self.trans[char] = 'se'
        for char in 'ソそ':
            self.trans[char] = 'so'
        for char in 'タた':
            self.trans[char] = 'ta'
        for char in 'チち':
            self.trans[char] = 'chi'
        for char in 'ツつ':
            self.trans[char] = 'tsu'
        for char in 'テて':
            self.trans[char] = 'te'
        for char in 'トと':
            self.trans[char] = 'to'
        for char in 'ナな':
            self.trans[char] = 'na'
        for char in 'ニに':
            self.trans[char] = 'ni'
        for char in 'ヌぬ':
            self.trans[char] = 'nu'
        for char in 'ネね':
            self.trans[char] = 'ne'
        for char in 'ノの':
            self.trans[char] = 'no'
        for char in 'ハは':
            self.trans[char] = 'ha'
        for char in 'ヒひ':
            self.trans[char] = 'hi'
        for char in 'フふ':
            self.trans[char] = 'fu'
        for char in 'ヘへ':
            self.trans[char] = 'he'
        for char in 'ホほ':
            self.trans[char] = 'ho'
        for char in 'マま':
            self.trans[char] = 'ma'
        for char in 'ミみ':
            self.trans[char] = 'mi'
        for char in 'ムむ':
            self.trans[char] = 'mu'
        for char in 'メめ':
            self.trans[char] = 'me'
        for char in 'モも':
            self.trans[char] = 'mo'
        for char in 'ラら':
            self.trans[char] = 'ra'
        for char in 'リり':
            self.trans[char] = 'ri'
        for char in 'ルる':
            self.trans[char] = 'ru'
        for char in 'レれ':
            self.trans[char] = 're'
        for char in 'ロろ':
            self.trans[char] = 'ro'
        for char in 'ワわ':
            self.trans[char] = 'wa'
        for char in 'ヰゐ':
            self.trans[char] = 'wi'
        for char in 'ヱゑ':
            self.trans[char] = 'we'
        for char in 'ヲを':
            self.trans[char] = 'wo'
        for char in 'ンん':
            self.trans[char] = 'n'
        for char in 'ガが':
            self.trans[char] = 'ga'
        for char in 'ギぎ':
            self.trans[char] = 'gi'
        for char in 'グぐ':
            self.trans[char] = 'gu'
        for char in 'ゲげ':
            self.trans[char] = 'ge'
        for char in 'ゴご':
            self.trans[char] = 'go'
        for char in 'ザざ':
            self.trans[char] = 'za'
        for char in 'ジじ':
            self.trans[char] = 'ji'
        for char in 'ズず':
            self.trans[char] = 'zu'
        for char in 'ゼぜ':
            self.trans[char] = 'ze'
        for char in 'ゾぞ':
            self.trans[char] = 'zo'
        for char in 'ダだ':
            self.trans[char] = 'da'
        for char in 'ヂぢ':
            self.trans[char] = 'dji'
        for char in 'ヅづ':
            self.trans[char] = 'dzu'
        for char in 'デで':
            self.trans[char] = 'de'
        for char in 'ドど':
            self.trans[char] = 'do'
        for char in 'バば':
            self.trans[char] = 'ba'
        for char in 'ビび':
            self.trans[char] = 'bi'
        for char in 'ブぶ':
            self.trans[char] = 'bu'
        for char in 'ベべ':
            self.trans[char] = 'be'
        for char in 'ボぼ':
            self.trans[char] = 'bo'
        for char in 'パぱ':
            self.trans[char] = 'pa'
        for char in 'ピぴ':
            self.trans[char] = 'pi'
        for char in 'プぷ':
            self.trans[char] = 'pu'
        for char in 'ペぺ':
            self.trans[char] = 'pe'
        for char in 'ポぽ':
            self.trans[char] = 'po'
        for char in 'ヴゔ':
            self.trans[char] = 'vu'
        self.trans['ヷ'] = 'va'
        self.trans['ヸ'] = 'vi'
        self.trans['ヹ'] = 've'
        self.trans['ヺ'] = 'vo'

        # Japanese and Chinese punctuation and typography
        for char in '・·':
            self.trans[char] = ' '
        for char in '〃『』《》':
            self.trans[char] = u'"'
        for char in '「」〈〉〘〙〚〛':
            self.trans[char] = u"'"
        for char in '（〔':
            self.trans[char] = '('
        for char in '）〕':
            self.trans[char] = ')'
        for char in '［【〖':
            self.trans[char] = '['
        for char in '］】〗':
            self.trans[char] = ']'
        self.trans['｛'] = '{'
        self.trans['｝'] = '}'
        self.trans['っ'] = ':'
        self.trans['ー'] = 'h'
        self.trans['゛'] = "'"
        self.trans['゜'] = 'p'
        self.trans['。'] = '. '
        self.trans['、'] = ', '
        self.trans['・'] = ' '
        self.trans['〆'] = 'shime'
        self.trans['〜'] = '-'
        self.trans['…'] = '...'
        self.trans['‥'] = '..'
        self.trans['ヶ'] = 'months'
        for char in '•◦':
            self.trans[char] = '_'
        for char in '※＊':
            self.trans[char] = '*'
        self.trans['Ⓧ'] = '(X)'
        self.trans['Ⓨ'] = '(Y)'
        self.trans['！'] = '!'
        self.trans['？'] = '?'
        self.trans['；'] = ';'
        self.trans['：'] = ':'
        self.trans['。'] = '.'
        for char in '，、':
            self.trans[char] = ','

        # Georgian
        self.trans['ა'] = 'a'
        self.trans['ბ'] = 'b'
        self.trans['გ'] = 'g'
        self.trans['დ'] = 'd'
        for char in 'ეჱ':
            self.trans[char] = 'e'
        self.trans['ვ'] = 'v'
        self.trans['ზ'] = 'z'
        self.trans['თ'] = 'th'
        self.trans['ი'] = 'i'
        self.trans['კ'] = 'k'
        self.trans['ლ'] = 'l'
        self.trans['მ'] = 'm'
        self.trans['ნ'] = 'n'
        self.trans['ო'] = 'o'
        self.trans['პ'] = 'p'
        self.trans['ჟ'] = 'zh'
        self.trans['რ'] = 'r'
        self.trans['ს'] = 's'
        self.trans['ტ'] = 't'
        self.trans['უ'] = 'u'
        self.trans['ფ'] = 'ph'
        self.trans['ქ'] = 'q'
        self.trans['ღ'] = 'gh'
        for char in 'ყ':
            self.trans[char] = u"q'"
        self.trans['შ'] = 'sh'
        self.trans['ჩ'] = 'ch'
        self.trans['ც'] = 'ts'
        self.trans['ძ'] = 'dz'
        for char in 'წ':
            self.trans[char] = u"ts'"
        for char in 'ჭ':
            self.trans[char] = u"ch'"
        self.trans['ხ'] = 'kh'
        self.trans['ჯ'] = 'j'
        self.trans['ჰ'] = 'h'
        self.trans['ჳ'] = 'w'
        self.trans['ჵ'] = 'o'
        self.trans['ჶ'] = 'f'

        # Devanagari
        for char in 'पप':
            self.trans[char] = 'p'
        self.trans['अ'] = 'a'
        for char in 'आा':
            self.trans[char] = 'aa'
        self.trans['प'] = 'pa'
        for char in 'इि':
            self.trans[char] = 'i'
        for char in 'ईी':
            self.trans[char] = 'ii'
        for char in 'उु':
            self.trans[char] = 'u'
        for char in 'ऊू':
            self.trans[char] = 'uu'
        for char in 'एे':
            self.trans[char] = 'e'
        for char in 'ऐै':
            self.trans[char] = 'ai'
        for char in 'ओो':
            self.trans[char] = 'o'
        for char in 'औौ':
            self.trans[char] = 'au'
        for char in 'ऋृर':
            self.trans[char] = 'r'
        for char in 'ॠॄ':
            self.trans[char] = 'rr'
        for char in 'ऌॢल':
            self.trans[char] = 'l'
        for char in 'ॡॣ':
            self.trans[char] = 'll'
        self.trans['क'] = 'k'
        self.trans['ख'] = 'kh'
        self.trans['ग'] = 'g'
        self.trans['घ'] = 'gh'
        self.trans['ङ'] = 'ng'
        self.trans['च'] = 'c'
        self.trans['छ'] = 'ch'
        self.trans['ज'] = 'j'
        self.trans['झ'] = 'jh'
        self.trans['ञ'] = 'ñ'
        for char in 'टत':
            self.trans[char] = 't'
        for char in 'ठथ':
            self.trans[char] = 'th'
        for char in 'डद':
            self.trans[char] = 'd'
        for char in 'ढध':
            self.trans[char] = 'dh'
        for char in 'णन':
            self.trans[char] = 'n'
        self.trans['फ'] = 'ph'
        self.trans['ब'] = 'b'
        self.trans['भ'] = 'bh'
        self.trans['म'] = 'm'
        self.trans['य'] = 'y'
        self.trans['व'] = 'v'
        self.trans['श'] = 'sh'
        for char in 'षस':
            self.trans[char] = 's'
        self.trans['ह'] = 'h'
        self.trans['क'] = 'x'
        self.trans['त'] = 'tr'
        self.trans['ज'] = 'gj'
        for char in 'क़':
            self.trans[char] = 'q'
        self.trans['फ'] = 'f'
        self.trans['ख'] = 'hh'
        self.trans['H'] = 'gh'
        self.trans['ज'] = 'z'
        for char in 'डढ':
            self.trans[char] = 'r'
        # Devanagari ligatures (possibly incomplete and/or incorrect)
        for char in 'ख्':
            self.trans[char] = 'khn'
        self.trans['त'] = 'tn'
        for char in 'द्':
            self.trans[char] = 'dn'
        self.trans['श'] = 'cn'
        for char in 'ह्':
            self.trans[char] = 'fn'
        for char in 'अँ':
            self.trans[char] = 'm'
        for char in '॒॑':
            self.trans[char] = u""
        self.trans['०'] = '0'
        self.trans['१'] = '1'
        self.trans['२'] = '2'
        self.trans['३'] = '3'
        self.trans['४'] = '4'
        self.trans['५'] = '5'
        self.trans['६'] = '6'
        self.trans['७'] = '7'
        self.trans['८'] = '8'
        self.trans['९'] = '9'

        # Armenian
        self.trans['Ա'] = 'A'
        self.trans['ա'] = 'a'
        self.trans['Բ'] = 'B'
        self.trans['բ'] = 'b'
        self.trans['Գ'] = 'G'
        self.trans['գ'] = 'g'
        self.trans['Դ'] = 'D'
        self.trans['դ'] = 'd'
        self.trans['Ե'] = 'Je'
        self.trans['ե'] = 'e'
        self.trans['Զ'] = 'Z'
        self.trans['զ'] = 'z'
        self.trans['Է'] = 'É'
        self.trans['է'] = 'é'
        self.trans['Ը'] = 'Ë'
        self.trans['ը'] = 'ë'
        self.trans['Թ'] = 'Th'
        self.trans['թ'] = 'th'
        self.trans['Ժ'] = 'Zh'
        self.trans['ժ'] = 'zh'
        self.trans['Ի'] = 'I'
        self.trans['ի'] = 'i'
        self.trans['Լ'] = 'L'
        self.trans['լ'] = 'l'
        self.trans['Խ'] = 'Ch'
        self.trans['խ'] = 'ch'
        self.trans['Ծ'] = 'Ts'
        self.trans['ծ'] = 'ts'
        self.trans['Կ'] = 'K'
        self.trans['կ'] = 'k'
        self.trans['Հ'] = 'H'
        self.trans['հ'] = 'h'
        self.trans['Ձ'] = 'Dz'
        self.trans['ձ'] = 'dz'
        self.trans['Ղ'] = 'R'
        self.trans['ղ'] = 'r'
        self.trans['Ճ'] = 'Cz'
        self.trans['ճ'] = 'cz'
        self.trans['Մ'] = 'M'
        self.trans['մ'] = 'm'
        self.trans['Յ'] = 'J'
        self.trans['յ'] = 'j'
        self.trans['Ն'] = 'N'
        self.trans['ն'] = 'n'
        self.trans['Շ'] = 'S'
        self.trans['շ'] = 's'
        self.trans['Շ'] = 'Vo'
        self.trans['շ'] = 'o'
        self.trans['Չ'] = 'Tsh'
        self.trans['չ'] = 'tsh'
        self.trans['Պ'] = 'P'
        self.trans['պ'] = 'p'
        self.trans['Ջ'] = 'Dz'
        self.trans['ջ'] = 'dz'
        self.trans['Ռ'] = 'R'
        self.trans['ռ'] = 'r'
        self.trans['Ս'] = 'S'
        self.trans['ս'] = 's'
        self.trans['Վ'] = 'V'
        self.trans['վ'] = 'v'
        for char in 'Տ':
            self.trans[char] = u"T'"
        for char in 'տ':
            self.trans[char] = u"t'"
        self.trans['Ր'] = 'R'
        self.trans['ր'] = 'r'
        self.trans['Ց'] = 'Tsh'
        self.trans['ց'] = 'tsh'
        self.trans['Ւ'] = 'V'
        self.trans['ւ'] = 'v'
        self.trans['Փ'] = 'Ph'
        self.trans['փ'] = 'ph'
        self.trans['Ք'] = 'Kh'
        self.trans['ք'] = 'kh'
        self.trans['Օ'] = 'O'
        self.trans['օ'] = 'o'
        self.trans['Ֆ'] = 'F'
        self.trans['ֆ'] = 'f'
        self.trans['և'] = '&'
        self.trans['՟'] = '.'
        self.trans['՞'] = '?'
        self.trans['՝'] = ';'
        self.trans['՛'] = ''

        # Tamil
        for char in 'க்':
            self.trans[char] = 'k'
        for char in 'ஙண்ந்ன்':
            self.trans[char] = 'n'
        self.trans['ச'] = 'c'
        for char in 'ஞ்':
            self.trans[char] = 'ñ'
        for char in 'ட்':
            self.trans[char] = 'th'
        self.trans['த'] = 't'
        self.trans['ப'] = 'p'
        for char in 'ம்':
            self.trans[char] = 'm'
        for char in 'ய்':
            self.trans[char] = 'y'
        for char in 'ர்ழ்ற':
            self.trans[char] = 'r'
        for char in 'ல்ள':
            self.trans[char] = 'l'
        for char in 'வ்':
            self.trans[char] = 'v'
        self.trans['ஜ'] = 'j'
        self.trans['ஷ'] = 'sh'
        self.trans['ஸ'] = 's'
        self.trans['ஹ'] = 'h'
        for char in 'க்ஷ':
            self.trans[char] = 'x'
        self.trans['அ'] = 'a'
        self.trans['ஆ'] = 'aa'
        self.trans['இ'] = 'i'
        self.trans['ஈ'] = 'ii'
        self.trans['உ'] = 'u'
        self.trans['ஊ'] = 'uu'
        self.trans['எ'] = 'e'
        self.trans['ஏ'] = 'ee'
        self.trans['ஐ'] = 'ai'
        self.trans['ஒ'] = 'o'
        self.trans['ஓ'] = 'oo'
        self.trans['ஔ'] = 'au'
        self.trans['ஃ'] = ''

        # Bengali
        self.trans['অ'] = 'ô'
        for char in 'আা':
            self.trans[char] = 'a'
        for char in 'ইিঈী':
            self.trans[char] = 'i'
        for char in 'উুঊূ':
            self.trans[char] = 'u'
        for char in 'ঋৃ':
            self.trans[char] = 'ri'
        for char in 'এেয়':
            self.trans[char] = 'e'
        for char in 'ঐৈ':
            self.trans[char] = 'oi'
        for char in 'ওো':
            self.trans[char] = 'o'
        for char in 'ঔৌ':
            self.trans[char] = 'ou'
        self.trans['্'] = ''
        self.trans['ৎ'] = 't'
        self.trans['ং'] = 'n'
        self.trans['ঃ'] = 'h'
        self.trans['ঁ'] = 'ñ'
        self.trans['ক'] = 'k'
        self.trans['খ'] = 'kh'
        self.trans['গ'] = 'g'
        self.trans['ঘ'] = 'gh'
        self.trans['ঙ'] = 'ng'
        self.trans['চ'] = 'ch'
        self.trans['ছ'] = 'chh'
        self.trans['জ'] = 'j'
        self.trans['ঝ'] = 'jh'
        self.trans['ঞ'] = 'n'
        for char in 'টত':
            self.trans[char] = 't'
        for char in 'ঠথ':
            self.trans[char] = 'th'
        for char in 'ডদ':
            self.trans[char] = 'd'
        for char in 'ঢধ':
            self.trans[char] = 'dh'
        for char in 'ণন':
            self.trans[char] = 'n'
        self.trans['প'] = 'p'
        self.trans['ফ'] = 'ph'
        self.trans['ব'] = 'b'
        self.trans['ভ'] = 'bh'
        self.trans['ম'] = 'm'
        self.trans['য'] = 'dzh'
        self.trans['র'] = 'r'
        self.trans['ল'] = 'l'
        self.trans['শ'] = 's'
        self.trans['হ'] = 'h'
        for char in 'য়':
            self.trans[char] = '-'
        for char in 'ড়':
            self.trans[char] = 'r'
        self.trans['ঢ'] = 'rh'
        self.trans['০'] = '0'
        self.trans['১'] = '1'
        self.trans['২'] = '2'
        self.trans['৩'] = '3'
        self.trans['৪'] = '4'
        self.trans['৫'] = '5'
        self.trans['৬'] = '6'
        self.trans['৭'] = '7'
        self.trans['৮'] = '8'
        self.trans['৯'] = '9'

        # Thai (because of complications of the alphabet, self.transliterations
        #       are very imprecise here)
        self.trans['ก'] = 'k'
        for char in 'ขฃคฅฆ':
            self.trans[char] = 'kh'
        self.trans['ง'] = 'ng'
        for char in 'จฉชฌ':
            self.trans[char] = 'ch'
        for char in 'ซศษส':
            self.trans[char] = 's'
        for char in 'ญย':
            self.trans[char] = 'y'
        for char in 'ฎด':
            self.trans[char] = 'd'
        for char in 'ฏต':
            self.trans[char] = 't'
        for char in 'ฐฑฒถทธ':
            self.trans[char] = 'th'
        for char in 'ณน':
            self.trans[char] = 'n'
        self.trans['บ'] = 'b'
        self.trans['ป'] = 'p'
        for char in 'ผพภ':
            self.trans[char] = 'ph'
        for char in 'ฝฟ':
            self.trans[char] = 'f'
        self.trans['ม'] = 'm'
        self.trans['ร'] = 'r'
        self.trans['ฤ'] = 'rue'
        self.trans['ๅ'] = ':'
        for char in 'ลฬ':
            self.trans[char] = 'l'
        self.trans['ฦ'] = 'lue'
        self.trans['ว'] = 'w'
        for char in 'หฮ':
            self.trans[char] = 'h'
        self.trans['อ'] = ''
        self.trans['ร'] = 'ü'
        self.trans['ว'] = 'ua'
        for char in 'อวโิ':
            self.trans[char] = 'o'
        for char in 'ะัา':
            self.trans[char] = 'a'
        self.trans['ว'] = 'u'
        self.trans['ำ'] = 'am'
        self.trans['ิ'] = 'i'
        self.trans['ี'] = 'i:'
        self.trans['ึ'] = 'ue'
        self.trans['ื'] = 'ue:'
        self.trans['ุ'] = 'u'
        self.trans['ู'] = 'u:'
        for char in 'เ็':
            self.trans[char] = 'e'
        self.trans['แ'] = 'ae'
        for char in 'ใไ':
            self.trans[char] = 'ai'
        for char in '่้๊๋็์':
            self.trans[char] = u""
        self.trans['ฯ'] = '.'
        self.trans['ๆ'] = '(2)'

        # Korean (Revised Romanization system within possible, incomplete)
        self.trans['국'] = 'guk'
        self.trans['명'] = 'myeong'
        self.trans['검'] = 'geom'
        self.trans['타'] = 'ta'
        self.trans['분'] = 'bun'
        self.trans['사'] = 'sa'
        self.trans['류'] = 'ryu'
        self.trans['포'] = 'po'
        self.trans['르'] = 'reu'
        self.trans['투'] = 'tu'
        self.trans['갈'] = 'gal'
        self.trans['어'] = 'eo'
        self.trans['노'] = 'no'
        self.trans['웨'] = 'we'
        self.trans['이'] = 'i'
        self.trans['라'] = 'ra'
        self.trans['틴'] = 'tin'
        self.trans['루'] = 'ru'
        self.trans['마'] = 'ma'
        self.trans['니'] = 'ni'
        self.trans['아'] = 'a'
        self.trans['독'] = 'dok'
        self.trans['일'] = 'il'
        self.trans['모'] = 'mo'
        self.trans['크'] = 'keu'
        self.trans['샤'] = 'sya'
        self.trans['영'] = 'yeong'
        self.trans['불'] = 'bul'
        self.trans['가'] = 'ga'
        self.trans['리'] = 'ri'
        self.trans['그'] = 'geu'
        self.trans['지'] = 'ji'
        self.trans['야'] = 'ya'
        self.trans['바'] = 'ba'
        self.trans['슈'] = 'syu'
        self.trans['키'] = 'ki'
        self.trans['프'] = 'peu'
        self.trans['랑'] = 'rang'
        self.trans['스'] = 'seu'
        self.trans['로'] = 'ro'
        self.trans['메'] = 'me'
        self.trans['역'] = 'yeok'
        self.trans['도'] = 'do'

        # Kannada
        self.trans['ಅ'] = 'a'
        for char in 'ಆಾ':
            self.trans[char] = 'aa'
        for char in 'ಇಿ':
            self.trans[char] = 'i'
        for char in 'ಈೀ':
            self.trans[char] = 'ii'
        for char in 'ಉು':
            self.trans[char] = 'u'
        for char in 'ಊೂ':
            self.trans[char] = 'uu'
        for char in 'ಋೂ':
            self.trans[char] = u"r'"
        for char in 'ಎೆ':
            self.trans[char] = 'e'
        for char in 'ಏೇ':
            self.trans[char] = 'ee'
        for char in 'ಐೈ':
            self.trans[char] = 'ai'
        for char in 'ಒೊ':
            self.trans[char] = 'o'
        for char in 'ಓೋ':
            self.trans[char] = 'oo'
        for char in 'ಔೌ':
            self.trans[char] = 'au'
        self.trans['ಂ'] = "m'"
        self.trans['ಃ'] = "h'"
        self.trans['ಕ'] = 'k'
        self.trans['ಖ'] = 'kh'
        self.trans['ಗ'] = 'g'
        self.trans['ಘ'] = 'gh'
        self.trans['ಙ'] = 'ng'
        self.trans['ಚ'] = 'c'
        self.trans['ಛ'] = 'ch'
        self.trans['ಜ'] = 'j'
        self.trans['ಝ'] = 'ny'
        self.trans['ಟ'] = 'tt'
        self.trans['ಠ'] = 'tth'
        self.trans['ಡ'] = 'dd'
        self.trans['ಢ'] = 'ddh'
        self.trans['ಣ'] = 'nn'
        self.trans['ತ'] = 't'
        self.trans['ಥ'] = 'th'
        self.trans['ದ'] = 'd'
        self.trans['ಧ'] = 'dh'
        self.trans['ನ'] = 'n'
        self.trans['ಪ'] = 'p'
        self.trans['ಫ'] = 'ph'
        self.trans['ಬ'] = 'b'
        self.trans['ಭ'] = 'bh'
        self.trans['ಮ'] = 'm'
        self.trans['ಯ'] = 'y'
        self.trans['ರ'] = 'r'
        self.trans['ಲ'] = 'l'
        self.trans['ವ'] = 'v'
        self.trans['ಶ'] = 'sh'
        self.trans['ಷ'] = 'ss'
        self.trans['ಸ'] = 's'
        self.trans['ಹ'] = 'h'
        self.trans['ಳ'] = 'll'
        self.trans['೦'] = '0'
        self.trans['೧'] = '1'
        self.trans['೨'] = '2'
        self.trans['೩'] = '3'
        self.trans['೪'] = '4'
        self.trans['೫'] = '5'
        self.trans['೬'] = '6'
        self.trans['೭'] = '7'
        self.trans['೮'] = '8'
        self.trans['೯'] = '9'
        # Telugu
        self.trans['అ'] = 'a'
        for char in 'ఆా':
            self.trans[char] = 'aa'
        for char in 'ఇి':
            self.trans[char] = 'i'
        for char in 'ఈీ':
            self.trans[char] = 'ii'
        for char in 'ఉు':
            self.trans[char] = 'u'
        for char in 'ఊూ':
            self.trans[char] = 'uu'
        for char in 'ఋృ':
            self.trans[char] = "r'"
        for char in 'ౠౄ':
            self.trans[char] = 'r"'
        self.trans['ఌ'] = "l'"
        self.trans['ౡ'] = 'l"'
        for char in 'ఎె':
            self.trans[char] = 'e'
        for char in 'ఏే':
            self.trans[char] = 'ee'
        for char in 'ఐై':
            self.trans[char] = 'ai'
        for char in 'ఒొ':
            self.trans[char] = 'o'
        for char in 'ఓో':
            self.trans[char] = 'oo'
        for char in 'ఔౌ':
            self.trans[char] = 'au'
        self.trans['ం'] = "'"
        self.trans['ః'] = '"'
        self.trans['క'] = 'k'
        self.trans['ఖ'] = 'kh'
        self.trans['గ'] = 'g'
        self.trans['ఘ'] = 'gh'
        self.trans['ఙ'] = 'ng'
        self.trans['చ'] = 'ts'
        self.trans['ఛ'] = 'tsh'
        self.trans['జ'] = 'j'
        self.trans['ఝ'] = 'jh'
        self.trans['ఞ'] = 'ñ'
        for char in 'టత':
            self.trans[char] = 't'
        for char in 'ఠథ':
            self.trans[char] = 'th'
        for char in 'డద':
            self.trans[char] = 'd'
        for char in 'ఢధ':
            self.trans[char] = 'dh'
        for char in 'ణన':
            self.trans[char] = 'n'
        self.trans['ప'] = 'p'
        self.trans['ఫ'] = 'ph'
        self.trans['బ'] = 'b'
        self.trans['భ'] = 'bh'
        self.trans['మ'] = 'm'
        self.trans['య'] = 'y'
        for char in 'రఱ':
            self.trans[char] = 'r'
        for char in 'లళ':
            self.trans[char] = 'l'
        self.trans['వ'] = 'v'
        self.trans['శ'] = 'sh'
        for char in 'షస':
            self.trans[char] = 's'
        self.trans['హ'] = 'h'
        self.trans['్'] = ""
        for char in 'ంఁ':
            self.trans[char] = '^'
        self.trans['ః'] = '-'
        self.trans['౦'] = '0'
        self.trans['౧'] = '1'
        self.trans['౨'] = '2'
        self.trans['౩'] = '3'
        self.trans['౪'] = '4'
        self.trans['౫'] = '5'
        self.trans['౬'] = '6'
        self.trans['౭'] = '7'
        self.trans['౮'] = '8'
        self.trans['౯'] = '9'
        self.trans['౹'] = '1/4'
        self.trans['౺'] = '1/2'
        self.trans['౻'] = '3/4'
        self.trans['౼'] = '1/16'
        self.trans['౽'] = '1/8'
        self.trans['౾'] = '3/16'
        # Lao - note: pronounciation in initial position is used;
        # different pronounciation in final position is ignored
        self.trans['ກ'] = 'k'
        for char in 'ຂຄ':
            self.trans[char] = 'kh'
        self.trans['ງ'] = 'ng'
        self.trans['ຈ'] = 'ch'
        for char in 'ສຊ':
            self.trans[char] = 's'
        self.trans['ຍ'] = 'ny'
        self.trans['ດ'] = 'd'
        self.trans['ຕ'] = 't'
        for char in 'ຖທ':
            self.trans[char] = 'th'
        self.trans['ນ'] = 'n'
        self.trans['ບ'] = 'b'
        self.trans['ປ'] = 'p'
        for char in 'ຜພ':
            self.trans[char] = 'ph'
        for char in 'ຝຟ':
            self.trans[char] = 'f'
        for char in 'ມໝ':
            self.trans[char] = 'm'
        self.trans['ຢ'] = 'y'
        for char in 'ຣຼ':
            self.trans[char] = 'r'
        for char in 'ລຼ':
            self.trans[char] = 'l'
        self.trans['ວ'] = 'v'
        self.trans['ຮ'] = 'h'
        self.trans['ອ'] = "'"
        for char in 'ະັ':
            self.trans[char] = 'a'
        self.trans['ິ'] = 'i'
        self.trans['ຶ'] = 'ue'
        self.trans['ຸ'] = 'u'
        self.trans['ເ'] = 'é'
        self.trans['ແ'] = 'è'
        for char in 'ໂົາໍ':
            self.trans[char] = 'o'
        self.trans['ຽ'] = 'ia'
        self.trans['ເຶ'] = 'uea'
        self.trans['ຍ'] = 'i'
        for char in 'ໄໃ':
            self.trans[char] = 'ai'
        self.trans['ຳ'] = 'am'
        self.trans['າ'] = 'aa'
        self.trans['ີ'] = 'ii'
        self.trans['ື'] = 'yy'
        self.trans['ູ'] = 'uu'
        self.trans['ເ'] = 'e'
        self.trans['ແ'] = 'ei'
        self.trans['໐'] = '0'
        self.trans['໑'] = '1'
        self.trans['໒'] = '2'
        self.trans['໓'] = '3'
        self.trans['໔'] = '4'
        self.trans['໕'] = '5'
        self.trans['໖'] = '6'
        self.trans['໗'] = '7'
        self.trans['໘'] = '8'
        self.trans['໙'] = '9'
        # Chinese -- note: incomplete
        for char in '埃挨哎唉哀皑癌蔼矮艾碍爱隘':
            self.trans[char] = 'ai'
        for char in '鞍氨安俺按暗岸胺案':
            self.trans[char] = 'an'
        for char in '肮昂盎':
            self.trans[char] = 'ang'
        for char in '凹敖熬翱袄傲奥懊澳':
            self.trans[char] = 'ao'
        for char in '芭捌扒叭吧笆八疤巴拔跋靶把耙坝霸罢爸':
            self.trans[char] = 'ba'
        for char in '白柏百摆佰败拜稗':
            self.trans[char] = 'bai'
        for char in '斑班搬扳般颁板版扮拌伴瓣半办绊':
            self.trans[char] = 'ban'
        for char in '邦帮梆榜膀绑棒磅蚌镑傍谤':
            self.trans[char] = 'bang'
        for char in '苞胞包褒剥薄雹保堡饱宝抱报暴豹鲍爆':
            self.trans[char] = 'bao'
        for char in '杯碑悲卑北辈背贝钡倍狈备惫焙被':
            self.trans[char] = 'bei'
        for char in '奔苯本笨':
            self.trans[char] = 'ben'
        for char in '崩绷甭泵蹦迸':
            self.trans[char] = 'beng'
        for char in '逼鼻比鄙笔彼碧蓖蔽毕毙毖币庇痹闭敝弊必辟壁臂避陛':
            self.trans[char] = 'bi'
        for char in '鞭边编贬扁便变卞辨辩辫遍':
            self.trans[char] = 'bian'
        for char in '标彪膘表':
            self.trans[char] = 'biao'
        for char in '鳖憋别瘪':
            self.trans[char] = 'bie'
        for char in '彬斌濒滨宾摈':
            self.trans[char] = 'bin'
        for char in '兵冰柄丙秉饼炳病并':
            self.trans[char] = 'bing'
        for char in '玻菠播拨钵波博勃搏铂箔伯帛舶脖膊渤泊驳捕卜亳':
            self.trans[char] = 'bo'
        for char in '哺补埠不布步簿部怖':
            self.trans[char] = 'bu'
        for char in '猜裁材才财睬踩采彩菜蔡':
            self.trans[char] = 'cai'
        for char in '餐参蚕残惭惨灿':
            self.trans[char] = 'can'
        for char in '苍舱仓沧藏':
            self.trans[char] = 'cang'
        for char in '操糙槽曹草':
            self.trans[char] = 'cao'
        for char in '厕策侧册测':
            self.trans[char] = 'ce'
        for char in '层蹭':
            self.trans[char] = 'ceng'
        for char in '插叉茬茶查碴搽察岔差诧':
            self.trans[char] = 'cha'
        for char in '拆柴豺':
            self.trans[char] = 'chai'
        for char in '搀掺蝉馋谗缠铲产阐颤':
            self.trans[char] = 'chan'
        for char in '昌猖场尝常长偿肠厂敞畅唱倡':
            self.trans[char] = 'chang'
        for char in '超抄钞朝嘲潮巢吵炒':
            self.trans[char] = 'chao'
        for char in '车扯撤掣彻澈':
            self.trans[char] = 'che'
        for char in '郴臣辰尘晨忱沉陈趁衬':
            self.trans[char] = 'chen'
        for char in '撑称城橙成呈乘程惩澄诚承逞骋秤':
            self.trans[char] = 'cheng'
        for char in '吃痴持匙池迟弛驰耻齿侈尺赤翅斥炽':
            self.trans[char] = 'chi'
        for char in '充冲虫崇宠':
            self.trans[char] = 'chong'
        for char in '抽酬畴踌稠愁筹仇绸瞅丑臭':
            self.trans[char] = 'chou'
        for char in '初出橱厨躇锄雏滁除楚储矗搐触处':
            self.trans[char] = 'chu'
        self.trans['揣'] = 'chuai'
        for char in '川穿椽传船喘串':
            self.trans[char] = 'chuan'
        for char in '疮窗幢床闯创':
            self.trans[char] = 'chuang'
        for char in '吹炊捶锤垂':
            self.trans[char] = 'chui'
        for char in '春椿醇唇淳纯蠢':
            self.trans[char] = 'chun'
        for char in '戳绰':
            self.trans[char] = 'chuo'
        for char in '疵茨磁雌辞慈瓷词此刺赐次':
            self.trans[char] = 'ci'
        for char in '聪葱囱匆从丛':
            self.trans[char] = 'cong'
        self.trans['凑'] = 'cou'
        for char in '粗醋簇促':
            self.trans[char] = 'cu'
        for char in '蹿篡窜':
            self.trans[char] = 'cuan'
        for char in '摧崔催脆瘁粹淬翠':
            self.trans[char] = 'cui'
        for char in '村存寸':
            self.trans[char] = 'cun'
        for char in '磋撮搓措挫错':
            self.trans[char] = 'cuo'
        for char in '搭达答瘩打大':
            self.trans[char] = 'da'
        for char in '呆歹傣戴带殆代贷袋待逮怠':
            self.trans[char] = 'dai'
        for char in '耽担丹单郸掸胆旦氮但惮淡诞弹蛋儋':
            self.trans[char] = 'dan'
        for char in '当挡党荡档':
            self.trans[char] = 'dang'
        for char in '刀捣蹈倒岛祷导到稻悼道盗':
            self.trans[char] = 'dao'
        for char in '德得的':
            self.trans[char] = 'de'
        for char in '蹬灯登等瞪凳邓':
            self.trans[char] = 'deng'
        for char in '堤低滴迪敌笛狄涤翟嫡抵底地蒂第帝弟递缔':
            self.trans[char] = 'di'
        for char in '颠掂滇碘点典靛垫电佃甸店惦奠淀殿':
            self.trans[char] = 'dian'
        for char in '碉叼雕凋刁掉吊钓调':
            self.trans[char] = 'diao'
        for char in '跌爹碟蝶迭谍叠':
            self.trans[char] = 'die'
        for char in '丁盯叮钉顶鼎锭定订':
            self.trans[char] = 'ding'
        self.trans['丢'] = 'diu'
        for char in '东冬董懂动栋侗恫冻洞':
            self.trans[char] = 'dong'
        for char in '兜抖斗陡豆逗痘':
            self.trans[char] = 'dou'
        for char in '都督毒犊独读堵睹赌杜镀肚度渡妒':
            self.trans[char] = 'du'
        for char in '端短锻段断缎':
            self.trans[char] = 'duan'
        for char in '堆兑队对':
            self.trans[char] = 'dui'
        for char in '墩吨蹲敦顿囤钝盾遁':
            self.trans[char] = 'dun'
        for char in '掇哆多夺垛躲朵跺舵剁惰堕':
            self.trans[char] = 'duo'
        for char in '蛾峨鹅俄额讹娥恶厄扼遏鄂饿':
            self.trans[char] = 'e'
        for char in '恩嗯':
            self.trans[char] = 'en'
        for char in '而儿耳尔饵洱二贰':
            self.trans[char] = 'er'
        for char in '发罚筏伐乏阀法珐':
            self.trans[char] = 'fa'
        for char in '藩帆番翻樊矾钒繁凡烦反返范贩犯饭泛':
            self.trans[char] = 'fan'
        for char in '坊芳方肪房防妨仿访纺放':
            self.trans[char] = 'fang'
        for char in '菲非啡飞肥匪诽吠肺废沸费':
            self.trans[char] = 'fei'
        for char in '芬酚吩氛分纷坟焚汾粉奋份忿愤粪':
            self.trans[char] = 'fen'
        for char in '丰封枫蜂峰锋风疯烽逢冯缝讽奉凤':
            self.trans[char] = 'feng'
        self.trans['佛'] = 'fo'
        self.trans['否'] = 'fou'
        for char in ('夫敷肤孵扶拂辐幅氟符伏俘服浮涪福袱弗甫抚辅俯釜斧脯腑府腐赴副覆赋'
                     '复傅付阜父腹负富讣附妇缚咐'):
            self.trans[char] = 'fu'
        for char in '噶嘎':
            self.trans[char] = 'ga'
        for char in '该改概钙盖溉':
            self.trans[char] = 'gai'
        for char in '干甘杆柑竿肝赶感秆敢赣':
            self.trans[char] = 'gan'
        for char in '冈刚钢缸肛纲岗港杠':
            self.trans[char] = 'gang'
        for char in '篙皋高膏羔糕搞镐稿告':
            self.trans[char] = 'gao'
        for char in '哥歌搁戈鸽胳疙割革葛格蛤阁隔铬个各':
            self.trans[char] = 'ge'
        self.trans['给'] = 'gei'
        for char in '根跟':
            self.trans[char] = 'gen'
        for char in '耕更庚羹埂耿梗':
            self.trans[char] = 'geng'
        for char in '工攻功恭龚供躬公宫弓巩汞拱贡共':
            self.trans[char] = 'gong'
        for char in '钩勾沟苟狗垢构购够':
            self.trans[char] = 'gou'
        for char in '辜菇咕箍估沽孤姑鼓古蛊骨谷股故顾固雇':
            self.trans[char] = 'gu'
        for char in '刮瓜剐寡挂褂':
            self.trans[char] = 'gua'
        for char in '乖拐怪':
            self.trans[char] = 'guai'
        for char in '棺关官冠观管馆罐惯灌贯':
            self.trans[char] = 'guan'
        for char in '光广逛':
            self.trans[char] = 'guang'
        for char in '瑰规圭硅归龟闺轨鬼诡癸桂柜跪贵刽':
            self.trans[char] = 'gui'
        for char in '辊滚棍':
            self.trans[char] = 'gun'
        for char in '锅郭国果裹过':
            self.trans[char] = 'guo'
        self.trans['哈'] = 'ha'
        for char in '骸孩海氦亥害骇':
            self.trans[char] = 'hai'
        for char in '酣憨邯韩含涵寒函喊罕翰撼捍旱憾悍焊汗汉':
            self.trans[char] = 'han'
        for char in '夯杭航':
            self.trans[char] = 'hang'
        for char in '壕嚎豪毫郝好耗号浩':
            self.trans[char] = 'hao'
        for char in '呵喝荷菏核禾和何合盒貉阂河涸赫褐鹤贺':
            self.trans[char] = 'he'
        for char in '嘿黑':
            self.trans[char] = 'hei'
        for char in '痕很狠恨':
            self.trans[char] = 'hen'
        for char in '哼亨横衡恒':
            self.trans[char] = 'heng'
        for char in '轰哄烘虹鸿洪宏弘红':
            self.trans[char] = 'hong'
        for char in '喉侯猴吼厚候后':
            self.trans[char] = 'hou'
        for char in '呼乎忽瑚壶葫胡蝴狐糊湖弧虎唬护互沪户':
            self.trans[char] = 'hu'
        for char in '花哗华猾滑画划化话':
            self.trans[char] = 'hua'
        for char in '槐徊怀淮坏':
            self.trans[char] = 'huai'
        for char in '欢环桓还缓换患唤痪豢焕涣宦幻':
            self.trans[char] = 'huan'
        for char in '荒慌黄磺蝗簧皇凰惶煌晃幌恍谎':
            self.trans[char] = 'huang'
        for char in '灰挥辉徽恢蛔回毁悔慧卉惠晦贿秽会烩汇讳诲绘':
            self.trans[char] = 'hui'
        for char in '荤昏婚魂浑混':
            self.trans[char] = 'hun'
        for char in '豁活伙火获或惑霍货祸':
            self.trans[char] = 'huo'
        for char in ('击圾基机畸稽积箕肌饥迹激讥鸡姬绩缉吉极棘辑籍集及急疾汲即嫉级挤几'
                     '脊己蓟技冀季伎祭剂悸济寄寂计记既忌际妓继纪'):
            self.trans[char] = 'ji'
        for char in '嘉枷夹佳家加荚颊贾甲钾假稼价架驾嫁':
            self.trans[char] = 'jia'
        for char in ('歼监坚尖笺间煎兼肩艰奸缄茧检柬碱硷拣捡简俭剪减荐槛鉴践贱见键箭件健'
                     '舰剑饯渐溅涧建'):
            self.trans[char] = 'jian'
        for char in '僵姜将浆江疆蒋桨奖讲匠酱降':
            self.trans[char] = 'jiang'
        for char in '蕉椒礁焦胶交郊浇骄娇嚼搅铰矫侥脚狡角饺缴绞剿教酵轿较叫窖':
            self.trans[char] = 'jiao'
        for char in '揭接皆秸街阶截劫节桔杰捷睫竭洁结解姐戒藉芥界借介疥诫届':
            self.trans[char] = 'jie'
        for char in '巾筋斤金今津襟紧锦仅谨进靳晋禁近烬浸尽劲':
            self.trans[char] = 'jin'
        for char in '荆兢茎睛晶鲸京惊精粳经井警景颈静境敬镜径痉靖竟竞净':
            self.trans[char] = 'jing'
        for char in '囧炯窘':
            self.trans[char] = 'jiong'
        for char in '揪究纠玖韭久灸九酒厩救旧臼舅咎就疚':
            self.trans[char] = 'jiu'
        for char in '鞠拘狙疽居驹菊局咀矩举沮聚拒据巨具距踞锯俱句惧炬剧':
            self.trans[char] = 'ju'
        for char in '捐鹃娟倦眷卷绢':
            self.trans[char] = 'juan'
        for char in '撅攫抉掘倔爵觉决诀绝':
            self.trans[char] = 'jue'
        for char in '均菌钧军君峻俊竣浚郡骏':
            self.trans[char] = 'jun'
        for char in '喀咖卡咯':
            self.trans[char] = 'ka'
        for char in '开揩楷凯慨':
            self.trans[char] = 'kai'
        for char in '刊堪勘坎砍看':
            self.trans[char] = 'kan'
        for char in '康慷糠扛抗亢炕':
            self.trans[char] = 'kang'
        for char in '考拷烤靠':
            self.trans[char] = 'kao'
        for char in '坷苛柯棵磕颗科壳咳可渴克刻客课':
            self.trans[char] = 'ke'
        for char in '肯啃垦恳':
            self.trans[char] = 'ken'
        for char in '坑吭':
            self.trans[char] = 'keng'
        for char in '空恐孔控':
            self.trans[char] = 'kong'
        for char in '抠口扣寇':
            self.trans[char] = 'kou'
        for char in '枯哭窟苦酷库裤':
            self.trans[char] = 'ku'
        for char in '夸垮挎跨胯':
            self.trans[char] = 'kua'
        for char in '块筷侩快':
            self.trans[char] = 'kuai'
        for char in '宽款':
            self.trans[char] = 'kuan'
        for char in '匡筐狂框矿眶旷况':
            self.trans[char] = 'kuang'
        for char in '亏盔岿窥葵奎魁傀馈愧溃':
            self.trans[char] = 'kui'
        for char in '坤昆捆困':
            self.trans[char] = 'kun'
        for char in '括扩廓阔':
            self.trans[char] = 'kuo'
        for char in '垃拉喇蜡腊辣啦':
            self.trans[char] = 'la'
        for char in '莱来赖':
            self.trans[char] = 'lai'
        for char in '蓝婪栏拦篮阑兰澜谰揽览懒缆烂滥':
            self.trans[char] = 'lan'
        for char in '琅榔狼廊郎朗浪':
            self.trans[char] = 'lang'
        for char in '捞劳牢老佬姥酪烙涝':
            self.trans[char] = 'lao'
        for char in '勒乐':
            self.trans[char] = 'le'
        for char in '雷镭蕾磊累儡垒擂肋类泪':
            self.trans[char] = 'lei'
        for char in '棱楞冷':
            self.trans[char] = 'leng'
        for char in ('厘梨犁黎篱狸离漓理李里鲤礼莉荔吏栗丽厉励砾历利傈例俐痢立粒沥隶力'
                     '璃哩'):
            self.trans[char] = 'li'
        self.trans['俩'] = 'lia'
        for char in '联莲连镰廉怜涟帘敛脸链恋炼练':
            self.trans[char] = 'lian'
        for char in '粮凉梁粱良两辆量晾亮谅':
            self.trans[char] = 'liang'
        for char in '撩聊僚疗燎寥辽潦了撂镣廖料':
            self.trans[char] = 'liao'
        for char in '列裂烈劣猎':
            self.trans[char] = 'lie'
        for char in '琳林磷霖临邻鳞淋凛赁吝拎':
            self.trans[char] = 'lin'
        for char in '玲菱零龄铃伶羚凌灵陵岭领另令':
            self.trans[char] = 'ling'
        for char in '溜琉榴硫馏留刘瘤流柳六':
            self.trans[char] = 'liu'
        for char in '龙聋咙笼窿隆垄拢陇':
            self.trans[char] = 'long'
        for char in '楼娄搂篓漏陋':
            self.trans[char] = 'lou'
        for char in '芦卢颅庐炉掳卤虏鲁麓碌露路赂鹿潞禄录陆戮泸':
            self.trans[char] = 'lu'
        for char in '峦挛孪滦卵乱':
            self.trans[char] = 'luan'
        for char in '掠略':
            self.trans[char] = 'lue'
        for char in '抡轮伦仑沦纶论':
            self.trans[char] = 'lun'
        for char in '萝螺罗逻锣箩骡裸落洛骆络漯':
            self.trans[char] = 'luo'
        for char in '驴吕铝侣旅履屡缕虑氯律率滤绿':
            self.trans[char] = 'lv'
        for char in '妈麻玛码蚂马骂嘛吗':
            self.trans[char] = 'ma'
        for char in '埋买麦卖迈脉':
            self.trans[char] = 'mai'
        for char in '瞒馒蛮满蔓曼慢漫谩':
            self.trans[char] = 'man'
        for char in '芒茫盲氓忙莽':
            self.trans[char] = 'mang'
        for char in '猫茅锚毛矛铆卯茂冒帽貌贸':
            self.trans[char] = 'mao'
        self.trans['么'] = 'me'
        for char in '玫枚梅酶霉煤没眉媒镁每美昧寐妹媚':
            self.trans[char] = 'mei'
        for char in '门闷们':
            self.trans[char] = 'men'
        for char in '萌蒙檬盟锰猛梦孟':
            self.trans[char] = 'meng'
        for char in '眯醚靡糜迷谜弥米秘觅泌蜜密幂':
            self.trans[char] = 'mi'
        for char in '棉眠绵冕免勉娩缅面':
            self.trans[char] = 'mian'
        for char in '苗描瞄藐秒渺庙妙':
            self.trans[char] = 'miao'
        for char in '蔑灭':
            self.trans[char] = 'mie'
        for char in '民抿皿敏悯闽':
            self.trans[char] = 'min'
        for char in '明螟鸣铭名命':
            self.trans[char] = 'ming'
        self.trans['谬'] = 'miu'
        for char in '摸摹蘑模膜磨摩魔抹末莫墨默沫漠寞陌':
            self.trans[char] = 'mo'
        for char in '谋牟某':
            self.trans[char] = 'mou'
        for char in '拇牡亩姆母墓暮幕募慕木目睦牧穆':
            self.trans[char] = 'mu'
        for char in '拿哪呐钠那娜纳':
            self.trans[char] = 'na'
        for char in '氖乃奶耐奈':
            self.trans[char] = 'nai'
        for char in '南男难':
            self.trans[char] = 'nan'
        self.trans['囊'] = 'nang'
        for char in '挠脑恼闹淖':
            self.trans[char] = 'nao'
        self.trans['呢'] = 'ne'
        for char in '馁内':
            self.trans[char] = 'nei'
        self.trans['嫩'] = 'nen'
        self.trans['能'] = 'neng'
        for char in '妮霓倪泥尼拟你匿腻逆溺':
            self.trans[char] = 'ni'
        for char in '蔫拈年碾撵捻念':
            self.trans[char] = 'nian'
        for char in '娘酿':
            self.trans[char] = 'niang'
        for char in '鸟尿':
            self.trans[char] = 'niao'
        for char in '捏聂孽啮镊镍涅':
            self.trans[char] = 'nie'
        self.trans['您'] = 'nin'
        for char in '柠狞凝宁拧泞':
            self.trans[char] = 'ning'
        for char in '牛扭钮纽':
            self.trans[char] = 'niu'
        for char in '脓浓农弄':
            self.trans[char] = 'nong'
        for char in '奴努怒':
            self.trans[char] = 'nu'
        self.trans['暖'] = 'nuan'
        for char in '虐疟':
            self.trans[char] = 'nue'
        for char in '挪懦糯诺':
            self.trans[char] = 'nuo'
        self.trans['女'] = 'nv'
        self.trans['哦'] = 'o'
        for char in '欧鸥殴藕呕偶沤':
            self.trans[char] = 'ou'
        for char in '啪趴爬帕怕琶':
            self.trans[char] = 'pa'
        for char in '拍排牌徘湃派':
            self.trans[char] = 'pai'
        for char in '攀潘盘磐盼畔判叛':
            self.trans[char] = 'pan'
        for char in '乓庞旁耪胖':
            self.trans[char] = 'pang'
        for char in '抛咆刨炮袍跑泡':
            self.trans[char] = 'pao'
        for char in '呸胚培裴赔陪配佩沛':
            self.trans[char] = 'pei'
        for char in '喷盆':
            self.trans[char] = 'pen'
        for char in '砰抨烹澎彭蓬棚硼篷膨朋鹏捧碰':
            self.trans[char] = 'peng'
        for char in '坯砒霹批披劈琵毗啤脾疲皮匹痞僻屁譬':
            self.trans[char] = 'pi'
        for char in '篇偏片骗':
            self.trans[char] = 'pian'
        for char in '飘漂瓢票':
            self.trans[char] = 'piao'
        for char in '撇瞥':
            self.trans[char] = 'pie'
        for char in '拼频贫品聘':
            self.trans[char] = 'pin'
        for char in '乒坪苹萍平凭瓶评屏':
            self.trans[char] = 'ping'
        for char in '坡泼颇婆破魄迫粕剖':
            self.trans[char] = 'po'
        for char in '扑铺仆莆葡菩蒲埔朴圃普浦谱曝瀑濮':
            self.trans[char] = 'pu'
        for char in ('期欺栖戚妻七凄漆柒沏其棋奇歧畦崎脐齐旗祈祁骑起岂乞企启契砌器气迄'
                     '弃汽泣讫'):
            self.trans[char] = 'qi'
        for char in '掐恰洽':
            self.trans[char] = 'qia'
        for char in '牵扦钎铅千迁签仟谦乾黔钱钳前潜遣浅谴堑嵌欠歉':
            self.trans[char] = 'qian'
        for char in '枪呛腔羌墙蔷强抢':
            self.trans[char] = 'qiang'
        for char in '橇锹敲悄桥瞧乔侨巧鞘撬翘峭俏窍':
            self.trans[char] = 'qiao'
        for char in '切茄且怯窃':
            self.trans[char] = 'qie'
        for char in '钦侵亲秦琴勤芹擒禽寝沁':
            self.trans[char] = 'qin'
        for char in '青轻氢倾卿清擎晴氰情顷请庆':
            self.trans[char] = 'qing'
        for char in '琼穷':
            self.trans[char] = 'qiong'
        for char in '秋丘邱球求囚酋泅':
            self.trans[char] = 'qiu'
        for char in '趋区蛆曲躯屈驱渠取娶龋趣去':
            self.trans[char] = 'qu'
        for char in '圈颧权醛泉全痊拳犬券劝':
            self.trans[char] = 'quan'
        for char in '缺炔瘸却鹊榷确雀':
            self.trans[char] = 'que'
        for char in '裙群':
            self.trans[char] = 'qun'
        for char in '然燃冉染':
            self.trans[char] = 'ran'
        for char in '瓤壤攘嚷让':
            self.trans[char] = 'rang'
        for char in '饶扰绕':
            self.trans[char] = 'rao'
        for char in '惹热':
            self.trans[char] = 're'
        for char in '壬仁人忍韧任认刃妊纫':
            self.trans[char] = 'ren'
        for char in '扔仍':
            self.trans[char] = 'reng'
        self.trans['日'] = 'ri'
        for char in '戎茸蓉荣融熔溶容绒冗':
            self.trans[char] = 'rong'
        for char in '揉柔肉':
            self.trans[char] = 'rou'
        for char in '茹蠕儒孺如辱乳汝入褥':
            self.trans[char] = 'ru'
        for char in '软阮':
            self.trans[char] = 'ruan'
        for char in '蕊瑞锐':
            self.trans[char] = 'rui'
        for char in '闰润':
            self.trans[char] = 'run'
        for char in '若弱':
            self.trans[char] = 'ruo'
        for char in '撒洒萨':
            self.trans[char] = 'sa'
        for char in '腮鳃塞赛':
            self.trans[char] = 'sai'
        for char in '三叁伞散':
            self.trans[char] = 'san'
        for char in '桑嗓丧':
            self.trans[char] = 'sang'
        for char in '搔骚扫嫂':
            self.trans[char] = 'sao'
        for char in '瑟色涩':
            self.trans[char] = 'se'
        self.trans['森'] = 'sen'
        self.trans['僧'] = 'seng'
        for char in '莎砂杀刹沙纱傻啥煞':
            self.trans[char] = 'sha'
        for char in '筛晒':
            self.trans[char] = 'shai'
        for char in '珊苫杉山删煽衫闪陕擅赡膳善汕扇缮':
            self.trans[char] = 'shan'
        for char in '墒伤商赏晌上尚裳':
            self.trans[char] = 'shang'
        for char in '梢捎稍烧芍勺韶少哨邵绍':
            self.trans[char] = 'shao'
        for char in '奢赊蛇舌舍赦摄射慑涉社设':
            self.trans[char] = 'she'
        for char in '砷申呻伸身深娠绅神沈审婶甚肾慎渗':
            self.trans[char] = 'shen'
        for char in '声生甥牲升绳省盛剩胜圣':
            self.trans[char] = 'sheng'
        for char in ('师失狮施湿诗尸虱十石拾时什食蚀实识史矢使屎驶始式示士世柿事拭誓逝'
                     '势是嗜噬适仕侍释饰氏市恃室视试'):
            self.trans[char] = 'shi'
        for char in '收手首守寿授售受瘦兽':
            self.trans[char] = 'shou'
        for char in (
                '蔬枢梳殊抒输叔舒淑疏书赎孰熟薯暑曙署蜀黍鼠属术述树束戍竖墅庶数漱恕'):
            self.trans[char] = 'shu'
        for char in '刷耍':
            self.trans[char] = 'shua'
        for char in '摔衰甩帅':
            self.trans[char] = 'shuai'
        for char in '栓拴':
            self.trans[char] = 'shuan'
        for char in '霜双爽':
            self.trans[char] = 'shuang'
        for char in '谁水睡税':
            self.trans[char] = 'shui'
        for char in '吮瞬顺舜':
            self.trans[char] = 'shun'
        for char in '说硕朔烁':
            self.trans[char] = 'shuo'
        for char in '斯撕嘶思私司丝死肆寺嗣四伺似饲巳':
            self.trans[char] = 'si'
        for char in '松耸怂颂送宋讼诵':
            self.trans[char] = 'song'
        for char in '搜艘擞':
            self.trans[char] = 'sou'
        for char in '嗽苏酥俗素速粟僳塑溯宿诉肃':
            self.trans[char] = 'su'
        for char in '酸蒜算':
            self.trans[char] = 'suan'
        for char in '虽隋随绥髓碎岁穗遂隧祟':
            self.trans[char] = 'sui'
        for char in '孙损笋':
            self.trans[char] = 'sun'
        for char in '蓑梭唆缩琐索锁所':
            self.trans[char] = 'suo'
        for char in '塌他它她塔獭挞蹋踏':
            self.trans[char] = 'ta'
        for char in '胎苔抬台泰酞太态汰':
            self.trans[char] = 'tai'
        for char in '坍摊贪瘫滩坛檀痰潭谭谈坦毯袒碳探叹炭':
            self.trans[char] = 'tan'
        for char in '汤塘搪堂棠膛唐糖倘躺淌趟烫':
            self.trans[char] = 'tang'
        for char in '掏涛滔绦萄桃逃淘陶讨套':
            self.trans[char] = 'tao'
        self.trans['特'] = 'te'
        for char in '藤腾疼誊':
            self.trans[char] = 'teng'
        for char in '梯剔踢锑提题蹄啼体替嚏惕涕剃屉':
            self.trans[char] = 'ti'
        for char in '兲天添填田甜恬舔腆':
            self.trans[char] = 'tian'
        for char in '挑条迢眺跳':
            self.trans[char] = 'tiao'
        for char in '贴铁帖':
            self.trans[char] = 'tie'
        for char in '厅听烃汀廷停亭庭挺艇':
            self.trans[char] = 'ting'
        for char in '通桐酮瞳同铜彤童桶捅筒统痛':
            self.trans[char] = 'tong'
        for char in '偷投头透':
            self.trans[char] = 'tou'
        for char in '凸秃突图徒途涂屠土吐兔':
            self.trans[char] = 'tu'
        for char in '湍团':
            self.trans[char] = 'tuan'
        for char in '推颓腿蜕褪退':
            self.trans[char] = 'tui'
        for char in '吞屯臀':
            self.trans[char] = 'tun'
        for char in '拖托脱鸵陀驮驼椭妥拓唾':
            self.trans[char] = 'tuo'
        for char in '挖哇蛙洼娃瓦袜':
            self.trans[char] = 'wa'
        for char in '歪外':
            self.trans[char] = 'wai'
        for char in '豌弯湾玩顽丸烷完碗挽晚皖惋宛婉万腕莞':
            self.trans[char] = 'wan'
        for char in '汪王亡枉网往旺望忘妄':
            self.trans[char] = 'wang'
        for char in '威巍微危韦违桅围唯惟为潍维苇萎委伟伪尾纬未蔚味畏胃喂魏位渭谓尉慰卫':
            self.trans[char] = 'wei'
        for char in '瘟温蚊文闻纹吻稳紊问':
            self.trans[char] = 'wen'
        for char in '嗡翁瓮':
            self.trans[char] = 'weng'
        for char in '挝蜗涡窝我斡卧握沃':
            self.trans[char] = 'wo'
        for char in '巫呜钨乌污诬屋无芜梧吾吴毋武五捂午舞伍侮坞戊雾晤物勿务悟误':
            self.trans[char] = 'wu'
        for char in ('昔熙析西硒矽晰嘻吸锡牺稀息希悉膝夕惜熄烯溪汐犀檄袭席习媳喜铣洗系'
                     '隙戏细'):
            self.trans[char] = 'xi'
        for char in '瞎虾匣霞辖暇峡侠狭下厦夏吓':
            self.trans[char] = 'xia'
        for char in '掀锨先仙鲜纤咸贤衔舷闲涎弦嫌显险现献县腺馅羡宪陷限线':
            self.trans[char] = 'xian'
        for char in '相厢镶香箱襄湘乡翔祥详想响享项巷橡像向象':
            self.trans[char] = 'xiang'
        for char in '萧硝霄削哮嚣销消宵淆晓小孝校肖啸笑效':
            self.trans[char] = 'xiao'
        for char in '楔些歇蝎鞋协挟携邪斜胁谐写械卸蟹懈泄泻谢屑':
            self.trans[char] = 'xie'
        for char in '薪芯锌欣辛新忻心信衅':
            self.trans[char] = 'xin'
        for char in '星腥猩惺兴刑型形邢行醒幸杏性姓':
            self.trans[char] = 'xing'
        for char in '兄凶胸匈汹雄熊':
            self.trans[char] = 'xiong'
        for char in '休修羞朽嗅锈秀袖绣':
            self.trans[char] = 'xiu'
        for char in '墟戌需虚嘘须徐许蓄酗叙旭序畜恤絮婿绪续':
            self.trans[char] = 'xu'
        for char in '轩喧宣悬旋玄选癣眩绚':
            self.trans[char] = 'xuan'
        for char in '靴薛学穴雪血':
            self.trans[char] = 'xue'
        for char in '勋熏循旬询寻驯巡殉汛训讯逊迅':
            self.trans[char] = 'xun'
        for char in '压押鸦鸭呀丫芽牙蚜崖衙涯雅哑亚讶':
            self.trans[char] = 'ya'
        for char in '焉咽阉烟淹盐严研蜒岩延言颜阎炎沿奄掩眼衍演艳堰燕厌砚雁唁彦焰宴谚验':
            self.trans[char] = 'yan'
        for char in '殃央鸯秧杨扬佯疡羊洋阳氧仰痒养样漾':
            self.trans[char] = 'yang'
        for char in '邀腰妖瑶摇尧遥窑谣姚咬舀药要耀':
            self.trans[char] = 'yao'
        for char in '椰噎耶爷野冶也页掖业叶曳腋夜液':
            self.trans[char] = 'ye'
        for char in ('一壹医揖铱依伊衣颐夷遗移仪胰疑沂宜姨彝椅蚁倚已乙矣以艺抑易邑屹亿'
                     '役臆逸肄疫亦裔意毅忆义益溢诣议谊译异翼翌绎'):
            self.trans[char] = 'yi'
        for char in '茵荫因殷音阴姻吟银淫寅饮尹引隐印':
            self.trans[char] = 'yin'
        for char in '英樱婴鹰应缨莹萤营荧蝇迎赢盈影颖硬映':
            self.trans[char] = 'ying'
        self.trans['哟'] = 'yo'
        for char in '拥佣臃痈庸雍踊蛹咏泳涌永恿勇用':
            self.trans[char] = 'yong'
        for char in '幽优悠忧尤由邮铀犹油游酉有友右佑釉诱又幼迂':
            self.trans[char] = 'you'
        for char in ('淤于盂榆虞愚舆余俞逾鱼愉渝渔隅予娱雨与屿禹宇语羽玉域芋郁吁遇喻'
                     '峪御愈欲狱育誉浴寓裕预豫驭'):
            self.trans[char] = 'yu'
        for char in '鸳渊冤元垣袁原援辕园员圆猿源缘远苑愿怨院':
            self.trans[char] = 'yuan'
        for char in '曰约越跃钥岳粤月悦阅':
            self.trans[char] = 'yue'
        for char in '耘云郧匀陨允运蕴酝晕韵孕':
            self.trans[char] = 'yun'
        for char in '匝砸杂':
            self.trans[char] = 'za'
        for char in '栽哉灾宰载再在':
            self.trans[char] = 'zai'
        for char in '咱攒暂赞':
            self.trans[char] = 'zan'
        for char in '赃脏葬':
            self.trans[char] = 'zang'
        for char in '遭糟凿藻枣早澡蚤躁噪造皂灶燥':
            self.trans[char] = 'zao'
        for char in '责择则泽':
            self.trans[char] = 'ze'
        self.trans['贼'] = 'zei'
        self.trans['怎'] = 'zen'
        for char in '增憎曾赠':
            self.trans[char] = 'zeng'
        for char in '扎喳渣札轧铡闸眨栅榨咋乍炸诈':
            self.trans[char] = 'zha'
        for char in '摘斋宅窄债寨':
            self.trans[char] = 'zhai'
        for char in '瞻毡詹粘沾盏斩辗崭展蘸栈占战站湛绽':
            self.trans[char] = 'zhan'
        for char in '樟章彰漳张掌涨杖丈帐账仗胀瘴障':
            self.trans[char] = 'zhang'
        for char in '招昭找沼赵照罩兆肇召':
            self.trans[char] = 'zhao'
        for char in '遮折哲蛰辙者锗蔗这浙':
            self.trans[char] = 'zhe'
        for char in '珍斟真甄砧臻贞针侦枕疹诊震振镇阵圳':
            self.trans[char] = 'zhen'
        for char in '蒸挣睁征狰争怔整拯正政帧症郑证':
            self.trans[char] = 'zheng'
        for char in ('芝枝支吱蜘知肢脂汁之织职直植殖执值侄址指止趾只旨纸志挚掷至致置'
                     '帜峙制智秩稚质炙痔滞治窒'):
            self.trans[char] = 'zhi'
        for char in '中盅忠钟衷终种肿重仲众':
            self.trans[char] = 'zhong'
        for char in '舟周州洲诌粥轴肘帚咒皱宙昼骤':
            self.trans[char] = 'zhou'
        for char in '珠株蛛朱猪诸诛逐竹烛煮拄瞩嘱主著柱助蛀贮铸筑住注祝驻':
            self.trans[char] = 'zhu'
        for char in '抓爪':
            self.trans[char] = 'zhua'
        self.trans['拽'] = 'zhuai'
        for char in '专砖转撰赚篆':
            self.trans[char] = 'zhuan'
        for char in '桩庄装妆撞壮状':
            self.trans[char] = 'zhuang'
        for char in '椎锥追赘坠缀':
            self.trans[char] = 'zhui'
        for char in '谆准':
            self.trans[char] = 'zhun'
        for char in '捉拙卓桌琢茁酌啄着灼浊':
            self.trans[char] = 'zhuo'
        for char in '兹咨资姿滋淄孜紫仔籽滓子自渍字':
            self.trans[char] = 'zi'
        for char in '鬃棕踪宗综总纵':
            self.trans[char] = 'zong'
        for char in '邹走奏揍':
            self.trans[char] = 'zou'
        for char in '租足卒族祖诅阻组':
            self.trans[char] = 'zu'
        for char in '钻纂':
            self.trans[char] = 'zuan'
        for char in '嘴醉最罪':
            self.trans[char] = 'zui'
        for char in '尊遵':
            self.trans[char] = 'zun'
        for char in '昨左佐柞做作坐座':
            self.trans[char] = 'zuo'
        # from:
        # https://www.wikidata.org/wiki/MediaWiki:Gadget-SimpleTransliterate.js
        self.trans['ଂ'] = 'anusvara'
        self.trans['ઇ'] = 'i'
        self.trans['എ'] = 'e'
        self.trans['ગ'] = 'ga'
        self.trans['ਜ'] = 'ja'
        self.trans['ഞ'] = 'nya'
        self.trans['ଢ'] = 'ddha'
        self.trans['ધ'] = 'dha'
        self.trans['ਬ'] = 'ba'
        self.trans['മ'] = 'ma'
        self.trans['ଲ'] = 'la'
        self.trans['ષ'] = 'ssa'
        self.trans['਼'] = 'nukta'
        self.trans['ാ'] = 'aa'
        self.trans['ୂ'] = 'uu'
        self.trans['ે'] = 'e'
        self.trans['ੌ'] = 'au'
        self.trans['ൎ'] = 'reph'
        self.trans['ੜ'] = 'rra'
        self.trans['՞'] = '?'
        self.trans['ୢ'] = 'l'
        self.trans['૧'] = '1'
        self.trans['੬'] = '6'
        self.trans['൮'] = '8'
        self.trans['୲'] = 'quarter'
        self.trans['ൾ'] = 'll'
        self.trans['ਇ'] = 'i'
        self.trans['ഉ'] = 'u'
        self.trans['ઌ'] = 'l'
        self.trans['ਗ'] = 'ga'
        self.trans['ങ'] = 'nga'
        self.trans['ଝ'] = 'jha'
        self.trans['જ'] = 'ja'
        self.trans['؟'] = '?'
        self.trans['ਧ'] = 'dha'
        self.trans['ഩ'] = 'nnna'
        self.trans['ଭ'] = 'bha'
        self.trans['બ'] = 'ba'
        self.trans['ഹ'] = 'ha'
        self.trans['ଽ'] = 'avagraha'
        self.trans['઼'] = 'nukta'
        self.trans['ੇ'] = 'ee'
        self.trans['୍'] = 'virama'
        self.trans['ૌ'] = 'au'
        self.trans['੧'] = '1'
        self.trans['൩'] = '3'
        self.trans['୭'] = '7'
        self.trans['૬'] = '6'
        self.trans['൹'] = 'mark'
        self.trans['ਖ਼'] = 'khha'
        self.trans['ਂ'] = 'bindi'
        self.trans['ഈ'] = 'ii'
        self.trans['ઍ'] = 'e'
        self.trans['ଌ'] = 'l'
        self.trans['ഘ'] = 'gha'
        self.trans['ઝ'] = 'jha'
        self.trans['ଡ଼'] = 'rra'
        self.trans['ਢ'] = 'ddha'
        self.trans['ന'] = 'na'
        self.trans['ભ'] = 'bha'
        self.trans['ବ'] = 'ba'
        self.trans['ਲ'] = 'la'
        self.trans['സ'] = 'sa'
        self.trans['ઽ'] = 'avagraha'
        self.trans['଼'] = 'nukta'
        self.trans['ੂ'] = 'uu'
        self.trans['ൈ'] = 'ai'
        self.trans['્'] = 'virama'
        self.trans['ୌ'] = 'au'
        self.trans['൨'] = '2'
        self.trans['૭'] = '7'
        self.trans['୬'] = '6'
        self.trans['ੲ'] = 'iri'
        self.trans['ഃ'] = 'visarga'
        self.trans['ં'] = 'anusvara'
        self.trans['ଇ'] = 'i'
        self.trans['ഓ'] = 'oo'
        self.trans['ଗ'] = 'ga'
        self.trans['ਝ'] = 'jha'
        self.trans['？'] = '?'
        self.trans['ണ'] = 'nna'
        self.trans['ઢ'] = 'ddha'
        self.trans['ଧ'] = 'dha'
        self.trans['ਭ'] = 'bha'
        self.trans['ള'] = 'lla'
        self.trans['લ'] = 'la'
        self.trans['ଷ'] = 'ssa'
        self.trans['ൃ'] = 'r'
        self.trans['ૂ'] = 'uu'
        self.trans['େ'] = 'e'
        self.trans['੍'] = 'virama'
        self.trans['ୗ'] = 'mark'
        self.trans['ൣ'] = 'll'
        self.trans['ૢ'] = 'l'
        self.trans['୧'] = '1'
        self.trans['੭'] = '7'
        self.trans['൳'] = '1/4'
        self.trans['୷'] = 'sixteenths'
        self.trans['ଆ'] = 'aa'
        self.trans['ઋ'] = 'r'
        self.trans['ഊ'] = 'uu'
        self.trans['ਐ'] = 'ai'
        self.trans['ଖ'] = 'kha'
        self.trans['છ'] = 'cha'
        self.trans['ച'] = 'ca'
        self.trans['ਠ'] = 'ttha'
        self.trans['ଦ'] = 'da'
        self.trans['ફ'] = 'pha'
        self.trans['പ'] = 'pa'
        self.trans['ਰ'] = 'ra'
        self.trans['ଶ'] = 'sha'
        self.trans['ഺ'] = 'ttta'
        self.trans['ੀ'] = 'ii'
        self.trans['ો'] = 'o'
        self.trans['ൊ'] = 'o'
        self.trans['ୖ'] = 'mark'
        self.trans['୦'] = '0'
        self.trans['૫'] = '5'
        self.trans['൪'] = '4'
        self.trans['ੰ'] = 'tippi'
        self.trans['୶'] = 'eighth'
        self.trans['ൺ'] = 'nn'
        self.trans['ଁ'] = 'candrabindu'
        self.trans['അ'] = 'a'
        self.trans['ઐ'] = 'ai'
        self.trans['ക'] = 'ka'
        self.trans['ਸ਼'] = 'sha'
        self.trans['ਛ'] = 'cha'
        self.trans['ଡ'] = 'dda'
        self.trans['ઠ'] = 'ttha'
        self.trans['ഥ'] = 'tha'
        self.trans['ਫ'] = 'pha'
        self.trans['ર'] = 'ra'
        self.trans['വ'] = 'va'
        self.trans['ୁ'] = 'u'
        self.trans['ી'] = 'ii'
        self.trans['ੋ'] = 'oo'
        self.trans['ૐ'] = 'om'
        self.trans['ୡ'] = 'll'
        self.trans['ૠ'] = 'rr'
        self.trans['੫'] = '5'
        self.trans['ୱ'] = 'wa'
        self.trans['૰'] = 'sign'
        self.trans['൵'] = 'quarters'
        self.trans['ਫ਼'] = 'fa'
        self.trans['ઁ'] = 'candrabindu'
        self.trans['ਆ'] = 'aa'
        self.trans['ઑ'] = 'o'
        self.trans['ଐ'] = 'ai'
        self.trans['ഔ'] = 'au'
        self.trans['ਖ'] = 'kha'
        self.trans['ડ'] = 'dda'
        self.trans['ଠ'] = 'ttha'
        self.trans['ത'] = 'ta'
        self.trans['ਦ'] = 'da'
        self.trans['ର'] = 'ra'
        self.trans['ഴ'] = 'llla'
        self.trans['ુ'] = 'u'
        self.trans['ୀ'] = 'ii'
        self.trans['ൄ'] = 'rr'
        self.trans['ૡ'] = 'll'
        self.trans['ୠ'] = 'rr'
        self.trans['੦'] = '0'
        self.trans['૱'] = 'sign'
        self.trans['୰'] = 'isshar'
        self.trans['൴'] = '1/2'
        self.trans['ਁ'] = 'bindi'
        self.trans['આ'] = 'aa'
        self.trans['ଋ'] = 'r'
        self.trans['ഏ'] = 'ee'
        self.trans['ખ'] = 'kha'
        self.trans['ଛ'] = 'cha'
        self.trans['ട'] = 'tta'
        self.trans['ਡ'] = 'dda'
        self.trans['દ'] = 'da'
        self.trans['ଫ'] = 'pha'
        self.trans['യ'] = 'ya'
        self.trans['શ'] = 'sha'
        self.trans['ി'] = 'i'
        self.trans['ੁ'] = 'u'
        self.trans['ୋ'] = 'o'
        self.trans['ੑ'] = 'udaat'
        self.trans['૦'] = '0'
        self.trans['୫'] = '5'
        self.trans['൯'] = '9'
        self.trans['ੱ'] = 'addak'
        self.trans['ൿ'] = 'k'
        self.trans['ആ'] = 'aa'
        self.trans['ଊ'] = 'uu'
        self.trans['એ'] = 'e'
        self.trans['ਔ'] = 'au'
        self.trans['ഖ'] = 'kha'
        self.trans['ଚ'] = 'ca'
        self.trans['ટ'] = 'tta'
        self.trans['ਤ'] = 'ta'
        self.trans['ദ'] = 'da'
        self.trans['ପ'] = 'pa'
        self.trans['ય'] = 'ya'
        self.trans['ശ'] = 'sha'
        self.trans['િ'] = 'i'
        self.trans['െ'] = 'e'
        self.trans['൦'] = '0'
        self.trans['୪'] = '4'
        self.trans['૯'] = '9'
        self.trans['ੴ'] = 'onkar'
        self.trans['ଅ'] = 'a'
        self.trans['ਏ'] = 'ee'
        self.trans['କ'] = 'ka'
        self.trans['ઔ'] = 'au'
        self.trans['ਟ'] = 'tta'
        self.trans['ഡ'] = 'dda'
        self.trans['ଥ'] = 'tha'
        self.trans['ત'] = 'ta'
        self.trans['ਯ'] = 'ya'
        self.trans['റ'] = 'rra'
        self.trans['ଵ'] = 'va'
        self.trans['ਿ'] = 'i'
        self.trans['ു'] = 'u'
        self.trans['ૄ'] = 'rr'
        self.trans['ൡ'] = 'll'
        self.trans['੯'] = '9'
        self.trans['൱'] = '100'
        self.trans['୵'] = 'sixteenth'
        self.trans['અ'] = 'a'
        self.trans['ਊ'] = 'uu'
        self.trans['ഐ'] = 'ai'
        self.trans['ક'] = 'ka'
        self.trans['ଔ'] = 'au'
        self.trans['ਚ'] = 'ca'
        self.trans['ഠ'] = 'ttha'
        self.trans['થ'] = 'tha'
        self.trans['ତ'] = 'ta'
        self.trans['ਪ'] = 'pa'
        self.trans['ര'] = 'ra'
        self.trans['વ'] = 'va'
        self.trans['ീ'] = 'ii'
        self.trans['ૅ'] = 'e'
        self.trans['ୄ'] = 'rr'
        self.trans['ൠ'] = 'rr'
        self.trans['ਜ਼'] = 'za'
        self.trans['੪'] = '4'
        self.trans['൰'] = '10'
        self.trans['୴'] = 'quarters'
        self.trans['ਅ'] = 'a'
        self.trans['ഋ'] = 'r'
        self.trans['ઊ'] = 'uu'
        self.trans['ଏ'] = 'e'
        self.trans['ਕ'] = 'ka'
        self.trans['ഛ'] = 'cha'
        self.trans['ચ'] = 'ca'
        self.trans['ଟ'] = 'tta'
        self.trans['ਥ'] = 'tha'
        self.trans['ഫ'] = 'pha'
        self.trans['પ'] = 'pa'
        self.trans['ଯ'] = 'ya'
        self.trans['ਵ'] = 'va'
        self.trans['ି'] = 'i'
        self.trans['ോ'] = 'oo'
        self.trans['ୟ'] = 'yya'
        self.trans['൫'] = '5'
        self.trans['૪'] = '4'
        self.trans['୯'] = '9'
        self.trans['ੵ'] = 'yakash'
        self.trans['ൻ'] = 'n'
        self.trans['ઃ'] = 'visarga'
        self.trans['ം'] = 'anusvara'
        self.trans['ਈ'] = 'ii'
        self.trans['ઓ'] = 'o'
        self.trans['ഒ'] = 'o'
        self.trans['ਘ'] = 'gha'
        self.trans['ଞ'] = 'nya'
        self.trans['ણ'] = 'nna'
        self.trans['ഢ'] = 'ddha'
        self.trans['ਲ਼'] = 'lla'
        self.trans['ਨ'] = 'na'
        self.trans['ମ'] = 'ma'
        self.trans['ળ'] = 'lla'
        self.trans['ല'] = 'la'
        self.trans['ਸ'] = 'sa'
        self.trans['¿'] = '?'
        self.trans['ା'] = 'aa'
        self.trans['ૃ'] = 'r'
        self.trans['ൂ'] = 'uu'
        self.trans['ੈ'] = 'ai'
        self.trans['ૣ'] = 'll'
        self.trans['ൢ'] = 'l'
        self.trans['੨'] = '2'
        self.trans['୮'] = '8'
        self.trans['൲'] = '1000'
        self.trans['ਃ'] = 'visarga'
        self.trans['ଉ'] = 'u'
        self.trans['ઈ'] = 'ii'
        self.trans['ਓ'] = 'oo'
        self.trans['ଙ'] = 'nga'
        self.trans['ઘ'] = 'gha'
        self.trans['ഝ'] = 'jha'
        self.trans['ਣ'] = 'nna'
        self.trans['ન'] = 'na'
        self.trans['ഭ'] = 'bha'
        self.trans['ଜ'] = 'ja'
        self.trans['ହ'] = 'ha'
        self.trans['સ'] = 'sa'
        self.trans['ഽ'] = 'avagraha'
        self.trans['ૈ'] = 'ai'
        self.trans['്'] = 'virama'
        self.trans['୩'] = '3'
        self.trans['૨'] = '2'
        self.trans['൭'] = '7'
        self.trans['ੳ'] = 'ura'
        self.trans['ൽ'] = 'l'
        self.trans['ઉ'] = 'u'
        self.trans['ଈ'] = 'ii'
        self.trans['ഌ'] = 'l'
        self.trans['ઙ'] = 'nga'
        self.trans['ଘ'] = 'gha'
        self.trans['ജ'] = 'ja'
        self.trans['ਞ'] = 'nya'
        self.trans['ନ'] = 'na'
        self.trans['ബ'] = 'ba'
        self.trans['ਮ'] = 'ma'
        self.trans['હ'] = 'ha'
        self.trans['ସ'] = 'sa'
        self.trans['ਾ'] = 'aa'
        self.trans['ૉ'] = 'o'
        self.trans['ୈ'] = 'ai'
        self.trans['ൌ'] = 'au'
        self.trans['૩'] = '3'
        self.trans['୨'] = '2'
        self.trans['൬'] = '6'
        self.trans['੮'] = '8'
        self.trans['ർ'] = 'rr'
        self.trans['ଃ'] = 'visarga'
        self.trans['ഇ'] = 'i'
        self.trans['ਉ'] = 'u'
        self.trans['ଓ'] = 'o'
        self.trans['ഗ'] = 'ga'
        self.trans['ਙ'] = 'nga'
        self.trans['ઞ'] = 'nya'
        self.trans['ଣ'] = 'nna'
        self.trans['ധ'] = 'dha'
        self.trans['મ'] = 'ma'
        self.trans['ଳ'] = 'lla'
        self.trans['ഷ'] = 'ssa'
        self.trans['ਹ'] = 'ha'
        self.trans['ਗ਼'] = 'ghha'
        self.trans['ા'] = 'aa'
        self.trans['ୃ'] = 'r'
        self.trans['േ'] = 'ee'
        self.trans['ൗ'] = 'mark'
        self.trans['ଢ଼'] = 'rha'
        self.trans['ୣ'] = 'll'
        self.trans['൧'] = '1'
        self.trans['੩'] = '3'
        self.trans['૮'] = '8'
        self.trans['୳'] = 'half'
        for char in self.trans:
            value = self.trans[char]
            if value == '?':
                continue
            while (value.encode(encoding, 'replace').decode(encoding) == '?'
                   and value in self.trans):
                assert value != self.trans[value], \
                    '{!r} == self.trans[{!r}]!'.format(value, value)
                value = self.trans[value]
            self.trans[char] = value

    def transliterate(self, char, default="?", prev="-", next="-"):
        """
        Transliterate the character.

        @param char: The character to transliterate.
        @type char: str
        @param default: The character used when there is no transliteration.
        @type default: str
        @param prev: The previous character
        @type prev: str
        @param next: The next character
        @type next: str
        @return: The transliterated character which may be an empty string
        @rtype: str
        """
        if char in self.trans:
            return self.trans[char]
        # Arabic
        if char == '◌':
            return prev
        # Japanese
        if char == 'ッ':
            return self.transliterate(next)[0]
        if char in '々仝ヽヾゝゞ〱〲〳〵〴〵':
            return prev
        # Lao
        if char == 'ຫ':
            if next in 'ງຍນຣລຼຼວ':
                return ""
            else:
                return 'h'
        return default
