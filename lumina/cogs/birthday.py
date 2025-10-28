from __future__ import annotations

import calendar
import itertools
from typing import TYPE_CHECKING, Any

from discord import ButtonStyle, Locale, app_commands
from discord.ext import commands

from lumina.components import Button, Modal, Paginator, TextInput, View
from lumina.embeds import DefaultEmbed
from lumina.exceptions import DidNotSetBirthdayError, InvalidBirthdayInputError, InvalidInputError, NoBirthdaysError
from lumina.l10n import LocaleStr, translator
from lumina.models import Birthday, LuminaUser, get_locale, get_timezone
from lumina.types import UserOrMember  # noqa: TC001
from lumina.utils import absolute_send, get_now, sort_birthdays_by_next

if TYPE_CHECKING:
    from lumina.bot import Lumina
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


class BirthdayCog(commands.GroupCog, name=app_commands.locale_str("birthday", key="birthday_group_name")):  # type: ignore
    def __init__(self, bot: Lumina) -> None:
        self.bot = bot

        self.set_bday_ctx_menu = app_commands.ContextMenu(
            name=app_commands.locale_str("Set birthday", key="set_birthday_ctx_menu_name"),
            callback=self.set_birthday_ctx_menu,
        )
        self.remove_bday_ctx_menu = app_commands.ContextMenu(
            name=app_commands.locale_str("Remove birthday", key="remove_birthday_ctx_menu_name"),
            callback=self.remove_birthday_ctx_menu,
        )
        self.see_bday_ctx_menu = app_commands.ContextMenu(
            name=app_commands.locale_str("See birthday", key="see_birthday_ctx_menu_name"),
            callback=self.see_birthday_ctx_menu,
        )

    async def cog_load(self) -> None:
        self.bot.tree.add_command(self.remove_bday_ctx_menu)
        self.bot.tree.add_command(self.set_bday_ctx_menu)
        self.bot.tree.add_command(self.see_bday_ctx_menu)

    async def cog_unload(self) -> None:
        self.bot.tree.remove_command(self.set_bday_ctx_menu.name, type=self.set_bday_ctx_menu.type)
        self.bot.tree.remove_command(self.remove_bday_ctx_menu.name, type=self.remove_bday_ctx_menu.type)
        self.bot.tree.remove_command(self.see_bday_ctx_menu.name, type=self.see_bday_ctx_menu.type)

    async def set_birthday_ctx_menu(self, i: Interaction, user: UserOrMember) -> Any:
        modal = BirthdayModal(title=LocaleStr("birthday_modal_title"))
        modal.translate(await get_locale(i))

        await i.response.send_modal(modal)
        await modal.wait()
        if modal.incomplete:
            return

        await self.set_birthday(i, month=int(modal.month.value), day=int(modal.day.value), user=user)

    async def remove_birthday_ctx_menu(self, i: Interaction, user: UserOrMember) -> Any:
        await self.remove_birthday(i, user=user)

    async def see_birthday_ctx_menu(self, i: Interaction, user: UserOrMember) -> Any:
        await i.response.defer(ephemeral=True)

        lumina_user, _ = await LuminaUser.get_or_create(id=i.user.id)
        bday = await Birthday.get_or_none(lumina_user.id, user=user)
        if bday is None:
            msg = f"<@{user.id}>"
            raise DidNotSetBirthdayError(msg)

        embed = bday.get_display_embed(
            await get_locale(i), user=user, timezone=lumina_user.timezone, avatar_url=user.display_avatar.url
        )
        await i.followup.send(embed=embed)

    async def set_birthday(
        self,
        i: Interaction,
        *,
        month: int,
        day: int,
        user: UserOrMember | None = None,
        name: str | None = None,
        notify_days_before: int | None = None,
    ) -> None:
        if (user is None and name is None) or (user is not None and name is not None):
            raise InvalidBirthdayInputError

        num_days = calendar.monthrange(2000, month)[1]
        if month == FEBRUARY:
            num_days = 29

        if day > num_days:
            raise InvalidInputError(str(day))

        lumina_user, _ = await LuminaUser.get_or_create(id=i.user.id)
        locale = await get_locale(i)

        bday = await Birthday.create_or_update(lumina_user.id, month=month, day=day, user=user, name=name)

        # Set early notification if specified
        if notify_days_before is not None:
            bday.notify_days_before = notify_days_before if notify_days_before > 0 else None
            await bday.save(update_fields=("notify_days_before",))

        embeds = [
            bday.get_created_embed(
                locale,
                timezone=lumina_user.timezone,
                user=user,
                avatar_url=user.display_avatar.url if user is not None else None,
            )
        ]

        # Add early notification info to embed if set
        if notify_days_before is not None and notify_days_before > 0:
            embeds.append(
                DefaultEmbed(
                    locale=locale,
                    title=LocaleStr("birthday_early_notify_set_embed_title"),
                    description=LocaleStr(
                        "birthday_early_notify_set_embed_description",
                        params={"user": bday.get_user_name(user), "days": str(notify_days_before)},
                    ),
                )
            )

        if (month, day) == (2, 29):
            embeds.append(Birthday.get_leap_year_notify_embed(locale))
            view = LeapYearNotifyView(locale, birthday=bday)
        else:
            view = None

        await absolute_send(i, embeds=embeds, ephemeral=True, view=view)

    async def remove_birthday(self, i: Interaction, user: UserOrMember | None = None, name: str | None = None) -> Any:
        if (user is None and name is None) or (user is not None and name is not None):
            raise InvalidBirthdayInputError

        lumina_user, _ = await LuminaUser.get_or_create(id=i.user.id)
        bday = await Birthday.get_or_none(lumina_user.id, user=user, name=name)
        if bday is None:
            raise DidNotSetBirthdayError(f"<@{user.id}>" if user is not None else name)  # type: ignore[reportArgumentType]

        await bday.delete()
        await i.response.send_message(embed=bday.get_removed_embed(await get_locale(i), user=user), ephemeral=True)  # pyright: ignore[reportArgumentType]

    @app_commands.command(
        name=app_commands.locale_str("set", key="birthday_set_command_name"),
        description=app_commands.locale_str("Set someone's birthday", key="birthday_set_command_description"),
    )
    @app_commands.rename(
        month=app_commands.locale_str("month", key="month_parameter_name"),
        day=app_commands.locale_str("day", key="day_parameter_name"),
        user=app_commands.locale_str("user", key="user_parameter_name"),
        name=app_commands.locale_str("name", key="name_parameter_name"),
        notify_days_before=app_commands.locale_str("notify-days-before", key="notify_days_before_parameter_name"),
    )
    @app_commands.describe(
        user=app_commands.locale_str("The user whose birthday you want to set", key="bday_set_user_param_desc"),
        month=app_commands.locale_str("The month of the birthday", key="bday_set_month_param_desc"),
        day=app_commands.locale_str("The day of the birthday", key="bday_set_day_param_desc"),
        name=app_commands.locale_str("The name of the user", key="bday_set_name_param_desc"),
        notify_days_before=app_commands.locale_str(
            "Days before birthday to send early notification (optional)", key="bday_set_notify_days_before_param_desc"
        ),
    )
    async def birthday_set(
        self,
        i: Interaction,
        month: app_commands.Range[int, 1, 12],
        day: app_commands.Range[int, 1, 31],
        *,
        user: UserOrMember | None = None,
        name: str | None = None,
        notify_days_before: app_commands.Range[int, 1, 365] | None = None,
    ) -> None:
        await i.response.defer(ephemeral=True)
        await self.set_birthday(i, month=month, day=day, user=user, name=name, notify_days_before=notify_days_before)

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
    @app_commands.rename(
        user=app_commands.locale_str("user", key="user_parameter_name"),
        name=app_commands.locale_str("name", key="name_parameter_name"),
    )
    @app_commands.describe(
        user=app_commands.locale_str("The user whose birthday you want to remove", key="bday_remove_user_param_desc"),
        name=app_commands.locale_str("The name of the user", key="bday_set_name_param_desc"),
    )
    async def birthday_remove(self, i: Interaction, user: UserOrMember | None = None, name: str | None = None) -> None:
        await self.remove_birthday(i, user, name)

    @app_commands.command(
        name=app_commands.locale_str("list", key="birthday_list_command_name"),
        description=app_commands.locale_str("List all birthdays you have set", key="birthday_list_command_description"),
    )
    async def birthday_list(self, i: Interaction) -> None:
        await i.response.defer(ephemeral=True)

        birthdays = await Birthday.filter(user_id=i.user.id)
        if not birthdays:
            raise NoBirthdaysError

        now = get_now(await get_timezone(i.user.id))
        birthdays = sort_birthdays_by_next(birthdays, now)

        split_birthdays = itertools.batched(birthdays, 10)
        timezone = (await LuminaUser.get_or_create(id=i.user.id))[0].timezone
        locale = await get_locale(i)
        embeds: list[DefaultEmbed] = []

        for index, bdays in enumerate(split_birthdays):
            embeds.append(Birthday.get_list_embed(locale, birthdays=bdays, timezone=timezone, start=1 + index * 10))

        view = Paginator(embeds, locale=locale)
        await view.start(i)

    @birthday_remove.autocomplete("name")
    async def bday_name_autocomplete(self, i: Interaction, current: str) -> list[app_commands.Choice[str]]:
        bdays = await Birthday.filter(
            bday_username__isnull=False, bday_username__icontains=current, user_id=i.user.id, bday_user_id=0
        ).limit(25)
        return [app_commands.Choice(name=str(bday.bday_username), value=str(bday.bday_username)) for bday in bdays]


async def setup(bot: Lumina) -> None:
    await bot.add_cog(BirthdayCog(bot))
