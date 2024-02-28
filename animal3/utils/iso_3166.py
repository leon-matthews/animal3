"""
ISO 3166-1 country names and codes.

The format of all three lists is a tuple of 2-tuples for ease of use with
Django model field choices.  All lists are ordered by country name.  Country
names are Unicode, encoded using utf-8.

For fast conversion from key to country name create a dictionary as follows::

    >>> m = dict(ALPHA_2)
    >>> len(m)
    250
    >>> m['NZ']
    'New Zealand'

List details:

ALPHA_2
    Two-letter country codes which are the most widely used
    of the three, and used most prominently for the Internet's country code
    top-level domains (with a few exceptions).

ALPHA_3
    Three-letter country codes which allow a better visual association
    between the codes and the country names than the alpha-2 codes.

NUMERIC
    Three-digit country codes which are identical to those developed and
    maintained by the United Nations Statistics Division, with the advantage
    of script (writing system) independence, and hence useful for people or
    systems using non-Latin scripts.
"""

from typing import Iterable, Optional, Tuple

from django.core.exceptions import ValidationError


Cities = Iterable[Tuple[str, str]]


def guess_country_code(
        address: str, *,
        cities: Optional[Cities] = None,
        default: Optional[str] = None) -> Optional[str]:
    """
    Attempt to guess the country-code given address refers to.

    It does this by looking for country names, then country codes at the
    end of the address. If all of that fails it will attempt to find a match
    using the optional cities list, if provided.

    For example::

        >>> address = (
        ...   "Burgemeester van Leeuwenlaan 59, "
        ...   "1064 KL Amsterdam, "
        ...   "Netherlands ")
        >>> guess_country_code(address)
        'NL'

    Args:
        address:
            Full, possibly multi-line address.
        cities (list of 2-tuples):

            eg.[('RU', 'St. Petersburg'),
                ('JP', 'Tokyo'),
                ('JP', 'Okinawa'),
                ('ZA', 'Johannesburg')]
        default:
            Value to use if no match is made. Defaults to None.

    Returns (str|None):
        A two-letter country code, or `None`.

    """
    address = address.lower()
    if cities is None:
        cities = []

    # Look for full country name, preferable at the end of the address
    current: Tuple[int, Optional[str]] = (0, None)
    for code, name in ALPHA_2:
        pos = address.find(name.lower())
        if pos > current[0]:
            current = (pos, code)
    if current[1] is not None:
        return current[1]

    # Look for a country code at the very end of the address
    address = address.strip()
    suffix = address[-2:].upper()
    if suffix == 'UK':
        suffix = 'GB'
    for code, name in ALPHA_2:
        if code == suffix:
            return code

    # Still nothing?! Bring out the cities
    for code, name in cities:
        code = code.upper()
        name = name.lower()
        if name in address:
            return code

    return default


def validate_iso_3166_alpha_2(value: str) -> None:
    """
    Django validator for a country code in the ISO-3166 ALPHA2 format, eg. 'NZ'

    Args:
        value: 2-character country code string

    Raises:
        ValidationError: If validation fails.

    See:
        https://docs.djangoproject.com/en/stable/ref/validators/
    """
    # Two characters long
    if len(value) != 2:
        message = "Given value ({!r}) must be two characters long"
        raise ValidationError(message.format(value))

    # Upper-case
    if value != value.upper():
        message = "Given value ({!r}) is not upper-case"
        raise ValidationError(message.format(value))

    # A valid code
    found = [x[0] for x in ALPHA_2 if x[0] == value]
    if not found:
        message = "Given value ({!r}) is not a valid ISO 3166 alpha-2 country code"
        raise ValidationError(message.format(value))


def validate_iso_3166_alpha_3(value: str) -> None:
    """
    Django validator for a country code in the ISO-3166 ALPHA2 format, eg. 'NZL'

    Args:
        value: 3-character country code string

    Raises:
        ValidationError: If validation fails.

    See:
        https://docs.djangoproject.com/en/stable/ref/validators/
    """
    # Three characters long
    if len(value) != 3:
        message = "Given value ({!r}) must be three characters long"
        raise ValidationError(message.format(value))

    # Upper-case
    if value != value.upper():
        message = "Given value ({!r}) is not upper-case"
        raise ValidationError(message.format(value))

    # A valid code
    found = [x[0] for x in ALPHA_3 if x[0] == value]
    if not found:
        message = "Given value ({!r}) is not a valid ISO 3166 alpha-3 country code"
        raise ValidationError(message.format(value))


