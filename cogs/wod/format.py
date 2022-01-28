from typing import Iterable

from discord import Embed

from cogs.wod import WoDRoll
from cogs.wod.wod_roll import WoDDice


def roll_to_embed(author: str, icon_url: str, roll: WoDRoll, stats: Iterable[str] = ()) -> Embed:
    title = ' + '.join(stats) or 'Чистый бросок'

    if roll.mod > 0:
        title += f' + {roll.mod}'
    elif roll.mod < 0:
        title += f' - {-roll.mod}'
    if roll.additional_dice > 0:
        title += f' + __{roll.additional_dice}__'

    if not roll.blind:
        difficulty = f'Сложность: {roll.difficulty}'
    else:
        difficulty = f'Бросок вслепую, не хватает кубов: {1 - roll.pool}'

    success_count = f'Успехи: {roll.success_count}'

    embed = Embed()
    embed.title = title
    embed.description = f'{roll_to_str(roll)}\n\n{difficulty} | {success_count}'
    embed.set_footer(text=author, icon_url=icon_url)
    return embed


def dice_to_str(dice: WoDDice, difficulty: int) -> str:
    s = str(dice.result)
    if dice.additional:
        s = f'__{s}__'
    if dice.result >= difficulty:
        s = f'**{s}**'
    return s


def roll_to_str(roll: WoDRoll) -> str:
    nsbp = '\xa0'
    sep = nsbp * 2
    difficulty = 10 if roll.blind else roll.difficulty
    lines = []
    for row in roll.results:
        values = map(lambda d: dice_to_str(d, difficulty), row)
        lines.append(sep.join(values))
    return '\n'.join(lines)
