from portality.datasets import countries_dict, countries, country_options_two_char_code_index

def get_country_code(current_country):
    new_country = current_country
    if new_country:
        if new_country not in country_options_two_char_code_index:
            for two_char_code, info in countries:
                if new_country.lower() == info['name'].lower():
                    new_country = two_char_code
                    break
                
                if new_country.lower() == info['ISO3166-1-Alpha-3'].lower():
                    new_country = two_char_code
                    break

                if info['name'].lower().startswith(new_country.lower()):
                    new_country = two_char_code

    return new_country

def get_country_name(code):
    return countries_dict.get(code, {}).get('name', code)  # return what was passed in if not found