def validate_iso_3166_numeric(value: int) -> None:
    """
    Django validator for a country code in the ISO-3166 ALPHA2 format, eg. 554

    Args:
        value: 2-character country code string

    Raises:
        ValidationError: If validation fails.

    See:
        https://docs.djangoproject.com/en/stable/ref/validators/
    """
    # An integer
    try:
        value = int(value)
    except ValueError:
        message = "Given value ({!r}) must be an integer"
        raise ValidationError(message.format(value))

    # A valid code
    found = [x[0] for x in NUMERIC if x[0] == value]
    if not found:
        message = "Given value ({!r}) is not a valid ISO 3166 numeric country code"
        raise ValidationError(message.format(value))


ALPHA_2 = (
    ("AF", "Afghanistan"),
    ("AX", "Åland Islands"),
    ("AL", "Albania"),
    ("DZ", "Algeria"),
    ("AS", "American Samoa"),
    ("AD", "Andorra"),
    ("AO", "Angola"),
    ("AI", "Anguilla"),
    ("AQ", "Antarctica"),
    ("AG", "Antigua and Barbuda"),
    ("AR", "Argentina"),
    ("AM", "Armenia"),
    ("AW", "Aruba"),
    ("AU", "Australia"),
    ("AT", "Austria"),
    ("AZ", "Azerbaijan"),
    ("BS", "Bahamas"),
    ("BH", "Bahrain"),
    ("BD", "Bangladesh"),
    ("BB", "Barbados"),
    ("BY", "Belarus"),
    ("BE", "Belgium"),
    ("BZ", "Belize"),
    ("BJ", "Benin"),
    ("BM", "Bermuda"),
    ("BT", "Bhutan"),
    ("BO", "Bolivia, Plurinational State of"),
    ("BQ", "Bonaire, Sint Eustatius and Saba"),
    ("BA", "Bosnia and Herzegovina"),
    ("BW", "Botswana"),
    ("BV", "Bouvet Island"),
    ("BR", "Brazil"),
    ("IO", "British Indian Ocean Territory"),
    ("BN", "Brunei Darussalam"),
    ("BG", "Bulgaria"),
    ("BF", "Burkina Faso"),
    ("BI", "Burundi"),
    ("KH", "Cambodia"),
    ("CM", "Cameroon"),
    ("CA", "Canada"),
    ("CV", "Cape Verde"),
    ("KY", "Cayman Islands"),
    ("CF", "Central African Republic"),
    ("TD", "Chad"),
    ("CL", "Chile"),
    ("CN", "China"),
    ("CX", "Christmas Island"),
    ("CC", "Cocos (Keeling) Islands"),
    ("CO", "Colombia"),
    ("KM", "Comoros"),
    ("CG", "Congo"),
    ("CD", "Congo, The Democratic Republic of the"),
    ("CK", "Cook Islands"),
    ("CR", "Costa Rica"),
    ("CI", "Côte d'Ivoire"),
    ("HR", "Croatia"),
    ("CU", "Cuba"),
    ("CW", "Curaçao"),
    ("CY", "Cyprus"),
    ("CZ", "Czech Republic"),
    ("DK", "Denmark"),
    ("DJ", "Djibouti"),
    ("DM", "Dominica"),
    ("DO", "Dominican Republic"),
    ("EC", "Ecuador"),
    ("EG", "Egypt"),
    ("SV", "El Salvador"),
    ("GQ", "Equatorial Guinea"),
    ("ER", "Eritrea"),
    ("EE", "Estonia"),
    ("ET", "Ethiopia"),
    ("FK", "Falkland Islands (Malvinas)"),
    ("FO", "Faroe Islands"),
    ("FJ", "Fiji"),
    ("FI", "Finland"),
    ("FR", "France"),
    ("GF", "French Guiana"),
    ("PF", "French Polynesia"),
    ("TF", "French Southern Territories"),
    ("GA", "Gabon"),
    ("GM", "Gambia"),
    ("GE", "Georgia"),
    ("DE", "Germany"),
    ("GH", "Ghana"),
    ("GI", "Gibraltar"),
    ("GR", "Greece"),
    ("GL", "Greenland"),
    ("GD", "Grenada"),
    ("GP", "Guadeloupe"),
    ("GU", "Guam"),
    ("GT", "Guatemala"),
    ("GG", "Guernsey"),
    ("GN", "Guinea"),
    ("GW", "Guinea-Bissau"),
    ("GY", "Guyana"),
    ("HT", "Haiti"),
    ("HM", "Heard Island and McDonald Islands"),
    ("VA", "Holy See (Vatican City State)"),
    ("HN", "Honduras"),
    ("HK", "Hong Kong"),
    ("HU", "Hungary"),
    ("IS", "Iceland"),
    ("IN", "India"),
    ("ID", "Indonesia"),
    ("IR", "Iran, Islamic Republic of"),
    ("IQ", "Iraq"),
    ("IE", "Ireland"),
    ("IM", "Isle of Man"),
    ("IL", "Israel"),
    ("IT", "Italy"),
    ("JM", "Jamaica"),
    ("JP", "Japan"),
    ("JE", "Jersey"),
    ("JO", "Jordan"),
    ("KZ", "Kazakhstan"),
    ("KE", "Kenya"),
    ("KI", "Kiribati"),
    ("KP", "Korea, Democratic People's Republic of"),
    ("KR", "Korea, Republic of"),
    ("XK", "Kosovo, Republic of"),      # Pending: Used by EU, not ISO-3166 yet
    ("KW", "Kuwait"),
    ("KG", "Kyrgyzstan"),
    ("LA", "Lao People's Democratic Republic"),
    ("LV", "Latvia"),
    ("LB", "Lebanon"),
    ("LS", "Lesotho"),
    ("LR", "Liberia"),
    ("LY", "Libya"),
    ("LI", "Liechtenstein"),
    ("LT", "Lithuania"),
    ("LU", "Luxembourg"),
    ("MO", "Macao"),
    ("MK", "Macedonia, The Former Yugoslav Republic of"),
    ("MG", "Madagascar"),
    ("MW", "Malawi"),
    ("MY", "Malaysia"),
    ("MV", "Maldives"),
    ("ML", "Mali"),
    ("MT", "Malta"),
    ("MH", "Marshall Islands"),
    ("MQ", "Martinique"),
    ("MR", "Mauritania"),
    ("MU", "Mauritius"),
    ("YT", "Mayotte"),
    ("MX", "Mexico"),
    ("FM", "Micronesia, Federated States of"),
    ("MD", "Moldova, Republic of"),
    ("MC", "Monaco"),
    ("MN", "Mongolia"),
    ("ME", "Montenegro"),
    ("MS", "Montserrat"),
    ("MA", "Morocco"),
    ("MZ", "Mozambique"),
    ("MM", "Myanmar"),
    ("NA", "Namibia"),
    ("NR", "Nauru"),
    ("NP", "Nepal"),
    ("NL", "Netherlands"),
    ("NC", "New Caledonia"),
    ("NZ", "New Zealand"),
    ("NI", "Nicaragua"),
    ("NE", "Niger"),
    ("NG", "Nigeria"),
    ("NU", "Niue"),
    ("NF", "Norfolk Island"),
    ("MP", "Northern Mariana Islands"),
    ("NO", "Norway"),
    ("OM", "Oman"),
    ("PK", "Pakistan"),
    ("PW", "Palau"),
    ("PS", "Palestinian Territory, Occupied"),
    ("PA", "Panama"),
    ("PG", "Papua New Guinea"),
    ("PY", "Paraguay"),
    ("PE", "Peru"),
    ("PH", "Philippines"),
    ("PN", "Pitcairn"),
    ("PL", "Poland"),
    ("PT", "Portugal"),
    ("PR", "Puerto Rico"),
    ("QA", "Qatar"),
    ("RE", "Réunion"),
    ("RO", "Romania"),
    ("RU", "Russian Federation"),
    ("RW", "Rwanda"),
    ("BL", "Saint Barthélemy"),
    ("SH", "Saint Helena, Ascension and Tristan da Cunha"),
    ("KN", "Saint Kitts and Nevis"),
    ("LC", "Saint Lucia"),
    ("MF", "Saint Martin (French Part)"),
    ("PM", "Saint Pierre and Miquelon"),
    ("VC", "Saint Vincent and the Grenadines"),
    ("WS", "Samoa"),
    ("SM", "San Marino"),
    ("ST", "Sao Tome and Principe"),
    ("SA", "Saudi Arabia"),
    ("SN", "Senegal"),
    ("RS", "Serbia"),
    ("SC", "Seychelles"),
    ("SL", "Sierra Leone"),
    ("SG", "Singapore"),
    ("SX", "Sint Maarten (Dutch Part)"),
    ("SK", "Slovakia"),
    ("SI", "Slovenia"),
    ("SB", "Solomon Islands"),
    ("SO", "Somalia"),
    ("ZA", "South Africa"),
    ("GS", "South Georgia and the South Sandwich Islands"),
    ("SS", "South Sudan"),
    ("ES", "Spain"),
    ("LK", "Sri Lanka"),
    ("SD", "Sudan"),
    ("SR", "Suriname"),
    ("SJ", "Svalbard and Jan Mayen"),
    ("SZ", "Swaziland"),
    ("SE", "Sweden"),
    ("CH", "Switzerland"),
    ("SY", "Syrian Arab Republic"),
    ("TW", "Taiwan, Province of China"),
    ("TJ", "Tajikistan"),
    ("TZ", "Tanzania, United Republic of"),
    ("TH", "Thailand"),
    ("TL", "Timor-Leste"),
    ("TG", "Togo"),
    ("TK", "Tokelau"),
    ("TO", "Tonga"),
    ("TT", "Trinidad and Tobago"),
    ("TN", "Tunisia"),
    ("TR", "Turkey"),
    ("TM", "Turkmenistan"),
    ("TC", "Turks and Caicos Islands"),
    ("TV", "Tuvalu"),
    ("UG", "Uganda"),
    ("UA", "Ukraine"),
    ("AE", "United Arab Emirates"),
    ("GB", "United Kingdom"),
    ("US", "United States"),
    ("UM", "United States Minor Outlying Islands"),
    ("UY", "Uruguay"),
    ("UZ", "Uzbekistan"),
    ("VU", "Vanuatu"),
    ("VE", "Venezuela, Bolivarian Republic of"),
    ("VN", "Viet Nam"),
    ("VG", "Virgin Islands, British"),
    ("VI", "Virgin Islands, U.S."),
    ("WF", "Wallis and Futuna"),
    ("EH", "Western Sahara"),
    ("YE", "Yemen"),
    ("ZM", "Zambia"),
    ("ZW", "Zimbabwe"),
)


