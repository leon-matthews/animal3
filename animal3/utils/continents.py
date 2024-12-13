
from typing import List

from animal3.utils.iso_3166 import ALPHA_2


def find_continent(country_code: str) -> (str, str):
    """
    Find continent from given country code.

    Args:
        code:
            2-character country code for a country

    Raises:
        KeyError:
            If country code is invalid.

    Returns:
        2-tuple containing continent code name, in that order.
    """
    try:
        continent = ALPHA2_TO_CONTINENT[country_code]
    except KeyError:
        raise KeyError(f"Invalid country code: {country_code!r}") from None
    return continent


def find_countries(continent_code: str) -> List[str]:
    """
    Build sorted list of country ALPHA_2 codes for the given continent code.
    """
    country_codes = []

    for alpha2, _ in ALPHA_2:
        continent = ALPHA2_TO_CONTINENT[alpha2]
        if continent == continent_code:
            country_codes.append(alpha2)

    country_codes.sort()
    return country_codes


def in_africa(code: str) -> bool:
    """
    Is the given 2-character country code for a country in Africa?
    """
    return code in AFRICA


def in_antarctica(code: str) -> bool:
    """
    Is the given 2-character country code for a country in Antarctica?
    """
    return code in ANTARCTICA


def in_asia(code: str) -> bool:
    """
    Is the given 2-character country code for a country in Asia?
    """
    return code in ASIA


def in_europe(code: str) -> bool:
    """
    Is the given 2-character country code for a country in Europe?
    """
    return code in EUROPE


def in_north_america(code: str) -> bool:
    """
    Is the given 2-character country code for a country in North America?
    """
    return code in NORTH_AMERICA


def in_oceania(code: str) -> bool:
    """
    Is the given 2-character country code for a country in Oceania?
    """
    return code in OCEANIA


def in_south_america(code: str) -> bool:
    """
    Is the given 2-character country code for a country in South America?
    """
    return code in SOUTH_AMERICA


"""
Mapping between continent code and its name.
"""
CONTINENTS = {
    "AF": "Africa",
    "AN": "Antarctica",
    "AS": "Asia",
    "EU": "Europe",
    "NA": "North America",
    "OC": "Oceania",
    "SA": "South America",
}


