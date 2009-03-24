# -*- coding: utf-8 -*-
#
# (C) Pywikipedia bot team, 2006-2008
#
# Distributed under the terms of the MIT license.
#
def trans(char, default = '?', prev = '-', next = '-'):
    # Give a transliteration for char, or default if none is known
    # Accented etc. Latin characters
    if char in u"ÀÁÂẦẤẪẨẬÃĀĂẰẮẴẶẲȦǠẠḀȂĄǍẢ":
        return u"A"
    if char in u"ȀǞ":
        return u"Ä"
    if char == u"Ǻ":
        return u"Å"
    if char == u"Ä":
        return u"Ae"
    if char == u"Å":
        return u"Aa"
    if char in u"àáâầấẫẩậãāăằắẵặẳȧǡạḁȃąǎảẚ":
        return u"a"
    if char in u"ȁǟ":
        return u"ä"
    if char == u"ǻ":
        return u"å"
    if char == u"ä":
        return u"ae"
    if char == u"å":
        return u"aa"
    if char in u"ḂḄḆƁƂ":
        return u"B"
    if char in u"ḃḅḇƀɓƃ":
        return u"b"
    if char in u"ĆĈĊÇČƇ":
        return u"C"
    if char in u"ćĉċçčƈȼ":
        return u"c"
    if char == u"Ḉ":
        return u"Ç"
    if char == u"ḉ":
        return u"ç"
    if char == u"Ð":
        return u"Dh"
    if char == u"ð":
        return u"dh"    
    if char in u"ĎḊḌḎḐḒĐƉƊƋ":
        return u"D"
    if char in u"ďḋḍḏḑḓđɖɗƌ":
        return u"d"
    if char in u"ÈȄÉÊḚËĒḔḖĔĖẸE̩ȆȨḜĘĚẼḘẺ":
        return u"E"
    if char in u"ỀẾỄỆỂ":
        return u"Ê"
    if char in u"èȅéêḛëēḕḗĕėẹe̩ȇȩḝęěẽḙẻ":
        return u"e"
    if char in u"ềếễệể":
        return u"ê"
    if char in u"ḞƑ":
        return u"F"
    if char in u"ḟƒ":
        return u"f"
    if char in u"ǴḠĞĠĢǦǤƓ":
        return u"G"
    if char in u"ǵḡğġģǧǥɠ":
        return u"g"
    if char == u"Ĝ":
        return u"Gx"
    if char == u"ĝ":
        return u"gx"
    if char in u"ḢḤḦȞḨḪH̱ĦǶ":
        return u"H"
    if char in u"ḣḥḧȟḩḫ̱ẖħƕ":
        return u"h"
    if char in u"IÌȈÍÎĨḬÏḮĪĬȊĮǏİỊỈƗ":
        return u"I"
    if char in u"ıìȉíîĩḭïḯīĭȋįǐiịỉɨ":
        return u"i"
    if char in u"ĴJ":
        return u"J"
    if char in u"ɟĵ̌ǰ":
        return u"j"
    if char in u"ḰǨĶḲḴƘ":
        return u"K"
    if char in u"ḱǩķḳḵƙ":
        return u"k"
    if char in u"ĹĻĽḶḸḺḼȽŁ":
        return u"L"
    if char in u"ĺļľḷḹḻḽƚłɫ":
        return u"l"
    if char in u"ḾṀṂ":
        return u"M"
    if char in u"ḿṁṃɱ":
        return u"m"
    if char in u"ǸŃÑŅŇṄṆṈṊŊƝɲȠ":
        return u"N"
    if char in u"ǹńñņňṅṇṉṋŋɲƞ":
        return u"n"
    if char in u"ÒÓÔÕṌṎȬÖŌṐṒŎǑȮȰỌǪǬƠỜỚỠỢỞỎƟØǾ":
        return u"O"
    if char in u"òóôõṍṏȭöōṑṓŏǒȯȱọǫǭơờớỡợởỏɵøǿ":
        return u"o"
    if char in u"ȌŐȪ":
        return u"Ö"
    if char in u"ȍőȫ":
        return u"ö"
    if char in u"ỒỐỖỘỔȎ":
        return u"Ô"
    if char in u"ồốỗộổȏ":
        return u"ô"
    if char in u"ṔṖƤ":
        return u"P"
    if char in u"ṕṗƥ":
        return u"p"
    if char == u"ᵽ":
        return u"q"
    if char in u"ȐŔŖŘȒṘṚṜṞ":
        return u"R"
    if char in u"ȑŕŗřȓṙṛṝṟɽ":
        return u"r"
    if char in u"ŚṤŞȘŠṦṠṢṨ":
        return u"S"
    if char in u"śṥşșšṧṡṣṩȿ":
        return u"s"
    if char == u"Ŝ":
        return u"Sx"
    if char == u"ŝ":
        return u"sx"
    if char in u"ŢȚŤṪṬṮṰŦƬƮ":
        return u"T"
    if char in u"ţțťṫṭṯṱŧȾƭʈ":
        return u"t"
    if char in u"ÙÚŨṸṴÜṲŪṺŬỤŮŲǓṶỦƯỮỰỬ":
        return u"U"
    if char in u"ùúũṹṵüṳūṻŭụůųǔṷủưữựửʉ":
        return u"u"
    if char in u"ȔŰǛǗǕǙ":
        return u"Ü"
    if char in u"ȕűǜǘǖǚ":
        return u"ü"
    if char == u"Û":
        return u"Ux"
    if char == u"û":
        return u"ux"
    if char == u"Ȗ":
        return u"Û"
    if char == u"ȗ":
        return u"û"
    if char == u"Ừ":
        return u"Ù"
    if char == u"ừ":
        return u"ù"
    if char == u"Ứ":
        return u"Ú"
    if char == u"ứ":
        return u"ú"
    if char in u"ṼṾ":
        return u"V"
    if char in u"ṽṿ":
        return u"v"
    if char in u"ẀẂŴẄẆẈ":
        return u"W"
    if char in u"ẁẃŵẅẇẉ":
        return u"w"
    if char in u"ẊẌ":
        return u"X"
    if char in u"ẋẍ":
        return u"x"
    if char in u"ỲÝŶŸỸȲẎỴỶƳ":
        return u"Y"
    if char in u"ỳýŷÿỹȳẏỵỷƴ":
        return u"y"
    if char in u"ŹẐŻẒŽẔƵȤ":
        return u"Z"
    if char in u"źẑżẓžẕƶȥ":
        return u"z"
    if char == u"ɀ":
        return u"zv"
    
    # Latin: extended Latin alphabet
    if char == u"ɑ":
        return u"a"
    if char in u"ÆǼǢ":
        return u"AE"
    if char in u"æǽǣ":
        return u"ae"
    if char == u"Ð":
        return u"Dh"
    if char == u"ð":
        return u"dh"
    if char in u"ƎƏƐ":
        return u"E"
    if char in u"ǝəɛ":
        return u"e"
    if char in u"ƔƢ":
        return u"G"
    if char in u"ᵷɣƣᵹ":
        return u"g"
    if char == u"Ƅ":
        return u"H"
    if char == u"ƅ":
        return u"h"
    if char == u"Ƕ":
        return u"Wh"
    if char == u"ƕ":
        return u"wh"
    if char == u"Ɩ":
        return u"I"
    if char == u"ɩ":
        return u"i"
    if char == u"Ŋ":
        return u"Ng"
    if char == u"ŋ":
        return u"ng"
    if char == u"Œ":
        return u"OE"
    if char == u"œ":
        return u"oe"
    if char == u"Ɔ":
        return u"O"
    if char == u"ɔ":
        return u"o"
    if char == u"Ȣ":
        return u"Ou"
    if char == u"ȣ":
        return u"ou"
    if char == u"Ƽ":
        return u"Q"
    if char in u"ĸƽ":
        return u"q"
    if char == u"ȹ":
        return u"qp"
    if char == u"":
        return u"r"
    if char == u"ſ":
        return u"s"
    if char == u"ß":
        return u"ss"
    if char == u"Ʃ":
        return u"Sh"
    if char == u"ʃᶋ":
        return u"sh"
    if char == u"Ʉ":
        return u"U"
    if char == u"ʉ":
        return u"u"
    if char == u"Ʌ":
        return u"V"
    if char == u"ʌ":
        return u"v"
    if char in u"ƜǷ":
        return u"W"
    if char in u"ɯƿ":
        return u"w"
    if char == u"Ȝ":
        return u"Y"
    if char == u"ȝ":
        return u"y"
    if char == u"Ĳ":
        return u"IJ"
    if char == u"ĳ":
        return u"ij"
    if char == u"Ƨ":
        return u"Z"
    if char in u"ʮƨ":
        return u"z"
    if char == u"Ʒ":
        return u"Zh"
    if char == u"ʒ":
        return u"zh"
    if char == u"Ǯ":
        return u"Dzh"
    if char == u"ǯ":
        return u"dzh"
    if char in u"ƸƹʔˀɁɂ":
        return u"'"
    if char in u"Þ":
        return u"Th"
    if char in u"þ":
        return u"th"
    if char in u"Cʗǃ":
        return u"!"

    #Punctuation and typography
    if char in u"«»“”„¨":
        return u'"'
    if char in u"‘’′":
        return u"'"
    if char == u"•":
        return u"*"
    if char == u"@":
        return u"(at)"
    if char == u"¤":
        return u"$"
    if char == u"¢":
        return u"c"
    if char == u"€":
        return u"E"
    if char == u"£":
        return u"L"
    if char == u"¥":
        return u"yen"
    if char == u"†":
        return u"+"
    if char == u"‡":
        return u"++"
    if char == u"°":
        return u":"
    if char == u"¡":
        return u"!"
    if char == u"¿":
        return u"?"
    if char == u"‰":
        return u"o/oo"
    if char == u"‱":
        return u"o/ooo"
    if char in u"¶§":
        return u">"
    if char in u"…":
        return u"..."
    if char in u"‒–—―":
        return u"-"
    if char in u"·":
        return u" "
    if char == u"¦":
        return u"|"
    if char == u"⁂":
        return u"***"
    if char == u"◊":
        return u"<>"
    if char == u"‽":
        return u"?!"
    if char == u"؟":
        return u";-)"
    

    # Cyrillic
    if char == u"А":
        return u"A"
    if char == u"а":
        return u"a"
    if char == u"Б":
        return u"B"
    if char == u"б":
        return u"b"
    if char == u"В":
        return u"V"
    if char == u"в":
        return u"v"
    if char == u"Г":
        return u"G"
    if char == u"г":
        return u"g"
    if char == u"Д":
        return u"D"
    if char == u"д":
        return u"d"
    if char == u"Е":
        return u"E"
    if char == u"е":
        return u"e"
    if char == u"Ж":
        return u"Zh"
    if char == u"ж":
        return u"zh"
    if char == u"З":
        return u"Z"
    if char == u"з":
        return u"z"
    if char == u"И":
        return u"I"
    if char == u"и":
        return u"i"
    if char == u"Й":
        return u"J"
    if char == u"й":
        return u"j"
    if char == u"К":
        return u"K"
    if char == u"к":
        return u"k"
    if char == u"Л":
        return u"L"
    if char == u"л":
        return u"l"
    if char == u"М":
        return u"M"
    if char == u"м":
        return u"m"
    if char == u"Н":
        return u"N"
    if char == u"н":
        return u"n"
    if char == u"О":
        return u"O"
    if char == u"о":
        return u"o"
    if char == u"П":
        return u"P"
    if char == u"п":
        return u"p"
    if char == u"Р":
        return u"R"
    if char == u"р":
        return u"r"
    if char == u"С":
        return u"S"
    if char == u"с":
        return u"s"
    if char == u"Т":
        return u"T"
    if char == u"т":
        return u"t"
    if char in u"У":
        return u"U"
    if char == u"у":
        return u"u"
    if char == u"Ф":
        return u"F"
    if char == u"ф":
        return u"f"
    if char in u"ХΧ":
        if prev.lower() == prev:
            return u"Kh"
        else:
            return u"KH"
    if char == u"х":
        return u"kh"
    if char == u"Ц":
        return u"C"
    if char == u"ц":
        return u"c"
    if char == u"Ч":
        return u"Ch"
    if char == u"ч":
        return u"ch"
    if char == u"Ш":
        return u"Sh"
    if char == u"ш":
        return u"sh"
    if char == u"Щ":
        return u"Shch"
    if char == u"щ":
        return u"shch"
    if char in u"Ьь":
        return u"'"
    if char in u"Ъъ":
        return '"'
    if char == u"Ю":
        return u"Yu"
    if char == u"ю":
        return u"yu"
    if char == u"Я":
        return u"Ya"
    if char == u"я":
        return u"ya"
    # Additional Cyrillic letters, most occuring in only one or a few languages
    if char == u"Ы":
        return u"Y"
    if char == u"ы":
        return u"y"
    if char == u"Ё":
        return u"Ë"
    if char == u"ё":
        return u"ë"
    if char in u"ЭЀ":
        return u"È"
    if char in u"эѐ":
        return u"è"
    if char == u"І":
        return u"I"
    if char == u"і":
        return u"i"
    if char == u"Ї":
        return u"Ji"
    if char == u"ї":
        return u"ji"
    if char == u"Є":
        return u"Je"
    if char == u"є":
        return u"je"
    if char in u"ҐҜ":
        return u"G"
    if char in u"ґҝ":
        return u"g"
    if char == u"Ђ":
        return u"Dj"
    if char == u"ђ":
        return u"dj"
    if char in u"ЈӤҊ":
        return u"J"
    if char in u"јӥҋ":
        return u"j"
    if char == u"Ӣ":
        return u"Y"
    if char == u"ӣ":
        return u"y"
    if char == u"Љ":
        return u"Lj"
    if char == u"љ":
        return u"lj"
    if char == u"Њ":
        return u"Nj"
    if char == u"њ":
        return u"nj"
    if char == u"Ћ":
        return u"Cj"
    if char == u"ћ":
        return u"cj"
    if char in u"ЏӁӜҶ":
        return u"Dzh"
    if char in u"џӂӝҷ":
        return u"dzh"
    if char == u"Җ":
        return u"Zhj"
    if char == u"җ":
        return u"zhj"
    if char in u"ЅӞӠӋҸ":
        return u"Dz"
    if char in u"ѕӟӡӌҹ":
        return u"dz"
    if char == u"Ѓ":
        return u"Gj"
    if char == u"ѓ":
        return u"gj"
    if char == u"Ќ":
        return u"Kj"
    if char == u"ќ":
        return u"kj"
    if char in u"ҒӶҔ":
        return u"G"
    if char in u"ғӷҕ":
        return u"g"
    if char == u"Ӣ":
        return u"Ii"
    if char == u"ӣ":
        return u"ii"
    if char in u"ҚҞҠӃ":
        return u"Q"
    if char == u"қҟҡӄ":
        return u"q"
    if char == u"Ӯ":
        return u"U"
    if char == u"ӯ":
        return u"u"
    if char == u"Ҳ":
        return u"H"
    if char == u"ҳ":
        return u"h"
    if char == u"Ҷ":
        return u"Dz"
    if char == u"ҷ":
        return u"dz"
    if char in u"ӨӪ":
        return u"Ô"
    if char in u"өӫ":
        return u"ô"
    if char == u"Ү":
        return u"Y"
    if char == u"ү":
        return u"y"
    if char == u"Һ":
        return u"H"
    if char == u"һ":
        return u"h"
    if char in u"ӘӔ":
        return u"AE"
    if char == u"ә":
        return u"ae"
    if char == u"ӚӬ":
        return u"Ë"
    if char == u"ӛӭ":
        return u"ë"
    if char == u"Җ":
        return u"Zhj"
    if char == u"җ":
        return u"zhj"
    if char == u"ҢҤӉӇ":
        return u"Ng"
    if char == u"ңҥӊӈ":
        return u"ng"
    if char == u"Ұ":
        return u"U"
    if char == u"ұ":
        return u"u"
    if char == u"ў":
        return u"ù"
    if char == u"Ў":
        return u"Ù"
    if char == u"ѝ":
        return u"ì"
    if char == u"Ѝ":
        return u"Ì"
    if char == u"Ӑ":
        return u"A"
    if char == u"ă":
        return u"a"
    if char == u"Ӓ":
        return u"Ä"
    if char == u"ä":
        return u"ä"
    if char in u"ӖѢҌ":
        return u"E"
    if char in u"ӗѣҍ":
        return u"e"
    if char == u"ҼҾ":
        return u"Ts"
    if char == u"ҽҿ":
        return u"ts"
    if char == u"Ҙ":
        return u"Dh"
    if char == u"ҙ":
        return u"dh"
    if char in u"Ӏӏ":
        return u""
    if char == u"Ӆ":
        return u"L"
    if char == u"ӆ":
        return u"l"
    if char == u"Ӎ":
        return u"M"
    if char == u"ӎ":
        return u"m"
    if char == u"Ӧ":
        return u"Ö"
    if char == u"ӧ":
        return u"ö"
    if char == u"Ҩ":
        return u"u"
    if char == u"ҩ":
        return u"u"
    if char == u"Ҧ":
        return u"Ph"
    if char == u"ҧ":
        return u"ph"
    if char == u"Ҏ":
        return u"R"
    if char == u"ҏ":
        return u"r"
    if char == u"Ҫ":
        return u"Th"
    if char == u"ҫ":
        return u"th"
    if char == u"Ҭ":
        return u"T"
    if char == u"ҭ":
        return u"t"
    if char in u"ӲӰҮ":
        return u"Ü"
    if char in u"ӳӱү":
        return u"ü"
    if char == u"Ӯ":
        return u"Û"
    if char == u"ӯ":
        return u"û"
    if char == u"ҰӸ":
        return u"U"
    if char == u"ұӹ":
        return u"u"
    if char == u"Ҵ":
        return u"Tts"
    if char == u"ҵ":
        return u"tts"
    if char == u"Ӵ":
        return u"Ch"
    if char == u"ӵ":
        return u"ch"

    # Archaic Cyrillic letters
    if char == u"Ѹ":
        return u"Ou"
    if char == u"ѹ":
        return u"ou"
    if char in u"ѠѺ":
        return u"O"
    if char in u"ѡѻ":
        return u"o"
    if char == u"Ѿ":
        return u"Ot"
    if char == u"ѿ":
        return u"ot"
    if char == u"Ѣ":
        return u"E"
    if char == u"ѣ":
        return u"e"
    if char in u"ѤѦ":
        return u"Ei"
    if char in u"ѥѧ":
        return u"ei"
    if char == u"Ѫ":
        return u"Ai"
    if char == u"ѫ":
        return u"ai"
    if char == u"Ѯ":
        return u"X"
    if char == u"ѯ":
        return u"x"
    if char == u"Ѱ":
        return u"Ps"
    if char == u"ѱ":
        return u"ps"
    if char == u"Ѳ":
        return u"Th"
    if char == u"ѳ":
        return u"th"
    if char in u"ѴѶ":
        return u"Ü"
    if char == u"ѵ":
        return u"ü"
    

    # Hebrew alphabet
    if char in u"אע":
        return u"'"
    if char == u"ב":
        return u"b"
    if char == u"ג":
        return u"g"
    if char == u"ד":
        return u"d"
    if char == u"ה":
        return u"h"
    if char == u"ו":
        return u"v"
    if char == u"ז":
        return u"z"
    if char == u"ח":
        return u"kh"
    if char == u"ט":
        return u"t"
    if char == u"י":
        return u"y"
    if char in u"ךכ":
        return u"k"
    if char == u"ל":
        return u"l"
    if char in u"םמ":
        return u"m"
    if char in u"ןנ":
        return u"n"
    if char == u"ס":
        return u"s"
    if char in u"ףפ":
        return u"ph"
    if char in u"ץצ":
        return u"ts"
    if char == u"ק":
        return u"q"
    if char == u"ר":
        return u"r"
    if char == u"ש":
        return u"sh"
    if char == u"ת":
        return u"th"
    
    # Arab alphabet
    if char in u"اﺍﺎ":
        return u"a"
    if char in u"بﺏﺐﺒﺑ":
        return u"b"
    if char in u"تﺕﺖﺘﺗ":
        return u"t"
    if char in u"ثﺙﺚﺜﺛ":
        return u"th"
    if char in u"جﺝﺞﺠﺟ":
        return u"g"
    if char in u"حﺡﺢﺤﺣ":
        return u"h"
    if char in u"خﺥﺦﺨﺧ":
        return u"kh"
    if char in u"دﺩﺪ":
        return u"d"
    if char in u"ذﺫﺬ":
        return u"dh"
    if char in u"رﺭﺮ":
        return u"r"
    if char in u"زﺯﺰ":
        return u"z"
    if char in u"سﺱﺲﺴﺳ":
        return u"s"
    if char in u"شﺵﺶﺸﺷ":
        return u"sh"
    if char in u"صﺹﺺﺼﺻ":
        return u"s"
    if char in u"ضﺽﺾﻀﺿ":
        return u"d"
    if char in u"طﻁﻂﻄﻃ":
        return u"t"
    if char in u"ظﻅﻆﻈﻇ":
        return u"z"
    if char in u"عﻉﻊﻌﻋ":
        return u"'"
    if char in u"غﻍﻎﻐﻏ":
        return u"gh"
    if char in u"فﻑﻒﻔﻓ":
        return u"f"
    if char in u"قﻕﻖﻘﻗ":
        return u"q"
    if char in u"كﻙﻚﻜﻛک":
        return u"k"
    if char in u"لﻝﻞﻠﻟ":
        return u"l"
    if char in u"مﻡﻢﻤﻣ":
        return u"m"
    if char in u"نﻥﻦﻨﻧ":
        return u"n"
    if char in u"هﻩﻪﻬﻫ":
        return u"h"
    if char in u"وﻭﻮ":
        return u"w"
    if char in u"یيﻱﻲﻴﻳ":
        return u"y"
    # Arabic - additional letters, modified letters and ligatures
    if char == u"ﺀ":
        return u"'"
    if char in u"آﺁﺂ":
        return u"'a"
    if char in u"ةﺓﺔ":
        return u"th"
    if char in u"ىﻯﻰ":
        return u"á"
    if char in u"یﯼﯽﯿﯾ":
        return u"y"
    if char == u"؟":
        return u"?"
    # Arabic - ligatures
    if char in u"ﻻﻼ":
        return u"la"
    if char == u"ﷲ":
        return u"llah"
    if char in u"إأ":
        return u"a'"
    if char == u"ؤ":
        return u"w'"
    if char == u"ئ":
        return u"y'"
    if char == u"◌":
        return prev
    if char in u"◌◌":
        return u"" # indicates absence of vowels
    # Arabic vowels
    if char == u"◌":
        return u"a"
    if char == u"◌":
        return u"u"
    if char == u"◌":
        return u"i"
    if char == u"◌":
        return u"a"
    if char == u"◌":
        return u"ay"
    if char == u"◌":
        return u"ay"
    if char == u"◌":
        return u"u"
    if char == u"◌":
        return u"iy"
    # Arab numerals
    if char in u"٠۰":
        return u"0"
    if char in u"١۱":
        return u"1"
    if char in u"٢۲":
        return u"2"
    if char in u"٣۳":
        return u"3"
    if char in u"٤۴":
        return u"4"
    if char in u"٥۵":
        return u"5"
    if char in u"٦۶":
        return u"6"
    if char in u"٧۷":
        return u"7"
    if char in u"٨۸":
        return u"8"
    if char in u"٩۹":
        return u"9"
    # Perso-Arabic
    if char in u"پﭙﭙپ":
        return u"p"
    if char in u"چچچچ":
        return u"ch"
    if char in u"ژژ":
        return u"zh"
    if char in u"گﮔﮕﮓ":
        return u"g"

    # Greek
    if char == u"Α":
        return u"A"
    if char == u"α":
        return u"a"
    if char == u"Β":
        return u"B"
    if char == u"β":
        return u"b"
    if char == u"Γ":
        return u"G"
    if char == u"γ":
        return u"g"
    if char == u"Δ":
        return u"D"
    if char == u"δ":
        return u"d"
    if char == u"Ε":
        return u"E"
    if char == u"ε":
        return u"e"
    if char == u"Ζ":
        return u"Z"
    if char == u"ζ":
        return u"z"
    if char == u"Η":
        return u"I"
    if char == u"η":
        return u"i"
    if char == u"Θ":
        if prev.lower() == prev:
            return u"Th"
        else:
            return u"TH"
    if char == u"θ":
        return u"th"
    if char == u"Ι":
        return u"I"
    if char == u"ι":
        return u"i"
    if char == u"Κ":
        return u"K"
    if char == u"κ":
        return u"k"
    if char == u"Λ":
        return u"L"
    if char == u"λ":
        return u"l"
    if char == u"Μ":
        return u"M"
    if char == u"μ":
        return u"m"
    if char == u"Ν":
        return u"N"
    if char == u"ν":
        return u"n"
    if char == u"Ξ":
        return u"X"
    if char == u"ξ":
        return u"x"
    if char == u"Ο":
        return u"O"
    if char == u"ο":
        return u"o"
    if char == u"Π":
        return u"P"
    if char == u"π":
        return u"p"
    if char == u"Ρ":
        return u"R"
    if char == u"ρ":
        return u"r"
    if char == u"Σ":
        return u"S"
    if char in u"σς":
        return u"s"
    if char == u"Τ":
        return u"T"
    if char == u"τ":
        return u"t"
    if char == u"Υ":
        return u"Y"
    if char == u"υ":
        return u"y"
    if char == u"Φ":
        return u"F"
    if char == u"φ":
        return u"f"
    if char == u"Ψ":
        if prev.lower() == prev:
            return u"Ps"
        else:
            return u"PS"
    if char == u"ψ":
        return u"ps"
    if char == u"Ω":
        return u"O"
    if char == u"ω":
        return u"o"
    # Greek: Special and old characters
    if char == u"ϗ":
        return u"&"
    if char == u"Ϛ":
        if prev.lower() == prev:
            return u"St"
        else:
            return u"ST"
    if char == u"ϛ":
        return u"st"
    if char in u"ϘϞ":
        return u"Q"
    if char in u"ϙϟ":
        return u"q"
    if char == u"Ϻ":
        return u"S"
    if char == u"ϻ":
        return u"s"
    if char == u"Ϡ":
        if prev.lower() == prev:
            return u"Ss"
        else:
            return u"SS"
    if char == u"ϡ":
        return u"ss"
    if char == u"Ϸ":
        if prev.lower() == prev:
            return u"Sh"
        else:
            return u"SH"
    if char == u"ϸ":
        return u"sh"
    if char == u"·":
        return u":"
    # Greek: Accented characters
    if char == u"Ά":
        return u"Á"
    if char == u"ά":
        return u"á"
    if char in u"ΈΉ":
        return u"É"
    if char in u"έή":
        return u"é"
    if char == u"Ί":
        return u"Í"
    if char == u"ί":
        return u"í"
    if char == u"Ϊ":
        return u"Ï"
    if char in u"ϊΐ":
        return u"ï"
    if char == u"Ό":
        return u"Ó"
    if char == u"ό":
        return u"ó"
    if char == u"Ύ":
        return u"Ý"
    if char == u"ύ":
        return u"ý"
    if char == u"Ϋ":
        return u"Y"
    if char in u"ϋΰ":
        return u"ÿ"
    if char == u"Ώ":
        return u"Ó"
    if char == u"ώ":
        return u"ó"

    # Japanese (katakana and hiragana)
    if char in u"アァあ":
        return u"a"
    if char in u"イィい":
        return u"i"
    if char in u"ウう":
        return u"u"
    if char in u"エェえ":
        return u"e"
    if char in u"オォお":
        return u"o"
    if char in u"ャや":
        return u"ya"
    if char in u"ュゆ":
        return u"yu"
    if char in u"ョよ":
        return u"yo"
    if char in u"カか":
        return u"ka"
    if char in u"キき":
        return u"ki"
    if char in u"クく":
        return u"ku"
    if char in u"ケけ":
        return u"ke"
    if char in u"コこ":
        return u"ko"
    if char in u"サさ":
        return u"sa"
    if char in u"シし":
        return u"shi"
    if char in u"スす":
        return u"su"
    if char in u"セせ":
        return u"se"
    if char in u"ソそ":
        return u"so"
    if char in u"タた":
        return u"ta"
    if char in u"チち":
        return u"chi"
    if char in u"ツつ":
        return u"tsu"
    if char in u"テて":
        return u"te"
    if char in u"トと":
        return u"to"
    if char in u"ナな":
        return u"na"
    if char in u"ニに":
        return u"ni"
    if char in u"ヌぬ":
        return u"nu"
    if char in u"ネね":
        return u"ne"
    if char in u"ノの":
        return u"no"
    if char in u"ハは":
        return u"ha"
    if char in u"ヒひ":
        return u"hi"
    if char in u"フふ":
        return u"fu"
    if char in u"ヘへ":
        return u"he"
    if char in u"ホほ":
        return u"ho"
    if char in u"マま":
        return u"ma"
    if char in u"ミみ":
        return u"mi"
    if char in u"ムむ":
        return u"mu"
    if char in u"メめ":
        return u"me"
    if char in u"モも":
        return u"mo"
    if char in u"ラら":
        return u"ra"
    if char in u"リり":
        return u"ri"
    if char in u"ルる":
        return u"ru"
    if char in u"レれ":
        return u"re"
    if char in u"ロろ":
        return u"ro"
    if char in u"ワわ":
        return u"wa"
    if char in u"ヰゐ":
        return u"wi"
    if char in u"ヱゑ":
        return u"we"
    if char in u"ヲを":
        return u"wo"
    if char in u"ンん":
        return u"n"
    if char in u"ガが":
        return u"ga"
    if char in u"ギぎ":
        return u"gi"
    if char in u"グぐ":
        return u"gu"
    if char in u"ゲげ":
        return u"ge"
    if char in u"ゴご":
        return u"go"
    if char in u"ザざ":
        return u"za"
    if char in u"ジじ":
        return u"ji"
    if char in u"ズず":
        return u"zu"
    if char in u"ゼぜ":
        return u"ze"
    if char in u"ゾぞ":
        return u"zo"
    if char in u"ダだ":
        return u"da"
    if char in u"ヂぢ":
        return u"dji"
    if char in u"ヅづ":
        return u"dzu"
    if char in u"デで":
        return u"de"
    if char in u"ドど":
        return u"do"
    if char in u"バば":
        return u"ba"
    if char in u"ビび":
        return u"bi"
    if char in u"ブぶ":
        return u"bu"
    if char in u"ベべ":
        return u"be"
    if char in u"ボぼ":
        return u"bo"
    if char in u"パぱ":
        return u"pa"
    if char in u"ピぴ":
        return u"pi"
    if char in u"プぷ":
        return u"pu"
    if char in u"ペぺ":
        return u"pe"
    if char in u"ポぽ":
        return u"po"
    if char in u"ヴゔ":
        return u"vu"
    if char == u"ヷ":
        return u"va"
    if char == u"ヸ":
        return u"vi"
    if char == u"ヹ":
        return u"ve"
    if char == u"ヺ":
        return u"vo"
    if char == u"ッ":
        return trans(next)[0]

    # Japanese and Chinese punctuation and typography
    if char == u"・·":
        return u" "
    if char == u"々仝ヽヾゝゞ〱〲〳〵〴〵":
        return prev
    if char in u"〃『』《》":
        return u'"'
    if char in u"「」〈〉〘〙〚〛":
        return u"'"
    if char in u"（〔":
        return u"("
    if char in u"）〕":
        return u")"
    if char in u"［【〖":
        return u"["
    if char in u"］】〗":
        return u"]"
    if char == u"｛":
        return u"{"
    if char == u"｝":
        return u"}"
    if char == u"っ":
        return u":"
    if char == u"ー":
        return u"h"
    if char == u"゛":
        return u"'"
    if char == u"゜":
        return u"p"
    if char == u"。":
        return u". "
    if char == u"、":
        return u", "
    if char == u"・":
        return u" "
    if char == u"〆":
        return u"shime"
    if char == u"〜":
        return u"-"
    if char == u"…":
        return u"..."
    if char == u"‥":
        return u".."
    if char == u"ヶ":
        return u"months"
    if char in u"•◦":
        return u"_"
    if char in u"※＊":
        return u"*"
    if char == u"Ⓧ":
        return u"(X)"
    if char == u"Ⓨ":
        return u"(Y)"
    if char == u"！":
        return u"!"
    if char == u"？":
        return u"?"
    if char == u"；":
        return u";"
    if char == u"：":
        return u":"
    if char == u"。":
        return u"."
    if char in u"，、":
        return u","

    # Georgian
    if char == u"ა":
        return u"a"
    if char == u"ბ":
        return u"b"
    if char == u"გ":
        return u"g"
    if char == u"დ":
        return u"d"
    if char in u"ეჱ":
        return u"e"
    if char == u"ვ":
        return u"v"
    if char == u"ზ":
        return u"z"
    if char == u"თ":#
        return u"th"
    if char == u"ი":
        return u"i"
    if char == u"კ":#
        return u"k"
    if char == u"ლ":
        return u"l"
    if char == u"მ":
        return u"m"
    if char == u"ნ":
        return u"n"
    if char == u"ო":
        return u"o"
    if char == u"პ":#
        return u"p"
    if char == u"ჟ":#
        return u"zh"
    if char == u"რ":
        return u"r"
    if char == u"ს":
        return u"s"
    if char == u"ტ":#
        return u"t"
    if char == u"უ":
        return u"u"
    if char == u"ფ":#
        return u"ph"
    if char == u"ქ":#
        return u"q"
    if char == u"ღ":#
        return u"gh"
    if char == u"ყ":#
        return u"q'"
    if char == u"შ":
        return u"sh"
    if char == u"ჩ":
        return u"ch"
    if char == u"ც":
        return u"ts"
    if char == u"ძ":
        return u"dz"
    if char == u"წ":#
        return u"ts'"
    if char == u"ჭ":#
        return u"ch'"
    if char == u"ხ":
        return u"kh"
    if char == u"ჯ":#
        return u"j"
    if char == u"ჰ":
        return u"h"
    if char == u"ჳ":
        return u"w"
    if char == u"ჵ":
        return u"o"
    if char == u"ჶ":
        return u"f"

    # Devanagari
    if char in u"पप":
        return u"p"
    if char in u"अ":
        return u"a"
    if char in u"आा":
        return u"aa"
    if char == u"प":
        return u"pa"
    if char in u"इि":
        return u"i"
    if char in u"ईी":
        return u"ii"
    if char in u"उु":
        return u"u"
    if char in u"ऊू":
        return u"uu"
    if char in u"एे":
        return u"e"
    if char in u"ऐै":
        return u"ai"
    if char in u"ओो":
        return u"o"
    if char in u"औौ":
        return u"au"
    if char in u"ऋृर":
        return u"r"
    if char in u"ॠॄ":
        return u"rr"
    if char in u"ऌॢल":
        return u"l"
    if char in u"ॡॣ":
        return u"ll"
    if char == u"क":
        return u"k"
    if char == u"ख":
        return u"kh"
    if char == u"ग":
        return u"g"
    if char == u"घ":
        return u"gh"
    if char == u"ङ":
        return u"ng"
    if char == u"च":
        return u"c"
    if char == u"छ":
        return u"ch"
    if char == u"ज":
        return u"j"
    if char == u"झ":
        return u"jh"
    if char == u"ञ":
        return u"ñ"
    if char in u"टत":
        return u"t"
    if char in u"ठथ":
        return u"th"
    if char in u"डद":
        return u"d"
    if char in u"ढध":
        return u"dh"
    if char in u"णन":
        return u"n"
    if char == u"फ":
        return u"ph"
    if char == u"ब":
        return u"b"
    if char == u"भ":
        return u"bh"
    if char == u"म":
        return u"m"
    if char == u"य":
        return u"y"
    if char == u"व":
        return u"v"
    if char == u"श":
        return u"sh"
    if char in u"षस":
        return u"s"
    if char == u"ह":
        return u"h"
    if char == u"क":
        return u"x"
    if char == u"त":
        return u"tr"
    if char == u"ज":
        return u"gj"
    if char == u"क़":
        return u"q"
    if char == u"फ":
        return u"f"
    if char == u"ख":
        return u"hh"
    if char == u"H":
        return u"gh"
    if char == u"ज":
        return u"z"
    if char in u"डढ":
        return u"r"
    # Devanagari ligatures (possibly incomplete and/or incorrect)
    if char == u"ख्":
        return u"khn"
    if char == u"त":
        return u"tn"
    if char == u"द्":
        return u"dn"
    if char == u"श":
        return u"cn"
    if char == u"ह्":
        return u"fn"
    if char in u"अँ":
        return u"m"
    if char in u"॒॑":
        return u""
    if char == u"०":
        return u"0"
    if char == u"१":
        return u"1"
    if char == u"२":
        return u"2"
    if char == u"३":
        return u"3"
    if char == u"४":
        return u"4"
    if char == u"५":
        return u"5"
    if char == u"६":
        return u"6"
    if char == u"७":
        return u"7"
    if char == u"८":
        return u"8"
    if char == u"९":
        return u"9"

    # Armenian
    if char == u"Ա":
        return u"A"
    if char == u"ա":
        return u"a"
    if char == u"Բ":
        return u"B"
    if char == u"բ":
        return u"b"
    if char == u"Գ":
        return u"G"
    if char == u"գ":
        return u"g"
    if char == u"Դ":
        return u"D"
    if char == u"դ":
        return u"d"
    if char == u"Ե":
        return u"Je"
    if char == u"ե":
        return u"e"
    if char == u"Զ":
        return u"Z"
    if char == u"զ":
        return u"z"
    if char == u"Է":
        return u"É"
    if char == u"է":
        return u"é"
    if char == u"Ը":
        return u"Ë"
    if char == u"ը":
        return u"ë"
    if char == u"Թ":
        return u"Th"
    if char == u"թ":
        return u"th"
    if char == u"Ժ":
        return u"Zh"
    if char == u"ժ":
        return u"zh"
    if char == u"Ի":
        return u"I"
    if char == u"ի":
        return u"i"
    if char == u"Լ":
        return u"L"
    if char == u"լ":
        return u"l"
    if char == u"Խ":
        return u"Ch"
    if char == u"խ":
        return u"ch"
    if char == u"Ծ":
        return u"Ts"
    if char == u"ծ":
        return u"ts"
    if char == u"Կ":
        return u"K"
    if char == u"կ":
        return u"k"
    if char == u"Հ":
        return u"H"
    if char == u"հ":
        return u"h"
    if char == u"Ձ":
        return u"Dz"
    if char == u"ձ":
        return u"dz"
    if char == u"Ղ":
        return u"R"
    if char == u"ղ":
        return u"r"
    if char == u"Ճ":
        return u"Cz"
    if char == u"ճ":
        return u"cz"
    if char == u"Մ":
        return u"M"
    if char == u"մ":
        return u"m"
    if char == u"Յ":
        return u"J"
    if char == u"յ":
        return u"j"
    if char == u"Ն":
        return u"N"
    if char == u"ն":
        return u"n"
    if char == u"Շ":
        return u"S"
    if char == u"շ":
        return u"s"
    if char == u"Շ":
        return u"Vo"
    if char == u"շ":
        return u"o"
    if char == u"Չ":
        return u"Tsh"
    if char == u"չ":
        return u"tsh"
    if char == u"Պ":
        return u"P"
    if char == u"պ":
        return u"p"
    if char == u"Ջ":
        return u"Dz"
    if char == u"ջ":
        return u"dz"
    if char == u"Ռ":
        return u"R"
    if char == u"ռ":
        return u"r"
    if char == u"Ս":
        return u"S"
    if char == u"ս":
        return u"s"
    if char == u"Վ":
        return u"V"
    if char == u"վ":
        return u"v"
    if char == u"Տ":
        return u"T'"
    if char == u"տ":
        return u"t'"
    if char == u"Ր":
        return u"R"
    if char == u"ր":
        return u"r"
    if char == u"Ց":
        return u"Tsh"
    if char == u"ց":
        return u"tsh"
    if char == u"Ւ":
        return u"V"
    if char == u"ւ":
        return u"v"
    if char == u"Փ":
        return u"Ph"
    if char == u"փ":
        return u"ph"
    if char == u"Ք":
        return u"Kh"
    if char == u"ք":
        return u"kh"
    if char == u"Օ":
        return u"O"
    if char == u"օ":
        return u"o"
    if char == u"Ֆ":
        return u"F"
    if char == u"ֆ":
        return u"f"
    if char == u"և":
        return u"&"
    if char == u"՟":
        return u"."
    if char == u"՞":
        return u"?"
    if char == u"՝":
        return u";"
    if char == u"՛":
        return u""

    # Tamil
    if char == u"க்":
        return u"k"
    if char in u"ஙண்ந்ன்":
        return u"n"
    if char == u"ச":
        return u"c"
    if char == u"ஞ்":
        return u"ñ"
    if char == u"ட்":
        return u"th"
    if char == u"த":
        return u"t"
    if char == u"ப":
        return u"p"
    if char == u"ம்":
        return u"m"
    if char == u"ய்":
        return u"y"
    if char in u"ர்ழ்ற":
        return u"r"
    if char in u"ல்ள":
        return u"l"
    if char == u"வ்":
        return u"v"
    if char == u"ஜ":
        return u"j"
    if char == u"ஷ":
        return u"sh"
    if char == u"ஸ":
        return u"s"
    if char == u"ஹ":
        return u"h"
    if char == u"க்ஷ":
        return u"x"
    if char == u"அ":
        return u"a"
    if char == u"ஆ":
        return u"aa"
    if char == u"இ":
        return u"i"
    if char == u"ஈ":
        return u"ii"
    if char == u"உ":
        return u"u"
    if char == u"ஊ":
        return u"uu"
    if char == u"எ":
        return u"e"
    if char == u"ஏ":
        return u"ee"
    if char == u"ஐ":
        return u"ai"
    if char == u"ஒ":
        return u"o"
    if char == u"ஓ":
        return u"oo"
    if char == u"ஔ":
        return u"au"
    if char == u"ஃ":
        return ""

    # Bengali
    if char == u"অ":
        return u"ô"
    if char in u"আা":
        return u"a"
    if char in u"ইিঈী":
        return u"i"
    if char in u"উুঊূ":
        return u"u"
    if char in u"ঋৃ":
        return u"ri"
    if char in u"এেয়":
        return u"e"
    if char in u"ঐৈ":
        return u"oi"
    if char in u"ওো":
        return u"o"
    if char in u"ঔৌ":
        return "ou"
    if char == u"্":
        return u""
    if char == u"ৎ":
        return u"t"
    if char == u"ং":
        return u"n"
    if char == u"ঃ":
        return u"h"
    if char == u"ঁ":
        return u"ñ"
    if char == u"ক":
        return u"k"
    if char == u"খ":
        return u"kh"
    if char == u"গ":
        return u"g"
    if char == u"ঘ":
        return u"gh"
    if char == u"ঙ":
        return u"ng"
    if char == u"চ":
        return u"ch"
    if char == u"ছ":
        return u"chh"
    if char in u"জ":
        return u"j"
    if char == u"ঝ":
        return u"jh"
    if char == u"ঞ":
        return u"n"
    if char in u"টত":
        return u"t"
    if char in u"ঠথ":
        return u"th"
    if char in u"ডদ":
        return u"d"
    if char in u"ঢধ":
        return u"dh"
    if char in u"ণন":
        return u"n"
    if char == u"প":
        return u"p"
    if char == u"ফ":
        return u"ph"
    if char == u"ব":
        return u"b"
    if char == u"ভ":
        return u"bh"
    if char == u"ম":
        return u"m"
    if char == u"য":
        return u"dzh"
    if char == u"র":
        return u"r"
    if char == u"ল":
        return u"l"
    if char == u"শ":
        return u"s"
    if char == u"হ":
        return u"h"
    if char == u"য়":
        return u"-"
    if char == u"ড়":
        return u"r"
    if char == u"ঢ":
        return u"rh"
    if char == u"০":
        return u"0"
    if char == u"১":
        return u"1"
    if char == u"২":
        return u"2"
    if char == u"৩":
        return u"3"
    if char == u"৪":
        return u"4"
    if char == u"৫":
        return u"5"
    if char == u"৬":
        return u"6"
    if char == u"৭":
        return u"7"
    if char == u"৮":
        return u"8"
    if char == u"৯":
        return u"9"
    
    # Thai (because of complications of the alphabet, transliterations
    #       are very imprecise here)
    if char == u"ก":
        return u"k"
    if char in u"ขฃคฅฆ":
        return u"kh"
    if char == u"ง":
        return u"ng"
    if char in u"จฉชฌ":
        return u"ch"
    if char in u"ซศษส":
        return u"s"
    if char in u"ญย":
        return u"y"
    if char in u"ฎด":
        return u"d"
    if char in u"ฏต":
        return u"t"
    if char in u"ฐฑฒถทธ":
        return u"th"
    if char in u"ณน":
        return u"n"
    if char == u"บ":
        return u"b"
    if char == u"ป":
        return u"p"
    if char in u"ผพภ":
        return u"ph"
    if char in u"ฝฟ":
        return u"f"
    if char in u"ม":
        return u"m"
    if char == u"ร":
        return u"r"
    if char == u"ฤ":
        return u"rue"
    if char in u"ๅ":
        return u":"
    if char in u"ลฬ":
        return u"l"
    if char == u"ฦ":
        return u"lue"
    if char == u"ว":
        return u"w"
    if char in u"หฮ":
        return u"h"
    if char == u"อ":
        return u""
    if char == u"ร":
        return u"ü"
    if char == u"ว":
        return u"ua"
    if char in u"อว–โิ":
        return u"o"
    if char in u"ะัา":
        return u"a"
    if char in u"ว":
        return u"u"
    if char == u"ำ":
        return u"am"
    if char == u"ิ":
        return u"i"
    if char == u"ี":
        return u"i:"
    if char == u"ึ":
        return u"ue"
    if char == u"ื":
        return u"ue:"
    if char == u"ุ":
        return u"u"
    if char == u"ู":
        return u"u:"
    if char in u"เ็":
        return u"e"
    if char == u"แ":
        return u"ae"
    if char in u"ใไ":
        return u"ai"
    if char in u"่้๊๋็์":
        return u""
    if char in u"ฯ":
        return u"."
    if char in u"ๆ":
        return u"(2)"    
    
    return default