ALPHA_3 = (
    ("AFG", "Afghanistan"),
    ("ALA", "Åland Islands"),
    ("ALB", "Albania"),
    ("DZA", "Algeria"),
    ("ASM", "American Samoa"),
    ("AND", "Andorra"),
    ("AGO", "Angola"),
    ("AIA", "Anguilla"),
    ("ATA", "Antarctica"),
    ("ATG", "Antigua and Barbuda"),
    ("ARG", "Argentina"),
    ("ARM", "Armenia"),
    ("ABW", "Aruba"),
    ("AUS", "Australia"),
    ("AUT", "Austria"),
    ("AZE", "Azerbaijan"),
    ("BHS", "Bahamas"),
    ("BHR", "Bahrain"),
    ("BGD", "Bangladesh"),
    ("BRB", "Barbados"),
    ("BLR", "Belarus"),
    ("BEL", "Belgium"),
    ("BLZ", "Belize"),
    ("BEN", "Benin"),
    ("BMU", "Bermuda"),
    ("BTN", "Bhutan"),
    ("BOL", "Bolivia, Plurinational State of"),
    ("BES", "Bonaire, Sint Eustatius and Saba"),
    ("BIH", "Bosnia and Herzegovina"),
    ("BWA", "Botswana"),
    ("BVT", "Bouvet Island"),
    ("BRA", "Brazil"),
    ("IOT", "British Indian Ocean Territory"),
    ("BRN", "Brunei Darussalam"),
    ("BGR", "Bulgaria"),
    ("BFA", "Burkina Faso"),
    ("BDI", "Burundi"),
    ("KHM", "Cambodia"),
    ("CMR", "Cameroon"),
    ("CAN", "Canada"),
    ("CPV", "Cape Verde"),
    ("CYM", "Cayman Islands"),
    ("CAF", "Central African Republic"),
    ("TCD", "Chad"),
    ("CHL", "Chile"),
    ("CHN", "China"),
    ("CXR", "Christmas Island"),
    ("CCK", "Cocos (Keeling) Islands"),
    ("COL", "Colombia"),
    ("COM", "Comoros"),
    ("COG", "Congo"),
    ("COD", "Congo, The Democratic Republic of the"),
    ("COK", "Cook Islands"),
    ("CRI", "Costa Rica"),
    ("CIV", "Côte d'Ivoire"),
    ("HRV", "Croatia"),
    ("CUB", "Cuba"),
    ("CUW", "Curaçao"),
    ("CYP", "Cyprus"),
    ("CZE", "Czech Republic"),
    ("DNK", "Denmark"),
    ("DJI", "Djibouti"),
    ("DMA", "Dominica"),
    ("DOM", "Dominican Republic"),
    ("ECU", "Ecuador"),
    ("EGY", "Egypt"),
    ("SLV", "El Salvador"),
    ("GNQ", "Equatorial Guinea"),
    ("ERI", "Eritrea"),
    ("EST", "Estonia"),
    ("ETH", "Ethiopia"),
    ("FLK", "Falkland Islands (Malvinas)"),
    ("FRO", "Faroe Islands"),
    ("FJI", "Fiji"),
    ("FIN", "Finland"),
    ("FRA", "France"),
    ("GUF", "French Guiana"),
    ("PYF", "French Polynesia"),
    ("ATF", "French Southern Territories"),
    ("GAB", "Gabon"),
    ("GMB", "Gambia"),
    ("GEO", "Georgia"),
    ("DEU", "Germany"),
    ("GHA", "Ghana"),
    ("GIB", "Gibraltar"),
    ("GRC", "Greece"),
    ("GRL", "Greenland"),
    ("GRD", "Grenada"),
    ("GLP", "Guadeloupe"),
    ("GUM", "Guam"),
    ("GTM", "Guatemala"),
    ("GGY", "Guernsey"),
    ("GIN", "Guinea"),
    ("GNB", "Guinea-Bissau"),
    ("GUY", "Guyana"),
    ("HTI", "Haiti"),
    ("HMD", "Heard Island and McDonald Islands"),
    ("VAT", "Holy See (Vatican City State)"),
    ("HND", "Honduras"),
    ("HKG", "Hong Kong"),
    ("HUN", "Hungary"),
    ("ISL", "Iceland"),
    ("IND", "India"),
    ("IDN", "Indonesia"),
    ("IRN", "Iran, Islamic Republic of"),
    ("IRQ", "Iraq"),
    ("IRL", "Ireland"),
    ("IMN", "Isle of Man"),
    ("ISR", "Israel"),
    ("ITA", "Italy"),
    ("JAM", "Jamaica"),
    ("JPN", "Japan"),
    ("JEY", "Jersey"),
    ("JOR", "Jordan"),
    ("KAZ", "Kazakhstan"),
    ("KEN", "Kenya"),
    ("KIR", "Kiribati"),
    ("PRK", "Korea, Democratic People's Republic of"),
    ("KOR", "Korea, Republic of"),
    ("XKX", "Kosovo, Republic of"),    # Pending: Used by EU, not ISO-3166 yet
    ("KWT", "Kuwait"),
    ("KGZ", "Kyrgyzstan"),
    ("LAO", "Lao People's Democratic Republic"),
    ("LVA", "Latvia"),
    ("LBN", "Lebanon"),
    ("LSO", "Lesotho"),
    ("LBR", "Liberia"),
    ("LBY", "Libya"),
    ("LIE", "Liechtenstein"),
    ("LTU", "Lithuania"),
    ("LUX", "Luxembourg"),
    ("MAC", "Macao"),
    ("MKD", "Macedonia, The Former Yugoslav Republic of"),
    ("MDG", "Madagascar"),
    ("MWI", "Malawi"),
    ("MYS", "Malaysia"),
    ("MDV", "Maldives"),
    ("MLI", "Mali"),
    ("MLT", "Malta"),
    ("MHL", "Marshall Islands"),
    ("MTQ", "Martinique"),
    ("MRT", "Mauritania"),
    ("MUS", "Mauritius"),
    ("MYT", "Mayotte"),
    ("MEX", "Mexico"),
    ("FSM", "Micronesia, Federated States of"),
    ("MDA", "Moldova, Republic of"),
    ("MCO", "Monaco"),
    ("MNG", "Mongolia"),
    ("MNE", "Montenegro"),
    ("MSR", "Montserrat"),
    ("MAR", "Morocco"),
    ("MOZ", "Mozambique"),
    ("MMR", "Myanmar"),
    ("NAM", "Namibia"),
    ("NRU", "Nauru"),
    ("NPL", "Nepal"),
    ("NLD", "Netherlands"),
    ("NCL", "New Caledonia"),
    ("NZL", "New Zealand"),
    ("NIC", "Nicaragua"),
    ("NER", "Niger"),
    ("NGA", "Nigeria"),
    ("NIU", "Niue"),
    ("NFK", "Norfolk Island"),
    ("MNP", "Northern Mariana Islands"),
    ("NOR", "Norway"),
    ("OMN", "Oman"),
    ("PAK", "Pakistan"),
    ("PLW", "Palau"),
    ("PSE", "Palestinian Territory, Occupied"),
    ("PAN", "Panama"),
    ("PNG", "Papua New Guinea"),
    ("PRY", "Paraguay"),
    ("PER", "Peru"),
    ("PHL", "Philippines"),
    ("PCN", "Pitcairn"),
    ("POL", "Poland"),
    ("PRT", "Portugal"),
    ("PRI", "Puerto Rico"),
    ("QAT", "Qatar"),
    ("REU", "Réunion"),
    ("ROU", "Romania"),
    ("RUS", "Russian Federation"),
    ("RWA", "Rwanda"),
    ("BLM", "Saint Barthélemy"),
    ("SHN", "Saint Helena, Ascension and Tristan da Cunha"),
    ("KNA", "Saint Kitts and Nevis"),
    ("LCA", "Saint Lucia"),
    ("MAF", "Saint Martin (French Part)"),
    ("SPM", "Saint Pierre and Miquelon"),
    ("VCT", "Saint Vincent and the Grenadines"),
    ("WSM", "Samoa"),
    ("SMR", "San Marino"),
    ("STP", "Sao Tome and Principe"),
    ("SAU", "Saudi Arabia"),
    ("SEN", "Senegal"),
    ("SRB", "Serbia"),
    ("SYC", "Seychelles"),
    ("SLE", "Sierra Leone"),
    ("SGP", "Singapore"),
    ("SXM", "Sint Maarten (Dutch Part)"),
    ("SVK", "Slovakia"),
    ("SVN", "Slovenia"),
    ("SLB", "Solomon Islands"),
    ("SOM", "Somalia"),
    ("ZAF", "South Africa"),
    ("SGS", "South Georgia and the South Sandwich Islands"),
    ("SSD", "South Sudan"),
    ("ESP", "Spain"),
    ("LKA", "Sri Lanka"),
    ("SDN", "Sudan"),
    ("SUR", "Suriname"),
    ("SJM", "Svalbard and Jan Mayen"),
    ("SWZ", "Swaziland"),
    ("SWE", "Sweden"),
    ("CHE", "Switzerland"),
    ("SYR", "Syrian Arab Republic"),
    ("TWN", "Taiwan, Province of China"),
    ("TJK", "Tajikistan"),
    ("TZA", "Tanzania, United Republic of"),
    ("THA", "Thailand"),
    ("TLS", "Timor-Leste"),
    ("TGO", "Togo"),
    ("TKL", "Tokelau"),
    ("TON", "Tonga"),
    ("TTO", "Trinidad and Tobago"),
    ("TUN", "Tunisia"),
    ("TUR", "Turkey"),
    ("TKM", "Turkmenistan"),
    ("TCA", "Turks and Caicos Islands"),
    ("TUV", "Tuvalu"),
    ("UGA", "Uganda"),
    ("UKR", "Ukraine"),
    ("ARE", "United Arab Emirates"),
    ("GBR", "United Kingdom"),
    ("USA", "United States"),
    ("UMI", "United States Minor Outlying Islands"),
    ("URY", "Uruguay"),
    ("UZB", "Uzbekistan"),
    ("VUT", "Vanuatu"),
    ("VEN", "Venezuela, Bolivarian Republic of"),
    ("VNM", "Viet Nam"),
    ("VGB", "Virgin Islands, British"),
    ("VIR", "Virgin Islands, U.S."),
    ("WLF", "Wallis and Futuna"),
    ("ESH", "Western Sahara"),
    ("YEM", "Yemen"),
    ("ZMB", "Zambia"),
    ("ZWE", "Zimbabwe"),
)


