# -*- coding: UTF-8 -*-
# the comment above is for the Python interpreter, there are Unicode
# characters written straight into this source file

import pycountry
import json
import sys
import os

if sys.version_info[0] == 2 and sys.version_info[1] < 7:
    from portality.ordereddict import OrderedDict
else:
    from collections import OrderedDict

# countries
with open(os.path.join(os.path.dirname(os.path.realpath(__file__)), "..", 'country-codes.json'), 'rb') as f:
    countries = json.loads(f.read())
countries_dict = OrderedDict(sorted(countries.items(), key=lambda x: x[1]['name']))
countries = countries_dict.items()

country_options = [('','')]
country_options_two_char_code_index = []

CURRENCY_DEFAULT = ''
currency_options = [(CURRENCY_DEFAULT, CURRENCY_DEFAULT)]
currency_options_code_index = []
currency_name_opts = []

for code, country_info in countries:        # FIXME: a bit of a mess - would be better to have an object that just gave us the answers on demand
    country_options.append((code, country_info['name']))
    country_options_two_char_code_index.append(code)
    if 'currency_alphabetic_code' in country_info and 'currency_name' in country_info:
        if country_info['currency_alphabetic_code'] not in currency_options_code_index:
            # prevent duplicates in the currency options by checking if
            # that currency has already been added - multiple countries
            # use the same currency after all (GBP, EUR..)
            currency_options.append(
                (
                    country_info['currency_alphabetic_code'],
                    country_info['currency_alphabetic_code'] + ' - ' + country_info['currency_name']
                )
            )
            currency_name_opts.append(
                (
                    country_info['currency_alphabetic_code'],
                    country_info['currency_name']
                )
            )
            currency_options_code_index.append(country_info['currency_alphabetic_code'])

currencies_dict = dict(currency_options)
currency_name_map = dict(currency_name_opts)

