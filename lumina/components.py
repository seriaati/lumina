from __future__ import annotations

from typing import TYPE_CHECKING, Any, Generic, Self, TypeVar

import discord
from discord.ui.item import Item
from loguru import logger

from lumina.exceptions import InvalidInputError
from lumina.l10n import LocaleStr
from lumina.utils import absolute_send

if TYPE_CHECKING:
    from collections.abc import Sequence

    from discord.ui.item import Item

    from lumina.embeds import LuminaEmbed
    from lumina.l10n import Translator
    from lumina.types import Interaction

V_co = TypeVar("V_co", bound="View", covariant=True)


class View(discord.ui.View):
    def __init__(self, translator: Translator, locale: discord.Locale) -> None:
        self.translator = translator
        self.locale = locale
        self.message: discord.Message | None = None

        super().__init__()

    def disable_items(self) -> None:
        for item in self.children:
            if isinstance(item, discord.ui.Select | discord.ui.Button):
                item.disabled = True

    async def on_error(self, i: Interaction, error: Exception, item: Item[Any]) -> None:
        embed, recognized = i.client.create_error_embed(error, locale=i.locale)
        if not recognized:
            logger.exception(f"An unrecognized error occurred in {item.__class__.__name__}.")

        await absolute_send(i, embed=embed, ephemeral=True)

    async def on_timeout(self) -> None:
        if self.message is None:
            logger.warning(f"{self.__class__.__name__} timed out without a message.")
            return

        self.disable_items()
        await self.message.edit(view=self)

    def add_item(self, item: Button) -> Self:
        item.translate(self.translator, self.locale)
        return super().add_item(item)


class Button(discord.ui.Button, Generic[V_co]):
    def __init__(
        self,
        *,
        style: discord.ButtonStyle = discord.ButtonStyle.secondary,
        label: LocaleStr | str | None = None,
        disabled: bool = False,
        custom_id: str | None = None,
        url: str | None = None,
        emoji: str | discord.Emoji | discord.PartialEmoji | None = None,
        row: int | None = None,
    ) -> None:
        self.locale_label = label
        self.view: V_co

        super().__init__(
            style=style,
            label=label.key if isinstance(label, LocaleStr) else label,
            disabled=disabled,
            custom_id=custom_id,
            url=url,
            emoji=emoji,
            row=row,
        )

    def translate(self, translator: Translator, locale: discord.Locale) -> None:
        if isinstance(self.locale_label, LocaleStr):
            self.label = translator.translate(self.locale_label, locale=locale)


class Modal(discord.ui.Modal):
    def __init__(self, title: LocaleStr | str) -> None:
        super().__init__(title=title if isinstance(title, str) else "#NoTrans")

        self.locale_title = title

    async def on_submit(self, i: Interaction) -> None:
        for child in self.children:
            if isinstance(child, TextInput):
                child.validate(child.value)

        await i.response.defer(ephemeral=True)
        self.stop()

    async def on_error(self, i: Interaction, error: Exception) -> None:
        embed, recognized = i.client.create_error_embed(error, locale=i.locale)
        if not recognized:
            logger.exception(f"An unrecognized error occurred in {self.__class__.__name__}.")

        await absolute_send(i, embed=embed, ephemeral=True)

    @property
    def incomplete(self) -> bool:
        return any(
            isinstance(child, discord.ui.TextInput) and child.required and not child.value for child in self.children
        )

    def translate(self, translator: Translator, locale: discord.Locale) -> None:
        if isinstance(self.locale_title, LocaleStr):
            self.title = translator.translate(self.locale_title, locale=locale).title()

        for child in self.children:
            if isinstance(child, TextInput):
                child.translate(translator, locale=locale)


class TextInput(discord.ui.TextInput):
    def __init__(
        self,
        *,
        label: LocaleStr | str,
        placeholder: LocaleStr | str | None = None,
        default: LocaleStr | str | None = None,
        style: discord.TextStyle = discord.TextStyle.short,
        min_length: int | None = None,
        max_length: int | None = None,
        is_integer: bool = False,
        is_positive: bool = False,
        min_value: int | None = None,
        max_value: int | None = None,
    ) -> None:
        super().__init__(
            label=label if isinstance(label, str) else "#NoTrans",
            style=style,
            min_length=min_length,
            max_length=max_length,
        )

        self.locale_label = label
        self.locale_placeholder = placeholder
        self.locale_default = default

        self.is_integer = is_integer
        self.is_positive = is_positive
        self.min_value = min_value
        self.max_value = max_value

    def translate(self, translator: Translator, locale: discord.Locale) -> None:
        if isinstance(self.locale_label, LocaleStr):
            self.label = translator.translate(self.locale_label, locale=locale)

        if isinstance(self.locale_placeholder, LocaleStr):
            self.placeholder = translator.translate(self.locale_placeholder, locale=locale)
        elif self.locale_placeholder is None and self.min_value is not None and self.max_value is not None:
            self.placeholder = f"{self.min_value}~{self.max_value}"

        if isinstance(self.locale_default, LocaleStr):
            self.default = translator.translate(self.locale_default, locale=locale)

    def validate(self, value: str) -> None:
        if self.is_integer:
            try:
                int_value = int(value)
            except ValueError as e:
                raise InvalidInputError(value) from e

            if self.is_positive and int_value <= 0:
                raise InvalidInputError(value)

            if self.min_value is not None and int_value < self.min_value:
                raise InvalidInputError(value)

            if self.max_value is not None and int_value > self.max_value:
                raise InvalidInputError(value)


class Paginator(View):
    def __init__(self, embeds: Sequence[LuminaEmbed], *, translator: Translator, locale: discord.Locale) -> None:
        super().__init__(translator, locale)
        self._embeds = embeds
        self._page = 0

    def _set_footers(self) -> None:
        for i, embed in enumerate(self._embeds):
            embed.set_footer(text=LocaleStr("paginator_footer", params={"page": i + 1, "total": len(self._embeds)}))

    def _toggle_buttons(self) -> None:
        self.previous_page.disabled = self._page == 0
        self.next_page.disabled = self._page == len(self._embeds) - 1

    async def _update(self, i: Interaction) -> None:
        self._toggle_buttons()
        await i.response.edit_message(embed=self._embeds[self._page], view=self)

    @discord.ui.button(style=discord.ButtonStyle.primary, emoji="<:left:1284353344466583562>")
    async def previous_page(self, i: Interaction, _: discord.ui.Button) -> None:
        self._page = max(0, self._page - 1)
        await self._update(i)

    @discord.ui.button(style=discord.ButtonStyle.primary, emoji="<:right:1284353315408183317>")
    async def next_page(self, i: Interaction, _: discord.ui.Button) -> None:
        self._page = min(len(self._embeds) - 1, self._page + 1)
        await self._update(i)

    async def start(self, i: Interaction) -> Any:
        self._set_footers()
        self._toggle_buttons()
        await absolute_send(i, embed=self._embeds[self._page], view=self, ephemeral=True)
        self.message = await i.original_response()
