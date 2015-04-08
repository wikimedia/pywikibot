# -*- coding: utf-8  -*-
"""Module to transliterate text."""
from __future__ import unicode_literals

__version__ = '$Id$'


class transliterator(object):

    """Class to transliterating text."""

    def __init__(self, encoding):
        self.trans = {}
        for char in u"ÀÁÂẦẤẪẨẬÃĀĂẰẮẴẶẲȦǠẠḀȂĄǍẢ":
            self.trans[char] = u"A"
        for char in u"ȀǞ":
            self.trans[char] = u"Ä"
        self.trans[u"Ǻ"] = u"Å"
        self.trans[u"Ä"] = u"Ae"
        self.trans[u"Å"] = u"Aa"
        for char in u"àáâầấẫẩậãāăằắẵặẳȧǡạḁȃąǎảẚ":
            self.trans[char] = u"a"
        for char in u"ȁǟ":
            self.trans[char] = u"ä"
        self.trans[u"ǻ"] = u"å"
        self.trans[u"ä"] = u"ae"
        self.trans[u"å"] = u"aa"
        for char in u"ḂḄḆƁƂ":
            self.trans[char] = u"B"
        for char in u"ḃḅḇƀɓƃ":
            self.trans[char] = u"b"
        for char in u"ĆĈĊÇČƇ":
            self.trans[char] = u"C"
        for char in u"ćĉċçčƈȼ":
            self.trans[char] = u"c"
        self.trans[u"Ḉ"] = u"Ç"
        self.trans[u"ḉ"] = u"ç"
        self.trans[u"Ð"] = u"Dh"
        self.trans[u"ð"] = u"dh"
        for char in u"ĎḊḌḎḐḒĐƉƊƋ":
            self.trans[char] = u"D"
        for char in u"ďḋḍḏḑḓđɖɗƌ":
            self.trans[char] = u"d"
        for char in u"ÈȄÉÊḚËĒḔḖĔĖẸE̩ȆȨḜĘĚẼḘẺ":
            self.trans[char] = u"E"
        for char in u"ỀẾỄỆỂ":
            self.trans[char] = u"Ê"
        for char in u"èȅéêḛëēḕḗĕėẹe̩ȇȩḝęěẽḙẻ":
            self.trans[char] = u"e"
        for char in u"ềếễệể":
            self.trans[char] = u"ê"
        for char in u"ḞƑ":
            self.trans[char] = u"F"
        for char in u"ḟƒ":
            self.trans[char] = u"f"
        for char in u"ǴḠĞĠĢǦǤƓ":
            self.trans[char] = u"G"
        for char in u"ǵḡğġģǧǥɠ":
            self.trans[char] = u"g"
        self.trans[u"Ĝ"] = u"Gx"
        self.trans[u"ĝ"] = u"gx"
        for char in u"ḢḤḦȞḨḪH̱ĦǶ":
            self.trans[char] = u"H"
        for char in u"ḣḥḧȟḩḫ̱ẖħƕ":
            self.trans[char] = u"h"
        for char in u"IÌȈÍÎĨḬÏḮĪĬȊĮǏİỊỈƗ":
            self.trans[char] = u"I"
        for char in u"ıìȉíîĩḭïḯīĭȋįǐiịỉɨ":
            self.trans[char] = u"i"
        for char in u"ĴJ":
            self.trans[char] = u"J"
        for char in u"ɟĵ̌ǰ":
            self.trans[char] = u"j"
        for char in u"ḰǨĶḲḴƘ":
            self.trans[char] = u"K"
        for char in u"ḱǩķḳḵƙ":
            self.trans[char] = u"k"
        for char in u"ĹĻĽḶḸḺḼȽŁ":
            self.trans[char] = u"L"
        for char in u"ĺļľḷḹḻḽƚłɫ":
            self.trans[char] = u"l"
        for char in u"ḾṀṂ":
            self.trans[char] = u"M"
        for char in u"ḿṁṃɱ":
            self.trans[char] = u"m"
        for char in u"ǸŃÑŅŇṄṆṈṊŊƝɲȠ":
            self.trans[char] = u"N"
        for char in u"ǹńñņňṅṇṉṋŋɲƞ":
            self.trans[char] = u"n"
        for char in u"ÒÓÔÕṌṎȬÖŌṐṒŎǑȮȰỌǪǬƠỜỚỠỢỞỎƟØǾ":
            self.trans[char] = u"O"
        for char in u"òóôõṍṏȭöōṑṓŏǒȯȱọǫǭơờớỡợởỏɵøǿ":
            self.trans[char] = u"o"
        for char in u"ȌŐȪ":
            self.trans[char] = u"Ö"
        for char in u"ȍőȫ":
            self.trans[char] = u"ö"
        for char in u"ỒỐỖỘỔȎ":
            self.trans[char] = u"Ô"
        for char in u"ồốỗộổȏ":
            self.trans[char] = u"ô"
        for char in u"ṔṖƤ":
            self.trans[char] = u"P"
        for char in u"ṕṗƥ":
            self.trans[char] = u"p"
        self.trans[u"ᵽ"] = u"q"
        for char in u"ȐŔŖŘȒṘṚṜṞ":
            self.trans[char] = u"R"
        for char in u"ȑŕŗřȓṙṛṝṟɽ":
            self.trans[char] = u"r"
        for char in u"ŚṤŞȘŠṦṠṢṨ":
            self.trans[char] = u"S"
        for char in u"śṥşșšṧṡṣṩȿ":
            self.trans[char] = u"s"
        self.trans[u"Ŝ"] = u"Sx"
        self.trans[u"ŝ"] = u"sx"
        for char in u"ŢȚŤṪṬṮṰŦƬƮ":
            self.trans[char] = u"T"
        for char in u"ţțťṫṭṯṱŧȾƭʈ":
            self.trans[char] = u"t"
        for char in u"ÙÚŨṸṴÜṲŪṺŬỤŮŲǓṶỦƯỮỰỬ":
            self.trans[char] = u"U"
        for char in u"ùúũṹṵüṳūṻŭụůųǔṷủưữựửʉ":
            self.trans[char] = u"u"
        for char in u"ȔŰǛǗǕǙ":
            self.trans[char] = u"Ü"
        for char in u"ȕűǜǘǖǚ":
            self.trans[char] = u"ü"
        self.trans[u"Û"] = u"Ux"
        self.trans[u"û"] = u"ux"
        self.trans[u"Ȗ"] = u"Û"
        self.trans[u"ȗ"] = u"û"
        self.trans[u"Ừ"] = u"Ù"
        self.trans[u"ừ"] = u"ù"
        self.trans[u"Ứ"] = u"Ú"
        self.trans[u"ứ"] = u"ú"
        for char in u"ṼṾ":
            self.trans[char] = u"V"
        for char in u"ṽṿ":
            self.trans[char] = u"v"
        for char in u"ẀẂŴẄẆẈ":
            self.trans[char] = u"W"
        for char in u"ẁẃŵẅẇẉ":
            self.trans[char] = u"w"
        for char in u"ẊẌ":
            self.trans[char] = u"X"
        for char in u"ẋẍ":
            self.trans[char] = u"x"
        for char in u"ỲÝŶŸỸȲẎỴỶƳ":
            self.trans[char] = u"Y"
        for char in u"ỳýŷÿỹȳẏỵỷƴ":
            self.trans[char] = u"y"
        for char in u"ŹẐŻẒŽẔƵȤ":
            self.trans[char] = u"Z"
        for char in u"źẑżẓžẕƶȥ":
            self.trans[char] = u"z"
        self.trans[u"ɀ"] = u"zv"

        # Latin: extended Latin alphabet
        self.trans[u"ɑ"] = u"a"
        for char in u"ÆǼǢ":
            self.trans[char] = u"AE"
        for char in u"æǽǣ":
            self.trans[char] = u"ae"
        self.trans[u"Ð"] = u"Dh"
        self.trans[u"ð"] = u"dh"
        for char in u"ƎƏƐ":
            self.trans[char] = u"E"
        for char in u"ǝəɛ":
            self.trans[char] = u"e"
        for char in u"ƔƢ":
            self.trans[char] = u"G"
        for char in u"ᵷɣƣᵹ":
            self.trans[char] = u"g"
        self.trans[u"Ƅ"] = u"H"
        self.trans[u"ƅ"] = u"h"
        self.trans[u"Ƕ"] = u"Wh"
        self.trans[u"ƕ"] = u"wh"
        self.trans[u"Ɩ"] = u"I"
        self.trans[u"ɩ"] = u"i"
        self.trans[u"Ŋ"] = u"Ng"
        self.trans[u"ŋ"] = u"ng"
        self.trans[u"Œ"] = u"OE"
        self.trans[u"œ"] = u"oe"
        self.trans[u"Ɔ"] = u"O"
        self.trans[u"ɔ"] = u"o"
        self.trans[u"Ȣ"] = u"Ou"
        self.trans[u"ȣ"] = u"ou"
        self.trans[u"Ƽ"] = u"Q"
        for char in u"ĸƽ":
            self.trans[char] = u"q"
        self.trans[u"ȹ"] = u"qp"
        self.trans[u""] = u"r"
        self.trans[u"ſ"] = u"s"
        self.trans[u"ß"] = u"ss"
        self.trans[u"Ʃ"] = u"Sh"
        for char in u"ʃᶋ":
            self.trans[char] = u"sh"
        self.trans[u"Ʉ"] = u"U"
        self.trans[u"ʉ"] = u"u"
        self.trans[u"Ʌ"] = u"V"
        self.trans[u"ʌ"] = u"v"
        for char in u"ƜǷ":
            self.trans[char] = u"W"
        for char in u"ɯƿ":
            self.trans[char] = u"w"
        self.trans[u"Ȝ"] = u"Y"
        self.trans[u"ȝ"] = u"y"
        self.trans[u"Ĳ"] = u"IJ"
        self.trans[u"ĳ"] = u"ij"
        self.trans[u"Ƨ"] = u"Z"
        for char in u"ʮƨ":
            self.trans[char] = u"z"
        self.trans[u"Ʒ"] = u"Zh"
        self.trans[u"ʒ"] = u"zh"
        self.trans[u"Ǯ"] = u"Dzh"
        self.trans[u"ǯ"] = u"dzh"
        for char in u"ƸƹʔˀɁɂ":
            self.trans[char] = u"'"
        for char in u"Þ":
            self.trans[char] = u"Th"
        for char in u"þ":
            self.trans[char] = u"th"
        for char in u"Cʗǃ":
            self.trans[char] = u"!"

        # Punctuation and typography
        for char in u"«»“”„¨":
            self.trans[char] = u'"'
        for char in u"‘’′":
            self.trans[char] = u"'"
        self.trans[u"•"] = u"*"
        self.trans[u"@"] = u"(at)"
        self.trans[u"¤"] = u"$"
        self.trans[u"¢"] = u"c"
        self.trans[u"€"] = u"E"
        self.trans[u"£"] = u"L"
        self.trans[u"¥"] = u"yen"
        self.trans[u"†"] = u"+"
        self.trans[u"‡"] = u"++"
        self.trans[u"°"] = u":"
        self.trans[u"¡"] = u"!"
        self.trans[u"¿"] = u"?"
        self.trans[u"‰"] = u"o/oo"
        self.trans[u"‱"] = u"o/ooo"
        for char in u"¶§":
            self.trans[char] = u">"
        for char in u"…":
            self.trans[char] = u"..."
        for char in u"‒–—―":
            self.trans[char] = u"-"
        for char in u"·":
            self.trans[char] = u" "
        self.trans[u"¦"] = u"|"
        self.trans[u"⁂"] = u"***"
        self.trans[u"◊"] = u"<>"
        self.trans[u"‽"] = u"?!"
        self.trans[u"؟"] = u";-)"
        self.trans[u"¹"] = u"1"
        self.trans[u"²"] = u"2"
        self.trans[u"³"] = u"3"

        # Cyrillic
        self.trans.update({u"А": u"A", u"а": u"a", u"Б": u"B", u"б": u"b",
                           u"В": u"V", u"в": u"v", u"Г": u"G", u"г": u"g",
                           u"Д": u"D", u"д": u"d", u"Е": u"E", u"е": u"e",
                           u"Ж": u"Zh", u"ж": u"zh", u"З": u"Z", u"з": u"z",
                           u"И": u"I", u"и": u"i", u"Й": u"J", u"й": u"j",
                           u"К": u"K", u"к": u"k", u"Л": u"L", u"л": u"l",
                           u"М": u"M", u"м": u"m", u"Н": u"N", u"н": u"n",
                           u"О": u"O", u"о": u"o", u"П": u"P", u"п": u"p",
                           u"Р": u"R", u"р": u"r", u"С": u"S", u"с": u"s",
                           u"Т": u"T", u"т": u"t", u"У": u"U", u"у": u"u",
                           u"Ф": u"F", u"ф": u"f", u"х": u"kh", u"Ц": u"C",
                           u"ц": u"c", u"Ч": u"Ch", u"ч": u"ch", u"Ш": u"Sh",
                           u"ш": u"sh", u"Щ": u"Shch", u"щ": u"shch", u"Ь": u"'",
                           u"ь": "'", u"Ъ": u'"', u"ъ": '"', u"Ю": u"Yu",
                           u"ю": u"yu", u"Я": u"Ya", u"я": u"ya", u"Х": u"Kh",
                           u"Χ": u"Kh"})

        # Additional Cyrillic letters, most occuring in only one or a few languages
        self.trans.update({u"Ы": u"Y", u"ы": u"y", u"Ё": u"Ë", u"ё": u"ë",
                           u"Э": u"È", u"Ѐ": u"È", u"э": u"è", u"ѐ": u"è",
                           u"І": u"I", u"і": u"i", u"Ї": u"Ji", u"ї": u"ji",
                           u"Є": u"Je", u"є": u"je", u"Ґ": u"G", u"Ҝ": u"G",
                           u"ґ": u"g", u"ҝ": u"g", u"Ђ": u"Dj", u"ђ": u"dj",
                           u"Ӣ": u"Y", u"ӣ": u"y", u"Љ": u"Lj", u"љ": u"lj",
                           u"Њ": u"Nj", u"њ": u"nj", u"Ћ": u"Cj", u"ћ": u"cj",
                           u"Җ": u"Zhj", u"җ": u"zhj", u"Ѓ": u"Gj", u"ѓ": u"gj",
                           u"Ќ": u"Kj", u"ќ": u"kj", u"Ӣ": u"Ii", u"ӣ": u"ii",
                           u"Ӯ": u"U", u"ӯ": u"u", u"Ҳ": u"H", u"ҳ": u"h",
                           u"Ҷ": u"Dz", u"ҷ": u"dz", u"Ө": u"Ô", u"Ӫ": u"Ô",
                           u"ө": u"ô", u"ӫ": u"ô", u"Ү": u"Y", u"ү": u"y", u"Һ": u"H",
                           u"һ": u"h", u"Ә": u"AE", u"Ӕ": u"AE", u"ә": u"ae",
                           u"Ӛ": u"Ë", u"Ӭ": u"Ë", u"ӛ": u"ë", u"ӭ": u"ë", u"Җ": u"Zhj",
                           u"җ": u"zhj", u"Ұ": u"U", u"ұ": u"u", u"ў": u"ù", u"Ў": u"Ù",
                           u"ѝ": u"ì", u"Ѝ": u"Ì", u"Ӑ": u"A", u"ă": u"a", u"Ӓ": u"Ä",
                           u"ҿ": u"ä", u"Ҽ": u"Ts", u"Ҿ": u"Ts", u"ҽ": u"ts", u"ҿ": u"ts",
                           u"Ҙ": u"Dh", u"ҙ": u"dh", u"Ӏ": u"", u"ӏ": u"", u"Ӆ": u"L",
                           u"ӆ": u"l", u"Ӎ": u"M", u"ӎ": u"m", u"Ӧ": u"Ö", u"ӧ": u"ö",
                           u"Ҩ": u"u", u"ҩ": u"u", u"Ҧ": u"Ph", u"ҧ": u"ph", u"Ҏ": u"R",
                           u"ҏ": u"r", u"Ҫ": u"Th", u"ҫ": u"th", u"Ҭ": u"T", u"ҭ": u"t",
                           u"Ӯ": u"Û", u"ӯ": u"û", u"Ұ": u"U", u"Ӹ": u"U", u"ұ": u"u",
                           u"ӹ": u"u", u"Ҵ": u"Tts", u"ҵ": u"tts", u"Ӵ": u"Ch", u"ӵ": u"ch"})

        for char in u"ЈӤҊ":
            self.trans[char] = u"J"
        for char in u"јӥҋ":
            self.trans[char] = u"j"
        for char in u"ЏӁӜҶ":
            self.trans[char] = u"Dzh"
        for char in u"џӂӝҷ":
            self.trans[char] = u"dzh"
        for char in u"ЅӞӠӋҸ":
            self.trans[char] = u"Dz"
        for char in u"ѕӟӡӌҹ":
            self.trans[char] = u"dz"
        for char in u"ҒӶҔ":
            self.trans[char] = u"G"
        for char in u"ғӷҕ":
            self.trans[char] = u"g"
        for char in u"ҚҞҠӃ":
            self.trans[char] = u"Q"
        for char in u"қҟҡӄ":
            self.trans[char] = u"q"
        for char in u"ҢҤӉӇ":
            self.trans[char] = u"Ng"
        for char in u"ңҥӊӈ":
            self.trans[char] = u"ng"
        for char in u"ӖѢҌ":
            self.trans[char] = u"E"
        for char in u"ӗѣҍ":
            self.trans[char] = u"e"
        for char in u"ӲӰҮ":
            self.trans[char] = u"Ü"
        for char in u"ӳӱү":
            self.trans[char] = u"ü"

        # Archaic Cyrillic letters
        self.trans.update({u"Ѹ": u"Ou", u"ѹ": u"ou", u"Ѡ": u"O", u"Ѻ": u"O", u"ѡ": u"o",
                           u"ѻ": u"o", u"Ѿ": u"Ot", u"ѿ": u"ot", u"Ѣ": u"E", u"ѣ": u"e",
                           u"Ѥ": u"Ei", u"Ѧ": u"Ei", u"ѥ": u"ei", u"ѧ": u"ei", u"Ѫ": u"Ai",
                           u"ѫ": u"ai", u"Ѯ": u"X", u"ѯ": u"x", u"Ѱ": u"Ps", u"ѱ": u"ps",
                           u"Ѳ": u"Th", u"ѳ": u"th", u"Ѵ": u"Ü", u"Ѷ": u"Ü", u"ѵ": u"ü"})

        # Hebrew alphabet
        for char in u"אע":
            self.trans[char] = u"'"
        self.trans[u"ב"] = u"b"
        self.trans[u"ג"] = u"g"
        self.trans[u"ד"] = u"d"
        self.trans[u"ה"] = u"h"
        self.trans[u"ו"] = u"v"
        self.trans[u"ז"] = u"z"
        self.trans[u"ח"] = u"kh"
        self.trans[u"ט"] = u"t"
        self.trans[u"י"] = u"y"
        for char in u"ךכ":
            self.trans[char] = u"k"
        self.trans[u"ל"] = u"l"
        for char in u"םמ":
            self.trans[char] = u"m"
        for char in u"ןנ":
            self.trans[char] = u"n"
        self.trans[u"ס"] = u"s"
        for char in u"ףפ":
            self.trans[char] = u"ph"
        for char in u"ץצ":
            self.trans[char] = u"ts"
        self.trans[u"ק"] = u"q"
        self.trans[u"ר"] = u"r"
        self.trans[u"ש"] = u"sh"
        self.trans[u"ת"] = u"th"

        # Arab alphabet
        for char in u"اﺍﺎ":
            self.trans[char] = u"a"
        for char in u"بﺏﺐﺒﺑ":
            self.trans[char] = u"b"
        for char in u"تﺕﺖﺘﺗ":
            self.trans[char] = u"t"
        for char in u"ثﺙﺚﺜﺛ":
            self.trans[char] = u"th"
        for char in u"جﺝﺞﺠﺟ":
            self.trans[char] = u"g"
        for char in u"حﺡﺢﺤﺣ":
            self.trans[char] = u"h"
        for char in u"خﺥﺦﺨﺧ":
            self.trans[char] = u"kh"
        for char in u"دﺩﺪ":
            self.trans[char] = u"d"
        for char in u"ذﺫﺬ":
            self.trans[char] = u"dh"
        for char in u"رﺭﺮ":
            self.trans[char] = u"r"
        for char in u"زﺯﺰ":
            self.trans[char] = u"z"
        for char in u"سﺱﺲﺴﺳ":
            self.trans[char] = u"s"
        for char in u"شﺵﺶﺸﺷ":
            self.trans[char] = u"sh"
        for char in u"صﺹﺺﺼﺻ":
            self.trans[char] = u"s"
        for char in u"ضﺽﺾﻀﺿ":
            self.trans[char] = u"d"
        for char in u"طﻁﻂﻄﻃ":
            self.trans[char] = u"t"
        for char in u"ظﻅﻆﻈﻇ":
            self.trans[char] = u"z"
        for char in u"عﻉﻊﻌﻋ":
            self.trans[char] = u"'"
        for char in u"غﻍﻎﻐﻏ":
            self.trans[char] = u"gh"
        for char in u"فﻑﻒﻔﻓ":
            self.trans[char] = u"f"
        for char in u"قﻕﻖﻘﻗ":
            self.trans[char] = u"q"
        for char in u"كﻙﻚﻜﻛک":
            self.trans[char] = u"k"
        for char in u"لﻝﻞﻠﻟ":
            self.trans[char] = u"l"
        for char in u"مﻡﻢﻤﻣ":
            self.trans[char] = u"m"
        for char in u"نﻥﻦﻨﻧ":
            self.trans[char] = u"n"
        for char in u"هﻩﻪﻬﻫ":
            self.trans[char] = u"h"
        for char in u"وﻭﻮ":
            self.trans[char] = u"w"
        for char in u"یيﻱﻲﻴﻳ":
            self.trans[char] = u"y"
        # Arabic - additional letters, modified letters and ligatures
        self.trans[u"ﺀ"] = u"'"
        for char in u"آﺁﺂ":
            self.trans[char] = u"'a"
        for char in u"ةﺓﺔ":
            self.trans[char] = u"th"
        for char in u"ىﻯﻰ":
            self.trans[char] = u"á"
        for char in u"یﯼﯽﯿﯾ":
            self.trans[char] = u"y"
        self.trans[u"؟"] = u"?"
        # Arabic - ligatures
        for char in u"ﻻﻼ":
            self.trans[char] = u"la"
        self.trans[u"ﷲ"] = u"llah"
        for char in u"إأ":
            self.trans[char] = u"a'"
        self.trans[u"ؤ"] = u"w'"
        self.trans[u"ئ"] = u"y'"
        for char in u"◌◌":
            self.trans[char] = u""  # indicates absence of vowels
        # Arabic vowels
        self.trans[u"◌"] = u"a"
        self.trans[u"◌"] = u"u"
        self.trans[u"◌"] = u"i"
        self.trans[u"◌"] = u"a"
        self.trans[u"◌"] = u"ay"
        self.trans[u"◌"] = u"ay"
        self.trans[u"◌"] = u"u"
        self.trans[u"◌"] = u"iy"
        # Arab numerals
        for char in u"٠۰":
            self.trans[char] = u"0"
        for char in u"١۱":
            self.trans[char] = u"1"
        for char in u"٢۲":
            self.trans[char] = u"2"
        for char in u"٣۳":
            self.trans[char] = u"3"
        for char in u"٤۴":
            self.trans[char] = u"4"
        for char in u"٥۵":
            self.trans[char] = u"5"
        for char in u"٦۶":
            self.trans[char] = u"6"
        for char in u"٧۷":
            self.trans[char] = u"7"
        for char in u"٨۸":
            self.trans[char] = u"8"
        for char in u"٩۹":
            self.trans[char] = u"9"
        # Perso-Arabic
        for char in u"پﭙﭙپ":
            self.trans[char] = u"p"
        for char in u"چچچچ":
            self.trans[char] = u"ch"
        for char in u"ژژ":
            self.trans[char] = u"zh"
        for char in u"گﮔﮕﮓ":
            self.trans[char] = u"g"

        # Greek
        self.trans.update({u"Α": u"A", u"α": u"a", u"Β": u"B", u"β": u"b", u"Γ": u"G",
                           u"γ": u"g", u"Δ": u"D", u"δ": u"d", u"Ε": u"E", u"ε": u"e",
                           u"Ζ": u"Z", u"ζ": u"z", u"Η": u"I", u"η": u"i", u"θ": u"th",
                           u"Θ": u"Th", u"Ι": u"I", u"ι": u"i", u"Κ": u"K", u"κ": u"k",
                           u"Λ": u"L", u"λ": u"l", u"Μ": u"M", u"μ": u"m", u"Ν": u"N",
                           u"ν": u"n", u"Ξ": u"X", u"ξ": u"x", u"Ο": u"O", u"ο": u"o",
                           u"Π": u"P", u"π": u"p", u"Ρ": u"R", u"ρ": u"r", u"Σ": u"S",
                           u"σ": u"s", u"ς": u"s", u"Τ": u"T", u"τ": u"t", u"Υ": u"Y",
                           u"υ": u"y", u"Φ": u"F", u"φ": u"f", u"Ψ": u"Ps", u"ψ": u"ps",
                           u"Ω": u"O", u"ω": u"o", u"ϗ": u"&", u"Ϛ": u"St", u"ϛ": u"st",
                           u"Ϙ": u"Q", u"Ϟ": u"Q", u"ϙ": u"q", u"ϟ": u"q", u"Ϻ": u"S",
                           u"ϻ": u"s", u"Ϡ": u"Ss", u"ϡ": u"ss", u"Ϸ": u"Sh", u"ϸ": u"sh",
                           u"·": u":", u"Ά": u"Á", u"ά": u"á", u"Έ": u"É", u"Ή": u"É",
                           u"έ": u"é", u"ή": u"é", u"Ί": u"Í", u"ί": u"í", u"Ϊ": u"Ï",
                           u"ϊ": u"ï", u"ΐ": u"ï", u"Ό": u"Ó", u"ό": u"ó", u"Ύ": u"Ý",
                           u"ύ": u"ý", u"Ϋ": u"Y", u"ϋ": u"ÿ", u"ΰ": u"ÿ", u"Ώ": u"Ó",
                           u"ώ": u"ó"})

        # Japanese (katakana and hiragana)
        for char in u"アァあ":
            self.trans[char] = u"a"
        for char in u"イィい":
            self.trans[char] = u"i"
        for char in u"ウう":
            self.trans[char] = u"u"
        for char in u"エェえ":
            self.trans[char] = u"e"
        for char in u"オォお":
            self.trans[char] = u"o"
        for char in u"ャや":
            self.trans[char] = u"ya"
        for char in u"ュゆ":
            self.trans[char] = u"yu"
        for char in u"ョよ":
            self.trans[char] = u"yo"
        for char in u"カか":
            self.trans[char] = u"ka"
        for char in u"キき":
            self.trans[char] = u"ki"
        for char in u"クく":
            self.trans[char] = u"ku"
        for char in u"ケけ":
            self.trans[char] = u"ke"
        for char in u"コこ":
            self.trans[char] = u"ko"
        for char in u"サさ":
            self.trans[char] = u"sa"
        for char in u"シし":
            self.trans[char] = u"shi"
        for char in u"スす":
            self.trans[char] = u"su"
        for char in u"セせ":
            self.trans[char] = u"se"
        for char in u"ソそ":
            self.trans[char] = u"so"
        for char in u"タた":
            self.trans[char] = u"ta"
        for char in u"チち":
            self.trans[char] = u"chi"
        for char in u"ツつ":
            self.trans[char] = u"tsu"
        for char in u"テて":
            self.trans[char] = u"te"
        for char in u"トと":
            self.trans[char] = u"to"
        for char in u"ナな":
            self.trans[char] = u"na"
        for char in u"ニに":
            self.trans[char] = u"ni"
        for char in u"ヌぬ":
            self.trans[char] = u"nu"
        for char in u"ネね":
            self.trans[char] = u"ne"
        for char in u"ノの":
            self.trans[char] = u"no"
        for char in u"ハは":
            self.trans[char] = u"ha"
        for char in u"ヒひ":
            self.trans[char] = u"hi"
        for char in u"フふ":
            self.trans[char] = u"fu"
        for char in u"ヘへ":
            self.trans[char] = u"he"
        for char in u"ホほ":
            self.trans[char] = u"ho"
        for char in u"マま":
            self.trans[char] = u"ma"
        for char in u"ミみ":
            self.trans[char] = u"mi"
        for char in u"ムむ":
            self.trans[char] = u"mu"
        for char in u"メめ":
            self.trans[char] = u"me"
        for char in u"モも":
            self.trans[char] = u"mo"
        for char in u"ラら":
            self.trans[char] = u"ra"
        for char in u"リり":
            self.trans[char] = u"ri"
        for char in u"ルる":
            self.trans[char] = u"ru"
        for char in u"レれ":
            self.trans[char] = u"re"
        for char in u"ロろ":
            self.trans[char] = u"ro"
        for char in u"ワわ":
            self.trans[char] = u"wa"
        for char in u"ヰゐ":
            self.trans[char] = u"wi"
        for char in u"ヱゑ":
            self.trans[char] = u"we"
        for char in u"ヲを":
            self.trans[char] = u"wo"
        for char in u"ンん":
            self.trans[char] = u"n"
        for char in u"ガが":
            self.trans[char] = u"ga"
        for char in u"ギぎ":
            self.trans[char] = u"gi"
        for char in u"グぐ":
            self.trans[char] = u"gu"
        for char in u"ゲげ":
            self.trans[char] = u"ge"
        for char in u"ゴご":
            self.trans[char] = u"go"
        for char in u"ザざ":
            self.trans[char] = u"za"
        for char in u"ジじ":
            self.trans[char] = u"ji"
        for char in u"ズず":
            self.trans[char] = u"zu"
        for char in u"ゼぜ":
            self.trans[char] = u"ze"
        for char in u"ゾぞ":
            self.trans[char] = u"zo"
        for char in u"ダだ":
            self.trans[char] = u"da"
        for char in u"ヂぢ":
            self.trans[char] = u"dji"
        for char in u"ヅづ":
            self.trans[char] = u"dzu"
        for char in u"デで":
            self.trans[char] = u"de"
        for char in u"ドど":
            self.trans[char] = u"do"
        for char in u"バば":
            self.trans[char] = u"ba"
        for char in u"ビび":
            self.trans[char] = u"bi"
        for char in u"ブぶ":
            self.trans[char] = u"bu"
        for char in u"ベべ":
            self.trans[char] = u"be"
        for char in u"ボぼ":
            self.trans[char] = u"bo"
        for char in u"パぱ":
            self.trans[char] = u"pa"
        for char in u"ピぴ":
            self.trans[char] = u"pi"
        for char in u"プぷ":
            self.trans[char] = u"pu"
        for char in u"ペぺ":
            self.trans[char] = u"pe"
        for char in u"ポぽ":
            self.trans[char] = u"po"
        for char in u"ヴゔ":
            self.trans[char] = u"vu"
        self.trans[u"ヷ"] = u"va"
        self.trans[u"ヸ"] = u"vi"
        self.trans[u"ヹ"] = u"ve"
        self.trans[u"ヺ"] = u"vo"

        # Japanese and Chinese punctuation and typography
        for char in u"・·":
            self.trans[char] = u" "
        for char in u"〃『』《》":
            self.trans[char] = u'"'
        for char in u"「」〈〉〘〙〚〛":
            self.trans[char] = u"'"
        for char in u"（〔":
            self.trans[char] = u"("
        for char in u"）〕":
            self.trans[char] = u")"
        for char in u"［【〖":
            self.trans[char] = u"["
        for char in u"］】〗":
            self.trans[char] = u"]"
        for char in u"｛":
            self.trans[char] = u"{"
        for char in u"｝":
            self.trans[char] = u"}"
        for char in u"っ":
            self.trans[char] = u":"
        for char in u"ー":
            self.trans[char] = u"h"
        for char in u"゛":
            self.trans[char] = u"'"
        for char in u"゜":
            self.trans[char] = u"p"
        for char in u"。":
            self.trans[char] = u". "
        for char in u"、":
            self.trans[char] = u", "
        for char in u"・":
            self.trans[char] = u" "
        for char in u"〆":
            self.trans[char] = u"shime"
        for char in u"〜":
            self.trans[char] = u"-"
        for char in u"…":
            self.trans[char] = u"..."
        for char in u"‥":
            self.trans[char] = u".."
        for char in u"ヶ":
            self.trans[char] = u"months"
        for char in u"•◦":
            self.trans[char] = u"_"
        for char in u"※＊":
            self.trans[char] = u"*"
        for char in u"Ⓧ":
            self.trans[char] = u"(X)"
        for char in u"Ⓨ":
            self.trans[char] = u"(Y)"
        for char in u"！":
            self.trans[char] = u"!"
        for char in u"？":
            self.trans[char] = u"?"
        for char in u"；":
            self.trans[char] = u";"
        for char in u"：":
            self.trans[char] = u":"
        for char in u"。":
            self.trans[char] = u"."
        for char in u"，、":
            self.trans[char] = u","

        # Georgian
        for char in u"ა":
            self.trans[char] = u"a"
        for char in u"ბ":
            self.trans[char] = u"b"
        for char in u"გ":
            self.trans[char] = u"g"
        for char in u"დ":
            self.trans[char] = u"d"
        for char in u"ეჱ":
            self.trans[char] = u"e"
        for char in u"ვ":
            self.trans[char] = u"v"
        for char in u"ზ":
            self.trans[char] = u"z"
        for char in u"თ":
            self.trans[char] = u"th"
        for char in u"ი":
            self.trans[char] = u"i"
        for char in u"კ":
            self.trans[char] = u"k"
        for char in u"ლ":
            self.trans[char] = u"l"
        for char in u"მ":
            self.trans[char] = u"m"
        for char in u"ნ":
            self.trans[char] = u"n"
        for char in u"ო":
            self.trans[char] = u"o"
        for char in u"პ":
            self.trans[char] = u"p"
        for char in u"ჟ":
            self.trans[char] = u"zh"
        for char in u"რ":
            self.trans[char] = u"r"
        for char in u"ს":
            self.trans[char] = u"s"
        for char in u"ტ":
            self.trans[char] = u"t"
        for char in u"უ":
            self.trans[char] = u"u"
        for char in u"ფ":
            self.trans[char] = u"ph"
        for char in u"ქ":
            self.trans[char] = u"q"
        for char in u"ღ":
            self.trans[char] = u"gh"
        for char in u"ყ":
            self.trans[char] = u"q'"
        for char in u"შ":
            self.trans[char] = u"sh"
        for char in u"ჩ":
            self.trans[char] = u"ch"
        for char in u"ც":
            self.trans[char] = u"ts"
        for char in u"ძ":
            self.trans[char] = u"dz"
        for char in u"წ":
            self.trans[char] = u"ts'"
        for char in u"ჭ":
            self.trans[char] = u"ch'"
        for char in u"ხ":
            self.trans[char] = u"kh"
        for char in u"ჯ":
            self.trans[char] = u"j"
        for char in u"ჰ":
            self.trans[char] = u"h"
        for char in u"ჳ":
            self.trans[char] = u"w"
        for char in u"ჵ":
            self.trans[char] = u"o"
        for char in u"ჶ":
            self.trans[char] = u"f"

        # Devanagari
        for char in u"पप":
            self.trans[char] = u"p"
        for char in u"अ":
            self.trans[char] = u"a"
        for char in u"आा":
            self.trans[char] = u"aa"
        for char in u"प":
            self.trans[char] = u"pa"
        for char in u"इि":
            self.trans[char] = u"i"
        for char in u"ईी":
            self.trans[char] = u"ii"
        for char in u"उु":
            self.trans[char] = u"u"
        for char in u"ऊू":
            self.trans[char] = u"uu"
        for char in u"एे":
            self.trans[char] = u"e"
        for char in u"ऐै":
            self.trans[char] = u"ai"
        for char in u"ओो":
            self.trans[char] = u"o"
        for char in u"औौ":
            self.trans[char] = u"au"
        for char in u"ऋृर":
            self.trans[char] = u"r"
        for char in u"ॠॄ":
            self.trans[char] = u"rr"
        for char in u"ऌॢल":
            self.trans[char] = u"l"
        for char in u"ॡॣ":
            self.trans[char] = u"ll"
        for char in u"क":
            self.trans[char] = u"k"
        for char in u"ख":
            self.trans[char] = u"kh"
        for char in u"ग":
            self.trans[char] = u"g"
        for char in u"घ":
            self.trans[char] = u"gh"
        for char in u"ङ":
            self.trans[char] = u"ng"
        for char in u"च":
            self.trans[char] = u"c"
        for char in u"छ":
            self.trans[char] = u"ch"
        for char in u"ज":
            self.trans[char] = u"j"
        for char in u"झ":
            self.trans[char] = u"jh"
        for char in u"ञ":
            self.trans[char] = u"ñ"
        for char in u"टत":
            self.trans[char] = u"t"
        for char in u"ठथ":
            self.trans[char] = u"th"
        for char in u"डद":
            self.trans[char] = u"d"
        for char in u"ढध":
            self.trans[char] = u"dh"
        for char in u"णन":
            self.trans[char] = u"n"
        for char in u"फ":
            self.trans[char] = u"ph"
        for char in u"ब":
            self.trans[char] = u"b"
        for char in u"भ":
            self.trans[char] = u"bh"
        for char in u"म":
            self.trans[char] = u"m"
        for char in u"य":
            self.trans[char] = u"y"
        for char in u"व":
            self.trans[char] = u"v"
        for char in u"श":
            self.trans[char] = u"sh"
        for char in u"षस":
            self.trans[char] = u"s"
        for char in u"ह":
            self.trans[char] = u"h"
        for char in u"क":
            self.trans[char] = u"x"
        for char in u"त":
            self.trans[char] = u"tr"
        for char in u"ज":
            self.trans[char] = u"gj"
        for char in u"क़":
            self.trans[char] = u"q"
        for char in u"फ":
            self.trans[char] = u"f"
        for char in u"ख":
            self.trans[char] = u"hh"
        for char in u"H":
            self.trans[char] = u"gh"
        for char in u"ज":
            self.trans[char] = u"z"
        for char in u"डढ":
            self.trans[char] = u"r"
        # Devanagari ligatures (possibly incomplete and/or incorrect)
        for char in u"ख्":
            self.trans[char] = u"khn"
        for char in u"त":
            self.trans[char] = u"tn"
        for char in u"द्":
            self.trans[char] = u"dn"
        for char in u"श":
            self.trans[char] = u"cn"
        for char in u"ह्":
            self.trans[char] = u"fn"
        for char in u"अँ":
            self.trans[char] = u"m"
        for char in u"॒॑":
            self.trans[char] = u""
        for char in u"०":
            self.trans[char] = u"0"
        for char in u"१":
            self.trans[char] = u"1"
        for char in u"२":
            self.trans[char] = u"2"
        for char in u"३":
            self.trans[char] = u"3"
        for char in u"४":
            self.trans[char] = u"4"
        for char in u"५":
            self.trans[char] = u"5"
        for char in u"६":
            self.trans[char] = u"6"
        for char in u"७":
            self.trans[char] = u"7"
        for char in u"८":
            self.trans[char] = u"8"
        for char in u"९":
            self.trans[char] = u"9"

        # Armenian
        for char in u"Ա":
            self.trans[char] = u"A"
        for char in u"ա":
            self.trans[char] = u"a"
        for char in u"Բ":
            self.trans[char] = u"B"
        for char in u"բ":
            self.trans[char] = u"b"
        for char in u"Գ":
            self.trans[char] = u"G"
        for char in u"գ":
            self.trans[char] = u"g"
        for char in u"Դ":
            self.trans[char] = u"D"
        for char in u"դ":
            self.trans[char] = u"d"
        for char in u"Ե":
            self.trans[char] = u"Je"
        for char in u"ե":
            self.trans[char] = u"e"
        for char in u"Զ":
            self.trans[char] = u"Z"
        for char in u"զ":
            self.trans[char] = u"z"
        for char in u"Է":
            self.trans[char] = u"É"
        for char in u"է":
            self.trans[char] = u"é"
        for char in u"Ը":
            self.trans[char] = u"Ë"
        for char in u"ը":
            self.trans[char] = u"ë"
        for char in u"Թ":
            self.trans[char] = u"Th"
        for char in u"թ":
            self.trans[char] = u"th"
        for char in u"Ժ":
            self.trans[char] = u"Zh"
        for char in u"ժ":
            self.trans[char] = u"zh"
        for char in u"Ի":
            self.trans[char] = u"I"
        for char in u"ի":
            self.trans[char] = u"i"
        for char in u"Լ":
            self.trans[char] = u"L"
        for char in u"լ":
            self.trans[char] = u"l"
        for char in u"Խ":
            self.trans[char] = u"Ch"
        for char in u"խ":
            self.trans[char] = u"ch"
        for char in u"Ծ":
            self.trans[char] = u"Ts"
        for char in u"ծ":
            self.trans[char] = u"ts"
        for char in u"Կ":
            self.trans[char] = u"K"
        for char in u"կ":
            self.trans[char] = u"k"
        for char in u"Հ":
            self.trans[char] = u"H"
        for char in u"հ":
            self.trans[char] = u"h"
        for char in u"Ձ":
            self.trans[char] = u"Dz"
        for char in u"ձ":
            self.trans[char] = u"dz"
        for char in u"Ղ":
            self.trans[char] = u"R"
        for char in u"ղ":
            self.trans[char] = u"r"
        for char in u"Ճ":
            self.trans[char] = u"Cz"
        for char in u"ճ":
            self.trans[char] = u"cz"
        for char in u"Մ":
            self.trans[char] = u"M"
        for char in u"մ":
            self.trans[char] = u"m"
        for char in u"Յ":
            self.trans[char] = u"J"
        for char in u"յ":
            self.trans[char] = u"j"
        for char in u"Ն":
            self.trans[char] = u"N"
        for char in u"ն":
            self.trans[char] = u"n"
        for char in u"Շ":
            self.trans[char] = u"S"
        for char in u"շ":
            self.trans[char] = u"s"
        for char in u"Շ":
            self.trans[char] = u"Vo"
        for char in u"շ":
            self.trans[char] = u"o"
        for char in u"Չ":
            self.trans[char] = u"Tsh"
        for char in u"չ":
            self.trans[char] = u"tsh"
        for char in u"Պ":
            self.trans[char] = u"P"
        for char in u"պ":
            self.trans[char] = u"p"
        for char in u"Ջ":
            self.trans[char] = u"Dz"
        for char in u"ջ":
            self.trans[char] = u"dz"
        for char in u"Ռ":
            self.trans[char] = u"R"
        for char in u"ռ":
            self.trans[char] = u"r"
        for char in u"Ս":
            self.trans[char] = u"S"
        for char in u"ս":
            self.trans[char] = u"s"
        for char in u"Վ":
            self.trans[char] = u"V"
        for char in u"վ":
            self.trans[char] = u"v"
        for char in u"Տ":
            self.trans[char] = u"T'"
        for char in u"տ":
            self.trans[char] = u"t'"
        for char in u"Ր":
            self.trans[char] = u"R"
        for char in u"ր":
            self.trans[char] = u"r"
        for char in u"Ց":
            self.trans[char] = u"Tsh"
        for char in u"ց":
            self.trans[char] = u"tsh"
        for char in u"Ւ":
            self.trans[char] = u"V"
        for char in u"ւ":
            self.trans[char] = u"v"
        for char in u"Փ":
            self.trans[char] = u"Ph"
        for char in u"փ":
            self.trans[char] = u"ph"
        for char in u"Ք":
            self.trans[char] = u"Kh"
        for char in u"ք":
            self.trans[char] = u"kh"
        for char in u"Օ":
            self.trans[char] = u"O"
        for char in u"օ":
            self.trans[char] = u"o"
        for char in u"Ֆ":
            self.trans[char] = u"F"
        for char in u"ֆ":
            self.trans[char] = u"f"
        for char in u"և":
            self.trans[char] = u"&"
        for char in u"՟":
            self.trans[char] = u"."
        for char in u"՞":
            self.trans[char] = u"?"
        for char in u"՝":
            self.trans[char] = u";"
        for char in u"՛":
            self.trans[char] = u""

        # Tamil
        for char in u"க்":
            self.trans[char] = u"k"
        for char in u"ஙண்ந்ன்":
            self.trans[char] = u"n"
        for char in u"ச":
            self.trans[char] = u"c"
        for char in u"ஞ்":
            self.trans[char] = u"ñ"
        for char in u"ட்":
            self.trans[char] = u"th"
        for char in u"த":
            self.trans[char] = u"t"
        for char in u"ப":
            self.trans[char] = u"p"
        for char in u"ம்":
            self.trans[char] = u"m"
        for char in u"ய்":
            self.trans[char] = u"y"
        for char in u"ர்ழ்ற":
            self.trans[char] = u"r"
        for char in u"ல்ள":
            self.trans[char] = u"l"
        for char in u"வ்":
            self.trans[char] = u"v"
        for char in u"ஜ":
            self.trans[char] = u"j"
        for char in u"ஷ":
            self.trans[char] = u"sh"
        for char in u"ஸ":
            self.trans[char] = u"s"
        for char in u"ஹ":
            self.trans[char] = u"h"
        for char in u"க்ஷ":
            self.trans[char] = u"x"
        for char in u"அ":
            self.trans[char] = u"a"
        for char in u"ஆ":
            self.trans[char] = u"aa"
        for char in u"இ":
            self.trans[char] = u"i"
        for char in u"ஈ":
            self.trans[char] = u"ii"
        for char in u"உ":
            self.trans[char] = u"u"
        for char in u"ஊ":
            self.trans[char] = u"uu"
        for char in u"எ":
            self.trans[char] = u"e"
        for char in u"ஏ":
            self.trans[char] = u"ee"
        for char in u"ஐ":
            self.trans[char] = u"ai"
        for char in u"ஒ":
            self.trans[char] = u"o"
        for char in u"ஓ":
            self.trans[char] = u"oo"
        for char in u"ஔ":
            self.trans[char] = u"au"
        for char in u"ஃ":
            self.trans[char] = ""

        # Bengali
        for char in u"অ":
            self.trans[char] = u"ô"
        for char in u"আা":
            self.trans[char] = u"a"
        for char in u"ইিঈী":
            self.trans[char] = u"i"
        for char in u"উুঊূ":
            self.trans[char] = u"u"
        for char in u"ঋৃ":
            self.trans[char] = u"ri"
        for char in u"এেয়":
            self.trans[char] = u"e"
        for char in u"ঐৈ":
            self.trans[char] = u"oi"
        for char in u"ওো":
            self.trans[char] = u"o"
        for char in u"ঔৌ":
            self.trans[char] = "ou"
        for char in u"্":
            self.trans[char] = u""
        for char in u"ৎ":
            self.trans[char] = u"t"
        for char in u"ং":
            self.trans[char] = u"n"
        for char in u"ঃ":
            self.trans[char] = u"h"
        for char in u"ঁ":
            self.trans[char] = u"ñ"
        for char in u"ক":
            self.trans[char] = u"k"
        for char in u"খ":
            self.trans[char] = u"kh"
        for char in u"গ":
            self.trans[char] = u"g"
        for char in u"ঘ":
            self.trans[char] = u"gh"
        for char in u"ঙ":
            self.trans[char] = u"ng"
        for char in u"চ":
            self.trans[char] = u"ch"
        for char in u"ছ":
            self.trans[char] = u"chh"
        for char in u"জ":
            self.trans[char] = u"j"
        for char in u"ঝ":
            self.trans[char] = u"jh"
        for char in u"ঞ":
            self.trans[char] = u"n"
        for char in u"টত":
            self.trans[char] = u"t"
        for char in u"ঠথ":
            self.trans[char] = u"th"
        for char in u"ডদ":
            self.trans[char] = u"d"
        for char in u"ঢধ":
            self.trans[char] = u"dh"
        for char in u"ণন":
            self.trans[char] = u"n"
        for char in u"প":
            self.trans[char] = u"p"
        for char in u"ফ":
            self.trans[char] = u"ph"
        for char in u"ব":
            self.trans[char] = u"b"
        for char in u"ভ":
            self.trans[char] = u"bh"
        for char in u"ম":
            self.trans[char] = u"m"
        for char in u"য":
            self.trans[char] = u"dzh"
        for char in u"র":
            self.trans[char] = u"r"
        for char in u"ল":
            self.trans[char] = u"l"
        for char in u"শ":
            self.trans[char] = u"s"
        for char in u"হ":
            self.trans[char] = u"h"
        for char in u"য়":
            self.trans[char] = u"-"
        for char in u"ড়":
            self.trans[char] = u"r"
        for char in u"ঢ":
            self.trans[char] = u"rh"
        for char in u"০":
            self.trans[char] = u"0"
        for char in u"১":
            self.trans[char] = u"1"
        for char in u"২":
            self.trans[char] = u"2"
        for char in u"৩":
            self.trans[char] = u"3"
        for char in u"৪":
            self.trans[char] = u"4"
        for char in u"৫":
            self.trans[char] = u"5"
        for char in u"৬":
            self.trans[char] = u"6"
        for char in u"৭":
            self.trans[char] = u"7"
        for char in u"৮":
            self.trans[char] = u"8"
        for char in u"৯":
            self.trans[char] = u"9"

        # Thai (because of complications of the alphabet, self.transliterations
        #       are very imprecise here)
        for char in u"ก":
            self.trans[char] = u"k"
        for char in u"ขฃคฅฆ":
            self.trans[char] = u"kh"
        for char in u"ง":
            self.trans[char] = u"ng"
        for char in u"จฉชฌ":
            self.trans[char] = u"ch"
        for char in u"ซศษส":
            self.trans[char] = u"s"
        for char in u"ญย":
            self.trans[char] = u"y"
        for char in u"ฎด":
            self.trans[char] = u"d"
        for char in u"ฏต":
            self.trans[char] = u"t"
        for char in u"ฐฑฒถทธ":
            self.trans[char] = u"th"
        for char in u"ณน":
            self.trans[char] = u"n"
        for char in u"บ":
            self.trans[char] = u"b"
        for char in u"ป":
            self.trans[char] = u"p"
        for char in u"ผพภ":
            self.trans[char] = u"ph"
        for char in u"ฝฟ":
            self.trans[char] = u"f"
        for char in u"ม":
            self.trans[char] = u"m"
        for char in u"ร":
            self.trans[char] = u"r"
        for char in u"ฤ":
            self.trans[char] = u"rue"
        for char in u"ๅ":
            self.trans[char] = u":"
        for char in u"ลฬ":
            self.trans[char] = u"l"
        for char in u"ฦ":
            self.trans[char] = u"lue"
        for char in u"ว":
            self.trans[char] = u"w"
        for char in u"หฮ":
            self.trans[char] = u"h"
        for char in u"อ":
            self.trans[char] = u""
        for char in u"ร":
            self.trans[char] = u"ü"
        for char in u"ว":
            self.trans[char] = u"ua"
        for char in u"อวโิ":
            self.trans[char] = u"o"
        for char in u"ะัา":
            self.trans[char] = u"a"
        for char in u"ว":
            self.trans[char] = u"u"
        for char in u"ำ":
            self.trans[char] = u"am"
        for char in u"ิ":
            self.trans[char] = u"i"
        for char in u"ี":
            self.trans[char] = u"i:"
        for char in u"ึ":
            self.trans[char] = u"ue"
        for char in u"ื":
            self.trans[char] = u"ue:"
        for char in u"ุ":
            self.trans[char] = u"u"
        for char in u"ู":
            self.trans[char] = u"u:"
        for char in u"เ็":
            self.trans[char] = u"e"
        for char in u"แ":
            self.trans[char] = u"ae"
        for char in u"ใไ":
            self.trans[char] = u"ai"
        for char in u"่้๊๋็์":
            self.trans[char] = u""
        for char in u"ฯ":
            self.trans[char] = u"."
        for char in u"ๆ":
            self.trans[char] = u"(2)"

        # Korean (Revised Romanization system within possible, incomplete)
        for char in u"국":
            self.trans[char] = u"guk"
        for char in u"명":
            self.trans[char] = u"myeong"
        for char in u"검":
            self.trans[char] = u"geom"
        for char in u"타":
            self.trans[char] = u"ta"
        for char in u"분":
            self.trans[char] = u"bun"
        for char in u"사":
            self.trans[char] = u"sa"
        for char in u"류":
            self.trans[char] = u"ryu"
        for char in u"포":
            self.trans[char] = u"po"
        for char in u"르":
            self.trans[char] = u"reu"
        for char in u"투":
            self.trans[char] = u"tu"
        for char in u"갈":
            self.trans[char] = u"gal"
        for char in u"어":
            self.trans[char] = u"eo"
        for char in u"노":
            self.trans[char] = u"no"
        for char in u"웨":
            self.trans[char] = u"we"
        for char in u"이":
            self.trans[char] = u"i"
        for char in u"라":
            self.trans[char] = u"ra"
        for char in u"틴":
            self.trans[char] = u"tin"
        for char in u"루":
            self.trans[char] = u"ru"
        for char in u"마":
            self.trans[char] = u"ma"
        for char in u"니":
            self.trans[char] = u"ni"
        for char in u"아":
            self.trans[char] = u"a"
        for char in u"독":
            self.trans[char] = u"dok"
        for char in u"일":
            self.trans[char] = u"il"
        for char in u"모":
            self.trans[char] = u"mo"
        for char in u"크":
            self.trans[char] = u"keu"
        for char in u"샤":
            self.trans[char] = u"sya"
        for char in u"영":
            self.trans[char] = u"yeong"
        for char in u"불":
            self.trans[char] = u"bul"
        for char in u"가":
            self.trans[char] = u"ga"
        for char in u"리":
            self.trans[char] = u"ri"
        for char in u"그":
            self.trans[char] = u"geu"
        for char in u"지":
            self.trans[char] = u"ji"
        for char in u"야":
            self.trans[char] = u"ya"
        for char in u"바":
            self.trans[char] = u"ba"
        for char in u"슈":
            self.trans[char] = u"syu"
        for char in u"키":
            self.trans[char] = u"ki"
        for char in u"프":
            self.trans[char] = u"peu"
        for char in u"랑":
            self.trans[char] = u"rang"
        for char in u"스":
            self.trans[char] = u"seu"
        for char in u"로":
            self.trans[char] = u"ro"
        for char in u"메":
            self.trans[char] = u"me"
        for char in u"역":
            self.trans[char] = u"yeok"
        for char in u"도":
            self.trans[char] = u"do"

        # Kannada
        self.trans[u"ಅ"] = u"a"
        for char in u"ಆಾ":
            self.trans[char] = u"aa"
        for char in u"ಇಿ":
            self.trans[char] = u"i"
        for char in u"ಈೀ":
            self.trans[char] = u"ii"
        for char in u"ಉು":
            self.trans[char] = u"u"
        for char in u"ಊೂ":
            self.trans[char] = u"uu"
        for char in u"ಋೂ":
            self.trans[char] = u"r'"
        for char in u"ಎೆ":
            self.trans[char] = u"e"
        for char in u"ಏೇ":
            self.trans[char] = u"ee"
        for char in u"ಐೈ":
            self.trans[char] = u"ai"
        for char in u"ಒೊ":
            self.trans[char] = u"o"
        for char in u"ಓೋ":
            self.trans[char] = u"oo"
        for char in u"ಔೌ":
            self.trans[char] = u"au"
        self.trans[u"ಂ"] = u"m'"
        self.trans[u"ಃ"] = u"h'"
        self.trans[u"ಕ"] = u"k"
        self.trans[u"ಖ"] = u"kh"
        self.trans[u"ಗ"] = u"g"
        self.trans[u"ಘ"] = u"gh"
        self.trans[u"ಙ"] = u"ng"
        self.trans[u"ಚ"] = u"c"
        self.trans[u"ಛ"] = u"ch"
        self.trans[u"ಜ"] = u"j"
        self.trans[u"ಝ"] = u"ny"
        self.trans[u"ಟ"] = u"tt"
        self.trans[u"ಠ"] = u"tth"
        self.trans[u"ಡ"] = u"dd"
        self.trans[u"ಢ"] = u"ddh"
        self.trans[u"ಣ"] = u"nn"
        self.trans[u"ತ"] = u"t"
        self.trans[u"ಥ"] = u"th"
        self.trans[u"ದ"] = u"d"
        self.trans[u"ಧ"] = u"dh"
        self.trans[u"ನ"] = u"n"
        self.trans[u"ಪ"] = u"p"
        self.trans[u"ಫ"] = u"ph"
        self.trans[u"ಬ"] = u"b"
        self.trans[u"ಭ"] = u"bh"
        self.trans[u"ಮ"] = u"m"
        self.trans[u"ಯ"] = u"y"
        self.trans[u"ರ"] = u"r"
        self.trans[u"ಲ"] = u"l"
        self.trans[u"ವ"] = u"v"
        self.trans[u"ಶ"] = u"sh"
        self.trans[u"ಷ"] = u"ss"
        self.trans[u"ಸ"] = u"s"
        self.trans[u"ಹ"] = u"h"
        self.trans[u"ಳ"] = u"ll"
        self.trans[u"೦"] = u"0"
        self.trans[u"೧"] = u"1"
        self.trans[u"೨"] = u"2"
        self.trans[u"೩"] = u"3"
        self.trans[u"೪"] = u"4"
        self.trans[u"೫"] = u"5"
        self.trans[u"೬"] = u"6"
        self.trans[u"೭"] = u"7"
        self.trans[u"೮"] = u"8"
        self.trans[u"೯"] = u"9"
        # Telugu
        for char in u"అ":
            self.trans[char] = u"a"
        for char in u"ఆా":
            self.trans[char] = u"aa"
        for char in u"ఇి":
            self.trans[char] = u"i"
        for char in u"ఈీ":
            self.trans[char] = u"ii"
        for char in u"ఉు":
            self.trans[char] = u"u"
        for char in u"ఊూ":
            self.trans[char] = u"uu"
        for char in u"ఋృ":
            self.trans[char] = u"r'"
        for char in u"ౠౄ":
            self.trans[char] = u'r"'
        self.trans[u"ఌ"] = u"l'"
        self.trans[u"ౡ"] = u'l"'
        for char in u"ఎె":
            self.trans[char] = u"e"
        for char in u"ఏే":
            self.trans[char] = u"ee"
        for char in u"ఐై":
            self.trans[char] = u"ai"
        for char in u"ఒొ":
            self.trans[char] = u"o"
        for char in u"ఓో":
            self.trans[char] = u"oo"
        for char in u"ఔౌ":
            self.trans[char] = u"au"
        self.trans[u"ం"] = u"'"
        self.trans[u"ః"] = u'"'
        self.trans[u"క"] = u"k"
        self.trans[u"ఖ"] = u"kh"
        self.trans[u"గ"] = u"g"
        self.trans[u"ఘ"] = u"gh"
        self.trans[u"ఙ"] = u"ng"
        self.trans[u"చ"] = u"ts"
        self.trans[u"ఛ"] = u"tsh"
        self.trans[u"జ"] = u"j"
        self.trans[u"ఝ"] = u"jh"
        self.trans[u"ఞ"] = u"ñ"
        for char in u"టత":
            self.trans[char] = u"t"
        for char in u"ఠథ":
            self.trans[char] = u"th"
        for char in u"డద":
            self.trans[char] = u"d"
        for char in u"ఢధ":
            self.trans[char] = u"dh"
        for char in u"ణన":
            self.trans[char] = u"n"
        self.trans[u"ప"] = u"p"
        self.trans[u"ఫ"] = u"ph"
        self.trans[u"బ"] = u"b"
        self.trans[u"భ"] = u"bh"
        self.trans[u"మ"] = u"m"
        self.trans[u"య"] = u"y"
        for char in u"రఱ":
            self.trans[char] = u"r"
        for char in u"లళ":
            self.trans[char] = u"l"
        self.trans[u"వ"] = u"v"
        self.trans[u"శ"] = u"sh"
        for char in u"షస":
            self.trans[char] = u"s"
        self.trans[u"హ"] = u"h"
        self.trans[u"్"] = ""
        for char in u"ంఁ":
            self.trans[char] = u"^"
        self.trans[u"ః"] = u"-"
        self.trans[u"౦"] = u"0"
        self.trans[u"౧"] = u"1"
        self.trans[u"౨"] = u"2"
        self.trans[u"౩"] = u"3"
        self.trans[u"౪"] = u"4"
        self.trans[u"౫"] = u"5"
        self.trans[u"౬"] = u"6"
        self.trans[u"౭"] = u"7"
        self.trans[u"౮"] = u"8"
        self.trans[u"౯"] = u"9"
        self.trans[u"౹"] = u"1/4"
        self.trans[u"౺"] = u"1/2"
        self.trans[u"౻"] = u"3/4"
        self.trans[u"౼"] = u"1/16"
        self.trans[u"౽"] = u"1/8"
        self.trans[u"౾"] = u"3/16"
        # Lao - note: pronounciation in initial position is used;
        # different pronounciation in final position is ignored
        self.trans[u"ກ"] = "k"
        for char in u"ຂຄ":
            self.trans[char] = "kh"
        self.trans[u"ງ"] = "ng"
        self.trans[u"ຈ"] = "ch"
        for char in u"ສຊ":
            self.trans[char] = "s"
        self.trans[u"ຍ"] = "ny"
        self.trans[u"ດ"] = "d"
        self.trans[u"ຕ"] = "t"
        for char in u"ຖທ":
            self.trans[char] = "th"
        self.trans[u"ນ"] = "n"
        self.trans[u"ບ"] = "b"
        self.trans[u"ປ"] = "p"
        for char in u"ຜພ":
            self.trans[char] = "ph"
        for char in u"ຝຟ":
            self.trans[char] = "f"
        for char in u"ມໝ":
            self.trans[char] = "m"
        self.trans[u"ຢ"] = "y"
        for char in u"ຣຼ":
            self.trans[char] = "r"
        for char in u"ລຼ":
            self.trans[char] = "l"
        self.trans[u"ວ"] = "v"
        for char in u"ຮ":
            self.trans[char] = "h"
        self.trans[u"ອ"] = "'"
        for char in u"ະັ":
            self.trans[char] = "a"
        self.trans[u"ິ"] = "i"
        self.trans[u"ຶ"] = "ue"
        self.trans[u"ຸ"] = "u"
        self.trans[u"ເ"] = u"é"
        self.trans[u"ແ"] = u"è"
        for char in u"ໂົາໍ":
            self.trans[char] = "o"
        self.trans[u"ຽ"] = "ia"
        self.trans[u"ເຶ"] = "uea"
        self.trans[u"ຍ"] = "i"
        for char in u"ໄໃ":
            self.trans[char] = "ai"
        self.trans[u"ຳ"] = "am"
        self.trans[u"າ"] = "aa"
        self.trans[u"ີ"] = "ii"
        self.trans[u"ື"] = "yy"
        self.trans[u"ູ"] = "uu"
        self.trans[u"ເ"] = "e"
        self.trans[u"ແ"] = "ei"
        self.trans[u"໐"] = "0"
        self.trans[u"໑"] = "1"
        self.trans[u"໒"] = "2"
        self.trans[u"໓"] = "3"
        self.trans[u"໔"] = "4"
        self.trans[u"໕"] = "5"
        self.trans[u"໖"] = "6"
        self.trans[u"໗"] = "7"
        self.trans[u"໘"] = "8"
        self.trans[u"໙"] = "9"
        # Chinese -- note: incomplete
        for char in u"埃挨哎唉哀皑癌蔼矮艾碍爱隘":
            self.trans[char] = u"ai"
        for char in u"鞍氨安俺按暗岸胺案":
            self.trans[char] = u"an"
        for char in u"肮昂盎":
            self.trans[char] = u"ang"
        for char in u"凹敖熬翱袄傲奥懊澳":
            self.trans[char] = u"ao"
        for char in u"芭捌扒叭吧笆八疤巴拔跋靶把耙坝霸罢爸":
            self.trans[char] = u"ba"
        for char in u"白柏百摆佰败拜稗":
            self.trans[char] = u"bai"
        for char in u"斑班搬扳般颁板版扮拌伴瓣半办绊":
            self.trans[char] = u"ban"
        for char in u"邦帮梆榜膀绑棒磅蚌镑傍谤":
            self.trans[char] = u"bang"
        for char in u"苞胞包褒剥薄雹保堡饱宝抱报暴豹鲍爆":
            self.trans[char] = u"bao"
        for char in u"杯碑悲卑北辈背贝钡倍狈备惫焙被":
            self.trans[char] = u"bei"
        for char in u"奔苯本笨":
            self.trans[char] = u"ben"
        for char in u"崩绷甭泵蹦迸":
            self.trans[char] = u"beng"
        for char in u"逼鼻比鄙笔彼碧蓖蔽毕毙毖币庇痹闭敝弊必辟壁臂避陛":
            self.trans[char] = u"bi"
        for char in u"鞭边编贬扁便变卞辨辩辫遍":
            self.trans[char] = u"bian"
        for char in u"标彪膘表":
            self.trans[char] = u"biao"
        for char in u"鳖憋别瘪":
            self.trans[char] = u"bie"
        for char in u"彬斌濒滨宾摈":
            self.trans[char] = u"bin"
        for char in u"兵冰柄丙秉饼炳病并":
            self.trans[char] = u"bing"
        for char in u"玻菠播拨钵波博勃搏铂箔伯帛舶脖膊渤泊驳捕卜亳":
            self.trans[char] = u"bo"
        for char in u"哺补埠不布步簿部怖":
            self.trans[char] = u"bu"
        for char in u"猜裁材才财睬踩采彩菜蔡":
            self.trans[char] = u"cai"
        for char in u"餐参蚕残惭惨灿":
            self.trans[char] = u"can"
        for char in u"苍舱仓沧藏":
            self.trans[char] = u"cang"
        for char in u"操糙槽曹草":
            self.trans[char] = u"cao"
        for char in u"厕策侧册测":
            self.trans[char] = u"ce"
        for char in u"层蹭":
            self.trans[char] = u"ceng"
        for char in u"插叉茬茶查碴搽察岔差诧":
            self.trans[char] = u"cha"
        for char in u"拆柴豺":
            self.trans[char] = u"chai"
        for char in u"搀掺蝉馋谗缠铲产阐颤":
            self.trans[char] = u"chan"
        for char in u"昌猖场尝常长偿肠厂敞畅唱倡":
            self.trans[char] = u"chang"
        for char in u"超抄钞朝嘲潮巢吵炒":
            self.trans[char] = u"chao"
        for char in u"车扯撤掣彻澈":
            self.trans[char] = u"che"
        for char in u"郴臣辰尘晨忱沉陈趁衬":
            self.trans[char] = u"chen"
        for char in u"撑称城橙成呈乘程惩澄诚承逞骋秤":
            self.trans[char] = u"cheng"
        for char in u"吃痴持匙池迟弛驰耻齿侈尺赤翅斥炽":
            self.trans[char] = u"chi"
        for char in u"充冲虫崇宠":
            self.trans[char] = u"chong"
        for char in u"抽酬畴踌稠愁筹仇绸瞅丑臭":
            self.trans[char] = u"chou"
        for char in u"初出橱厨躇锄雏滁除楚储矗搐触处":
            self.trans[char] = u"chu"
        for char in u"揣":
            self.trans[char] = u"chuai"
        for char in u"川穿椽传船喘串":
            self.trans[char] = u"chuan"
        for char in u"疮窗幢床闯创":
            self.trans[char] = u"chuang"
        for char in u"吹炊捶锤垂":
            self.trans[char] = u"chui"
        for char in u"春椿醇唇淳纯蠢":
            self.trans[char] = u"chun"
        for char in u"戳绰":
            self.trans[char] = u"chuo"
        for char in u"疵茨磁雌辞慈瓷词此刺赐次":
            self.trans[char] = u"ci"
        for char in u"聪葱囱匆从丛":
            self.trans[char] = u"cong"
        for char in u"凑":
            self.trans[char] = u"cou"
        for char in u"粗醋簇促":
            self.trans[char] = u"cu"
        for char in u"蹿篡窜":
            self.trans[char] = u"cuan"
        for char in u"摧崔催脆瘁粹淬翠":
            self.trans[char] = u"cui"
        for char in u"村存寸":
            self.trans[char] = u"cun"
        for char in u"磋撮搓措挫错":
            self.trans[char] = u"cuo"
        for char in u"搭达答瘩打大":
            self.trans[char] = u"da"
        for char in u"呆歹傣戴带殆代贷袋待逮怠":
            self.trans[char] = u"dai"
        for char in u"耽担丹单郸掸胆旦氮但惮淡诞弹蛋儋":
            self.trans[char] = u"dan"
        for char in u"当挡党荡档":
            self.trans[char] = u"dang"
        for char in u"刀捣蹈倒岛祷导到稻悼道盗":
            self.trans[char] = u"dao"
        for char in u"德得的":
            self.trans[char] = u"de"
        for char in u"蹬灯登等瞪凳邓":
            self.trans[char] = u"deng"
        for char in u"堤低滴迪敌笛狄涤翟嫡抵底地蒂第帝弟递缔":
            self.trans[char] = u"di"
        for char in u"颠掂滇碘点典靛垫电佃甸店惦奠淀殿":
            self.trans[char] = u"dian"
        for char in u"碉叼雕凋刁掉吊钓调":
            self.trans[char] = u"diao"
        for char in u"跌爹碟蝶迭谍叠":
            self.trans[char] = u"die"
        for char in u"丁盯叮钉顶鼎锭定订":
            self.trans[char] = u"ding"
        for char in u"丢":
            self.trans[char] = u"diu"
        for char in u"东冬董懂动栋侗恫冻洞":
            self.trans[char] = u"dong"
        for char in u"兜抖斗陡豆逗痘":
            self.trans[char] = u"dou"
        for char in u"都督毒犊独读堵睹赌杜镀肚度渡妒":
            self.trans[char] = u"du"
        for char in u"端短锻段断缎":
            self.trans[char] = u"duan"
        for char in u"堆兑队对":
            self.trans[char] = u"dui"
        for char in u"墩吨蹲敦顿囤钝盾遁":
            self.trans[char] = u"dun"
        for char in u"掇哆多夺垛躲朵跺舵剁惰堕":
            self.trans[char] = u"duo"
        for char in u"蛾峨鹅俄额讹娥恶厄扼遏鄂饿":
            self.trans[char] = u"e"
        for char in u"恩嗯":
            self.trans[char] = u"en"
        for char in u"而儿耳尔饵洱二贰":
            self.trans[char] = u"er"
        for char in u"发罚筏伐乏阀法珐":
            self.trans[char] = u"fa"
        for char in u"藩帆番翻樊矾钒繁凡烦反返范贩犯饭泛":
            self.trans[char] = u"fan"
        for char in u"坊芳方肪房防妨仿访纺放":
            self.trans[char] = u"fang"
        for char in u"菲非啡飞肥匪诽吠肺废沸费":
            self.trans[char] = u"fei"
        for char in u"芬酚吩氛分纷坟焚汾粉奋份忿愤粪":
            self.trans[char] = u"fen"
        for char in u"丰封枫蜂峰锋风疯烽逢冯缝讽奉凤":
            self.trans[char] = u"feng"
        for char in u"佛":
            self.trans[char] = u"fo"
        for char in u"否":
            self.trans[char] = u"fou"
        for char in u"夫敷肤孵扶拂辐幅氟符伏俘服浮涪福袱弗甫抚辅俯釜斧脯腑府腐赴副覆赋复傅付阜父腹负富讣附妇缚咐":
            self.trans[char] = u"fu"
        for char in u"噶嘎":
            self.trans[char] = u"ga"
        for char in u"该改概钙盖溉":
            self.trans[char] = u"gai"
        for char in u"干甘杆柑竿肝赶感秆敢赣":
            self.trans[char] = u"gan"
        for char in u"冈刚钢缸肛纲岗港杠":
            self.trans[char] = u"gang"
        for char in u"篙皋高膏羔糕搞镐稿告":
            self.trans[char] = u"gao"
        for char in u"哥歌搁戈鸽胳疙割革葛格蛤阁隔铬个各":
            self.trans[char] = u"ge"
        for char in u"给":
            self.trans[char] = u"gei"
        for char in u"根跟":
            self.trans[char] = u"gen"
        for char in u"耕更庚羹埂耿梗":
            self.trans[char] = u"geng"
        for char in u"工攻功恭龚供躬公宫弓巩汞拱贡共":
            self.trans[char] = u"gong"
        for char in u"钩勾沟苟狗垢构购够":
            self.trans[char] = u"gou"
        for char in u"辜菇咕箍估沽孤姑鼓古蛊骨谷股故顾固雇":
            self.trans[char] = u"gu"
        for char in u"刮瓜剐寡挂褂":
            self.trans[char] = u"gua"
        for char in u"乖拐怪":
            self.trans[char] = u"guai"
        for char in u"棺关官冠观管馆罐惯灌贯":
            self.trans[char] = u"guan"
        for char in u"光广逛":
            self.trans[char] = u"guang"
        for char in u"瑰规圭硅归龟闺轨鬼诡癸桂柜跪贵刽":
            self.trans[char] = u"gui"
        for char in u"辊滚棍":
            self.trans[char] = u"gun"
        for char in u"锅郭国果裹过":
            self.trans[char] = u"guo"
        for char in u"哈":
            self.trans[char] = u"ha"
        for char in u"骸孩海氦亥害骇":
            self.trans[char] = u"hai"
        for char in u"酣憨邯韩含涵寒函喊罕翰撼捍旱憾悍焊汗汉":
            self.trans[char] = u"han"
        for char in u"夯杭航":
            self.trans[char] = u"hang"
        for char in u"壕嚎豪毫郝好耗号浩":
            self.trans[char] = u"hao"
        for char in u"呵喝荷菏核禾和何合盒貉阂河涸赫褐鹤贺":
            self.trans[char] = u"he"
        for char in u"嘿黑":
            self.trans[char] = u"hei"
        for char in u"痕很狠恨":
            self.trans[char] = u"hen"
        for char in u"哼亨横衡恒":
            self.trans[char] = u"heng"
        for char in u"轰哄烘虹鸿洪宏弘红":
            self.trans[char] = u"hong"
        for char in u"喉侯猴吼厚候后":
            self.trans[char] = u"hou"
        for char in u"呼乎忽瑚壶葫胡蝴狐糊湖弧虎唬护互沪户":
            self.trans[char] = u"hu"
        for char in u"花哗华猾滑画划化话":
            self.trans[char] = u"hua"
        for char in u"槐徊怀淮坏":
            self.trans[char] = u"huai"
        for char in u"欢环桓还缓换患唤痪豢焕涣宦幻":
            self.trans[char] = u"huan"
        for char in u"荒慌黄磺蝗簧皇凰惶煌晃幌恍谎":
            self.trans[char] = u"huang"
        for char in u"灰挥辉徽恢蛔回毁悔慧卉惠晦贿秽会烩汇讳诲绘":
            self.trans[char] = u"hui"
        for char in u"荤昏婚魂浑混":
            self.trans[char] = u"hun"
        for char in u"豁活伙火获或惑霍货祸":
            self.trans[char] = u"huo"
        for char in u"击圾基机畸稽积箕肌饥迹激讥鸡姬绩缉吉极棘辑籍集及急疾汲即嫉级挤几脊己蓟技冀季伎祭剂悸济寄寂计记既忌际妓继纪":
            self.trans[char] = u"ji"
        for char in u"嘉枷夹佳家加荚颊贾甲钾假稼价架驾嫁":
            self.trans[char] = u"jia"
        for char in u"歼监坚尖笺间煎兼肩艰奸缄茧检柬碱硷拣捡简俭剪减荐槛鉴践贱见键箭件健舰剑饯渐溅涧建":
            self.trans[char] = u"jian"
        for char in u"僵姜将浆江疆蒋桨奖讲匠酱降":
            self.trans[char] = u"jiang"
        for char in u"蕉椒礁焦胶交郊浇骄娇嚼搅铰矫侥脚狡角饺缴绞剿教酵轿较叫窖":
            self.trans[char] = u"jiao"
        for char in u"揭接皆秸街阶截劫节桔杰捷睫竭洁结解姐戒藉芥界借介疥诫届":
            self.trans[char] = u"jie"
        for char in u"巾筋斤金今津襟紧锦仅谨进靳晋禁近烬浸尽劲":
            self.trans[char] = u"jin"
        for char in u"荆兢茎睛晶鲸京惊精粳经井警景颈静境敬镜径痉靖竟竞净":
            self.trans[char] = u"jing"
        for char in u"囧炯窘":
            self.trans[char] = u"jiong"
        for char in u"揪究纠玖韭久灸九酒厩救旧臼舅咎就疚":
            self.trans[char] = u"jiu"
        for char in u"鞠拘狙疽居驹菊局咀矩举沮聚拒据巨具距踞锯俱句惧炬剧":
            self.trans[char] = u"ju"
        for char in u"捐鹃娟倦眷卷绢":
            self.trans[char] = u"juan"
        for char in u"撅攫抉掘倔爵觉决诀绝":
            self.trans[char] = u"jue"
        for char in u"均菌钧军君峻俊竣浚郡骏":
            self.trans[char] = u"jun"
        for char in u"喀咖卡咯":
            self.trans[char] = u"ka"
        for char in u"开揩楷凯慨":
            self.trans[char] = u"kai"
        for char in u"刊堪勘坎砍看":
            self.trans[char] = u"kan"
        for char in u"康慷糠扛抗亢炕":
            self.trans[char] = u"kang"
        for char in u"考拷烤靠":
            self.trans[char] = u"kao"
        for char in u"坷苛柯棵磕颗科壳咳可渴克刻客课":
            self.trans[char] = u"ke"
        for char in u"肯啃垦恳":
            self.trans[char] = u"ken"
        for char in u"坑吭":
            self.trans[char] = u"keng"
        for char in u"空恐孔控":
            self.trans[char] = u"kong"
        for char in u"抠口扣寇":
            self.trans[char] = u"kou"
        for char in u"枯哭窟苦酷库裤":
            self.trans[char] = u"ku"
        for char in u"夸垮挎跨胯":
            self.trans[char] = u"kua"
        for char in u"块筷侩快":
            self.trans[char] = u"kuai"
        for char in u"宽款":
            self.trans[char] = u"kuan"
        for char in u"匡筐狂框矿眶旷况":
            self.trans[char] = u"kuang"
        for char in u"亏盔岿窥葵奎魁傀馈愧溃":
            self.trans[char] = u"kui"
        for char in u"坤昆捆困":
            self.trans[char] = u"kun"
        for char in u"括扩廓阔":
            self.trans[char] = u"kuo"
        for char in u"垃拉喇蜡腊辣啦":
            self.trans[char] = u"la"
        for char in u"莱来赖":
            self.trans[char] = u"lai"
        for char in u"蓝婪栏拦篮阑兰澜谰揽览懒缆烂滥":
            self.trans[char] = u"lan"
        for char in u"琅榔狼廊郎朗浪":
            self.trans[char] = u"lang"
        for char in u"捞劳牢老佬姥酪烙涝":
            self.trans[char] = u"lao"
        for char in u"勒乐":
            self.trans[char] = u"le"
        for char in u"雷镭蕾磊累儡垒擂肋类泪":
            self.trans[char] = u"lei"
        for char in u"棱楞冷":
            self.trans[char] = u"leng"
        for char in u"厘梨犁黎篱狸离漓理李里鲤礼莉荔吏栗丽厉励砾历利傈例俐痢立粒沥隶力璃哩":
            self.trans[char] = u"li"
        for char in u"俩":
            self.trans[char] = u"lia"
        for char in u"联莲连镰廉怜涟帘敛脸链恋炼练":
            self.trans[char] = u"lian"
        for char in u"粮凉梁粱良两辆量晾亮谅":
            self.trans[char] = u"liang"
        for char in u"撩聊僚疗燎寥辽潦了撂镣廖料":
            self.trans[char] = u"liao"
        for char in u"列裂烈劣猎":
            self.trans[char] = u"lie"
        for char in u"琳林磷霖临邻鳞淋凛赁吝拎":
            self.trans[char] = u"lin"
        for char in u"玲菱零龄铃伶羚凌灵陵岭领另令":
            self.trans[char] = u"ling"
        for char in u"溜琉榴硫馏留刘瘤流柳六":
            self.trans[char] = u"liu"
        for char in u"龙聋咙笼窿隆垄拢陇":
            self.trans[char] = u"long"
        for char in u"楼娄搂篓漏陋":
            self.trans[char] = u"lou"
        for char in u"芦卢颅庐炉掳卤虏鲁麓碌露路赂鹿潞禄录陆戮泸":
            self.trans[char] = u"lu"
        for char in u"峦挛孪滦卵乱":
            self.trans[char] = u"luan"
        for char in u"掠略":
            self.trans[char] = u"lue"
        for char in u"抡轮伦仑沦纶论":
            self.trans[char] = u"lun"
        for char in u"萝螺罗逻锣箩骡裸落洛骆络漯":
            self.trans[char] = u"luo"
        for char in u"驴吕铝侣旅履屡缕虑氯律率滤绿":
            self.trans[char] = u"lv"
        for char in u"妈麻玛码蚂马骂嘛吗":
            self.trans[char] = u"ma"
        for char in u"埋买麦卖迈脉":
            self.trans[char] = u"mai"
        for char in u"瞒馒蛮满蔓曼慢漫谩":
            self.trans[char] = u"man"
        for char in u"芒茫盲氓忙莽":
            self.trans[char] = u"mang"
        for char in u"猫茅锚毛矛铆卯茂冒帽貌贸":
            self.trans[char] = u"mao"
        for char in u"么":
            self.trans[char] = u"me"
        for char in u"玫枚梅酶霉煤没眉媒镁每美昧寐妹媚":
            self.trans[char] = u"mei"
        for char in u"门闷们":
            self.trans[char] = u"men"
        for char in u"萌蒙檬盟锰猛梦孟":
            self.trans[char] = u"meng"
        for char in u"眯醚靡糜迷谜弥米秘觅泌蜜密幂":
            self.trans[char] = u"mi"
        for char in u"棉眠绵冕免勉娩缅面":
            self.trans[char] = u"mian"
        for char in u"苗描瞄藐秒渺庙妙":
            self.trans[char] = u"miao"
        for char in u"蔑灭":
            self.trans[char] = u"mie"
        for char in u"民抿皿敏悯闽":
            self.trans[char] = u"min"
        for char in u"明螟鸣铭名命":
            self.trans[char] = u"ming"
        for char in u"谬":
            self.trans[char] = u"miu"
        for char in u"摸摹蘑模膜磨摩魔抹末莫墨默沫漠寞陌":
            self.trans[char] = u"mo"
        for char in u"谋牟某":
            self.trans[char] = u"mou"
        for char in u"拇牡亩姆母墓暮幕募慕木目睦牧穆":
            self.trans[char] = u"mu"
        for char in u"拿哪呐钠那娜纳":
            self.trans[char] = u"na"
        for char in u"氖乃奶耐奈":
            self.trans[char] = u"nai"
        for char in u"南男难":
            self.trans[char] = u"nan"
        for char in u"囊":
            self.trans[char] = u"nang"
        for char in u"挠脑恼闹淖":
            self.trans[char] = u"nao"
        for char in u"呢":
            self.trans[char] = u"ne"
        for char in u"馁内":
            self.trans[char] = u"nei"
        for char in u"嫩":
            self.trans[char] = u"nen"
        for char in u"能":
            self.trans[char] = u"neng"
        for char in u"妮霓倪泥尼拟你匿腻逆溺":
            self.trans[char] = u"ni"
        for char in u"蔫拈年碾撵捻念":
            self.trans[char] = u"nian"
        for char in u"娘酿":
            self.trans[char] = u"niang"
        for char in u"鸟尿":
            self.trans[char] = u"niao"
        for char in u"捏聂孽啮镊镍涅":
            self.trans[char] = u"nie"
        for char in u"您":
            self.trans[char] = u"nin"
        for char in u"柠狞凝宁拧泞":
            self.trans[char] = u"ning"
        for char in u"牛扭钮纽":
            self.trans[char] = u"niu"
        for char in u"脓浓农弄":
            self.trans[char] = u"nong"
        for char in u"奴努怒":
            self.trans[char] = u"nu"
        for char in u"暖":
            self.trans[char] = u"nuan"
        for char in u"虐疟":
            self.trans[char] = u"nue"
        for char in u"挪懦糯诺":
            self.trans[char] = u"nuo"
        for char in u"女":
            self.trans[char] = u"nv"
        for char in u"哦":
            self.trans[char] = u"o"
        for char in u"欧鸥殴藕呕偶沤":
            self.trans[char] = u"ou"
        for char in u"啪趴爬帕怕琶":
            self.trans[char] = u"pa"
        for char in u"拍排牌徘湃派":
            self.trans[char] = u"pai"
        for char in u"攀潘盘磐盼畔判叛":
            self.trans[char] = u"pan"
        for char in u"乓庞旁耪胖":
            self.trans[char] = u"pang"
        for char in u"抛咆刨炮袍跑泡":
            self.trans[char] = u"pao"
        for char in u"呸胚培裴赔陪配佩沛":
            self.trans[char] = u"pei"
        for char in u"喷盆":
            self.trans[char] = u"pen"
        for char in u"砰抨烹澎彭蓬棚硼篷膨朋鹏捧碰":
            self.trans[char] = u"peng"
        for char in u"坯砒霹批披劈琵毗啤脾疲皮匹痞僻屁譬":
            self.trans[char] = u"pi"
        for char in u"篇偏片骗":
            self.trans[char] = u"pian"
        for char in u"飘漂瓢票":
            self.trans[char] = u"piao"
        for char in u"撇瞥":
            self.trans[char] = u"pie"
        for char in u"拼频贫品聘":
            self.trans[char] = u"pin"
        for char in u"乒坪苹萍平凭瓶评屏":
            self.trans[char] = u"ping"
        for char in u"坡泼颇婆破魄迫粕剖":
            self.trans[char] = u"po"
        for char in u"扑铺仆莆葡菩蒲埔朴圃普浦谱曝瀑濮":
            self.trans[char] = u"pu"
        for char in u"期欺栖戚妻七凄漆柒沏其棋奇歧畦崎脐齐旗祈祁骑起岂乞企启契砌器气迄弃汽泣讫":
            self.trans[char] = u"qi"
        for char in u"掐恰洽":
            self.trans[char] = u"qia"
        for char in u"牵扦钎铅千迁签仟谦乾黔钱钳前潜遣浅谴堑嵌欠歉":
            self.trans[char] = u"qian"
        for char in u"枪呛腔羌墙蔷强抢":
            self.trans[char] = u"qiang"
        for char in u"橇锹敲悄桥瞧乔侨巧鞘撬翘峭俏窍":
            self.trans[char] = u"qiao"
        for char in u"切茄且怯窃":
            self.trans[char] = u"qie"
        for char in u"钦侵亲秦琴勤芹擒禽寝沁":
            self.trans[char] = u"qin"
        for char in u"青轻氢倾卿清擎晴氰情顷请庆":
            self.trans[char] = u"qing"
        for char in u"琼穷":
            self.trans[char] = u"qiong"
        for char in u"秋丘邱球求囚酋泅":
            self.trans[char] = u"qiu"
        for char in u"趋区蛆曲躯屈驱渠取娶龋趣去":
            self.trans[char] = u"qu"
        for char in u"圈颧权醛泉全痊拳犬券劝":
            self.trans[char] = u"quan"
        for char in u"缺炔瘸却鹊榷确雀":
            self.trans[char] = u"que"
        for char in u"裙群":
            self.trans[char] = u"qun"
        for char in u"然燃冉染":
            self.trans[char] = u"ran"
        for char in u"瓤壤攘嚷让":
            self.trans[char] = u"rang"
        for char in u"饶扰绕":
            self.trans[char] = u"rao"
        for char in u"惹热":
            self.trans[char] = u"re"
        for char in u"壬仁人忍韧任认刃妊纫":
            self.trans[char] = u"ren"
        for char in u"扔仍":
            self.trans[char] = u"reng"
        for char in u"日":
            self.trans[char] = u"ri"
        for char in u"戎茸蓉荣融熔溶容绒冗":
            self.trans[char] = u"rong"
        for char in u"揉柔肉":
            self.trans[char] = u"rou"
        for char in u"茹蠕儒孺如辱乳汝入褥":
            self.trans[char] = u"ru"
        for char in u"软阮":
            self.trans[char] = u"ruan"
        for char in u"蕊瑞锐":
            self.trans[char] = u"rui"
        for char in u"闰润":
            self.trans[char] = u"run"
        for char in u"若弱":
            self.trans[char] = u"ruo"
        for char in u"撒洒萨":
            self.trans[char] = u"sa"
        for char in u"腮鳃塞赛":
            self.trans[char] = u"sai"
        for char in u"三叁伞散":
            self.trans[char] = u"san"
        for char in u"桑嗓丧":
            self.trans[char] = u"sang"
        for char in u"搔骚扫嫂":
            self.trans[char] = u"sao"
        for char in u"瑟色涩":
            self.trans[char] = u"se"
        for char in u"森":
            self.trans[char] = u"sen"
        for char in u"僧":
            self.trans[char] = u"seng"
        for char in u"莎砂杀刹沙纱傻啥煞":
            self.trans[char] = u"sha"
        for char in u"筛晒":
            self.trans[char] = u"shai"
        for char in u"珊苫杉山删煽衫闪陕擅赡膳善汕扇缮":
            self.trans[char] = u"shan"
        for char in u"墒伤商赏晌上尚裳":
            self.trans[char] = u"shang"
        for char in u"梢捎稍烧芍勺韶少哨邵绍":
            self.trans[char] = u"shao"
        for char in u"奢赊蛇舌舍赦摄射慑涉社设":
            self.trans[char] = u"she"
        for char in u"砷申呻伸身深娠绅神沈审婶甚肾慎渗":
            self.trans[char] = u"shen"
        for char in u"声生甥牲升绳省盛剩胜圣":
            self.trans[char] = u"sheng"
        for char in u"师失狮施湿诗尸虱十石拾时什食蚀实识史矢使屎驶始式示士世柿事拭誓逝势是嗜噬适仕侍释饰氏市恃室视试":
            self.trans[char] = u"shi"
        for char in u"收手首守寿授售受瘦兽":
            self.trans[char] = u"shou"
        for char in u"蔬枢梳殊抒输叔舒淑疏书赎孰熟薯暑曙署蜀黍鼠属术述树束戍竖墅庶数漱恕":
            self.trans[char] = u"shu"
        for char in u"刷耍":
            self.trans[char] = u"shua"
        for char in u"摔衰甩帅":
            self.trans[char] = u"shuai"
        for char in u"栓拴":
            self.trans[char] = u"shuan"
        for char in u"霜双爽":
            self.trans[char] = u"shuang"
        for char in u"谁水睡税":
            self.trans[char] = u"shui"
        for char in u"吮瞬顺舜":
            self.trans[char] = u"shun"
        for char in u"说硕朔烁":
            self.trans[char] = u"shuo"
        for char in u"斯撕嘶思私司丝死肆寺嗣四伺似饲巳":
            self.trans[char] = u"si"
        for char in u"松耸怂颂送宋讼诵":
            self.trans[char] = u"song"
        for char in u"搜艘擞":
            self.trans[char] = u"sou"
        for char in u"嗽苏酥俗素速粟僳塑溯宿诉肃":
            self.trans[char] = u"su"
        for char in u"酸蒜算":
            self.trans[char] = u"suan"
        for char in u"虽隋随绥髓碎岁穗遂隧祟":
            self.trans[char] = u"sui"
        for char in u"孙损笋":
            self.trans[char] = u"sun"
        for char in u"蓑梭唆缩琐索锁所":
            self.trans[char] = u"suo"
        for char in u"塌他它她塔獭挞蹋踏":
            self.trans[char] = u"ta"
        for char in u"胎苔抬台泰酞太态汰":
            self.trans[char] = u"tai"
        for char in u"坍摊贪瘫滩坛檀痰潭谭谈坦毯袒碳探叹炭":
            self.trans[char] = u"tan"
        for char in u"汤塘搪堂棠膛唐糖倘躺淌趟烫":
            self.trans[char] = u"tang"
        for char in u"掏涛滔绦萄桃逃淘陶讨套":
            self.trans[char] = u"tao"
        for char in u"特":
            self.trans[char] = u"te"
        for char in u"藤腾疼誊":
            self.trans[char] = u"teng"
        for char in u"梯剔踢锑提题蹄啼体替嚏惕涕剃屉":
            self.trans[char] = u"ti"
        for char in u"兲天添填田甜恬舔腆":
            self.trans[char] = u"tian"
        for char in u"挑条迢眺跳":
            self.trans[char] = u"tiao"
        for char in u"贴铁帖":
            self.trans[char] = u"tie"
        for char in u"厅听烃汀廷停亭庭挺艇":
            self.trans[char] = u"ting"
        for char in u"通桐酮瞳同铜彤童桶捅筒统痛":
            self.trans[char] = u"tong"
        for char in u"偷投头透":
            self.trans[char] = u"tou"
        for char in u"凸秃突图徒途涂屠土吐兔":
            self.trans[char] = u"tu"
        for char in u"湍团":
            self.trans[char] = u"tuan"
        for char in u"推颓腿蜕褪退":
            self.trans[char] = u"tui"
        for char in u"吞屯臀":
            self.trans[char] = u"tun"
        for char in u"拖托脱鸵陀驮驼椭妥拓唾":
            self.trans[char] = u"tuo"
        for char in u"挖哇蛙洼娃瓦袜":
            self.trans[char] = u"wa"
        for char in u"歪外":
            self.trans[char] = u"wai"
        for char in u"豌弯湾玩顽丸烷完碗挽晚皖惋宛婉万腕莞":
            self.trans[char] = u"wan"
        for char in u"汪王亡枉网往旺望忘妄":
            self.trans[char] = u"wang"
        for char in u"威巍微危韦违桅围唯惟为潍维苇萎委伟伪尾纬未蔚味畏胃喂魏位渭谓尉慰卫":
            self.trans[char] = u"wei"
        for char in u"瘟温蚊文闻纹吻稳紊问":
            self.trans[char] = u"wen"
        for char in u"嗡翁瓮":
            self.trans[char] = u"weng"
        for char in u"挝蜗涡窝我斡卧握沃":
            self.trans[char] = u"wo"
        for char in u"巫呜钨乌污诬屋无芜梧吾吴毋武五捂午舞伍侮坞戊雾晤物勿务悟误":
            self.trans[char] = u"wu"
        for char in u"昔熙析西硒矽晰嘻吸锡牺稀息希悉膝夕惜熄烯溪汐犀檄袭席习媳喜铣洗系隙戏细":
            self.trans[char] = u"xi"
        for char in u"瞎虾匣霞辖暇峡侠狭下厦夏吓":
            self.trans[char] = u"xia"
        for char in u"掀锨先仙鲜纤咸贤衔舷闲涎弦嫌显险现献县腺馅羡宪陷限线":
            self.trans[char] = u"xian"
        for char in u"相厢镶香箱襄湘乡翔祥详想响享项巷橡像向象":
            self.trans[char] = u"xiang"
        for char in u"萧硝霄削哮嚣销消宵淆晓小孝校肖啸笑效":
            self.trans[char] = u"xiao"
        for char in u"楔些歇蝎鞋协挟携邪斜胁谐写械卸蟹懈泄泻谢屑":
            self.trans[char] = u"xie"
        for char in u"薪芯锌欣辛新忻心信衅":
            self.trans[char] = u"xin"
        for char in u"星腥猩惺兴刑型形邢行醒幸杏性姓":
            self.trans[char] = u"xing"
        for char in u"兄凶胸匈汹雄熊":
            self.trans[char] = u"xiong"
        for char in u"休修羞朽嗅锈秀袖绣":
            self.trans[char] = u"xiu"
        for char in u"墟戌需虚嘘须徐许蓄酗叙旭序畜恤絮婿绪续":
            self.trans[char] = u"xu"
        for char in u"轩喧宣悬旋玄选癣眩绚":
            self.trans[char] = u"xuan"
        for char in u"靴薛学穴雪血":
            self.trans[char] = u"xue"
        for char in u"勋熏循旬询寻驯巡殉汛训讯逊迅":
            self.trans[char] = u"xun"
        for char in u"压押鸦鸭呀丫芽牙蚜崖衙涯雅哑亚讶":
            self.trans[char] = u"ya"
        for char in u"焉咽阉烟淹盐严研蜒岩延言颜阎炎沿奄掩眼衍演艳堰燕厌砚雁唁彦焰宴谚验":
            self.trans[char] = u"yan"
        for char in u"殃央鸯秧杨扬佯疡羊洋阳氧仰痒养样漾":
            self.trans[char] = u"yang"
        for char in u"邀腰妖瑶摇尧遥窑谣姚咬舀药要耀":
            self.trans[char] = u"yao"
        for char in u"椰噎耶爷野冶也页掖业叶曳腋夜液":
            self.trans[char] = u"ye"
        for char in u"一壹医揖铱依伊衣颐夷遗移仪胰疑沂宜姨彝椅蚁倚已乙矣以艺抑易邑屹亿役臆逸肄疫亦裔意毅忆义益溢诣议谊译异翼翌绎":
            self.trans[char] = u"yi"
        for char in u"茵荫因殷音阴姻吟银淫寅饮尹引隐印":
            self.trans[char] = u"yin"
        for char in u"英樱婴鹰应缨莹萤营荧蝇迎赢盈影颖硬映":
            self.trans[char] = u"ying"
        for char in u"哟":
            self.trans[char] = u"yo"
        for char in u"拥佣臃痈庸雍踊蛹咏泳涌永恿勇用":
            self.trans[char] = u"yong"
        for char in u"幽优悠忧尤由邮铀犹油游酉有友右佑釉诱又幼迂":
            self.trans[char] = u"you"
        for char in u"淤于盂榆虞愚舆余俞逾鱼愉渝渔隅予娱雨与屿禹宇语羽玉域芋郁吁遇喻峪御愈欲狱育誉浴寓裕预豫驭":
            self.trans[char] = u"yu"
        for char in u"鸳渊冤元垣袁原援辕园员圆猿源缘远苑愿怨院":
            self.trans[char] = u"yuan"
        for char in u"曰约越跃钥岳粤月悦阅":
            self.trans[char] = u"yue"
        for char in u"耘云郧匀陨允运蕴酝晕韵孕":
            self.trans[char] = u"yun"
        for char in u"匝砸杂":
            self.trans[char] = u"za"
        for char in u"栽哉灾宰载再在":
            self.trans[char] = u"zai"
        for char in u"咱攒暂赞":
            self.trans[char] = u"zan"
        for char in u"赃脏葬":
            self.trans[char] = u"zang"
        for char in u"遭糟凿藻枣早澡蚤躁噪造皂灶燥":
            self.trans[char] = u"zao"
        for char in u"责择则泽":
            self.trans[char] = u"ze"
        for char in u"贼":
            self.trans[char] = u"zei"
        for char in u"怎":
            self.trans[char] = u"zen"
        for char in u"增憎曾赠":
            self.trans[char] = u"zeng"
        for char in u"扎喳渣札轧铡闸眨栅榨咋乍炸诈":
            self.trans[char] = u"zha"
        for char in u"摘斋宅窄债寨":
            self.trans[char] = u"zhai"
        for char in u"瞻毡詹粘沾盏斩辗崭展蘸栈占战站湛绽":
            self.trans[char] = u"zhan"
        for char in u"樟章彰漳张掌涨杖丈帐账仗胀瘴障":
            self.trans[char] = u"zhang"
        for char in u"招昭找沼赵照罩兆肇召":
            self.trans[char] = u"zhao"
        for char in u"遮折哲蛰辙者锗蔗这浙":
            self.trans[char] = u"zhe"
        for char in u"珍斟真甄砧臻贞针侦枕疹诊震振镇阵圳":
            self.trans[char] = u"zhen"
        for char in u"蒸挣睁征狰争怔整拯正政帧症郑证":
            self.trans[char] = u"zheng"
        for char in u"芝枝支吱蜘知肢脂汁之织职直植殖执值侄址指止趾只旨纸志挚掷至致置帜峙制智秩稚质炙痔滞治窒":
            self.trans[char] = u"zhi"
        for char in u"中盅忠钟衷终种肿重仲众":
            self.trans[char] = u"zhong"
        for char in u"舟周州洲诌粥轴肘帚咒皱宙昼骤":
            self.trans[char] = u"zhou"
        for char in u"珠株蛛朱猪诸诛逐竹烛煮拄瞩嘱主著柱助蛀贮铸筑住注祝驻":
            self.trans[char] = u"zhu"
        for char in u"抓爪":
            self.trans[char] = u"zhua"
        for char in u"拽":
            self.trans[char] = u"zhuai"
        for char in u"专砖转撰赚篆":
            self.trans[char] = u"zhuan"
        for char in u"桩庄装妆撞壮状":
            self.trans[char] = u"zhuang"
        for char in u"椎锥追赘坠缀":
            self.trans[char] = u"zhui"
        for char in u"谆准":
            self.trans[char] = u"zhun"
        for char in u"捉拙卓桌琢茁酌啄着灼浊":
            self.trans[char] = u"zhuo"
        for char in u"兹咨资姿滋淄孜紫仔籽滓子自渍字":
            self.trans[char] = u"zi"
        for char in u"鬃棕踪宗综总纵":
            self.trans[char] = u"zong"
        for char in u"邹走奏揍":
            self.trans[char] = u"zou"
        for char in u"租足卒族祖诅阻组":
            self.trans[char] = u"zu"
        for char in u"钻纂":
            self.trans[char] = u"zuan"
        for char in u"嘴醉最罪":
            self.trans[char] = u"zui"
        for char in u"尊遵":
            self.trans[char] = u"zun"
        for char in u"昨左佐柞做作坐座":
            self.trans[char] = u"zuo"
        # from: https://www.wikidata.org/wiki/MediaWiki:Gadget-SimpleTransliterate.js
        self.trans[u"ଂ"] = "anusvara"
        self.trans[u"ઇ"] = "i"
        self.trans[u"എ"] = "e"
        self.trans[u"ગ"] = "ga"
        self.trans[u"ਜ"] = "ja"
        self.trans[u"ഞ"] = "nya"
        self.trans[u"ଢ"] = "ddha"
        self.trans[u"ધ"] = "dha"
        self.trans[u"ਬ"] = "ba"
        self.trans[u"മ"] = "ma"
        self.trans[u"ଲ"] = "la"
        self.trans[u"ષ"] = "ssa"
        self.trans[u"਼"] = "nukta"
        self.trans[u"ാ"] = "aa"
        self.trans[u"ୂ"] = "uu"
        self.trans[u"ે"] = "e"
        self.trans[u"ੌ"] = "au"
        self.trans[u"ൎ"] = "reph"
        self.trans[u"ੜ"] = "rra"
        self.trans[u"՞"] = "?"
        self.trans[u"ୢ"] = "l"
        self.trans[u"૧"] = "1"
        self.trans[u"੬"] = "6"
        self.trans[u"൮"] = "8"
        self.trans[u"୲"] = "quarter"
        self.trans[u"ൾ"] = "ll"
        self.trans[u"ਇ"] = "i"
        self.trans[u"ഉ"] = "u"
        self.trans[u"ઌ"] = "l"
        self.trans[u"ਗ"] = "ga"
        self.trans[u"ങ"] = "nga"
        self.trans[u"ଝ"] = "jha"
        self.trans[u"જ"] = "ja"
        self.trans[u"؟"] = "?"
        self.trans[u"ਧ"] = "dha"
        self.trans[u"ഩ"] = "nnna"
        self.trans[u"ଭ"] = "bha"
        self.trans[u"બ"] = "ba"
        self.trans[u"ഹ"] = "ha"
        self.trans[u"ଽ"] = "avagraha"
        self.trans[u"઼"] = "nukta"
        self.trans[u"ੇ"] = "ee"
        self.trans[u"୍"] = "virama"
        self.trans[u"ૌ"] = "au"
        self.trans[u"੧"] = "1"
        self.trans[u"൩"] = "3"
        self.trans[u"୭"] = "7"
        self.trans[u"૬"] = "6"
        self.trans[u"൹"] = "mark"
        self.trans[u"ਖ਼"] = "khha"
        self.trans[u"ਂ"] = "bindi"
        self.trans[u"ഈ"] = "ii"
        self.trans[u"ઍ"] = "e"
        self.trans[u"ଌ"] = "l"
        self.trans[u"ഘ"] = "gha"
        self.trans[u"ઝ"] = "jha"
        self.trans[u"ଡ଼"] = "rra"
        self.trans[u"ਢ"] = "ddha"
        self.trans[u"ന"] = "na"
        self.trans[u"ભ"] = "bha"
        self.trans[u"ବ"] = "ba"
        self.trans[u"ਲ"] = "la"
        self.trans[u"സ"] = "sa"
        self.trans[u"ઽ"] = "avagraha"
        self.trans[u"଼"] = "nukta"
        self.trans[u"ੂ"] = "uu"
        self.trans[u"ൈ"] = "ai"
        self.trans[u"્"] = "virama"
        self.trans[u"ୌ"] = "au"
        self.trans[u"൨"] = "2"
        self.trans[u"૭"] = "7"
        self.trans[u"୬"] = "6"
        self.trans[u"ੲ"] = "iri"
        self.trans[u"ഃ"] = "visarga"
        self.trans[u"ં"] = "anusvara"
        self.trans[u"ଇ"] = "i"
        self.trans[u"ഓ"] = "oo"
        self.trans[u"ଗ"] = "ga"
        self.trans[u"ਝ"] = "jha"
        self.trans[u"？"] = "?"
        self.trans[u"ണ"] = "nna"
        self.trans[u"ઢ"] = "ddha"
        self.trans[u"ଧ"] = "dha"
        self.trans[u"ਭ"] = "bha"
        self.trans[u"ള"] = "lla"
        self.trans[u"લ"] = "la"
        self.trans[u"ଷ"] = "ssa"
        self.trans[u"ൃ"] = "r"
        self.trans[u"ૂ"] = "uu"
        self.trans[u"େ"] = "e"
        self.trans[u"੍"] = "virama"
        self.trans[u"ୗ"] = "mark"
        self.trans[u"ൣ"] = "ll"
        self.trans[u"ૢ"] = "l"
        self.trans[u"୧"] = "1"
        self.trans[u"੭"] = "7"
        self.trans[u"൳"] = "1/4"
        self.trans[u"୷"] = "sixteenths"
        self.trans[u"ଆ"] = "aa"
        self.trans[u"ઋ"] = "r"
        self.trans[u"ഊ"] = "uu"
        self.trans[u"ਐ"] = "ai"
        self.trans[u"ଖ"] = "kha"
        self.trans[u"છ"] = "cha"
        self.trans[u"ച"] = "ca"
        self.trans[u"ਠ"] = "ttha"
        self.trans[u"ଦ"] = "da"
        self.trans[u"ફ"] = "pha"
        self.trans[u"പ"] = "pa"
        self.trans[u"ਰ"] = "ra"
        self.trans[u"ଶ"] = "sha"
        self.trans[u"ഺ"] = "ttta"
        self.trans[u"ੀ"] = "ii"
        self.trans[u"ો"] = "o"
        self.trans[u"ൊ"] = "o"
        self.trans[u"ୖ"] = "mark"
        self.trans[u"୦"] = "0"
        self.trans[u"૫"] = "5"
        self.trans[u"൪"] = "4"
        self.trans[u"ੰ"] = "tippi"
        self.trans[u"୶"] = "eighth"
        self.trans[u"ൺ"] = "nn"
        self.trans[u"ଁ"] = "candrabindu"
        self.trans[u"അ"] = "a"
        self.trans[u"ઐ"] = "ai"
        self.trans[u"ക"] = "ka"
        self.trans[u"ਸ਼"] = "sha"
        self.trans[u"ਛ"] = "cha"
        self.trans[u"ଡ"] = "dda"
        self.trans[u"ઠ"] = "ttha"
        self.trans[u"ഥ"] = "tha"
        self.trans[u"ਫ"] = "pha"
        self.trans[u"ર"] = "ra"
        self.trans[u"വ"] = "va"
        self.trans[u"ୁ"] = "u"
        self.trans[u"ી"] = "ii"
        self.trans[u"ੋ"] = "oo"
        self.trans[u"ૐ"] = "om"
        self.trans[u"ୡ"] = "ll"
        self.trans[u"ૠ"] = "rr"
        self.trans[u"੫"] = "5"
        self.trans[u"ୱ"] = "wa"
        self.trans[u"૰"] = "sign"
        self.trans[u"൵"] = "quarters"
        self.trans[u"ਫ਼"] = "fa"
        self.trans[u"ઁ"] = "candrabindu"
        self.trans[u"ਆ"] = "aa"
        self.trans[u"ઑ"] = "o"
        self.trans[u"ଐ"] = "ai"
        self.trans[u"ഔ"] = "au"
        self.trans[u"ਖ"] = "kha"
        self.trans[u"ડ"] = "dda"
        self.trans[u"ଠ"] = "ttha"
        self.trans[u"ത"] = "ta"
        self.trans[u"ਦ"] = "da"
        self.trans[u"ର"] = "ra"
        self.trans[u"ഴ"] = "llla"
        self.trans[u"ુ"] = "u"
        self.trans[u"ୀ"] = "ii"
        self.trans[u"ൄ"] = "rr"
        self.trans[u"ૡ"] = "ll"
        self.trans[u"ୠ"] = "rr"
        self.trans[u"੦"] = "0"
        self.trans[u"૱"] = "sign"
        self.trans[u"୰"] = "isshar"
        self.trans[u"൴"] = "1/2"
        self.trans[u"ਁ"] = "bindi"
        self.trans[u"આ"] = "aa"
        self.trans[u"ଋ"] = "r"
        self.trans[u"ഏ"] = "ee"
        self.trans[u"ખ"] = "kha"
        self.trans[u"ଛ"] = "cha"
        self.trans[u"ട"] = "tta"
        self.trans[u"ਡ"] = "dda"
        self.trans[u"દ"] = "da"
        self.trans[u"ଫ"] = "pha"
        self.trans[u"യ"] = "ya"
        self.trans[u"શ"] = "sha"
        self.trans[u"ി"] = "i"
        self.trans[u"ੁ"] = "u"
        self.trans[u"ୋ"] = "o"
        self.trans[u"ੑ"] = "udaat"
        self.trans[u"૦"] = "0"
        self.trans[u"୫"] = "5"
        self.trans[u"൯"] = "9"
        self.trans[u"ੱ"] = "addak"
        self.trans[u"ൿ"] = "k"
        self.trans[u"ആ"] = "aa"
        self.trans[u"ଊ"] = "uu"
        self.trans[u"એ"] = "e"
        self.trans[u"ਔ"] = "au"
        self.trans[u"ഖ"] = "kha"
        self.trans[u"ଚ"] = "ca"
        self.trans[u"ટ"] = "tta"
        self.trans[u"ਤ"] = "ta"
        self.trans[u"ദ"] = "da"
        self.trans[u"ପ"] = "pa"
        self.trans[u"ય"] = "ya"
        self.trans[u"ശ"] = "sha"
        self.trans[u"િ"] = "i"
        self.trans[u"െ"] = "e"
        self.trans[u"൦"] = "0"
        self.trans[u"୪"] = "4"
        self.trans[u"૯"] = "9"
        self.trans[u"ੴ"] = "onkar"
        self.trans[u"ଅ"] = "a"
        self.trans[u"ਏ"] = "ee"
        self.trans[u"କ"] = "ka"
        self.trans[u"ઔ"] = "au"
        self.trans[u"ਟ"] = "tta"
        self.trans[u"ഡ"] = "dda"
        self.trans[u"ଥ"] = "tha"
        self.trans[u"ત"] = "ta"
        self.trans[u"ਯ"] = "ya"
        self.trans[u"റ"] = "rra"
        self.trans[u"ଵ"] = "va"
        self.trans[u"ਿ"] = "i"
        self.trans[u"ു"] = "u"
        self.trans[u"ૄ"] = "rr"
        self.trans[u"ൡ"] = "ll"
        self.trans[u"੯"] = "9"
        self.trans[u"൱"] = "100"
        self.trans[u"୵"] = "sixteenth"
        self.trans[u"અ"] = "a"
        self.trans[u"ਊ"] = "uu"
        self.trans[u"ഐ"] = "ai"
        self.trans[u"ક"] = "ka"
        self.trans[u"ଔ"] = "au"
        self.trans[u"ਚ"] = "ca"
        self.trans[u"ഠ"] = "ttha"
        self.trans[u"થ"] = "tha"
        self.trans[u"ତ"] = "ta"
        self.trans[u"ਪ"] = "pa"
        self.trans[u"ര"] = "ra"
        self.trans[u"વ"] = "va"
        self.trans[u"ീ"] = "ii"
        self.trans[u"ૅ"] = "e"
        self.trans[u"ୄ"] = "rr"
        self.trans[u"ൠ"] = "rr"
        self.trans[u"ਜ਼"] = "za"
        self.trans[u"੪"] = "4"
        self.trans[u"൰"] = "10"
        self.trans[u"୴"] = "quarters"
        self.trans[u"ਅ"] = "a"
        self.trans[u"ഋ"] = "r"
        self.trans[u"ઊ"] = "uu"
        self.trans[u"ଏ"] = "e"
        self.trans[u"ਕ"] = "ka"
        self.trans[u"ഛ"] = "cha"
        self.trans[u"ચ"] = "ca"
        self.trans[u"ଟ"] = "tta"
        self.trans[u"ਥ"] = "tha"
        self.trans[u"ഫ"] = "pha"
        self.trans[u"પ"] = "pa"
        self.trans[u"ଯ"] = "ya"
        self.trans[u"ਵ"] = "va"
        self.trans[u"ି"] = "i"
        self.trans[u"ോ"] = "oo"
        self.trans[u"ୟ"] = "yya"
        self.trans[u"൫"] = "5"
        self.trans[u"૪"] = "4"
        self.trans[u"୯"] = "9"
        self.trans[u"ੵ"] = "yakash"
        self.trans[u"ൻ"] = "n"
        self.trans[u"ઃ"] = "visarga"
        self.trans[u"ം"] = "anusvara"
        self.trans[u"ਈ"] = "ii"
        self.trans[u"ઓ"] = "o"
        self.trans[u"ഒ"] = "o"
        self.trans[u"ਘ"] = "gha"
        self.trans[u"ଞ"] = "nya"
        self.trans[u"ણ"] = "nna"
        self.trans[u"ഢ"] = "ddha"
        self.trans[u"ਲ਼"] = "lla"
        self.trans[u"ਨ"] = "na"
        self.trans[u"ମ"] = "ma"
        self.trans[u"ળ"] = "lla"
        self.trans[u"ല"] = "la"
        self.trans[u"ਸ"] = "sa"
        self.trans[u"¿"] = "?"
        self.trans[u"ା"] = "aa"
        self.trans[u"ૃ"] = "r"
        self.trans[u"ൂ"] = "uu"
        self.trans[u"ੈ"] = "ai"
        self.trans[u"ૣ"] = "ll"
        self.trans[u"ൢ"] = "l"
        self.trans[u"੨"] = "2"
        self.trans[u"୮"] = "8"
        self.trans[u"൲"] = "1000"
        self.trans[u"ਃ"] = "visarga"
        self.trans[u"ଉ"] = "u"
        self.trans[u"ઈ"] = "ii"
        self.trans[u"ਓ"] = "oo"
        self.trans[u"ଙ"] = "nga"
        self.trans[u"ઘ"] = "gha"
        self.trans[u"ഝ"] = "jha"
        self.trans[u"ਣ"] = "nna"
        self.trans[u"ન"] = "na"
        self.trans[u"ഭ"] = "bha"
        self.trans[u"ଜ"] = "ja"
        self.trans[u"ହ"] = "ha"
        self.trans[u"સ"] = "sa"
        self.trans[u"ഽ"] = "avagraha"
        self.trans[u"ૈ"] = "ai"
        self.trans[u"്"] = "virama"
        self.trans[u"୩"] = "3"
        self.trans[u"૨"] = "2"
        self.trans[u"൭"] = "7"
        self.trans[u"ੳ"] = "ura"
        self.trans[u"ൽ"] = "l"
        self.trans[u"ઉ"] = "u"
        self.trans[u"ଈ"] = "ii"
        self.trans[u"ഌ"] = "l"
        self.trans[u"ઙ"] = "nga"
        self.trans[u"ଘ"] = "gha"
        self.trans[u"ജ"] = "ja"
        self.trans[u"ਞ"] = "nya"
        self.trans[u"ନ"] = "na"
        self.trans[u"ബ"] = "ba"
        self.trans[u"ਮ"] = "ma"
        self.trans[u"હ"] = "ha"
        self.trans[u"ସ"] = "sa"
        self.trans[u"ਾ"] = "aa"
        self.trans[u"ૉ"] = "o"
        self.trans[u"ୈ"] = "ai"
        self.trans[u"ൌ"] = "au"
        self.trans[u"૩"] = "3"
        self.trans[u"୨"] = "2"
        self.trans[u"൬"] = "6"
        self.trans[u"੮"] = "8"
        self.trans[u"ർ"] = "rr"
        self.trans[u"ଃ"] = "visarga"
        self.trans[u"ഇ"] = "i"
        self.trans[u"ਉ"] = "u"
        self.trans[u"ଓ"] = "o"
        self.trans[u"ഗ"] = "ga"
        self.trans[u"ਙ"] = "nga"
        self.trans[u"ઞ"] = "nya"
        self.trans[u"ଣ"] = "nna"
        self.trans[u"ധ"] = "dha"
        self.trans[u"મ"] = "ma"
        self.trans[u"ଳ"] = "lla"
        self.trans[u"ഷ"] = "ssa"
        self.trans[u"ਹ"] = "ha"
        self.trans[u"ਗ਼"] = "ghha"
        self.trans[u"ા"] = "aa"
        self.trans[u"ୃ"] = "r"
        self.trans[u"േ"] = "ee"
        self.trans[u"ൗ"] = "mark"
        self.trans[u"ଢ଼"] = "rha"
        self.trans[u"ୣ"] = "ll"
        self.trans[u"൧"] = "1"
        self.trans[u"੩"] = "3"
        self.trans[u"૮"] = "8"
        self.trans[u"୳"] = "half"
        for char in self.trans:
            value = self.trans[char]
            if value == "?":
                continue
            while value.encode(encoding, 'replace').decode(encoding) == "?" and value in self.trans:
                assert value != self.trans[value], "%r == self.trans[%r]!" % (value, value)
                value = self.trans[value]
            self.trans[char] = value

    def transliterate(self, char, default="?", prev="-", next="-"):
        if char in self.trans:
            return self.trans[char]
        # Arabic
        if char == u"◌":
            return prev
        # Japanese
        if char == u"ッ":
            return self.transliterate(next)[0]
        if char in u"々仝ヽヾゝゞ〱〲〳〵〴〵":
            return prev
        # Lao
        if char == u"ຫ":
            if next in u"ງຍນຣລຼຼວ":
                return ""
            else:
                return "h"
        return default
