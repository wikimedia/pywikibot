# -*- coding: utf-8  -*-
__version__ = '$Id$'


class transliterator(object):
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

        #Punctuation and typography
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
        self.trans.update({u"А" : u"A", u"а" : u"a", u"Б" : u"B", u"б" : u"b",
                      u"В" : u"V", u"в" : u"v", u"Г" : u"G", u"г" : u"g",
                      u"Д" : u"D", u"д" : u"d", u"Е" : u"E", u"е" : u"e",
                      u"Ж" : u"Zh", u"ж" : u"zh", u"З" : u"Z", u"з" : u"z",
                      u"И" : u"I", u"и" : u"i", u"Й" : u"J", u"й" : u"j",
                      u"К" : u"K", u"к" : u"k", u"Л" : u"L", u"л" : u"l",
                      u"М" : u"M", u"м" : u"m", u"Н" : u"N", u"н" : u"n",
                      u"О" : u"O", u"о" : u"o", u"П" : u"P", u"п" : u"p",
                      u"Р" : u"R", u"р" : u"r", u"С" : u"S", u"с" : u"s",
                      u"Т" : u"T", u"т" : u"t", u"У" : u"U", u"у" : u"u",
                      u"Ф" : u"F", u"ф" : u"f", u"х" : u"kh", u"Ц" : u"C",
                      u"ц" : u"c", u"Ч" : u"Ch", u"ч" : u"ch", u"Ш" : u"Sh",
                      u"ш" : u"sh", u"Щ" : u"Shch", u"щ" : u"shch", u"Ь" : u"'",
                      u"ь" : "'", u"Ъ" : u'"', u"ъ" : '"', u"Ю" : u"Yu",
                      u"ю" : u"yu", u"Я" : u"Ya", u"я" : u"ya", u"Х" : u"Kh",
                      u"Χ" : u"Kh"})

        # Additional Cyrillic letters, most occuring in only one or a few languages
        self.trans.update({u"Ы" : u"Y", u"ы" : u"y", u"Ё" : u"Ë", u"ё" : u"ë",
                      u"Э" : u"È", u"Ѐ" : u"È", u"э" : u"è", u"ѐ" : u"è",
                      u"І" : u"I", u"і" : u"i", u"Ї" : u"Ji", u"ї" : u"ji",
                      u"Є" : u"Je", u"є" : u"je", u"Ґ" : u"G", u"Ҝ" : u"G",
                      u"ґ" : u"g", u"ҝ" : u"g", u"Ђ" : u"Dj", u"ђ" : u"dj",
                      u"Ӣ" : u"Y", u"ӣ" : u"y", u"Љ" : u"Lj", u"љ" : u"lj",
                      u"Њ" : u"Nj", u"њ" : u"nj", u"Ћ" : u"Cj", u"ћ" : u"cj",
                      u"Җ" : u"Zhj", u"җ" : u"zhj", u"Ѓ" : u"Gj", u"ѓ" : u"gj",
                      u"Ќ" : u"Kj", u"ќ" : u"kj", u"Ӣ" : u"Ii", u"ӣ" : u"ii",
                      u"Ӯ" : u"U", u"ӯ" : u"u", u"Ҳ" : u"H", u"ҳ" : u"h",
                      u"Ҷ" : u"Dz",u"ҷ" : u"dz", u"Ө" :u"Ô", u"Ӫ" : u"Ô",
                      u"ө" : u"ô", u"ӫ" : u"ô", u"Ү": u"Y", u"ү": u"y", u"Һ": u"H",
                      u"һ": u"h", u"Ә": u"AE", u"Ӕ": u"AE", u"ә": u"ae",
                      u"Ӛ": u"Ë", u"Ӭ": u"Ë", u"ӛ": u"ë", u"ӭ": u"ë", u"Җ": u"Zhj",
                      u"җ": u"zhj", u"Ұ": u"U", u"ұ": u"u", u"ў": u"ù", u"Ў": u"Ù",
                      u"ѝ": u"ì", u"Ѝ": u"Ì", u"Ӑ": u"A", u"ă": u"a", u"Ӓ": u"Ä",
                      u"ҿ": u"ä", u"Ҽ" : u"Ts", u"Ҿ": u"Ts", u"ҽ": u"ts", u"ҿ": u"ts",
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
            self.trans[char] = u"" # indicates absence of vowels
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
        for char in u"თ":#
            self.trans[char] = u"th"
        for char in u"ი":
            self.trans[char] = u"i"
        for char in u"კ":#
            self.trans[char] = u"k"
        for char in u"ლ":
            self.trans[char] = u"l"
        for char in u"მ":
            self.trans[char] = u"m"
        for char in u"ნ":
            self.trans[char] = u"n"
        for char in u"ო":
            self.trans[char] = u"o"
        for char in u"პ":#
            self.trans[char] = u"p"
        for char in u"ჟ":#
            self.trans[char] = u"zh"
        for char in u"რ":
            self.trans[char] = u"r"
        for char in u"ს":
            self.trans[char] = u"s"
        for char in u"ტ":#
            self.trans[char] = u"t"
        for char in u"უ":
            self.trans[char] = u"u"
        for char in u"ფ":#
            self.trans[char] = u"ph"
        for char in u"ქ":#
            self.trans[char] = u"q"
        for char in u"ღ":#
            self.trans[char] = u"gh"
        for char in u"ყ":#
            self.trans[char] = u"q'"
        for char in u"შ":
            self.trans[char] = u"sh"
        for char in u"ჩ":
            self.trans[char] = u"ch"
        for char in u"ც":
            self.trans[char] = u"ts"
        for char in u"ძ":
            self.trans[char] = u"dz"
        for char in u"წ":#
            self.trans[char] = u"ts'"
        for char in u"ჭ":#
            self.trans[char] = u"ch'"
        for char in u"ხ":
            self.trans[char] = u"kh"
        for char in u"ჯ":#
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
        for char in self.trans:
            value = self.trans[char]
            if value == "?": continue
            while value.encode(encoding, 'replace').decode(encoding) == "?" and value in self.trans:
                assert value != self.trans[value], "%r == self.trans[%r]!" % (value, value)
                value = self.trans[value]
            self.trans[char] = value
        
    def transliterate(self, char, default="?", prev="-", next="-"):
        if char in self.trans:
            return self.trans[char]
        #Arabic
        if char == u"◌":
            return prev
        #Japanese
        if char == u"ッ":
            return self.transliterate(next)[0]
        if char in u"々仝ヽヾゝゞ〱〲〳〵〴〵":
            return prev
        #Lao
        if char == u"ຫ":
            if next in u"ງຍນຣລຼຼວ":
                return ""
            else:
                return "h"
        return default