# languages
languages_iso639_2 = [
    [u"aar", u"", u"aa", u"Afar", u"afar"],
    [u"abk", u"", u"ab", u"Abkhazian", u"abkhaze"],
    [u"ace", u"", u"", u"Achinese", u"aceh"],
    [u"ach", u"", u"", u"Acoli", u"acoli"],
    [u"ada", u"", u"", u"Adangme", u"adangme"],
    [u"ady", u"", u"", u"Adyghe; Adygei", u"adyghé"],
    [u"afa", u"", u"", u"Afro-Asiatic languages", u"afro-asiatiques, langues"],
    [u"afh", u"", u"", u"Afrihili", u"afrihili"],
    [u"afr", u"", u"af", u"Afrikaans", u"afrikaans"],
    [u"ain", u"", u"", u"Ainu", u"aïnou"],
    [u"aka", u"", u"ak", u"Akan", u"akan"],
    [u"akk", u"", u"", u"Akkadian", u"akkadien"],
    [u"alb", u"sqi", u"sq", u"Albanian", u"albanais"],
    [u"ale", u"", u"", u"Aleut", u"aléoute"],
    [u"alg", u"", u"", u"Algonquian languages", u"algonquines, langues"],
    [u"alt", u"", u"", u"Southern Altai", u"altai du Sud"],
    [u"amh", u"", u"am", u"Amharic", u"amharique"],
    [u"ang", u"", u"", u"English, Old (ca.450-1100)", u"anglo-saxon (ca.450-1100)"],
    [u"anp", u"", u"", u"Angika", u"angika"],
    [u"apa", u"", u"", u"Apache languages", u"apaches, langues"],
    [u"ara", u"", u"ar", u"Arabic", u"arabe"],
    [u"arc", u"", u"", u"Official Aramaic (700-300 BCE); Imperial Aramaic (700-300 BCE)", u"araméen d'empire (700-300 BCE)"],
    [u"arg", u"", u"an", u"Aragonese", u"aragonais"],
    [u"arm", u"hye", u"hy", u"Armenian", u"arménien"],
    [u"arn", u"", u"", u"Mapudungun; Mapuche", u"mapudungun; mapuche; mapuce"],
    [u"arp", u"", u"", u"Arapaho", u"arapaho"],
    [u"art", u"", u"", u"Artificial languages", u"artificielles, langues"],
    [u"arw", u"", u"", u"Arawak", u"arawak"],
    [u"asm", u"", u"as", u"Assamese", u"assamais"],
    [u"ast", u"", u"", u"Asturian; Bable; Leonese; Asturleonese", u"asturien; bable; léonais; asturoléonais"],
    [u"ath", u"", u"", u"Athapascan languages", u"athapascanes, langues"],
    [u"aus", u"", u"", u"Australian languages", u"australiennes, langues"],
    [u"ava", u"", u"av", u"Avaric", u"avar"],
    [u"ave", u"", u"ae", u"Avestan", u"avestique"],
    [u"awa", u"", u"", u"Awadhi", u"awadhi"],
    [u"aym", u"", u"ay", u"Aymara", u"aymara"],
    [u"aze", u"", u"az", u"Azerbaijani", u"azéri"],
    [u"bad", u"", u"", u"Banda languages", u"banda, langues"],
    [u"bai", u"", u"", u"Bamileke languages", u"bamiléké, langues"],
    [u"bak", u"", u"ba", u"Bashkir", u"bachkir"],
    [u"bal", u"", u"", u"Baluchi", u"baloutchi"],
    [u"bam", u"", u"bm", u"Bambara", u"bambara"],
    [u"ban", u"", u"", u"Balinese", u"balinais"],
    [u"baq", u"eus", u"eu", u"Basque", u"basque"],
    [u"bas", u"", u"", u"Basa", u"basa"],
    [u"bat", u"", u"", u"Baltic languages", u"baltes, langues"],
    [u"bej", u"", u"", u"Beja; Bedawiyet", u"bedja"],
    [u"bel", u"", u"be", u"Belarusian", u"biélorusse"],
    [u"bem", u"", u"", u"Bemba", u"bemba"],
    [u"ben", u"", u"bn", u"Bengali", u"bengali"],
    [u"ber", u"", u"", u"Berber languages", u"berbères, langues"],
    [u"bho", u"", u"", u"Bhojpuri", u"bhojpuri"],
    [u"bih", u"", u"bh", u"Bihari languages", u"langues biharis"],
    [u"bik", u"", u"", u"Bikol", u"bikol"],
    [u"bin", u"", u"", u"Bini; Edo", u"bini; edo"],
    [u"bis", u"", u"bi", u"Bislama", u"bichlamar"],
    [u"bla", u"", u"", u"Siksika", u"blackfoot"],
    [u"bnt", u"", u"", u"Bantu (Other)", u"bantoues, autres langues"],
    [u"bos", u"", u"bs", u"Bosnian", u"bosniaque"],
    [u"bra", u"", u"", u"Braj", u"braj"],
    [u"bre", u"", u"br", u"Breton", u"breton"],
    [u"btk", u"", u"", u"Batak languages", u"batak, langues"],
    [u"bua", u"", u"", u"Buriat", u"bouriate"],
    [u"bug", u"", u"", u"Buginese", u"bugi"],
    [u"bul", u"", u"bg", u"Bulgarian", u"bulgare"],
    [u"bur", u"mya", u"my", u"Burmese", u"birman"],
    [u"byn", u"", u"", u"Blin; Bilin", u"blin; bilen"],
    [u"cad", u"", u"", u"Caddo", u"caddo"],
    [u"cai", u"", u"", u"Central American Indian languages", u"amérindiennes de L'Amérique centrale, langues"],
    [u"car", u"", u"", u"Galibi Carib", u"karib; galibi; carib"],
    [u"cat", u"", u"ca", u"Catalan; Valencian", u"catalan; valencien"],
    [u"cau", u"", u"", u"Caucasian languages", u"caucasiennes, langues"],
    [u"ceb", u"", u"", u"Cebuano", u"cebuano"],
    [u"cel", u"", u"", u"Celtic languages", u"celtiques, langues; celtes, langues"],
    [u"cha", u"", u"ch", u"Chamorro", u"chamorro"],
    [u"chb", u"", u"", u"Chibcha", u"chibcha"],
    [u"che", u"", u"ce", u"Chechen", u"tchétchène"],
    [u"chg", u"", u"", u"Chagatai", u"djaghataï"],
    [u"chi", u"zho", u"zh", u"Chinese", u"chinois"],
    [u"chk", u"", u"", u"Chuukese", u"chuuk"],
    [u"chm", u"", u"", u"Mari", u"mari"],
    [u"chn", u"", u"", u"Chinook jargon", u"chinook, jargon"],
    [u"cho", u"", u"", u"Choctaw", u"choctaw"],
    [u"chp", u"", u"", u"Chipewyan; Dene Suline", u"chipewyan"],
    [u"chr", u"", u"", u"Cherokee", u"cherokee"],
    [u"chu", u"", u"cu", u"Church Slavic; Old Slavonic; Church Slavonic; Old Bulgarian; Old Church Slavonic", u"slavon d'église; vieux slave; slavon liturgique; vieux bulgare"],
    [u"chv", u"", u"cv", u"Chuvash", u"tchouvache"],
    [u"chy", u"", u"", u"Cheyenne", u"cheyenne"],
    [u"cmc", u"", u"", u"Chamic languages", u"chames, langues"],
    [u"cop", u"", u"", u"Coptic", u"copte"],
    [u"cor", u"", u"kw", u"Cornish", u"cornique"],
    [u"cos", u"", u"co", u"Corsican", u"corse"],
    [u"cpe", u"", u"", u"Creoles and pidgins, English based", u"créoles et pidgins basés sur l'anglais"],
    [u"cpf", u"", u"", u"Creoles and pidgins, French-based u", u"créoles et pidgins basés sur le français"],
    [u"cpp", u"", u"", u"Creoles and pidgins, Portuguese-based u", u"créoles et pidgins basés sur le portugais"],
    [u"cre", u"", u"cr", u"Cree", u"cree"],
    [u"crh", u"", u"", u"Crimean Tatar; Crimean Turkish", u"tatar de Crimé"],
    [u"crp", u"", u"", u"Creoles and pidgins u", u"créoles et pidgins"],
    [u"csb", u"", u"", u"Kashubian", u"kachoube"],
    [u"cus", u"", u"", u"Cushitic languages", u"couchitiques, langues"],
    [u"cze", u"ces", u"cs", u"Czech", u"tchèque"],
    [u"dak", u"", u"", u"Dakota", u"dakota"],
    [u"dan", u"", u"da", u"Danish", u"danois"],
    [u"dar", u"", u"", u"Dargwa", u"dargwa"],
    [u"day", u"", u"", u"Land Dayak languages", u"dayak, langues"],
    [u"del", u"", u"", u"Delaware", u"delaware"],
    [u"den", u"", u"", u"Slave (Athapascan)", u"esclave (athapascan)"],
    [u"dgr", u"", u"", u"Dogrib", u"dogrib"],
    [u"din", u"", u"", u"Dinka", u"dinka"],
    [u"div", u"", u"dv", u"Divehi; Dhivehi; Maldivian", u"maldivien"],
    [u"doi", u"", u"", u"Dogri", u"dogri"],
    [u"dra", u"", u"", u"Dravidian languages", u"dravidiennes, langues"],
    [u"dsb", u"", u"", u"Lower Sorbian", u"bas-sorabe"],
    [u"dua", u"", u"", u"Duala", u"douala"],
    [u"dum", u"", u"", u"Dutch, Middle (ca.1050-1350)", u"néerlandais moyen (ca. 1050-1350)"],
    [u"dut", u"nld", u"nl", u"Dutch; Flemish", u"néerlandais; flamand"],
    [u"dyu", u"", u"", u"Dyula", u"dioula"],
    [u"dzo", u"", u"dz", u"Dzongkha", u"dzongkha"],
    [u"efi", u"", u"", u"Efik", u"efik"],
    [u"egy", u"", u"", u"Egyptian (Ancient)", u"égyptien"],
    [u"eka", u"", u"", u"Ekajuk", u"ekajuk"],
    [u"elx", u"", u"", u"Elamite", u"élamite"],
    [u"eng", u"", u"en", u"English", u"anglais"],
    [u"enm", u"", u"", u"English, Middle (1100-1500)", u"anglais moyen (1100-1500)"],
    [u"epo", u"", u"eo", u"Esperanto", u"espéranto"],
    [u"est", u"", u"et", u"Estonian", u"estonien"],
    [u"ewe", u"", u"ee", u"Ewe", u"éwé"],
    [u"ewo", u"", u"", u"Ewondo", u"éwondo"],
    [u"fan", u"", u"", u"Fang", u"fang"],
    [u"fao", u"", u"fo", u"Faroese", u"féroïen"],
    [u"fat", u"", u"", u"Fanti", u"fanti"],
    [u"fij", u"", u"fj", u"Fijian", u"fidjien"],
    [u"fil", u"", u"", u"Filipino; Pilipino", u"filipino; pilipino"],
    [u"fin", u"", u"fi", u"Finnish", u"finnois"],
    [u"fiu", u"", u"", u"Finno-Ugrian languages", u"finno-ougriennes, langues"],
    [u"fon", u"", u"", u"Fon", u"fon"],
    [u"fre", u"fra", u"fr", u"French", u"français"],
    [u"frm", u"", u"", u"French, Middle (ca.1400-1600)", u"français moyen (1400-1600)"],
    [u"fro", u"", u"", u"French, Old (842-ca.1400)", u"français ancien (842-ca.1400)"],
    [u"frr", u"", u"", u"Northern Frisian", u"frison septentrional"],
    [u"frs", u"", u"", u"Eastern Frisian", u"frison oriental"],
    [u"fry", u"", u"fy", u"Western Frisian", u"frison occidental"],
    [u"ful", u"", u"ff", u"Fulah", u"peul"],
    [u"fur", u"", u"", u"Friulian", u"frioulan"],
    [u"gaa", u"", u"", u"Ga", u"ga"],
    [u"gay", u"", u"", u"Gayo", u"gayo"],
    [u"gba", u"", u"", u"Gbaya", u"gbaya"],
    [u"gem", u"", u"", u"Germanic languages", u"germaniques, langues"],
    [u"geo", u"kat", u"ka", u"Georgian", u"géorgien"],
    [u"ger", u"deu", u"de", u"German", u"allemand"],
    [u"gez", u"", u"", u"Geez", u"guèze"],
    [u"gil", u"", u"", u"Gilbertese", u"kiribati"],
    [u"gla", u"", u"gd", u"Gaelic; Scottish Gaelic", u"gaélique; gaélique écossais"],
    [u"gle", u"", u"ga", u"Irish", u"irlandais"],
    [u"glg", u"", u"gl", u"Galician", u"galicien"],
    [u"glv", u"", u"gv", u"Manx", u"manx; mannois"],
    [u"gmh", u"", u"", u"German, Middle High (ca.1050-1500)", u"allemand, moyen haut (ca. 1050-1500)"],
    [u"goh", u"", u"", u"German, Old High (ca.750-1050)", u"allemand, vieux haut (ca. 750-1050)"],
    [u"gon", u"", u"", u"Gondi", u"gond"],
    [u"gor", u"", u"", u"Gorontalo", u"gorontalo"],
    [u"got", u"", u"", u"Gothic", u"gothique"],
    [u"grb", u"", u"", u"Grebo", u"grebo"],
    [u"grc", u"", u"", u"Greek, Ancient (to 1453)", u"grec ancien (jusqu'à 1453)"],
    [u"gre", u"ell", u"el", u"Greek, Modern (1453-)", u"grec moderne (après 1453)"],
    [u"grn", u"", u"gn", u"Guarani", u"guarani"],
    [u"gsw", u"", u"", u"Swiss German; Alemannic; Alsatian", u"suisse alémanique; alémanique; alsacien"],
    [u"guj", u"", u"gu", u"Gujarati", u"goudjrati"],
    [u"gwi", u"", u"", u"Gwich'in", u"gwich'in"],
    [u"hai", u"", u"", u"Haida", u"haida"],
    [u"hat", u"", u"ht", u"Haitian; Haitian Creole", u"haïtien; créole haïtien"],
    [u"hau", u"", u"ha", u"Hausa", u"haoussa"],
    [u"haw", u"", u"", u"Hawaiian", u"hawaïen"],
    [u"heb", u"", u"he", u"Hebrew", u"hébreu"],
    [u"her", u"", u"hz", u"Herero", u"herero"],
    [u"hil", u"", u"", u"Hiligaynon", u"hiligaynon"],
    [u"him", u"", u"", u"Himachali languages; Western Pahari languages", u"langues himachalis; langues paharis occidentales"],
    [u"hin", u"", u"hi", u"Hindi", u"hindi"],
    [u"hit", u"", u"", u"Hittite", u"hittite"],
    [u"hmn", u"", u"", u"Hmong", u"hmong"],
    [u"hmo", u"", u"ho", u"Hiri Motu", u"hiri motu"],
    [u"hrv", u"", u"hr", u"Croatian", u"croate"],
    [u"hsb", u"", u"", u"Upper Sorbian", u"haut-sorabe"],
    [u"hun", u"", u"hu", u"Hungarian", u"hongrois"],
    [u"hup", u"", u"", u"Hupa", u"hupa"],
    [u"iba", u"", u"", u"Iban", u"iban"],
    [u"ibo", u"", u"ig", u"Igbo", u"igbo"],
    [u"ice", u"isl", u"is", u"Icelandic", u"islandais"],
    [u"ido", u"", u"io", u"Ido", u"ido"],
    [u"iii", u"", u"ii", u"Sichuan Yi; Nuosu", u"yi de Sichuan"],
    [u"ijo", u"", u"", u"Ijo languages", u"ijo, langues"],
    [u"iku", u"", u"iu", u"Inuktitut", u"inuktitut"],
    [u"ile", u"", u"ie", u"Interlingue; Occidental", u"interlingue"],
    [u"ilo", u"", u"", u"Iloko", u"ilocano"],
    [u"ina", u"", u"ia", u"Interlingua (International Auxiliary Language Association)", u"interlingua (langue auxiliaire internationale)"],
    [u"inc", u"", u"", u"Indic languages", u"indo-aryennes, langues"],
    [u"ind", u"", u"id", u"Indonesian", u"indonésien"],
    [u"ine", u"", u"", u"Indo-European languages", u"indo-européennes, langues"],
    [u"inh", u"", u"", u"Ingush", u"ingouche"],
    [u"ipk", u"", u"ik", u"Inupiaq", u"inupiaq"],
    [u"ira", u"", u"", u"Iranian languages", u"iraniennes, langues"],
    [u"iro", u"", u"", u"Iroquoian languages", u"iroquoises, langues"],
    [u"ita", u"", u"it", u"Italian", u"italien"],
    [u"jav", u"", u"jv", u"Javanese", u"javanais"],
    [u"jbo", u"", u"", u"Lojban", u"lojban"],
    [u"jpn", u"", u"ja", u"Japanese", u"japonais"],
    [u"jpr", u"", u"", u"Judeo-Persian", u"judéo-persan"],
    [u"jrb", u"", u"", u"Judeo-Arabic", u"judéo-arabe"],
    [u"kaa", u"", u"", u"Kara-Kalpak", u"karakalpak"],
    [u"kab", u"", u"", u"Kabyle", u"kabyle"],
    [u"kac", u"", u"", u"Kachin; Jingpho", u"kachin; jingpho"],
    [u"kal", u"", u"kl", u"Kalaallisut; Greenlandic", u"groenlandais"],
    [u"kam", u"", u"", u"Kamba", u"kamba"],
    [u"kan", u"", u"kn", u"Kannada", u"kannada"],
    [u"kar", u"", u"", u"Karen languages", u"karen, langues"],
    [u"kas", u"", u"ks", u"Kashmiri", u"kashmiri"],
    [u"kau", u"", u"kr", u"Kanuri", u"kanouri"],
    [u"kaw", u"", u"", u"Kawi", u"kawi"],
    [u"kaz", u"", u"kk", u"Kazakh", u"kazakh"],
    [u"kbd", u"", u"", u"Kabardian", u"kabardien"],
    [u"kha", u"", u"", u"Khasi", u"khasi"],
    [u"khi", u"", u"", u"Khoisan languages", u"khoïsan, langues"],
    [u"khm", u"", u"km", u"Central Khmer", u"khmer central"],
    [u"kho", u"", u"", u"Khotanese; Sakan", u"khotanais; sakan"],
    [u"kik", u"", u"ki", u"Kikuyu; Gikuyu", u"kikuyu"],
    [u"kin", u"", u"rw", u"Kinyarwanda", u"rwanda"],
    [u"kir", u"", u"ky", u"Kirghiz; Kyrgyz", u"kirghiz"],
    [u"kmb", u"", u"", u"Kimbundu", u"kimbundu"],
    [u"kok", u"", u"", u"Konkani", u"konkani"],
    [u"kom", u"", u"kv", u"Komi", u"kom"],
    [u"kon", u"", u"kg", u"Kongo", u"kongo"],
    [u"kor", u"", u"ko", u"Korean", u"coréen"],
    [u"kos", u"", u"", u"Kosraean", u"kosrae"],
    [u"kpe", u"", u"", u"Kpelle", u"kpellé"],
    [u"krc", u"", u"", u"Karachay-Balkar", u"karatchai balkar"],
    [u"krl", u"", u"", u"Karelian", u"carélien"],
    [u"kro", u"", u"", u"Kru languages", u"krou, langues"],
    [u"kru", u"", u"", u"Kurukh", u"kurukh"],
    [u"kua", u"", u"kj", u"Kuanyama; Kwanyama", u"kuanyama; kwanyama"],
    [u"kum", u"", u"", u"Kumyk", u"koumyk"],
    [u"kur", u"", u"ku", u"Kurdish", u"kurde"],
    [u"kut", u"", u"", u"Kutenai", u"kutenai"],
    [u"lad", u"", u"", u"Ladino", u"judéo-espagnol"],
    [u"lah", u"", u"", u"Lahnda", u"lahnda"],
    [u"lam", u"", u"", u"Lamba", u"lamba"],
    [u"lao", u"", u"lo", u"Lao", u"lao"],
    [u"lat", u"", u"la", u"Latin", u"latin"],
    [u"lav", u"", u"lv", u"Latvian", u"letton"],
    [u"lez", u"", u"", u"Lezghian", u"lezghien"],
    [u"lim", u"", u"li", u"Limburgan; Limburger; Limburgish", u"limbourgeois"],
    [u"lin", u"", u"ln", u"Lingala", u"lingala"],
    [u"lit", u"", u"lt", u"Lithuanian", u"lituanien"],
    [u"lol", u"", u"", u"Mongo", u"mongo"],
    [u"loz", u"", u"", u"Lozi", u"lozi"],
    [u"ltz", u"", u"lb", u"Luxembourgish; Letzeburgesch", u"luxembourgeois"],
    [u"lua", u"", u"", u"Luba-Lulua", u"luba-lulua"],
    [u"lub", u"", u"lu", u"Luba-Katanga", u"luba-katanga"],
    [u"lug", u"", u"lg", u"Ganda", u"ganda"],
    [u"lui", u"", u"", u"Luiseno", u"luiseno"],
    [u"lun", u"", u"", u"Lunda", u"lunda"],
    [u"luo", u"", u"", u"Luo (Kenya and Tanzania)", u"luo (Kenya et Tanzanie)"],
    [u"lus", u"", u"", u"Lushai", u"lushai"],
    [u"mac", u"mkd", u"mk", u"Macedonian", u"macédonien"],
    [u"mad", u"", u"", u"Madurese", u"madourais"],
    [u"mag", u"", u"", u"Magahi", u"magahi"],
    [u"mah", u"", u"mh", u"Marshallese", u"marshall"],
    [u"mai", u"", u"", u"Maithili", u"maithili"],
    [u"mak", u"", u"", u"Makasar", u"makassar"],
    [u"mal", u"", u"ml", u"Malayalam", u"malayalam"],
    [u"man", u"", u"", u"Mandingo", u"mandingue"],
    [u"mao", u"mri", u"mi", u"Maori", u"maori"],
    [u"map", u"", u"", u"Austronesian languages", u"austronésiennes, langues"],
    [u"mar", u"", u"mr", u"Marathi", u"marathe"],
    [u"mas", u"", u"", u"Masai", u"massaï"],
    [u"may", u"msa", u"ms", u"Malay", u"malais"],
    [u"mdf", u"", u"", u"Moksha", u"moksa"],
    [u"mdr", u"", u"", u"Mandar", u"mandar"],
    [u"men", u"", u"", u"Mende", u"mendé"],
    [u"mga", u"", u"", u"Irish, Middle (900-1200)", u"irlandais moyen (900-1200)"],
    [u"mic", u"", u"", u"Mi'kmaq; Micmac", u"mi'kmaq; micmac"],
    [u"min", u"", u"", u"Minangkabau", u"minangkabau"],
    [u"mis", u"", u"", u"Uncoded languages", u"langues non codées"],
    [u"mkh", u"", u"", u"Mon-Khmer languages", u"môn-khmer, langues"],
    [u"mlg", u"", u"mg", u"Malagasy", u"malgache"],
    [u"mlt", u"", u"mt", u"Maltese", u"maltais"],
    [u"mnc", u"", u"", u"Manchu", u"mandchou"],
    [u"mni", u"", u"", u"Manipuri", u"manipuri"],
    [u"mno", u"", u"", u"Manobo languages", u"manobo, langues"],
    [u"moh", u"", u"", u"Mohawk", u"mohawk"],
    [u"mon", u"", u"mn", u"Mongolian", u"mongol"],
    [u"mos", u"", u"", u"Mossi", u"moré"],
    [u"mul", u"", u"", u"Multiple languages", u"multilingue"],
    [u"mun", u"", u"", u"Munda languages", u"mounda, langues"],
    [u"mus", u"", u"", u"Creek", u"muskogee"],
    [u"mwl", u"", u"", u"Mirandese", u"mirandais"],
    [u"mwr", u"", u"", u"Marwari", u"marvari"],
    [u"myn", u"", u"", u"Mayan languages", u"maya, langues"],
    [u"myv", u"", u"", u"Erzya", u"erza"],
    [u"nah", u"", u"", u"Nahuatl languages", u"nahuatl, langues"],
    [u"nai", u"", u"", u"North American Indian languages", u"nord-amérindiennes, langues"],
    [u"nap", u"", u"", u"Neapolitan", u"napolitain"],
    [u"nau", u"", u"na", u"Nauru", u"nauruan"],
    [u"nav", u"", u"nv", u"Navajo; Navaho", u"navaho"],
    [u"nbl", u"", u"nr", u"Ndebele, South; South Ndebele", u"ndébélé du Sud"],
    [u"nde", u"", u"nd", u"Ndebele, North; North Ndebele", u"ndébélé du Nord"],
    [u"ndo", u"", u"ng", u"Ndonga", u"ndonga"],
    [u"nds", u"", u"", u"Low German; Low Saxon; German, Low; Saxon, Low", u"bas allemand; bas saxon; allemand, bas; saxon, bas"],
    [u"nep", u"", u"ne", u"Nepali", u"népalais"],
    [u"new", u"", u"", u"Nepal Bhasa; Newari", u"nepal bhasa; newari"],
    [u"nia", u"", u"", u"Nias", u"nias"],
    [u"nic", u"", u"", u"Niger-Kordofanian languages", u"nigéro-kordofaniennes, langues"],
    [u"niu", u"", u"", u"Niuean", u"niué"],
    [u"nno", u"", u"nn", u"Norwegian Nynorsk; Nynorsk, Norwegian", u"norvégien nynorsk; nynorsk, norvégien"],
    [u"nob", u"", u"nb", u"Bokmål, Norwegian; Norwegian Bokmål", u"norvégien bokmål"],
    [u"nog", u"", u"", u"Nogai", u"nogaï; nogay"],
    [u"non", u"", u"", u"Norse, Old", u"norrois, vieux"],
    [u"nor", u"", u"no", u"Norwegian", u"norvégien"],
    [u"nqo", u"", u"", u"N'Ko", u"n'ko"],
    [u"nso", u"", u"", u"Pedi; Sepedi; Northern Sotho", u"pedi; sepedi; sotho du Nord"],
    [u"nub", u"", u"", u"Nubian languages", u"nubiennes, langues"],
    [u"nwc", u"", u"", u"Classical Newari; Old Newari; Classical Nepal Bhasa", u"newari classique"],
    [u"nya", u"", u"ny", u"Chichewa; Chewa; Nyanja", u"chichewa; chewa; nyanja"],
    [u"nym", u"", u"", u"Nyamwezi", u"nyamwezi"],
    [u"nyn", u"", u"", u"Nyankole", u"nyankolé"],
    [u"nyo", u"", u"", u"Nyoro", u"nyoro"],
    [u"nzi", u"", u"", u"Nzima", u"nzema"],
    [u"oci", u"", u"oc", u"Occitan (post 1500); Provençal", u"occitan (après 1500); provençal"],
    [u"oji", u"", u"oj", u"Ojibwa", u"ojibwa"],
    [u"ori", u"", u"or", u"Oriya", u"oriya"],
    [u"orm", u"", u"om", u"Oromo", u"galla"],
    [u"osa", u"", u"", u"Osage", u"osage"],
    [u"oss", u"", u"os", u"Ossetian; Ossetic", u"ossète"],
    [u"ota", u"", u"", u"Turkish, Ottoman (1500-1928)", u"turc ottoman (1500-1928)"],
    [u"oto", u"", u"", u"Otomian languages", u"otomi, langues"],
    [u"paa", u"", u"", u"Papuan languages", u"papoues, langues"],
    [u"pag", u"", u"", u"Pangasinan", u"pangasinan"],
    [u"pal", u"", u"", u"Pahlavi", u"pahlavi"],
    [u"pam", u"", u"", u"Pampanga; Kapampangan", u"pampangan"],
    [u"pan", u"", u"pa", u"Panjabi; Punjabi", u"pendjabi"],
    [u"pap", u"", u"", u"Papiamento", u"papiamento"],
    [u"pau", u"", u"", u"Palauan", u"palau"],
    [u"peo", u"", u"", u"Persian, Old (ca.600-400 B.C.)", u"perse, vieux (ca. 600-400 av. J.-C.)"],
    [u"per", u"fas", u"fa", u"Persian", u"persan"],
    [u"phi", u"", u"", u"Philippine languages", u"philippines, langues"],
    [u"phn", u"", u"", u"Phoenician", u"phénicien"],
    [u"pli", u"", u"pi", u"Pali", u"pali"],
    [u"pol", u"", u"pl", u"Polish", u"polonais"],
    [u"pon", u"", u"", u"Pohnpeian", u"pohnpei"],
    [u"por", u"", u"pt", u"Portuguese", u"portugais"],
    [u"pra", u"", u"", u"Prakrit languages", u"prâkrit, langues"],
    [u"pro", u"", u"", u"Provençal, Old (to 1500)", u"provençal ancien (jusqu'à 1500)"],
    [u"pus", u"", u"ps", u"Pushto; Pashto", u"pachto"],
    [u"qaa-qtz", u"", u"", u"Reserved for local use", u"réservée à l'usage local"],
    [u"que", u"", u"qu", u"Quechua", u"quechua"],
    [u"raj", u"", u"", u"Rajasthani", u"rajasthani"],
    [u"rap", u"", u"", u"Rapanui", u"rapanui"],
    [u"rar", u"", u"", u"Rarotongan; Cook Islands Maori", u"rarotonga; maori des îles Cook"],
    [u"roa", u"", u"", u"Romance languages", u"romanes, langues"],
    [u"roh", u"", u"rm", u"Romansh", u"romanche"],
    [u"rom", u"", u"", u"Romany", u"tsigane"],
    [u"rum", u"ron", u"ro", u"Romanian; Moldavian; Moldovan", u"roumain; moldave"],
    [u"run", u"", u"rn", u"Rundi", u"rundi"],
    [u"rup", u"", u"", u"Aromanian; Arumanian; Macedo-Romanian", u"aroumain; macédo-roumain"],
    [u"rus", u"", u"ru", u"Russian", u"russe"],
    [u"sad", u"", u"", u"Sandawe", u"sandawe"],
    [u"sag", u"", u"sg", u"Sango", u"sango"],
    [u"sah", u"", u"", u"Yakut", u"iakoute"],
    [u"sai", u"", u"", u"South American Indian (Other)", u"indiennes d'Amérique du Sud, autres langues"],
    [u"sal", u"", u"", u"Salishan languages", u"salishennes, langues"],
    [u"sam", u"", u"", u"Samaritan Aramaic", u"samaritain"],
    [u"san", u"", u"sa", u"Sanskrit", u"sanskrit"],
    [u"sas", u"", u"", u"Sasak", u"sasak"],
    [u"sat", u"", u"", u"Santali", u"santal"],
    [u"scn", u"", u"", u"Sicilian", u"sicilien"],
    [u"sco", u"", u"", u"Scots", u"écossais"],
    [u"sel", u"", u"", u"Selkup", u"selkoupe"],
    [u"sem", u"", u"", u"Semitic languages", u"sémitiques, langues"],
    [u"sga", u"", u"", u"Irish, Old (to 900)", u"irlandais ancien (jusqu'à 900)"],
    [u"sgn", u"", u"", u"Sign Languages", u"langues des signes"],
    [u"shn", u"", u"", u"Shan", u"chan"],
    [u"sid", u"", u"", u"Sidamo", u"sidamo"],
    [u"sin", u"", u"si", u"Sinhala; Sinhalese", u"singhalais"],
    [u"sio", u"", u"", u"Siouan languages", u"sioux, langues"],
    [u"sit", u"", u"", u"Sino-Tibetan languages", u"sino-tibétaines, langues"],
    [u"sla", u"", u"", u"Slavic languages", u"slaves, langues"],
    [u"slo", u"slk", u"sk", u"Slovak", u"slovaque"],
    [u"slv", u"", u"sl", u"Slovenian", u"slovène"],
    [u"sma", u"", u"", u"Southern Sami", u"sami du Sud"],
    [u"sme", u"", u"se", u"Northern Sami", u"sami du Nord"],
    [u"smi", u"", u"", u"Sami languages", u"sames, langues"],
    [u"smj", u"", u"", u"Lule Sami", u"sami de Lule"],
    [u"smn", u"", u"", u"Inari Sami", u"sami d'Inari"],
    [u"smo", u"", u"sm", u"Samoan", u"samoan"],
    [u"sms", u"", u"", u"Skolt Sami", u"sami skolt"],
    [u"sna", u"", u"sn", u"Shona", u"shona"],
    [u"snd", u"", u"sd", u"Sindhi", u"sindhi"],
    [u"snk", u"", u"", u"Soninke", u"soninké"],
    [u"sog", u"", u"", u"Sogdian", u"sogdien"],
    [u"som", u"", u"so", u"Somali", u"somali"],
    [u"son", u"", u"", u"Songhai languages", u"songhai, langues"],
    [u"sot", u"", u"st", u"Sotho, Southern", u"sotho du Sud"],
    [u"spa", u"", u"es", u"Spanish; Castilian", u"espagnol; castillan"],
    [u"srd", u"", u"sc", u"Sardinian", u"sarde"],
    [u"srn", u"", u"", u"Sranan Tongo", u"sranan tongo"],
    [u"srp", u"", u"sr", u"Serbian", u"serbe"],
    [u"srr", u"", u"", u"Serer", u"sérère"],
    [u"ssa", u"", u"", u"Nilo-Saharan languages", u"nilo-sahariennes, langues"],
    [u"ssw", u"", u"ss", u"Swati", u"swati"],
    [u"suk", u"", u"", u"Sukuma", u"sukuma"],
    [u"sun", u"", u"su", u"Sundanese", u"soundanais"],
    [u"sus", u"", u"", u"Susu", u"soussou"],
    [u"sux", u"", u"", u"Sumerian", u"sumérien"],
    [u"swa", u"", u"sw", u"Swahili", u"swahili"],
    [u"swe", u"", u"sv", u"Swedish", u"suédois"],
    [u"syc", u"", u"", u"Classical Syriac", u"syriaque classique"],
    [u"syr", u"", u"", u"Syriac", u"syriaque"],
    [u"tah", u"", u"ty", u"Tahitian", u"tahitien"],
    [u"tai", u"", u"", u"Tai languages", u"tai, langues"],
    [u"tam", u"", u"ta", u"Tamil", u"tamoul"],
    [u"tat", u"", u"tt", u"Tatar", u"tatar"],
    [u"tel", u"", u"te", u"Telugu", u"télougou"],
    [u"tem", u"", u"", u"Timne", u"temne"],
    [u"ter", u"", u"", u"Tereno", u"tereno"],
    [u"tet", u"", u"", u"Tetum", u"tetum"],
    [u"tgk", u"", u"tg", u"Tajik", u"tadjik"],
    [u"tgl", u"", u"tl", u"Tagalog", u"tagalog"],
    [u"tha", u"", u"th", u"Thai", u"thaï"],
    [u"tib", u"bod", u"bo", u"Tibetan", u"tibétain"],
    [u"tig", u"", u"", u"Tigre", u"tigré"],
    [u"tir", u"", u"ti", u"Tigrinya", u"tigrigna"],
    [u"tiv", u"", u"", u"Tiv", u"tiv"],
    [u"tkl", u"", u"", u"Tokelau", u"tokelau"],
    [u"tlh", u"", u"", u"Klingon; tlhIngan-Hol", u"klingon"],
    [u"tli", u"", u"", u"Tlingit", u"tlingit"],
    [u"tmh", u"", u"", u"Tamashek", u"tamacheq"],
    [u"tog", u"", u"", u"Tonga (Nyasa)", u"tonga (Nyasa)"],
    [u"ton", u"", u"to", u"Tonga (Tonga Islands)", u"tongan (Îles Tonga)"],
    [u"tpi", u"", u"", u"Tok Pisin", u"tok pisin"],
    [u"tsi", u"", u"", u"Tsimshian", u"tsimshian"],
    [u"tsn", u"", u"tn", u"Tswana", u"tswana"],
    [u"tso", u"", u"ts", u"Tsonga", u"tsonga"],
    [u"tuk", u"", u"tk", u"Turkmen", u"turkmène"],
    [u"tum", u"", u"", u"Tumbuka", u"tumbuka"],
    [u"tup", u"", u"", u"Tupi languages", u"tupi, langues"],
    [u"tur", u"", u"tr", u"Turkish", u"turc"],
    [u"tut", u"", u"", u"Altaic languages", u"altaïques, langues"],
    [u"tvl", u"", u"", u"Tuvalu", u"tuvalu"],
    [u"twi", u"", u"tw", u"Twi", u"twi"],
    [u"tyv", u"", u"", u"Tuvinian", u"touva"],
    [u"udm", u"", u"", u"Udmurt", u"oudmourte"],
    [u"uga", u"", u"", u"Ugaritic", u"ougaritique"],
    [u"uig", u"", u"ug", u"Uighur; Uyghur", u"ouïgour"],
    [u"ukr", u"", u"uk", u"Ukrainian", u"ukrainien"],
    [u"umb", u"", u"", u"Umbundu", u"umbundu"],
    [u"und", u"", u"", u"Undetermined", u"indéterminée"],
    [u"urd", u"", u"ur", u"Urdu", u"ourdou"],
    [u"uzb", u"", u"uz", u"Uzbek", u"ouszbek"],
    [u"vai", u"", u"", u"Vai", u"vaï"],
    [u"ven", u"", u"ve", u"Venda", u"venda"],
    [u"vie", u"", u"vi", u"Vietnamese", u"vietnamien"],
    [u"vol", u"", u"vo", u"Volapük", u"volapük"],
    [u"vot", u"", u"", u"Votic", u"vote"],
    [u"wak", u"", u"", u"Wakashan languages", u"wakashanes, langues"],
    [u"wal", u"", u"", u"Walamo", u"walamo"],
    [u"war", u"", u"", u"Waray", u"waray"],
    [u"was", u"", u"", u"Washo", u"washo"],
    [u"wel", u"cym", u"cy", u"Welsh", u"gallois"],
    [u"wen", u"", u"", u"Sorbian languages", u"sorabes, langues"],
    [u"wln", u"", u"wa", u"Walloon", u"wallon"],
    [u"wol", u"", u"wo", u"Wolof", u"wolof"],
    [u"xal", u"", u"", u"Kalmyk; Oirat", u"kalmouk; oïrat"],
    [u"xho", u"", u"xh", u"Xhosa", u"xhosa"],
    [u"yao", u"", u"", u"Yao", u"yao"],
    [u"yap", u"", u"", u"Yapese", u"yapois"],
    [u"yid", u"", u"yi", u"Yiddish", u"yiddish"],
    [u"yor", u"", u"yo", u"Yoruba", u"yoruba"],
    [u"ypk", u"", u"", u"Yupik languages", u"yupik, langues"],
    [u"zap", u"", u"", u"Zapotec", u"zapotèque"],
    [u"zbl", u"", u"", u"Blissymbols; Blissymbolics; Bliss", u"symboles Bliss; Bliss"],
    [u"zen", u"", u"", u"Zenaga", u"zenaga"],
    [u"zha", u"", u"za", u"Zhuang; Chuang", u"zhuang; chuang"],
    [u"znd", u"", u"", u"Zande languages", u"zandé, langues"],
    [u"zul", u"", u"zu", u"Zulu", u"zoulou"],
    [u"zun", u"", u"", u"Zuni", u"zuni"],
    [u"zxx", u"", u"", u"No linguistic content; Not applicable", u"pas de contenu linguistique; non applicable"],
    [u"zza", u"", u"", u"Zaza; Dimili; Dimli; Kirdki; Kirmanjki; Zazaki", u"zaza; dimili; dimli; kirdki; kirmanjki; zazaki"]
]

