from __future__ import annotations

from typing import TYPE_CHECKING, Any

import discord
from discord import TextStyle, app_commands
from discord.ext import commands

from lumina.components import Modal, Paginator, TextInput
from lumina.exceptions import NoTasksError, TodoNotFoundError
from lumina.l10n import LocaleStr, translator
from lumina.models import LuminaUser, TodoTask, get_locale
from lumina.utils import shorten_text, split_list_to_chunks

if TYPE_CHECKING:
    from lumina.bot import Lumina
    from lumina.embeds import DefaultEmbed
    from lumina.types import Interaction


class TodoModal(Modal):
    text = TextInput(
        label=LocaleStr("todo_modal_text_label"),
        placeholder=LocaleStr("todo_modal_text_placeholder"),
        style=TextStyle.long,
    )


class TodoCog(commands.GroupCog, name=app_commands.locale_str("todo", key="todo_group_name")):
    def __init__(self, bot: Lumina) -> None:
        self.bot = bot

        self.add_to_todo_ctx_menu = app_commands.ContextMenu(
            name=app_commands.locale_str("Add to to-do list", key="add_todo_ctx_menu_name"), callback=self.add_to_todo
        )

    async def cog_load(self) -> None:
        self.bot.tree.add_command(self.add_to_todo_ctx_menu)

    async def cog_unload(self) -> None:
        self.bot.tree.remove_command(self.add_to_todo_ctx_menu.name, type=self.add_to_todo_ctx_menu.type)

    async def add_to_todo(self, i: Interaction, message: discord.Message) -> Any:
        await i.response.defer(ephemeral=True)

        locale = await get_locale(i)
        user, _ = await LuminaUser.get_or_create(id=i.user.id)
        todo = await TodoTask.create(
            text=message.content or translator.translate(LocaleStr("no_content"), locale=locale), user=user
        )
        await i.followup.send(embed=todo.get_created_embed(locale), ephemeral=True)

    @app_commands.command(
        name=app_commands.locale_str("add", key="todo_add_command_name"),
        description=app_commands.locale_str("Set a reminder", key="todo_add_command_description"),
    )
    @app_commands.rename(text=app_commands.locale_str("text", key="text_parameter_name"))
    @app_commands.describe(text=app_commands.locale_str("The task to add", key="todo_add_text_param_desc"))
    async def todo_add_command(self, i: Interaction, text: str) -> None:
        await i.response.defer(ephemeral=True)

        user, _ = await LuminaUser.get_or_create(id=i.user.id)
        todo = await TodoTask.create(text=text, user=user)
        await i.followup.send(embed=todo.get_created_embed(await get_locale(i)), ephemeral=True)

    @app_commands.command(
        name=app_commands.locale_str("done", key="todo_done_command_name"),
        description=app_commands.locale_str("Mark a task as done", key="todo_done_command_description"),
    )
    @app_commands.rename(task_id=app_commands.locale_str("task", key="task_parameter_name"))
    @app_commands.describe(task_id=app_commands.locale_str("The task to mark as done", key="task_param_desc"))
    async def todo_done(self, i: Interaction, task_id: int) -> None:
        user, _ = await LuminaUser.get_or_create(id=i.user.id)
        todo = await TodoTask.get_or_none(id=task_id, user=user)
        if todo is None:
            raise TodoNotFoundError

        await todo.mark_done()
        await i.response.send_message(embed=todo.get_done_embed(await get_locale(i)), ephemeral=True)

    @app_commands.command(
        name=app_commands.locale_str("remove", key="birthday_remove_command_name"),
        description=app_commands.locale_str(
            "Remove a task from your to-do list", key="todo_remove_command_description"
        ),
    )
    @app_commands.rename(task_id=app_commands.locale_str("task", key="task_parameter_name"))
    @app_commands.describe(task_id=app_commands.locale_str("The task to remove", key="task_remove_param_desc"))
    async def todo_remove(self, i: Interaction, task_id: int) -> None:
        user, _ = await LuminaUser.get_or_create(id=i.user.id)
        todo = await TodoTask.get_or_none(id=task_id, user=user)
        if todo is None:
            raise TodoNotFoundError

        await todo.delete()
        await i.response.send_message(embed=todo.get_removed_embed(await get_locale(i)), ephemeral=True)

    @todo_done.autocomplete("task_id")
    async def task_done_task_id_autocomplete(self, i: Interaction, current: str) -> list[app_commands.Choice[int]]:
        user, _ = await LuminaUser.get_or_create(id=i.user.id)
        tasks = await TodoTask.filter(user=user, done=False).all()

        if not tasks:
            return [
                app_commands.Choice(
                    name=translator.translate(LocaleStr("no_tasks_title"), locale=await get_locale(i)), value=-1
                )
            ]

        return [
            app_commands.Choice(name=shorten_text(task.text, 100), value=task.id)
            for task in tasks
            if current.lower() in task.text.lower()
        ][:25]

    @todo_remove.autocomplete("task_id")
    async def task_id_autocomplete(self, i: Interaction, current: str) -> list[app_commands.Choice[int]]:
        user, _ = await LuminaUser.get_or_create(id=i.user.id)
        tasks = await TodoTask.filter(user=user).all()

        if not tasks:
            return [
                app_commands.Choice(
                    name=translator.translate(LocaleStr("no_tasks_title"), locale=await get_locale(i)), value=-1
                )
            ]

        return [
            app_commands.Choice(name=shorten_text(task.text, 100), value=task.id)
            for task in tasks
            if current.lower() in task.text.lower()
        ][:25]

    @app_commands.command(
        name=app_commands.locale_str("list", key="birthday_list_command_name"),
        description=app_commands.locale_str("List all tasks in your to-do list", key="todo_list_command_description"),
    )
    @app_commands.rename(show_done_tasks=app_commands.locale_str("show-done", key="show_done_tasks_parameter_name"))
    @app_commands.describe(
        show_done_tasks=app_commands.locale_str("Show completed tasks", key="show_done_tasks_param_description")
    )
    @app_commands.choices(
        show_done_tasks=[
            app_commands.Choice(name=app_commands.locale_str("Yes", key="yes_text"), value=1),
            app_commands.Choice(name=app_commands.locale_str("No", key="no_text"), value=0),
        ]
    )
    async def todo_list(self, i: Interaction, show_done_tasks: int = 0) -> None:
        await i.response.defer(ephemeral=True)
        user, _ = await LuminaUser.get_or_create(id=i.user.id)
        show_done_tasks = bool(show_done_tasks)

        if not show_done_tasks:
            tasks = await TodoTask.filter(user=user, done=False).all()
        else:
            tasks = await TodoTask.filter(user=user).all()

        if not tasks:
            raise NoTasksError

        chunked_tasks = split_list_to_chunks(tasks, 10)
        locale = await get_locale(i)
        embeds: list[DefaultEmbed] = []

        for index, tasks_ in enumerate(chunked_tasks):
            embeds.append(TodoTask.get_list_embed(locale, todos=tasks_, start=1 + index * 10))

        view = Paginator(embeds, locale=locale)
        await view.start(i)


async def setup(bot: Lumina) -> None:
    await bot.add_cog(TodoCog(bot))
