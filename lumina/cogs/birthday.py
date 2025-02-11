from __future__ import annotations

import calendar
from typing import TYPE_CHECKING, Any

import tortoise
import tortoise.exceptions
from discord import ButtonStyle, Locale, app_commands
from discord.ext import commands

from lumina.components import Button, Modal, Paginator, TextInput, View
from lumina.exceptions import DidNotSetBirthdayError, InvalidInputError, NoBirthdaysError
from lumina.l10n import LocaleStr, translator
from lumina.models import Birthday, LuminaUser, get_locale
from lumina.types import UserOrMember  # noqa: TC001
from lumina.utils import absolute_send, split_list_to_chunks

if TYPE_CHECKING:
    from lumina.bot import Lumina
    from lumina.embeds import DefaultEmbed
    from lumina.types import Interaction

FEBRUARY = 2


class BirthdayModal(Modal):
    month = TextInput(label=LocaleStr("birthday_modal_month_label"), is_integer=True, min_value=1, max_value=12)
    day = TextInput(label=LocaleStr("birthday_modal_day_label"), is_integer=True, min_value=1, max_value=31)


class LeapYearNotifyView(View):
    def __init__(self, locale: Locale, *, birthday: Birthday) -> None:
        super().__init__(locale)

        self.birthday = birthday

        self.add_item(NotifyButton(LocaleStr("notify_on_mar_1"), month=3, day=1))
        self.add_item(NotifyButton(LocaleStr("notify_on_feb_28"), month=2, day=28))
        self.add_item(NotifyButton(LocaleStr("dont_notify"), month=None, day=None))


class NotifyButton(Button[LeapYearNotifyView]):
    def __init__(self, label: LocaleStr, *, month: int | None, day: int | None) -> None:
        super().__init__(label=label, style=ButtonStyle.blurple)

        self.month = month
        self.day = day

    async def callback(self, i: Interaction) -> None:
        self.view.birthday.leap_year_notify_month = self.month
        self.view.birthday.leap_year_notify_day = self.day
        await self.view.birthday.save(update_fields=("leap_year_notify_month", "leap_year_notify_day"))

        embed = LuminaUser.get_settings_saved_embed(self.view.locale)
        await i.response.send_message(embed=embed, ephemeral=True)