# ok, but we don't care about the Aramaic Empire ... we only want the ISO639-1 subset of those (the ones with 2-char codes)
languages = {}
languages_fullname_to_3char_code = {}
languages_3char_code_index = []
for l in languages_iso639_2:
    if l[2]:
        twochar_code = l[2].upper()
        lobj = {
            "iso639-2_code": twochar_code,
            "iso639-3_code": l[0].upper(),
            "iso639-3_altcode": l[1].upper(),
            "name": l[3]
        }
        languages[twochar_code] = lobj
        languages_3char_code_index.append(l[0].upper())

    if l[3] and l[0]:  # if a name and a 3-char code exist for this lang
        languages_fullname_to_3char_code[l[3]] = l[0]

languages_dict = OrderedDict(sorted(languages.items(), key=lambda x: x[1]['name']))
languages = languages_dict.items()

# Gather the languages with 2-character codes (ISO639-1)
language_options = []
language_options_two_char_code_index = []
for l in sorted(pycountry.languages, key=lambda x: x.name):
    try:
        language_options.append((l.alpha_2.upper(), l.name))
        language_options_two_char_code_index.append(l.alpha_2.upper())
    except AttributeError:
        continue

# license rights by license type
licenses = {
    # the titles and types are made to match the current values of
    # journals in the DOAJ for now - they can be cleaned up but it might
    # not be such a small job
    # Also DOAJ currently assumes type and title are the same.
    "CC BY": {'BY': True, 'NC': False, 'ND': False, 'SA': False, 'form_label': 'CC BY'},
    "CC BY-SA": {'BY': True, 'NC': False, 'ND': False, 'SA': True, 'form_label': 'CC BY-SA'},
    "CC BY-NC": {'BY': True, 'NC': True, 'ND': False, 'SA': False, 'form_label': 'CC BY-NC'},
    "CC BY-ND": {'BY': True, 'NC': False, 'ND': True, 'SA': False, 'form_label': 'CC BY-ND'},
    "CC BY-NC-ND": {'BY': True, 'NC': True, 'ND': True, 'SA': False, 'form_label': 'CC BY-NC-ND'},
    "CC BY-NC-SA": {'BY': True, 'NC': True, 'ND': False, 'SA': True, 'form_label': 'CC BY-NC-SA'},
}