NUMERIC = (
    (4, "Afghanistan"),
    (248, "Åland Islands"),
    (8, "Albania"),
    (2, "Algeria"),
    (6, "American Samoa"),
    (20, "Andorra"),
    (24, "Angola"),
    (660, "Anguilla"),
    (10, "Antarctica"),
    (28, "Antigua and Barbuda"),
    (32, "Argentina"),
    (51, "Armenia"),
    (533, "Aruba"),
    (36, "Australia"),
    (40, "Austria"),
    (31, "Azerbaijan"),
    (44, "Bahamas"),
    (48, "Bahrain"),
    (50, "Bangladesh"),
    (52, "Barbados"),
    (112, "Belarus"),
    (56, "Belgium"),
    (84, "Belize"),
    (204, "Benin"),
    (60, "Bermuda"),
    (64, "Bhutan"),
    (68, "Bolivia, Plurinational State of"),
    (535, "Bonaire, Sint Eustatius and Saba"),
    (70, "Bosnia and Herzegovina"),
    (72, "Botswana"),
    (74, "Bouvet Island"),
    (76, "Brazil"),
    (86, "British Indian Ocean Territory"),
    (96, "Brunei Darussalam"),
    (100, "Bulgaria"),
    (854, "Burkina Faso"),
    (108, "Burundi"),
    (116, "Cambodia"),
    (120, "Cameroon"),
    (124, "Canada"),
    (132, "Cape Verde"),
    (136, "Cayman Islands"),
    (140, "Central African Republic"),
    (148, "Chad"),
    (152, "Chile"),
    (156, "China"),
    (162, "Christmas Island"),
    (166, "Cocos (Keeling) Islands"),
    (170, "Colombia"),
    (174, "Comoros"),
    (178, "Congo"),
    (180, "Congo, The Democratic Republic of the"),
    (184, "Cook Islands"),
    (188, "Costa Rica"),
    (384, "Côte d'Ivoire"),
    (191, "Croatia"),
    (192, "Cuba"),
    (531, "Curaçao"),
    (196, "Cyprus"),
    (203, "Czech Republic"),
    (208, "Denmark"),
    (262, "Djibouti"),
    (212, "Dominica"),
    (214, "Dominican Republic"),
    (218, "Ecuador"),
    (818, "Egypt"),
    (222, "El Salvador"),
    (226, "Equatorial Guinea"),
    (232, "Eritrea"),
    (233, "Estonia"),
    (231, "Ethiopia"),
    (238, "Falkland Islands (Malvinas)"),
    (234, "Faroe Islands"),
    (242, "Fiji"),
    (246, "Finland"),
    (250, "France"),
    (254, "French Guiana"),
    (258, "French Polynesia"),
    (260, "French Southern Territories"),
    (266, "Gabon"),
    (270, "Gambia"),
    (268, "Georgia"),
    (276, "Germany"),
    (288, "Ghana"),
    (292, "Gibraltar"),
    (300, "Greece"),
    (304, "Greenland"),
    (308, "Grenada"),
    (312, "Guadeloupe"),
    (316, "Guam"),
    (320, "Guatemala"),
    (831, "Guernsey"),
    (324, "Guinea"),
    (624, "Guinea-Bissau"),
    (328, "Guyana"),
    (332, "Haiti"),
    (334, "Heard Island and McDonald Islands"),
    (336, "Holy See (Vatican City State)"),
    (340, "Honduras"),
    (344, "Hong Kong"),
    (348, "Hungary"),
    (352, "Iceland"),
    (356, "India"),
    (360, "Indonesia"),
    (364, "Iran, Islamic Republic of"),
    (368, "Iraq"),
    (372, "Ireland"),
    (833, "Isle of Man"),
    (376, "Israel"),
    (380, "Italy"),
    (388, "Jamaica"),
    (392, "Japan"),
    (832, "Jersey"),
    (400, "Jordan"),
    (398, "Kazakhstan"),
    (404, "Kenya"),
    (296, "Kiribati"),
    (408, "Korea, Democratic People's Republic of"),
    (410, "Korea, Republic of"),
    (999, "Kosovo, Republic of"),       # Pending: Not ISO-3166
    (414, "Kuwait"),
    (417, "Kyrgyzstan"),
    (418, "Lao People's Democratic Republic"),
    (428, "Latvia"),
    (422, "Lebanon"),
    (426, "Lesotho"),
    (430, "Liberia"),
    (434, "Libya"),
    (438, "Liechtenstein"),
    (440, "Lithuania"),
    (442, "Luxembourg"),
    (446, "Macao"),
    (807, "Macedonia, The Former Yugoslav Republic of"),
    (450, "Madagascar"),
    (454, "Malawi"),
    (458, "Malaysia"),
    (462, "Maldives"),
    (466, "Mali"),
    (470, "Malta"),
    (584, "Marshall Islands"),
    (474, "Martinique"),
    (478, "Mauritania"),
    (480, "Mauritius"),
    (175, "Mayotte"),
    (484, "Mexico"),
    (583, "Micronesia, Federated States of"),
    (498, "Moldova, Republic of"),
    (492, "Monaco"),
    (496, "Mongolia"),
    (499, "Montenegro"),
    (500, "Montserrat"),
    (504, "Morocco"),
    (508, "Mozambique"),
    (104, "Myanmar"),
    (516, "Namibia"),
    (520, "Nauru"),
    (524, "Nepal"),
    (528, "Netherlands"),
    (540, "New Caledonia"),
    (554, "New Zealand"),
    (558, "Nicaragua"),
    (562, "Niger"),
    (566, "Nigeria"),
    (570, "Niue"),
    (574, "Norfolk Island"),
    (580, "Northern Mariana Islands"),
    (578, "Norway"),
    (512, "Oman"),
    (586, "Pakistan"),
    (585, "Palau"),
    (275, "Palestinian Territory, Occupied"),
    (591, "Panama"),
    (598, "Papua New Guinea"),
    (600, "Paraguay"),
    (604, "Peru"),
    (608, "Philippines"),
    (612, "Pitcairn"),
    (616, "Poland"),
    (620, "Portugal"),
    (630, "Puerto Rico"),
    (634, "Qatar"),
    (638, "Réunion"),
    (642, "Romania"),
    (643, "Russian Federation"),
    (646, "Rwanda"),
    (652, "Saint Barthélemy"),
    (654, "Saint Helena, Ascension and Tristan da Cunha"),
    (659, "Saint Kitts and Nevis"),
    (662, "Saint Lucia"),
    (663, "Saint Martin (French Part)"),
    (666, "Saint Pierre and Miquelon"),
    (670, "Saint Vincent and the Grenadines"),
    (882, "Samoa"),
    (674, "San Marino"),
    (678, "Sao Tome and Principe"),
    (682, "Saudi Arabia"),
    (686, "Senegal"),
    (688, "Serbia"),
    (690, "Seychelles"),
    (694, "Sierra Leone"),
    (702, "Singapore"),
    (534, "Sint Maarten (Dutch Part)"),
    (703, "Slovakia"),
    (705, "Slovenia"),
    (90, "Solomon Islands"),
    (706, "Somalia"),
    (710, "South Africa"),
    (239, "South Georgia and the South Sandwich Islands"),
    (728, "South Sudan"),
    (724, "Spain"),
    (144, "Sri Lanka"),
    (736, "Sudan"),
    (740, "Suriname"),
    (744, "Svalbard and Jan Mayen"),
    (748, "Swaziland"),
    (752, "Sweden"),
    (756, "Switzerland"),
    (760, "Syrian Arab Republic"),
    (158, "Taiwan, Province of China"),
    (762, "Tajikistan"),
    (834, "Tanzania, United Republic of"),
    (764, "Thailand"),
    (626, "Timor-Leste"),
    (768, "Togo"),
    (772, "Tokelau"),
    (776, "Tonga"),
    (780, "Trinidad and Tobago"),
    (788, "Tunisia"),
    (792, "Turkey"),
    (795, "Turkmenistan"),
    (796, "Turks and Caicos Islands"),
    (798, "Tuvalu"),
    (800, "Uganda"),
    (804, "Ukraine"),
    (784, "United Arab Emirates"),
    (826, "United Kingdom"),
    (840, "United States"),
    (581, "United States Minor Outlying Islands"),
    (858, "Uruguay"),
    (860, "Uzbekistan"),
    (548, "Vanuatu"),
    (862, "Venezuela, Bolivarian Republic of"),
    (704, "Viet Nam"),
    (92, "Virgin Islands, British"),
    (850, "Virgin Islands, U.S."),
    (876, "Wallis and Futuna"),
    (732, "Western Sahara"),
    (887, "Yemen"),
    (894, "Zambia"),
    (716, "Zimbabwe"),
)
