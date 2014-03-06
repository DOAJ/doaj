import json
import sys

if sys.version_info[0] == 2 and sys.version_info[1] < 7:
    from portality.ordereddict import OrderedDict
else:
    from collections import OrderedDict

# countries
with open('country-codes.json', 'rb') as f:
    countries = json.loads(f.read())
countries_dict = OrderedDict(sorted(countries.items(), key=lambda x: x[1]['name']))
countries = countries_dict.items()
country_options = [('','')]
country_options_two_char_code_index = []
for code, country_info in countries:
    country_options.append((code, country_info['name']))
    country_options_two_char_code_index.append(code)