for lic_type, lic_info in licenses.iteritems():
    lic_info['type'] = lic_type  # do not change this - the top-level keys in the licenses dict should always be == to the "type" of each license object
    lic_info['title'] = lic_type

license_dict = OrderedDict(sorted(licenses.items(), key=lambda x: x[1]['type']))

main_license_options = []
for lic_type, lic_info in license_dict.iteritems():
    main_license_options.append((lic_type, lic_info['form_label']))


def name_for_lang(rep):
    """ Get the language name from a representation of the language"""
    try:
        return pycountry.languages.lookup(rep).name
    except LookupError:
        return rep


def get_country_code(current_country, fail_if_not_found=False):
    """ Get the two-character country code for a given country name """
    try:
        return pycountry.countries.lookup(current_country).alpha_2
    except LookupError:
        return None if fail_if_not_found else current_country


def get_country_name(code):
    """ Get the name of a country from its two-character code """
    try:
        return pycountry.countries.lookup(code).name
    except LookupError:
        return code  # return what was passed in if not found


def get_currency_name(code):
    """ get the name of a currency from its code """
    try:
        cur = pycountry.currencies.lookup(code)
        return '{code} - {name}'.format(code=cur.alpha_3, name=cur.name)
    except LookupError:
        return code  # return what was passed in if not found


def get_currency_code(name):
    """ Retrieve a currency code by the currency name """
    try:
        return pycountry.currencies.lookup(name).alpha_3
    except LookupError:
        return None