"""
Mapping between ISO-3166 ALPHA_2 country codes and continents.
"""
ALPHA2_TO_CONTINENT = {
    "AD": "EU",
    "AE": "AS",
    "AF": "AS",
    "AG": "NA",
    "AI": "NA",
    "AL": "EU",
    "AM": "AS",
    "AO": "AF",
    "AQ": "AN",
    "AR": "SA",
    "AS": "OC",
    "AT": "EU",
    "AU": "OC",
    "AW": "NA",
    "AX": "EU",
    "AZ": "AS",
    "BA": "EU",
    "BB": "NA",
    "BD": "AS",
    "BE": "EU",
    "BF": "AF",
    "BG": "EU",
    "BH": "AS",
    "BI": "AF",
    "BJ": "AF",
    "BL": "NA",
    "BM": "NA",
    "BN": "AS",
    "BO": "SA",
    "BQ": "NA",
    "BR": "SA",
    "BS": "NA",
    "BT": "AS",
    "BV": "AN",
    "BW": "AF",
    "BY": "EU",
    "BZ": "NA",
    "CA": "NA",
    "CC": "AS",
    "CD": "AF",
    "CF": "AF",
    "CG": "AF",
    "CH": "EU",
    "CI": "AF",
    "CK": "OC",
    "CL": "SA",
    "CM": "AF",
    "CN": "AS",
    "CO": "SA",
    "CR": "NA",
    "CU": "NA",
    "CV": "AF",
    "CW": "NA",
    "CX": "AS",
    "CY": "AS",
    "CZ": "EU",
    "DE": "EU",
    "DJ": "AF",
    "DK": "EU",
    "DM": "NA",
    "DO": "NA",
    "DZ": "AF",
    "EC": "SA",
    "EE": "EU",
    "EG": "AF",
    "EH": "AF",
    "ER": "AF",
    "ES": "EU",
    "ET": "AF",
    "FI": "EU",
    "FJ": "OC",
    "FK": "SA",
    "FM": "OC",
    "FO": "EU",
    "FR": "EU",
    "GA": "AF",
    "GB": "EU",
    "GD": "NA",
    "GE": "AS",
    "GF": "SA",
    "GG": "EU",
    "GH": "AF",
    "GI": "EU",
    "GL": "NA",
    "GM": "AF",
    "GN": "AF",
    "GP": "NA",
    "GQ": "AF",
    "GR": "EU",
    "GS": "AN",
    "GT": "NA",
    "GU": "OC",
    "GW": "AF",
    "GY": "SA",
    "HK": "AS",
    "HM": "AN",
    "HN": "NA",
    "HR": "EU",
    "HT": "NA",
    "HU": "EU",
    "ID": "AS",
    "IE": "EU",
    "IL": "AS",
    "IM": "EU",
    "IN": "AS",
    "IO": "AF",
    "IQ": "AS",
    "IR": "AS",
    "IS": "EU",
    "IT": "EU",
    "JE": "EU",
    "JM": "NA",
    "JO": "AS",
    "JP": "AS",
    "KE": "AF",
    "KG": "AS",
    "KH": "AS",
    "KI": "OC",
    "KM": "AF",
    "KN": "NA",
    "KP": "AS",
    "KR": "AS",
    "KW": "AS",
    "KY": "NA",
    "KZ": "AS",
    "LA": "AS",
    "LB": "AS",
    "LC": "NA",
    "LI": "EU",
    "LK": "AS",
    "LR": "AF",
    "LS": "AF",
    "LT": "EU",
    "LU": "EU",
    "LV": "EU",
    "LY": "AF",
    "MA": "AF",
    "MC": "EU",
    "MD": "EU",
    "ME": "EU",
    "MF": "NA",
    "MG": "AF",
    "MH": "OC",
    "MK": "EU",
    "ML": "AF",
    "MM": "AS",
    "MN": "AS",
    "MO": "AS",
    "MP": "OC",
    "MQ": "NA",
    "MR": "AF",
    "MS": "NA",
    "MT": "EU",
    "MU": "AF",
    "MV": "AS",
    "MW": "AF",
    "MX": "NA",
    "MY": "AS",
    "MZ": "AF",
    "NA": "AF",
    "NC": "OC",
    "NE": "AF",
    "NF": "OC",
    "NG": "AF",
    "NI": "NA",
    "NL": "EU",
    "NO": "EU",
    "NP": "AS",
    "NR": "OC",
    "NU": "OC",
    "NZ": "OC",
    "OM": "AS",
    "PA": "NA",
    "PE": "SA",
    "PF": "OC",
    "PG": "OC",
    "PH": "AS",
    "PK": "AS",
    "PL": "EU",
    "PM": "NA",
    "PN": "OC",
    "PR": "NA",
    "PS": "AS",
    "PT": "EU",
    "PW": "OC",
    "PY": "SA",
    "QA": "AS",
    "RE": "AF",
    "RO": "EU",
    "RS": "EU",
    "RU": "EU",
    "RW": "AF",
    "SA": "AS",
    "SB": "OC",
    "SC": "AF",
    "SD": "AF",
    "SE": "EU",
    "SG": "AS",
    "SH": "AF",
    "SI": "EU",
    "SJ": "EU",
    "SK": "EU",
    "SL": "AF",
    "SM": "EU",
    "SN": "AF",
    "SO": "AF",
    "SR": "SA",
    "SS": "AF",
    "ST": "AF",
    "SV": "NA",
    "SX": "NA",
    "SY": "AS",
    "SZ": "AF",
    "TC": "NA",
    "TD": "AF",
    "TF": "AF",
    "TG": "AF",
    "TH": "AS",
    "TJ": "AS",
    "TK": "OC",
    "TL": "AS",
    "TM": "AS",
    "TN": "AF",
    "TO": "OC",
    "TR": "AS",
    "TT": "NA",
    "TV": "OC",
    "TW": "AS",
    "TZ": "AF",
    "UA": "EU",
    "UG": "AF",
    "UM": "OC",
    "US": "NA",
    "UY": "SA",
    "UZ": "AS",
    "VA": "EU",
    "VC": "NA",
    "VE": "SA",
    "VG": "NA",
    "VI": "NA",
    "VN": "AS",
    "VU": "OC",
    "WF": "OC",
    "WS": "OC",
    "XD": "AS",
    "XK": "EU",
    "XS": "AS",
    "XX": "OC",
    "YE": "AS",
    "YT": "AF",
    "ZA": "AF",
    "ZM": "AF",
    "ZW": "AF",
}


