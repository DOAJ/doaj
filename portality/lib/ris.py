"""
very simple library for RIS format

file format references: https://en.wikipedia.org/wiki/RIS_(file_format)
"""
import logging
from collections import OrderedDict
from typing import Dict, Optional

log = logging.getLogger(__name__)

RTAG_TYPE = 'TY'
RTAG_END = 'ER'
RIS_TAGS = [
    'A1',  # primary_author
    'A2',  # secondary_author
    'A3',  # tertiary_author
    'A4',  # quaternary_author
    'A5',  # quinary_author_compiler
    'A6',  # website_editor
    'AB',  # abstract_synopsis
    'AD',  # author_editor_address
    'AN',  # accession_number
    'AU',  # author_editor_translator
    'AV',  # availability_location
    'BT',  # primary_secondary_title
    'C1',  # custom1
    'C2',  # custom2
    'C3',  # custom3
    'C4',  # custom4
    'C5',  # custom5
    'C6',  # custom6
    'C7',  # custom7
    'C8',  # custom8
    'CA',  # caption
    'CL',  # classification
    'CN',  # call_number
    'CP',  # city_place_publication
    'CR',  # cited_references
    'CT',  # caption_primary_title
    'CY',  # place_published
    'DA',  # date
    'DB',  # name_of_database
    'DI',  # digital_object_identifier
    'DO',  # digital_object_identifier2
    'DOI',  # digital_object_identifier3
    'DP',  # database_provider
    'DS',  # data_source
    'ED',  # secondary_author
    'EP',  # end_page
    'ET',  # edition
    'FD',  # free_form_publication_data
    'H1',  # location_library
    'H2',  # location_call_number
    'ID',  # reference_identifier
    'IP',  # identifying_phrase
    'IS',  # number_volumes
    'J1',  # journal_abbreviation_1
    'J2',  # alternate_title
    'JA',  # journal_standard_abbreviation
    'JF',  # journal_full_name
    'JO',  # journal_abbreviation
    'K1',  # keyword1
    'KW',  # keyword_phrase
    'L1',  # file_attachments
    'L2',  # url_link
    'L3',  # doi_link
    'L4',  # figure_image_link
    'LA',  # language
    'LB',  # label
    'LK',  # links
    'LL',  # sponsoring_library_location
    'M1',  # miscellaneous1
    'M2',  # miscellaneous2
    'M3',  # type_of_work
    'N1',  # notes1
    'N2',  # abstract_notes
    'NO',  # notes
    'NV',  # number_of_volumes
    'OL',  # output_language
    'OP',  # original_publication
    'PA',  # personal_notes
    'PB',  # publisher
    'PMCID',  # pmcid
    'PMID',  # pmid
    'PP',  # place_of_publication
    'PY',  # publication_year
    'RD',  # retrieved_date
    'RI',  # reviewed_item
    'RN',  # research_notes
    'RP',  # reprint_status
    'RT',  # reference_type
    'SE',  # section
    'SF',  # subfile_database
    'SL',  # sponsoring_library
    'SN',  # issn_isbn
    'SP',  # start_pages
    'SR',  # source_type
    'ST',  # short_title
    'SV',  # series_volume
    'T1',  # primary_title
    'T2',  # secondary_title
    'T3',  # tertiary_title
    'TA',  # translated_author
    'TI',  # title
    'TT',  # translated_title
    RTAG_TYPE,  # 'type_of_reference'
    'U1',  # user_definable1
    'U2',  # user_definable2
    'U3',  # user_definable3
    'U4',  # user_definable4
    'U5',  # user_definable5
    'U6',  # user_definable6
    'U7',  # user_definable7
    'U8',  # user_definable8
    'U9',  # user_definable9
    'U10',  # user_definable10
    'U11',  # user_definable11
    'U12',  # user_definable12
    'U13',  # user_definable13
    'U14',  # user_definable14
    'U15',  # user_definable15
    'UR',  # web_url
    'VL',  # volume
    'VO',  # volume_published_standard
    'WP',  # date_of_electronic_publication
    'WT',  # website_title
    'WV',  # website_version
    'Y1',  # year_date
    'Y2',  # access_date_secondary_date
    'YR',  # publication_year_ref
]


def find_tag(field_name) -> Optional[str]:
    field_name = field_name.upper()
    if field_name in RIS_TAGS:
        return field_name
    raise ValueError(f'Field not found: {field_name}')


class RisEntry:

    def __init__(self):
        self.data: Dict[str, str] = OrderedDict()

    def __setitem__(self, field_name, value):
        tag = find_tag(field_name)
        self.data[tag] = value

    def __getitem__(self, field_name) -> str:
        tag = find_tag(field_name)
        return self.data.get(tag)

    @property
    def type(self):
        return self[RTAG_TYPE]

    @type.setter
    def type(self, value):
        self[RTAG_TYPE] = value

    @classmethod
    def from_dict(cls, d: dict):
        instance = cls()
        for k, v in d.items():
            setattr(instance, k, v)
        return instance

    def to_dict(self) -> dict:
        return self.data.copy()

    @classmethod
    def from_text(cls, text: str):
        def _to_tag_value(line: str):
            tag, value = line.split('-', 1)
            tag = tag.strip()
            value = value.lstrip()
            value = value.replace('\\n', '\n')
            return tag, value

        text = text.strip()
        lines = text.splitlines()
        entry = RisEntry()
        for line in lines:
            tag, val = _to_tag_value(line)
            if tag == RTAG_END:
                break
            entry[tag] = val
        return entry

    def to_text(self) -> str:
        tags = list(self.data.keys())
        if RTAG_TYPE in tags:
            tags.remove(RTAG_TYPE)
            tags.insert(0, RTAG_TYPE)

        if RTAG_END in tags:
            tags.remove(RTAG_END)

        def _to_line(tag, value):
            if '\n' in value:
                value = value.replace('\n', '\\n')
            if value is None:
                value = ''
            return f'{tag}  - {value}\n'

        text = ''
        for tag in tags:
            text += _to_line(tag, self.data[tag])

        text += _to_line(RTAG_END, '')
        return text
