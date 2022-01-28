import os
from itertools import chain, repeat
from typing import Optional, Iterable, Tuple, TextIO

import gspread

from . import WoDRoll


class CharacterSheetContainer:
    DATA_SEP = ':'

    def __init__(self):
        self.g_client: gspread.Client = gspread.service_account(os.getenv('WOD_GOOGLE_CREDS_FILE'))
        self.file: TextIO = open(os.getenv('WOD_CHARACTER_SHEET_FILE'), 'r+')
        self.data: dict[int, CharacterSheet] = {}

    def get(self, user: int) -> Optional['CharacterSheet']:
        return self.data.get(user)

    def add(self, user: int, url: str):
        self.data[user] = CharacterSheet.from_url(self.g_client, url)
        self.save_all()

    def load_all(self):
        print('WoD: loadings sheets')
        self.file.seek(0)
        for line in self.file.readlines():
            key, value = line.strip().split(self.DATA_SEP, 1)
            try:
                self.data[int(key)] = CharacterSheet.from_url(self.g_client, value)
            except Exception as e:
                err = str(e) or e.__class__.__name__
                print(f'WoD: failed to access and parse spreadsheet of user with id {key} : {err}')
        print(f'WoD: read sheets: {len(self.data)}')

    def save_all(self):
        self.file.seek(0)
        for k, v in self.data.items():
            self.file.write(f'{k}{self.DATA_SEP}{v.spreadsheet_url}\n')
        self.file.truncate()


class CharacterSheet:
    def __init__(self):
        self.attributes: dict[str, int] = {}
        self.abilities: dict[str, int] = {}
        self.character_name: Optional[str] = None
        self.spreadsheet_url: Optional[str] = None

    def roll(self, attribute: str, ability: str, difficulty: int, mod: int = 0) -> 'WoDRoll':
        return WoDRoll(self.attributes.get(attribute, 0) + self.abilities.get(ability, 0), difficulty, mod)

    @classmethod
    def from_url(cls, gc: gspread.Client, url: str) -> 'CharacterSheet':
        sp = gc.open_by_url(url)
        values = sp.worksheets()[0].get_all_values()

        ch_sheet = cls()
        ch_sheet.spreadsheet_url = url
        ch_sheet.character_name = sp.title.split('|', 1)[0].strip()

        attribute_indexes = chain(
            zip(range(4, 4 + 3), repeat(1)),
            zip(range(4, 4 + 3), repeat(1 + 6)),
            zip(range(4, 4 + 3), repeat(1 + 6 + 6))
        )
        ability_indexes = chain(
            zip(range(11, 11 + 10), repeat(1)),
            zip(range(11, 11 + 10), repeat(1 + 6)),
            zip(range(11, 11 + 10), repeat(1 + 6 + 6))
        )

        cls._parse_span(values, attribute_indexes, ch_sheet.attributes)
        cls._parse_span(values, ability_indexes, ch_sheet.abilities)

        return ch_sheet

    @staticmethod
    def _parse_span(values: list[list[str]], indexes: Iterable[Tuple[int, int]], parse_to: dict[str, int]):
        for row_i, col_i in indexes:
            key = values[row_i][col_i].strip().replace('\n', ' ')
            value = values[row_i][col_i + 1:col_i + 6].count('TRUE')
            if '(' not in key:
                parse_to[key] = value
            else:
                raw = key.split('(', 1)[0].rstrip()
                parse_to[raw] = value
                parse_to[key] = value + 1