class BirthdayCog(commands.GroupCog, name=app_commands.locale_str("birthday", key="birthday_group_name")):
    def __init__(self, bot: Lumina) -> None:
        self.bot = bot

        self.set_bday_ctx_menu = app_commands.ContextMenu(
            name=app_commands.locale_str("Set birthday", key="set_birthday_ctx_menu_name"),
            callback=self.set_birthday_ctx_menu,
        )
        self.remove_bday_ctx_menu = app_commands.ContextMenu(
            name=app_commands.locale_str("Remove birthday", key="remove_birthday_ctx_menu_name"),
            callback=self.remove_birthday,
        )

    async def cog_load(self) -> None:
        self.bot.tree.add_command(self.remove_bday_ctx_menu)
        self.bot.tree.add_command(self.set_bday_ctx_menu)

    async def cog_unload(self) -> None:
        self.bot.tree.remove_command(self.set_bday_ctx_menu.name, type=self.set_bday_ctx_menu.type)
        self.bot.tree.remove_command(self.remove_bday_ctx_menu.name, type=self.remove_bday_ctx_menu.type)

    async def set_birthday_ctx_menu(self, i: Interaction, user: UserOrMember) -> Any:
        modal = BirthdayModal(title=LocaleStr("birthday_modal_title"))
        modal.translate(await get_locale(i))

        await i.response.send_modal(modal)
        await modal.wait()
        if modal.incomplete:
            return

        await self.set_birthday(i, user, int(modal.month.value), int(modal.day.value))

    async def set_birthday(self, i: Interaction, user: UserOrMember, month: int, day: int) -> None:
        num_days = calendar.monthrange(2000, month)[1]
        if month == FEBRUARY:
            num_days = 29

        if day > num_days:
            raise InvalidInputError(str(day))

        lumina_user, _ = await LuminaUser.get_or_create(id=i.user.id)
        locale = await get_locale(i)

        try:
            birthday = await Birthday.create(bday_user_id=user.id, user=lumina_user, month=month, day=day)
        except tortoise.exceptions.IntegrityError:
            birthday = await Birthday.get(bday_user_id=user.id, user=lumina_user)
            birthday.month = month
            birthday.day = day
            await birthday.save(update_fields=("month", "day"))

        embeds = [Birthday.get_created_embed(locale, user=user, month=month, day=day, timezone=lumina_user.timezone)]
        if (month, day) == (2, 29):
            embeds.append(Birthday.get_leap_year_notify_embed(locale))
            view = LeapYearNotifyView(locale, birthday=birthday)
        else:
            view = None

        await absolute_send(i, embeds=embeds, ephemeral=True, view=view)

    async def remove_birthday(self, i: Interaction, user: UserOrMember) -> Any:
        lumina_user, _ = await LuminaUser.get_or_create(id=i.user.id)
        bday = await Birthday.get_or_none(bday_user_id=user.id, user=lumina_user)
        if bday is None:
            raise DidNotSetBirthdayError(user_id=user.id)

        await bday.delete()
        await i.response.send_message(embed=Birthday.get_removed_embed(await get_locale(i), user=user), ephemeral=True)

    @app_commands.command(
        name=app_commands.locale_str("set", key="birthday_set_command_name"),
        description=app_commands.locale_str("Set someone's birthday", key="birthday_set_command_description"),
    )
    @app_commands.rename(
        user=app_commands.locale_str("user", key="user_parameter_name"),
        month=app_commands.locale_str("month", key="month_parameter_name"),
        day=app_commands.locale_str("day", key="day_parameter_name"),
    )
    @app_commands.describe(
        user=app_commands.locale_str("The user whose birthday you want to set", key="bday_set_user_param_desc"),
        month=app_commands.locale_str("The month of the birthday", key="bday_set_month_param_desc"),
        day=app_commands.locale_str("The day of the birthday", key="bday_set_day_param_desc"),
    )
    async def birthday_set(
        self,
        i: Interaction,
        user: UserOrMember,
        month: app_commands.Range[int, 1, 12],
        day: app_commands.Range[int, 1, 31],
    ) -> None:
        await i.response.defer(ephemeral=True)
        await self.set_birthday(i, user, month, day)

    @birthday_set.autocomplete("month")
    async def month_autocomplete(self, _: Interaction, current: str) -> list[app_commands.Choice[int]]:
        return [
            app_commands.Choice(name=str(month), value=month)
            for month in range(1, 13)
            if str(month).startswith(current)
        ][:25]

    @birthday_set.autocomplete("day")
    async def day_autocomplete(self, i: Interaction, current: str) -> list[app_commands.Choice[int]]:
        month = i.namespace.month
        if month is None:
            return [
                app_commands.Choice(
                    name=translator.translate(LocaleStr("select_month_first"), locale=await get_locale(i)), value=-1
                )
            ]

        num_days = calendar.monthrange(2000, month)[1]
        if month == FEBRUARY:
            num_days = 29

        return [
            app_commands.Choice(name=str(day), value=day)
            for day in range(1, num_days + 1)
            if str(day).startswith(current)
        ][:25]

    @app_commands.command(
        name=app_commands.locale_str("remove", key="birthday_remove_command_name"),
        description=app_commands.locale_str("Remove someone's birthday", key="birthday_remove_command_description"),
    )
    @app_commands.rename(user=app_commands.locale_str("user", key="user_parameter_name"))
    @app_commands.describe(
        user=app_commands.locale_str("The user whose birthday you want to remove", key="bday_remove_user_param_desc")
    )
    async def birthday_remove(self, i: Interaction, user: UserOrMember) -> None:
        await i.response.defer(ephemeral=True)

        lumina_user, _ = await LuminaUser.get_or_create(id=i.user.id)
        bday = await Birthday.get_or_none(bday_user_id=user.id, user=lumina_user)
        if bday is None:
            raise DidNotSetBirthdayError(user_id=user.id)

        await bday.delete()
        await i.followup.send(embed=Birthday.get_removed_embed(await get_locale(i), user=user), ephemeral=True)

    @app_commands.command(
        name=app_commands.locale_str("list", key="birthday_list_command_name"),
        description=app_commands.locale_str("List all birthdays you have set", key="birthday_list_command_description"),
    )
    async def birthday_list(self, i: Interaction) -> None:
        await i.response.defer(ephemeral=True)

        user, _ = await LuminaUser.get_or_create(id=i.user.id)
        birthdays = await Birthday.filter(user=user).all()
        if not birthdays:
            raise NoBirthdaysError

        split_birthdays = split_list_to_chunks(birthdays, 10)
        timezone = (await LuminaUser.get_or_create(id=i.user.id))[0].timezone
        locale = await get_locale(i)
        embeds: list[DefaultEmbed] = []

        for index, bdays in enumerate(split_birthdays):
            embeds.append(Birthday.get_list_embed(locale, birthdays=bdays, timezone=timezone, start=1 + index * 10))

        view = Paginator(embeds, locale=locale)
        await view.start(i)


async def setup(bot: Lumina) -> None:
    await bot.add_cog(BirthdayCog(bot))