AFRICA = {
    'AO',
    'BF',
    'BI',
    'BJ',
    'BW',
    'CD',
    'CF',
    'CG',
    'CI',
    'CM',
    'CV',
    'DJ',
    'DZ',
    'EG',
    'EH',
    'ER',
    'ET',
    'GA',
    'GH',
    'GM',
    'GN',
    'GQ',
    'GW',
    'IO',
    'KE',
    'KM',
    'LR',
    'LS',
    'LY',
    'MA',
    'MG',
    'ML',
    'MR',
    'MU',
    'MW',
    'MZ',
    'NA',
    'NE',
    'NG',
    'RE',
    'RW',
    'SC',
    'SD',
    'SH',
    'SL',
    'SN',
    'SO',
    'SS',
    'ST',
    'SZ',
    'TD',
    'TF',
    'TG',
    'TN',
    'TZ',
    'UG',
    'YT',
    'ZA',
    'ZM',
    'ZW',
}


ANTARCTICA = {
    'AQ',
    'BV',
    'GS',
    'HM',
}


ASIA = {
    'AE',
    'AF',
    'AM',
    'AZ',
    'BD',
    'BH',
    'BN',
    'BT',
    'CC',
    'CN',
    'CX',
    'CY',
    'GE',
    'HK',
    'ID',
    'IL',
    'IN',
    'IQ',
    'IR',
    'JO',
    'JP',
    'KG',
    'KH',
    'KP',
    'KR',
    'KW',
    'KZ',
    'LA',
    'LB',
    'LK',
    'MM',
    'MN',
    'MO',
    'MV',
    'MY',
    'NP',
    'OM',
    'PH',
    'PK',
    'PS',
    'QA',
    'SA',
    'SG',
    'SY',
    'TH',
    'TJ',
    'TL',
    'TM',
    'TR',
    'TW',
    'UZ',
    'VN',
    'YE',
}


EUROPE = {
    'AD',
    'AL',
    'AT',
    'AX',
    'BA',
    'BE',
    'BG',
    'BY',
    'CH',
    'CZ',
    'DE',
    'DK',
    'EE',
    'ES',
    'FI',
    'FO',
    'FR',
    'GB',
    'GG',
    'GI',
    'GR',
    'HR',
    'HU',
    'IE',
    'IM',
    'IS',
    'IT',
    'JE',
    'LI',
    'LT',
    'LU',
    'LV',
    'MC',
    'MD',
    'ME',
    'MK',
    'MT',
    'NL',
    'NO',
    'PL',
    'PT',
    'RO',
    'RS',
    'RU',
    'SE',
    'SI',
    'SJ',
    'SK',
    'SM',
    'UA',
    'VA',
    'XK',
}


NORTH_AMERICA = {
    'AG',
    'AI',
    'AW',
    'BB',
    'BL',
    'BM',
    'BQ',
    'BS',
    'BZ',
    'CA',
    'CR',
    'CU',
    'CW',
    'DM',
    'DO',
    'GD',
    'GL',
    'GP',
    'GT',
    'HN',
    'HT',
    'JM',
    'KN',
    'KY',
    'LC',
    'MF',
    'MQ',
    'MS',
    'MX',
    'NI',
    'PA',
    'PM',
    'PR',
    'SV',
    'SX',
    'TC',
    'TT',
    'US',
    'VC',
    'VG',
    'VI',
}


OCEANIA = {
    'AS',
    'AU',
    'CK',
    'FJ',
    'FM',
    'GU',
    'KI',
    'MH',
    'MP',
    'NC',
    'NF',
    'NR',
    'NU',
    'NZ',
    'PF',
    'PG',
    'PN',
    'PW',
    'SB',
    'TK',
    'TO',
    'TV',
    'UM',
    'VU',
    'WF',
    'WS',
}


SOUTH_AMERICA = {
    'AR',
    'BO',
    'BR',
    'CL',
    'CO',
    'EC',
    'FK',
    'GF',
    'GY',
    'PE',
    'PY',
    'SR',
    'UY',
    'VE',
}
