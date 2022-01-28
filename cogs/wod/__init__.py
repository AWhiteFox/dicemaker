import traceback
from itertools import chain

from discord import Cog, Bot, ApplicationContext, slash_command, Embed, AutocompleteContext, Option, Member, User
from typing import Iterable, Union

from .true_random import D10Pool
from .wod_roll import WoDRoll
from .character_sheet import CharacterSheetContainer
from .roll_views import RollView
from .format import roll_to_embed

Author = Union[Member, User]

GUILDS = [
    577072156249161739,
    859341805941293067
]


async def get_attributes(ctx: AutocompleteContext) -> Iterable[str]:
    cog = ctx.cog
    if isinstance(cog, WoDCog):
        sheet = cog.sheets.get(ctx.interaction.user.id)
        if sheet is not None:
            q = ctx.value.lower()
            return chain((cog.NO_ATTRIBUTE,), filter(lambda s: s.lower().startswith(q), sheet.attributes.keys()))
    return ()


async def get_abilities(ctx: AutocompleteContext) -> Iterable[str]:
    cog = ctx.cog
    if isinstance(cog, WoDCog):
        sheet = cog.sheets.get(ctx.interaction.user.id)
        if sheet is not None:
            q = ctx.value.lower()
            return chain((cog.NO_ABILITY,), filter(lambda s: s.lower().startswith(q), sheet.abilities.keys()))
    return ()


class WoDCog(Cog):
    NO_ATTRIBUTE = 'Без атрибута'
    NO_ABILITY = 'Без способности'

    def __init__(self, bot: Bot):
        self.bot: Bot = bot
        self.d10_pool: D10Pool = D10Pool()
        self.sheets: CharacterSheetContainer = CharacterSheetContainer()

    @Cog.listener()
    async def on_ready(self):
        self.sheets.load_all()
        print('WoD: ready')

    CountOpt = Option(int, 'Выбери количество кубов', name='количество', min_value=1, max_value=50)
    DifficultyOpt = Option(int, 'Выбери сложность', name='сложность', required=False, default=6, min_value=1, max_value=10)

    @slash_command(name='бросок', description='Сделать чистый бросок', guild_ids=GUILDS)
    async def roll(self, ctx: ApplicationContext, count: CountOpt, difficulty: DifficultyOpt):
        roll = WoDRoll(count, difficulty)
        await roll.execute(self.d10_pool)
        embed = self.create_roll_embed(ctx.author, roll)
        view = RollView(self, roll, ctx.interaction)
        await ctx.respond(embed=embed, view=view)

    AttributeOpt = Option(str, 'Выбери атрибут', name='атрибут', autocomplete=get_attributes)
    AbilityOpt = Option(str, 'Выбери способность', name='способность', autocomplete=get_abilities)
    ModOpt = Option(int, 'Выбери модификатор', name='модификатор', required=False, default=0, min_value=-50, max_value=50)

    @slash_command(name='проверка', description='Сделать бросок по листу персонажа', guild_ids=GUILDS)
    async def check(self, ctx: ApplicationContext, attribute: AttributeOpt, ability: AbilityOpt, difficulty: DifficultyOpt, mod: ModOpt):
        sheet = self.sheets.get(ctx.author.id)
        if sheet is None:
            await ctx.respond(content='Сначала привяжи лист персонажа', ephemeral=True)
            return

        stats = []
        if attribute != self.NO_ATTRIBUTE:
            stats.append(attribute)
        if ability != self.NO_ABILITY:
            stats.append(ability)
        if not stats:
            await ctx.respond(content='Ты ничего не выбрал', ephemeral=True)
            return

        roll = sheet.roll(attribute, ability, difficulty, mod)
        await roll.execute(self.d10_pool)
        embed = self.create_roll_embed(ctx.author, roll, stats)
        view = RollView(self, roll, ctx.interaction, stats)
        await ctx.respond(embed=embed, view=view)

    @slash_command(name='лист_персонажа', description='Привязать лист персонажа', guild_ids=GUILDS)
    async def character_sheet(self, ctx: ApplicationContext, url: str):
        # noinspection PyBroadException
        try:
            self.sheets.add(ctx.author.id, url)
        except Exception:
            await ctx.respond(f'```py\n{traceback.format_exc()}```', ephemeral=True)
            return
        await ctx.respond('Лист персонажа привязан!', ephemeral=True)

    def create_roll_embed(self, author: Author, roll: WoDRoll, stats: Iterable[str] = ()) -> Embed:
        sheet = self.sheets.get(author.id)
        if sheet is not None:
            author_name = sheet.character_name
        else:
            author_name = author.display_name
        return roll_to_embed(author_name, author.display_avatar.url, roll, stats)


def setup(bot: Bot):
    bot.add_cog(WoDCog(bot))
