from typing import Iterable

from discord import Interaction, ButtonStyle
from discord.ui import View, Button, button

import cogs.wod as wod
from . import WoDRoll


class RollView(View):
    def __init__(self, cog: 'wod.WoDCog', roll: WoDRoll, interaction: Interaction, stats: Iterable[str] = ()):
        super().__init__(timeout=60)
        self.cog: 'wod.WoDCog' = cog
        self.roll: WoDRoll = roll
        self.stats: list[str] = list(stats)
        self.original_interaction: Interaction = interaction

        self._update_button_states()

    async def interaction_check(self, interaction: Interaction) -> bool:
        if interaction.user.id != self.original_interaction.user.id:
            await interaction.response.send_message('Это не ваш бросок', ephemeral=True)
            return False
        return True

    async def on_timeout(self) -> None:
        await self.original_interaction.edit_original_message(view=None)

    @button(label='Добросить', style=ButtonStyle.green)
    async def add_dice(self, _: Button, interaction: Interaction):
        await self.roll.add_dice(self.cog.d10_pool)
        await self._update_message(interaction)

    @button(label='Сложность +1')
    async def increase_difficulty(self, _: Button, interaction: Interaction):
        self.roll.difficulty += 1
        await self._update_message(interaction)

    @button(label='Сложность -1')
    async def decrease_difficulty(self, _: Button, interaction: Interaction):
        self.roll.difficulty -= 1
        await self._update_message(interaction)

    async def _update_message(self, interaction: Interaction) -> None:
        self._update_button_states()
        embed = self.cog.create_roll_embed(interaction.user, self.roll, self.stats)
        await interaction.response.edit_message(embed=embed, view=self)

    def _update_button_states(self):
        roll = self.roll
        self.add_dice.disabled = roll.additional_dice >= 50
        self.increase_difficulty.disabled = roll.blind or roll.difficulty == 10
        self.decrease_difficulty.disabled = roll.blind or roll.difficulty == 1


class SheetSelectView(View):
    def __init__(self, cog: 'wod.WoDCog', interaction: Interaction):
        super().__init__(timeout=60)
        self.cog: 'wod.WoDCog' = cog
        self.original_interaction: Interaction = interaction

    async def on_timeout(self) -> None:
        await self.original_interaction.edit_original_message(view=None)
