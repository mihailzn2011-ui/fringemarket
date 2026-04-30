import discord
from discord.ext import commands
from discord import app_commands
import asyncio
import os
from dotenv import load_dotenv
from db import DBManager

load_dotenv()

intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)
db = DBManager()

# Channel IDs
WATCH_CHANNEL = 1429899592824258590
REVIEW_CHANNEL = 1499473605535203358
WARN_ANNOUNCE_CHANNEL = 1429895979863113832
PROMOTION_CHANNEL = 1493355826138583061

# Salary application channels
SALARY_FORUM = 1429899084331876494
SALARY_REVIEW = 1499473760673505387

# Day off application channels
DAYOFF_FORUM = 1429895980177821772
DAYOFF_REVIEW = 1499473645863571637
DAYOFF_ROLE = 1493325741444563198

# Promotion application channels
PROMO_APP_FORUM = 1429895980177821773
PROMO_APP_REVIEW = 1499473570617753700

# Leaderboard channel
LEADERBOARD_CHANNEL = 1441724727910469633
DAYOFF_LEADERBOARD_CHANNEL = 1496230104756523099  # Канал для таблицы отгулов
WARN_LEADERBOARD_CHANNEL = 1473657044899856414  # Канал для списка варнов

# Commands channel
COMMANDS_CHANNEL = 1499413386411114710

# Allowed roles for commands
ALLOWED_COMMAND_ROLES = [
    1429895978986635471,
    1429895978986635472,
    1432365999457308702,
    1429895978986635473,
    1429895978986635475,
    1430265900526862438,
    1429895978986635476,
]

# Warn role IDs
WARN_ROLES = [
    1429895978931978273,
    1429895978931978274,
    1429895978931978275,
]

# Mute role IDs
MUTE_ROLES = [
    1469416711798390927,
    1469416666772406335,
]

# Staff role IDs
STAFF_ROLES = [
    1429895978931978278,
    1429895978931978279,
    1430261456514977923,
    1429895978986635467,
    1438962347589898331,
    1429895978986635468,
    1429895978986635469,
]

STAFF_NAMES = ["Хелпер", "Ст. Хелпер", "Мл. Модер", "Модер", "Модер+", "Ст. Модер", "Гл. Модер"]

BONUS_SALARY_ROLE = 1466142358549823672
BONUS_POINTS_ROLE = 1466142620580450439


@bot.event
async def on_ready():
    print(f"Бот {bot.user} запущен!")
    print(f"Подключен к {len(bot.guilds)} серверам")
    
    try:
        # Синхронизируем команды
        synced = await bot.tree.sync()
        print(f"<:white_black_staff_badge:1499471650532360254> Синхронизировано {len(synced)} команд!")
        for cmd in synced:
            print(f"  - /{cmd.name}")
    except Exception as e:
        print(f"<:dnd_badge:1499472489112273077> Ошибка синхронизации команд: {e}")
        import traceback
        traceback.print_exc()
    
    # Обновляем лидерборды
    try:
        await update_leaderboard()
        print("<:white_black_staff_badge:1499471650532360254> Лидерборд баллов обновлен!")
    except Exception as e:
        print(f"<:dnd_badge:1499472489112273077> Ошибка обновления лидерборда баллов: {e}")
    
    try:
        await update_dayoff_leaderboard()
        print("<:white_black_staff_badge:1499471650532360254> Лидерборд отгулов обновлен!")
    except Exception as e:
        print(f"<:dnd_badge:1499472489112273077> Ошибка обновления лидерборда отгулов: {e}")
    
    try:
        await update_warn_leaderboard()
        print("<:white_black_staff_badge:1499471650532360254> Лидерборд варнов обновлен!")
    except Exception as e:
        print(f"<:dnd_badge:1499472489112273077> Ошибка обновления лидерборда варнов: {e}")
    
    # Восстанавливаем таймеры для отгулов
    try:
        await restore_dayoff_timers()
        print("<:white_black_staff_badge:1499471650532360254> Таймеры отгулов восстановлены!")
    except Exception as e:
        print(f"<:dnd_badge:1499472489112273077> Ошибка восстановления таймеров: {e}")


@bot.event
async def on_message(message):
    if (
        message.channel.id == WATCH_CHANNEL
        and not message.author.bot
        and not isinstance(message.channel, discord.Thread)
    ):
        await forward_to_review(message, thread_id=None)

    await bot.process_commands(message)


@bot.event
async def on_thread_create(thread: discord.Thread):
    # Заявки на баллы
    if thread.parent_id == WATCH_CHANNEL:
        await handle_points_thread(thread)
    # Заявки на зарплату
    elif thread.parent_id == SALARY_FORUM:
        await handle_salary_thread(thread)
    # Заявки на отгул
    elif thread.parent_id == DAYOFF_FORUM:
        await handle_dayoff_thread(thread)
    # Заявки на повышение
    elif thread.parent_id == PROMO_APP_FORUM:
        await handle_promotion_thread(thread)


async def handle_points_thread(thread: discord.Thread):
    await asyncio.sleep(1.5)

    try:
        starter = await thread.fetch_message(thread.id)
    except Exception:
        starter = None

    review_channel = bot.get_channel(REVIEW_CHANNEL)
    if not review_channel:
        return

    author = thread.owner
    content = starter.content if starter else ""
    attachment_url = starter.attachments[0].url if starter and starter.attachments else None

    embed = discord.Embed(
        title=f"📋 {thread.name}",
        description=content or "*Без текста*",
        color=0x5865F2
    )
    if author:
        embed.set_author(name=str(author), icon_url=author.display_avatar.url)
    embed.set_footer(text=f"ID автора: {thread.owner_id} | Тред: {thread.id}")
    if attachment_url:
        embed.set_image(url=attachment_url)

    view = ReviewView(author_id=thread.owner_id, source_thread_id=thread.id)
    await review_channel.send(embed=embed, view=view)


async def handle_salary_thread(thread: discord.Thread):
    await asyncio.sleep(1.5)

    try:
        starter = await thread.fetch_message(thread.id)
    except Exception:
        starter = None

    review_channel = bot.get_channel(SALARY_REVIEW)
    if not review_channel:
        return

    author = thread.owner
    content = starter.content if starter else ""
    attachment_url = starter.attachments[0].url if starter and starter.attachments else None

    embed = discord.Embed(
        title=f"💰 Заявка на зарплату: {thread.name}",
        description=content or "*Без текста*",
        color=0xF1C40F
    )
    if author:
        embed.set_author(name=str(author), icon_url=author.display_avatar.url)
    embed.set_footer(text=f"ID автора: {thread.owner_id} | Тред: {thread.id}")
    if attachment_url:
        embed.set_image(url=attachment_url)

    view = SalaryReviewView(author_id=thread.owner_id, source_thread_id=thread.id)
    await review_channel.send(embed=embed, view=view)


async def handle_dayoff_thread(thread: discord.Thread):
    await asyncio.sleep(1.5)

    try:
        starter = await thread.fetch_message(thread.id)
    except Exception:
        starter = None

    review_channel = bot.get_channel(DAYOFF_REVIEW)
    if not review_channel:
        return

    author = thread.owner
    content = starter.content if starter else ""
    attachment_url = starter.attachments[0].url if starter and starter.attachments else None

    embed = discord.Embed(
        title=f"🏖️ Заявка на отгул: {thread.name}",
        description=content or "*Без текста*",
        color=0x3498DB
    )
    if author:
        embed.set_author(name=str(author), icon_url=author.display_avatar.url)
    embed.set_footer(text=f"ID автора: {thread.owner_id} | Тред: {thread.id}")
    if attachment_url:
        embed.set_image(url=attachment_url)

    view = DayoffReviewView(author_id=thread.owner_id, source_thread_id=thread.id)
    await review_channel.send(embed=embed, view=view)


async def handle_promotion_thread(thread: discord.Thread):
    await asyncio.sleep(1.5)

    try:
        starter = await thread.fetch_message(thread.id)
    except Exception:
        starter = None

    review_channel = bot.get_channel(PROMO_APP_REVIEW)
    if not review_channel:
        return

    author = thread.owner
    content = starter.content if starter else ""
    attachment_url = starter.attachments[0].url if starter and starter.attachments else None

    embed = discord.Embed(
        title=f"⬆️ Заявка на повышение: {thread.name}",
        description=content or "*Без текста*",
        color=0x9B59B6
    )
    if author:
        embed.set_author(name=str(author), icon_url=author.display_avatar.url)
    embed.set_footer(text=f"ID автора: {thread.owner_id} | Тред: {thread.id}")
    if attachment_url:
        embed.set_image(url=attachment_url)

    view = PromotionAppReviewView(author_id=thread.owner_id, source_thread_id=thread.id)
    await review_channel.send(embed=embed, view=view)


async def forward_to_review(message: discord.Message, thread_id):
    review_channel = bot.get_channel(REVIEW_CHANNEL)
    if not review_channel:
        return

    embed = discord.Embed(
        title="📋 Новая заявка",
        description=message.content or "*Без текста*",
        color=0x5865F2
    )
    embed.set_author(name=str(message.author), icon_url=message.author.display_avatar.url)
    embed.set_footer(text=f"ID автора: {message.author.id}")
    if message.attachments:
        embed.set_image(url=message.attachments[0].url)

    view = ReviewView(author_id=message.author.id, source_thread_id=thread_id)
    await review_channel.send(embed=embed, view=view)


# ─── УВЕДОМЛЕНИЕ В ТРЕД ИГРОКА ────────────────────────────────────────────────

async def notify_author_in_thread(thread_id: int | None, author_id: int, approved: bool, details: str = "", admin_name: str = ""):
    if not thread_id:
        return

    channel = bot.get_channel(WATCH_CHANNEL)
    if not channel:
        return

    thread = None
    if isinstance(channel, discord.ForumChannel):
        try:
            thread = channel.get_thread(thread_id)
            if not thread:
                thread = await bot.fetch_channel(thread_id)
        except Exception:
            return
    else:
        return

    if approved:
        embed = discord.Embed(
            title="<:white_black_staff_badge:1499471650532360254> Заявка одобрена",
            description=f"<@{author_id}>, твоя заявка была **одобрена**. 🎉",
            color=0x57F287
        )
        embed.add_field(name="📌 Детали", value=details or "—", inline=False)
        embed.set_footer(text=f"Обработал: {admin_name}" if admin_name else "Обработано администрацией")
        embed.set_thumbnail(url="https://i.imgur.com/4M34hi2.png")
    else:
        embed = discord.Embed(
            title="<:dnd_badge:1499472489112273077> Заявка отклонена",
            description=f"<@{author_id}>, твоя заявка была **отклонена**.",
            color=0xED4245
        )
        embed.add_field(name="📌 Причина", value=details or "Причина не указана", inline=False)
        embed.set_footer(text=f"Обработал: {admin_name}" if admin_name else "Обработано администрацией")

    try:
        await thread.send(embed=embed)
    except Exception as e:
        print(f"[notify_author_in_thread] Ошибка: {e}")


# ─── SLASH COMMAND ────────────────────────────────────────────────────────────

@bot.tree.command(name="выдать", description="Выдать баллы игроку вручную")
@app_commands.describe(игрок="Упомяните игрока", количество="Количество баллов")
async def give_points(interaction: discord.Interaction, игрок: discord.Member, количество: int):
    # Проверка ролей
    user_role_ids = [role.id for role in interaction.user.roles]
    if not any(role_id in ALLOWED_COMMAND_ROLES for role_id in user_role_ids):
        await interaction.response.send_message("<:dnd_badge:1499472489112273077> У вас нет прав для использования этой команды.", ephemeral=True)
        return

    current = db.get_points(игрок.id)
    new_total = current + количество
    db.set_points(игрок.id, new_total, str(игрок))

    embed = discord.Embed(title="💰 Баллы выданы", color=0x57F287)
    embed.add_field(name="Игрок", value=игрок.mention, inline=True)
    embed.add_field(name="Выдано", value=f"+{количество} 🪙", inline=True)
    embed.add_field(name="Новый баланс", value=f"{new_total} 🪙", inline=True)
    embed.set_footer(text=f"Выдал: {interaction.user}")
    await interaction.response.send_message(embed=embed)
    
    await update_leaderboard()


@bot.tree.command(name="выдатьварн", description="Выдать варн игроку")
@app_commands.describe(игрок="Упомяните игрока", причина="Причина выдачи варна", скриншот="Ссылка на скриншот (опционально)")
async def give_warn(interaction: discord.Interaction, игрок: discord.Member, причина: str, скриншот: str = None):
    # Проверка ролей
    user_role_ids = [role.id for role in interaction.user.roles]
    if not any(role_id in ALLOWED_COMMAND_ROLES for role_id in user_role_ids):
        await interaction.response.send_message("<:dnd_badge:1499472489112273077> У вас нет прав для использования этой команды.", ephemeral=True)
        return
    
    await interaction.response.defer(ephemeral=True)
    
    guild = interaction.guild
    member_role_ids = [r.id for r in игрок.roles]
    warn_count = sum(1 for rid in WARN_ROLES if rid in member_role_ids)

    if warn_count >= 3:
        await interaction.followup.send("<:dnd_badge:1499472489112273077> У игрока уже максимум варнов (3/3).", ephemeral=True)
        return

    # Выдаем следующий варн
    role_to_add = guild.get_role(WARN_ROLES[warn_count])
    if role_to_add:
        await игрок.add_roles(role_to_add)

    new_count = warn_count + 1

    # Объявление в канал варнов
    announce_ch = bot.get_channel(WARN_ANNOUNCE_CHANNEL)
    if announce_ch:
        embed_announce = discord.Embed(title="<:warning:1499473741036654613> Выдача варна", color=0xED4245)
        embed_announce.add_field(name="Варны", value=f"{new_count}/3", inline=True)
        embed_announce.add_field(name="Причина", value=причина, inline=False)
        if скриншот:
            embed_announce.set_image(url=скриншот)
        embed_announce.set_footer(text=f"Выдал: {interaction.user.name}")
        await announce_ch.send(content=игрок.mention, embed=embed_announce)

    # Обновляем лидерборд варнов
    await update_warn_leaderboard()

    await interaction.followup.send(f"<:white_black_staff_badge:1499471650532360254> Варн выдан {игрок.mention}. Варны: **{new_count}/3**", ephemeral=True)


@bot.tree.command(name="выдатьустник", description="Выдать устник игроку")
@app_commands.describe(игрок="Упомяните игрока", причина="Причина выдачи устника", скриншот="Ссылка на скриншот (опционально)")
async def give_mute(interaction: discord.Interaction, игрок: discord.Member, причина: str, скриншот: str = None):
    # Проверка ролей
    user_role_ids = [role.id for role in interaction.user.roles]
    if not any(role_id in ALLOWED_COMMAND_ROLES for role_id in user_role_ids):
        await interaction.response.send_message("<:dnd_badge:1499472489112273077> У вас нет прав для использования этой команды.", ephemeral=True)
        return
    
    await interaction.response.defer(ephemeral=True)
    
    guild = interaction.guild
    member_role_ids = [r.id for r in игрок.roles]
    mute_count = sum(1 for rid in MUTE_ROLES if rid in member_role_ids)

    if mute_count >= 2:
        await interaction.followup.send("<:dnd_badge:1499472489112273077> У игрока уже максимум устников (2/2).", ephemeral=True)
        return

    # Выдаем следующий устник
    role_to_add = guild.get_role(MUTE_ROLES[mute_count])
    if role_to_add:
        await игрок.add_roles(role_to_add)

    new_count = mute_count + 1

    # Объявление в канал варнов
    announce_ch = bot.get_channel(WARN_ANNOUNCE_CHANNEL)
    if announce_ch:
        embed_announce = discord.Embed(title="  Выдача устника", color=0xF1C40F)
        embed_announce.add_field(name="Устники", value=f"{new_count}/2", inline=True)
        embed_announce.add_field(name="Причина", value=причина, inline=False)
        if скриншот:
            embed_announce.set_image(url=скриншот)
        embed_announce.set_footer(text=f"Выдал: {interaction.user.name}")
        await announce_ch.send(content=игрок.mention, embed=embed_announce)

    await interaction.followup.send(f"<:white_black_staff_badge:1499471650532360254> Устник выдан {игрок.mention}. Устники: **{new_count}/2**", ephemeral=True)


@bot.tree.command(name="снятьбаллы", description="Снять баллы у игрока")
@app_commands.describe(игрок="Упомяните игрока", количество="Количество баллов для снятия")
async def remove_points(interaction: discord.Interaction, игрок: discord.Member, количество: int):
    # Проверка ролей
    user_role_ids = [role.id for role in interaction.user.roles]
    if not any(role_id in ALLOWED_COMMAND_ROLES for role_id in user_role_ids):
        await interaction.response.send_message("<:dnd_badge:1499472489112273077> У вас нет прав для использования этой команды.", ephemeral=True)
        return
    
    await interaction.response.defer(ephemeral=True)
    
    current = db.get_points(игрок.id)
    new_total = max(0, current - количество)
    db.set_points(игрок.id, new_total, str(игрок))

    # Пост в канал проверки
    embed_review = discord.Embed(title="💸 Баллы сняты", color=0xE74C3C)
    embed_review.add_field(name="Игрок", value=игрок.mention, inline=True)
    embed_review.add_field(name="Снято", value=f"-{количество} 🪙", inline=True)
    embed_review.add_field(name="Новый баланс", value=f"{new_total} 🪙", inline=True)
    embed_review.set_footer(text=f"Снял: {interaction.user}")
    await bot.get_channel(REVIEW_CHANNEL).send(embed=embed_review)

    await interaction.followup.send(f"<:white_black_staff_badge:1499471650532360254> Снято **{количество} 🪙** у {игрок.mention}. Новый баланс: **{new_total} 🪙**", ephemeral=True)
    
    await update_leaderboard()


@bot.tree.command(name="выдатьповышение", description="Повысить игрока")
@app_commands.describe(игрок="Упомяните игрока")
async def give_promotion(interaction: discord.Interaction, игрок: discord.Member):
    # Проверка ролей
    user_role_ids = [role.id for role in interaction.user.roles]
    if not any(role_id in ALLOWED_COMMAND_ROLES for role_id in user_role_ids):
        await interaction.response.send_message("<:dnd_badge:1499472489112273077> У вас нет прав для использования этой команды.", ephemeral=True)
        return
    
    await interaction.response.defer(ephemeral=True)
    
    guild = interaction.guild
    member_role_ids = [r.id for r in игрок.roles]

    current_idx = -1
    for i, rid in enumerate(STAFF_ROLES):
        if rid in member_role_ids:
            current_idx = i

    if current_idx == -1:
        await interaction.followup.send("<:dnd_badge:1499472489112273077> У игрока нет штабной роли.", ephemeral=True)
        return
    if current_idx >= len(STAFF_ROLES) - 1:
        await interaction.followup.send("<:dnd_badge:1499472489112273077> У игрока максимальная роль.", ephemeral=True)
        return

    old_role = guild.get_role(STAFF_ROLES[current_idx])
    new_role = guild.get_role(STAFF_ROLES[current_idx + 1])

    if old_role:
        await игрок.remove_roles(old_role)
    if new_role:
        await игрок.add_roles(new_role)

    # Объявление в канал повышений
    promo_ch = bot.get_channel(PROMOTION_CHANNEL)
    if promo_ch:
        embed = discord.Embed(title="⬆️ Повышение", color=0x9B59B6)
        embed.add_field(name="Новая роль", value=new_role.mention if new_role else STAFF_NAMES[current_idx + 1], inline=True)
        embed.set_footer(text=f"Выдал: {interaction.user.name}")
        await promo_ch.send(
            content=f"{игрок.mention} Был повышен до {new_role.mention if new_role else STAFF_NAMES[current_idx + 1]}\nПоздравим его! 🎉🎉🎉",
            embed=embed
        )

    await interaction.followup.send(f"<:white_black_staff_badge:1499471650532360254> {игрок.mention} повышен до **{new_role.mention if new_role else STAFF_NAMES[current_idx + 1]}**!", ephemeral=True)


@bot.tree.command(name="обновитьлидерборд", description="Обновить таблицу баллов вручную")
async def update_leaderboard_command(interaction: discord.Interaction):
    # Проверка ролей
    user_role_ids = [role.id for role in interaction.user.roles]
    if not any(role_id in ALLOWED_COMMAND_ROLES for role_id in user_role_ids):
        await interaction.response.send_message("<:dnd_badge:1499472489112273077> У вас нет прав для использования этой команды.", ephemeral=True)
        return
    
    await interaction.response.defer(ephemeral=True)
    await update_leaderboard()
    await interaction.followup.send("<:white_black_staff_badge:1499471650532360254> Таблица баллов обновлена!", ephemeral=True)


@bot.tree.command(name="отгулы_обновить", description="Обновить таблицу отгулов вручную")
async def update_dayoff_leaderboard_command(interaction: discord.Interaction):
    # Проверка ролей
    user_role_ids = [role.id for role in interaction.user.roles]
    if not any(role_id in ALLOWED_COMMAND_ROLES for role_id in user_role_ids):
        await interaction.response.send_message("<:dnd_badge:1499472489112273077> У вас нет прав для использования этой команды.", ephemeral=True)
        return
    
    await interaction.response.defer(ephemeral=True)
    await update_dayoff_leaderboard()
    await interaction.followup.send("<:white_black_staff_badge:1499471650532360254> Таблица отгулов обновлена!", ephemeral=True)


@bot.tree.command(name="варны_обновить", description="Обновить список варнов вручную")
async def update_warn_leaderboard_command(interaction: discord.Interaction):
    # Проверка ролей
    user_role_ids = [role.id for role in interaction.user.roles]
    if not any(role_id in ALLOWED_COMMAND_ROLES for role_id in user_role_ids):
        await interaction.response.send_message("<:dnd_badge:1499472489112273077> У вас нет прав для использования этой команды.", ephemeral=True)
        return
    
    await interaction.response.defer(ephemeral=True)
    await update_warn_leaderboard()
    await interaction.followup.send("<:white_black_staff_badge:1499471650532360254> Список варнов обновлен!", ephemeral=True)


@bot.tree.command(name="отгул_снять", description="Снять отгул у игрока досрочно")
@app_commands.describe(игрок="Упомяните игрока")
async def remove_dayoff_command(interaction: discord.Interaction, игрок: discord.Member):
    # Проверка ролей
    user_role_ids = [role.id for role in interaction.user.roles]
    if not any(role_id in ALLOWED_COMMAND_ROLES for role_id in user_role_ids):
        await interaction.response.send_message("<:dnd_badge:1499472489112273077> У вас нет прав для использования этой команды.", ephemeral=True)
        return
    
    await interaction.response.defer(ephemeral=True)
    
    guild = interaction.guild
    dayoff_role = guild.get_role(DAYOFF_ROLE)
    
    if dayoff_role and dayoff_role in игрок.roles:
        await игрок.remove_roles(dayoff_role)
    
    db.remove_dayoff(игрок.id)
    await update_dayoff_leaderboard()
    
    await interaction.followup.send(f"<:white_black_staff_badge:1499471650532360254> Отгул снят у {игрок.mention}.", ephemeral=True)


@bot.tree.command(name="отгул_выдать", description="Выдать отгул игроку")
@app_commands.describe(игрок="Упомяните игрока", дни="Количество дней отгула")
async def give_dayoff_command(interaction: discord.Interaction, игрок: discord.Member, дни: int):
    # Проверка ролей
    user_role_ids = [role.id for role in interaction.user.roles]
    if not any(role_id in ALLOWED_COMMAND_ROLES for role_id in user_role_ids):
        await interaction.response.send_message("<:dnd_badge:1499472489112273077> У вас нет прав для использования этой команды.", ephemeral=True)
        return
    
    await interaction.response.defer(ephemeral=True)
    
    if дни <= 0:
        await interaction.followup.send("<:dnd_badge:1499472489112273077> Количество дней должно быть больше 0.", ephemeral=True)
        return
    
    guild = interaction.guild
    
    # Выдаем роль отгула
    dayoff_role = guild.get_role(DAYOFF_ROLE)
    if dayoff_role:
        await игрок.add_roles(dayoff_role)
    
    # Вычисляем даты
    from datetime import datetime, timedelta
    start_date = datetime.now()
    end_date = start_date + timedelta(days=дни)
    
    start_str = start_date.strftime("%d.%m.%Y")
    end_str = end_date.strftime("%d.%m.%Y")
    
    # Сохраняем в БД
    db.set_dayoff(игрок.id, start_str, end_str, дни)
    
    # Обновляем лидерборд отгулов
    await update_dayoff_leaderboard()
    
    # Планируем снятие роли
    asyncio.create_task(schedule_dayoff_removal(игрок.id, дни))
    
    await interaction.followup.send(
        f"<:white_black_staff_badge:1499471650532360254> Отгул выдан {игрок.mention} на **{дни} дней** (до {end_str}).\n"
        f"Роль будет автоматически снята через {дни} дней.",
        ephemeral=True
    )


@bot.tree.command(name="тест_лидерборд", description="Тестовая команда для проверки лидербордов")
async def test_leaderboard(interaction: discord.Interaction):
    # Проверка ролей
    user_role_ids = [role.id for role in interaction.user.roles]
    if not any(role_id in ALLOWED_COMMAND_ROLES for role_id in user_role_ids):
        await interaction.response.send_message("<:dnd_badge:1499472489112273077> У вас нет прав для использования этой команды.", ephemeral=True)
        return
    
    await interaction.response.defer(ephemeral=True)
    
    try:
        # Проверяем канал
        channel = bot.get_channel(LEADERBOARD_CHANNEL)
        if not channel:
            await interaction.followup.send(f"<:dnd_badge:1499472489112273077> Канал {LEADERBOARD_CHANNEL} не найден!", ephemeral=True)
            return
        
        await interaction.followup.send(f"<:white_black_staff_badge:1499471650532360254> Канал найден: {channel.name}\nОбновляю лидерборды...", ephemeral=True)
        
        await update_leaderboard()
        await update_dayoff_leaderboard()
        
        await interaction.followup.send("<:white_black_staff_badge:1499471650532360254> Лидерборды обновлены! Проверьте консоль для отладочной информации.", ephemeral=True)
    except Exception as e:
        await interaction.followup.send(f"<:dnd_badge:1499472489112273077> Ошибка: {e}", ephemeral=True)
        import traceback
        traceback.print_exc()


@bot.tree.command(name="создать_лидерборд", description="Принудительно создать лидерборд с тестовыми данными")
async def force_create_leaderboard(interaction: discord.Interaction):
    # Проверка ролей
    user_role_ids = [role.id for role in interaction.user.roles]
    if not any(role_id in ALLOWED_COMMAND_ROLES for role_id in user_role_ids):
        await interaction.response.send_message("<:dnd_badge:1499472489112273077> У вас нет прав для использования этой команды.", ephemeral=True)
        return
    
    await interaction.response.defer(ephemeral=True)
    
    try:
        channel = bot.get_channel(LEADERBOARD_CHANNEL)
        if not channel:
            await interaction.followup.send(f"<:dnd_badge:1499472489112273077> Канал {LEADERBOARD_CHANNEL} не найден!", ephemeral=True)
            return
        
        # Создаем тестовый embed
        embed = discord.Embed(
            title="🏆 Таблица баллов",
            description="Список всех игроков с баллами, сгруппированных по ролям",
            color=0xF1C40F
        )
        
        embed.add_field(
            name="Пусто",
            value="Пока нет игроков с баллами",
            inline=False
        )
        
        embed.set_footer(text="Обновляется автоматически")
        
        # Отправляем сообщение
        msg = await channel.send(embed=embed)
        
        await interaction.followup.send(f"<:white_black_staff_badge:1499471650532360254> Лидерборд создан в канале {channel.mention}!\nID сообщения: {msg.id}", ephemeral=True)
        
    except Exception as e:
        await interaction.followup.send(f"<:dnd_badge:1499472489112273077> Ошибка: {e}", ephemeral=True)
        import traceback
        traceback.print_exc()


# ─── VIEWS ────────────────────────────────────────────────────────────────────

class ReviewView(discord.ui.View):
    def __init__(self, author_id: int, source_thread_id: int | None = None):
        super().__init__(timeout=None)
        self.author_id = author_id
        self.source_thread_id = source_thread_id

    @discord.ui.button(label="<:white_black_staff_badge:1499471650532360254> Одобрить", style=discord.ButtonStyle.success)
    async def approve(self, interaction: discord.Interaction, button: discord.ui.Button):
        view = SelectTypeView(
            author_id=self.author_id,
            review_message=interaction.message,
            source_thread_id=self.source_thread_id
        )
        await interaction.response.send_message("Выберите тип:", view=view, ephemeral=True)

    @discord.ui.button(label="<:dnd_badge:1499472489112273077> Отклонить", style=discord.ButtonStyle.danger)
    async def reject(self, interaction: discord.Interaction, button: discord.ui.Button):
        modal = RejectModal(
            author_id=self.author_id,
            review_message=interaction.message,
            source_thread_id=self.source_thread_id
        )
        await interaction.response.send_modal(modal)


class RejectModal(discord.ui.Modal, title="Причина отклонения"):
    reason = discord.ui.TextInput(label="Причина", style=discord.TextStyle.paragraph)

    def __init__(self, author_id: int, review_message: discord.Message, source_thread_id: int | None = None):
        super().__init__()
        self.author_id = author_id
        self.review_message = review_message
        self.source_thread_id = source_thread_id

    async def on_submit(self, interaction: discord.Interaction):
        # <:white_black_staff_badge:1499471650532360254> defer первым — до любых тяжёлых операций
        await interaction.response.defer(ephemeral=True)

        guild = interaction.guild
        member = guild.get_member(self.author_id)

        embed = discord.Embed(title="<:dnd_badge:1499472489112273077> Заявка отклонена", color=0xED4245)
        embed.add_field(name="Игрок", value=member.mention if member else f"<@{self.author_id}>", inline=True)
        embed.add_field(name="Причина", value=str(self.reason), inline=False)
        embed.set_footer(text=f"Отклонил: {interaction.user}")

        await post_to_forum(guild, embed, f"Отклонено — {member or self.author_id}")
        await disable_buttons(self.review_message)

        await notify_author_in_thread(
            self.source_thread_id,
            self.author_id,
            approved=False,
            details=str(self.reason),
            admin_name=str(interaction.user)
        )

        await interaction.followup.send("<:white_black_staff_badge:1499471650532360254> Заявка отклонена.", ephemeral=True)


class SelectTypeView(discord.ui.View):
    def __init__(self, author_id: int, review_message: discord.Message, source_thread_id: int | None = None):
        super().__init__(timeout=120)
        self.author_id = author_id
        self.review_message = review_message
        self.source_thread_id = source_thread_id

    @discord.ui.button(label="📥 Зачисление", style=discord.ButtonStyle.primary)
    async def accrual(self, interaction: discord.Interaction, button: discord.ui.Button):
        modal = AccrualModal(
            author_id=self.author_id,
            review_message=self.review_message,
            source_thread_id=self.source_thread_id
        )
        await interaction.response.send_modal(modal)

    @discord.ui.button(label="🛒 Покупка", style=discord.ButtonStyle.secondary)
    async def purchase(self, interaction: discord.Interaction, button: discord.ui.Button):
        view = ShopSelectView(
            author_id=self.author_id,
            review_message=self.review_message,
            source_thread_id=self.source_thread_id
        )
        await interaction.response.send_message("Выберите товар:", view=view, ephemeral=True)


class AccrualModal(discord.ui.Modal, title="Зачисление баллов"):
    punishments = discord.ui.TextInput(label="Количество наказаний", placeholder="Например: 10")

    def __init__(self, author_id: int, review_message: discord.Message, source_thread_id: int | None = None):
        super().__init__()
        self.author_id = author_id
        self.review_message = review_message
        self.source_thread_id = source_thread_id

    async def on_submit(self, interaction: discord.Interaction):
        # <:white_black_staff_badge:1499471650532360254> defer первым
        await interaction.response.defer(ephemeral=True)

        try:
            count = int(str(self.punishments))
        except ValueError:
            await interaction.followup.send("<:dnd_badge:1499472489112273077> Введите число.", ephemeral=True)
            return

        points = round(count * 1.5)
        guild = interaction.guild
        member = guild.get_member(self.author_id)

        current = db.get_points(self.author_id)
        new_total = current + points
        db.set_points(self.author_id, new_total, str(member) if member else "")

        embed_forum = discord.Embed(title="🪙 Зачисление Fcoin", color=0xF1C40F)
        embed_forum.add_field(name="Зачислено", value=f"{points} 🪙 пользователю {member.mention if member else f'<@{self.author_id}>'}", inline=False)
        embed_forum.add_field(name="💰 Новый баланс", value=f"{new_total} 🪙", inline=False)
        embed_forum.set_footer(text=f"Администратор: {interaction.user.name}")
        await post_to_forum(guild, embed_forum, f"Зачисление — {member or self.author_id}")

        embed_review = discord.Embed(title="<:white_black_staff_badge:1499471650532360254> Баллы начислены", color=0x57F287)
        embed_review.add_field(name="Игрок", value=member.mention if member else f"<@{self.author_id}>", inline=True)
        embed_review.add_field(name="Наказаний", value=str(count), inline=True)
        embed_review.add_field(name="Начислено", value=f"+{points} 🪙", inline=True)
        embed_review.add_field(name="Новый баланс", value=f"{new_total} 🪙", inline=True)
        embed_review.set_footer(text=f"Обработал: {interaction.user}")
        await bot.get_channel(REVIEW_CHANNEL).send(embed=embed_review)

        await disable_buttons(self.review_message)

        await notify_author_in_thread(
            self.source_thread_id,
            self.author_id,
            approved=True,
            details=f"Начислено **+{points} 🪙**\nНовый баланс: **{new_total} 🪙**",
            admin_name=str(interaction.user)
        )

        await interaction.followup.send("<:white_black_staff_badge:1499471650532360254> Баллы начислены!", ephemeral=True)
        
        await update_leaderboard()


# ─── SHOP ─────────────────────────────────────────────────────────────────────

SHOP_ITEMS = [
    discord.SelectOption(label="🚫 Снятие варна", value="warn_remove"),
    discord.SelectOption(label="🔇 Снятие устника", value="mute_remove"),
    discord.SelectOption(label="💎 Донат Helper на твинк", value="donate_helper"),
    discord.SelectOption(label="🎁 Кит", value="kit"),
    discord.SelectOption(label="📦 Кейс с Рилликами", value="case_relic"),
    discord.SelectOption(label="✨ Рилики", value="relics"),
    discord.SelectOption(label="⬆️ Повышение без нормы", value="promote"),
    discord.SelectOption(label="💸 Бонус к зарплате", value="bonus_salary"),
    discord.SelectOption(label="⭐ Бонус к баллам", value="bonus_points"),
]


class ShopSelectView(discord.ui.View):
    def __init__(self, author_id: int, review_message: discord.Message, source_thread_id: int | None = None):
        super().__init__(timeout=120)
        self.author_id = author_id
        self.review_message = review_message
        self.source_thread_id = source_thread_id

        select = discord.ui.Select(placeholder="Выберите товар...", options=SHOP_ITEMS)
        select.callback = self.select_callback
        self.add_item(select)

    async def select_callback(self, interaction: discord.Interaction):
        value = interaction.data["values"][0]
        guild = interaction.guild
        member = guild.get_member(self.author_id)

        if member is None:
            await interaction.response.send_message(
                "<:dnd_badge:1499472489112273077> Не удалось найти игрока на сервере.", ephemeral=True
            )
            return

        # Модалки — send_modal должен быть первым ответом, defer несовместим
        if value == "case_relic":
            modal = QuantityModal(
                "📦 Кейс с Рилликами", "Количество кейсов",
                self.author_id, self.review_message,
                item_type="case_relic", source_thread_id=self.source_thread_id
            )
            await interaction.response.send_modal(modal)
            return

        if value == "relics":
            modal = QuantityModal(
                "✨ Рилики", "Количество риликов (20 шт = 1 балл)",
                self.author_id, self.review_message,
                item_type="relics", source_thread_id=self.source_thread_id
            )
            await interaction.response.send_modal(modal)
            return

        # <:white_black_staff_badge:1499471650532360254> Для всех остальных — defer первым
        await interaction.response.defer(ephemeral=True)

        try:
            if value == "warn_remove":
                await process_warn_remove(interaction, member, self.review_message, self.source_thread_id)
            elif value == "mute_remove":
                await process_mute_remove(interaction, member, self.review_message, self.source_thread_id)
            elif value == "donate_helper":
                await process_simple(interaction, member, 80, "💎 Донат Helper на твинк", "Для выдачи доната обратитесь к администрации.", self.review_message, self.source_thread_id)
            elif value == "kit":
                await process_simple(interaction, member, 65, "🎁 Кит", "Для выдачи кита обратитесь к администрации.", self.review_message, self.source_thread_id)
            elif value == "promote":
                await process_promotion(interaction, member, self.review_message, self.source_thread_id)
            elif value == "bonus_salary":
                await process_bonus(interaction, member, BONUS_SALARY_ROLE, "💸 Бонус к зарплате", 200, self.review_message, self.source_thread_id)
            elif value == "bonus_points":
                await process_bonus(interaction, member, BONUS_POINTS_ROLE, "⭐ Бонус к баллам", 200, self.review_message, self.source_thread_id)
        except Exception as e:
            print(f"[select_callback] Ошибка при обработке '{value}': {e}")
            try:
                await interaction.followup.send(f"<:dnd_badge:1499472489112273077> Произошла ошибка: `{e}`", ephemeral=True)
            except Exception:
                pass


class QuantityModal(discord.ui.Modal):
    def __init__(self, title: str, label: str, author_id: int, review_message: discord.Message, item_type: str, source_thread_id: int | None = None):
        super().__init__(title=title)
        self.author_id = author_id
        self.review_message = review_message
        self.item_type = item_type
        self.source_thread_id = source_thread_id
        self.qty_input = discord.ui.TextInput(label=label, placeholder="Введите число")
        self.add_item(self.qty_input)

    async def on_submit(self, interaction: discord.Interaction):
        # <:white_black_staff_badge:1499471650532360254> defer первым
        await interaction.response.defer(ephemeral=True)

        try:
            qty = int(str(self.qty_input))
        except ValueError:
            await interaction.followup.send("<:dnd_badge:1499472489112273077> Введите число.", ephemeral=True)
            return

        guild = interaction.guild
        member = guild.get_member(self.author_id)

        if member is None:
            await interaction.followup.send("<:dnd_badge:1499472489112273077> Не удалось найти игрока на сервере.", ephemeral=True)
            return

        if self.item_type == "case_relic":
            cost = qty * 20
            item_name = f"📦 Кейс с Рилликами x{qty}"
            description = f"{qty} кейс(ов)"
        else:
            cost = max(1, qty // 20)
            item_name = f"✨ Рилики x{qty}"
            description = f"{qty} риликов"

        try:
            success = await deduct_and_notify(
                interaction, member, cost, item_name, description,
                self.review_message, source_thread_id=self.source_thread_id
            )
            if success:
                await interaction.followup.send(f"<:white_black_staff_badge:1499471650532360254> **{item_name}** — списано {cost} 🪙", ephemeral=True)
        except Exception as e:
            print(f"[QuantityModal] Ошибка: {e}")
            await interaction.followup.send(f"<:dnd_badge:1499472489112273077> Ошибка: `{e}`", ephemeral=True)


# ─── HANDLERS ─────────────────────────────────────────────────────────────────

async def deduct_and_notify(interaction, member, cost, item_name, description, review_message, extra_fields=None, source_thread_id=None):
    current = db.get_points(member.id)
    if cost > 0 and current < cost:
        await interaction.followup.send(f"<:dnd_badge:1499472489112273077> Недостаточно баллов. Нужно: {cost}, есть: {current}", ephemeral=True)
        return False

    new_total = current - cost
    db.set_points(member.id, new_total, str(member))

    guild = interaction.guild

    embed_forum = discord.Embed(title=f"🛒 Покупка: {item_name}", color=0xE67E22)
    embed_forum.add_field(name="Игрок", value=member.mention, inline=True)
    embed_forum.add_field(name="Списано", value=f"-{cost} 🪙", inline=True)
    embed_forum.add_field(name="Новый баланс", value=f"{new_total} 🪙", inline=True)
    if description:
        embed_forum.add_field(name="Информация", value=description, inline=False)
    if extra_fields:
        for name, value in extra_fields:
            embed_forum.add_field(name=name, value=value, inline=True)
    embed_forum.set_footer(text=f"Администратор: {interaction.user.name}")
    await post_to_forum(guild, embed_forum, f"Покупка {item_name} — {member}")

    embed_review = discord.Embed(title=f"<:white_black_staff_badge:1499471650532360254> Покупка: {item_name}", color=0x57F287)
    embed_review.add_field(name="Игрок", value=member.mention, inline=True)
    embed_review.add_field(name="Списано", value=f"-{cost} 🪙", inline=True)
    embed_review.add_field(name="Новый баланс", value=f"{new_total} 🪙", inline=True)
    embed_review.set_footer(text=f"Обработал: {interaction.user}")
    await bot.get_channel(REVIEW_CHANNEL).send(embed=embed_review)

    await disable_buttons(review_message)

    details_parts = [f"**{item_name}**"]
    if description:
        details_parts.append(description)
    if extra_fields:
        for name, value in extra_fields:
            details_parts.append(f"{name}: {value}")
    details_parts.append(f"Списано: **-{cost} 🪙** | Баланс: **{new_total} 🪙**")

    await notify_author_in_thread(
        source_thread_id,
        member.id,
        approved=True,
        details="\n".join(details_parts),
        admin_name=str(interaction.user)
    )

    await update_leaderboard()

    return True


async def process_simple(interaction, member, cost, item_name, description, review_message, source_thread_id=None):
    success = await deduct_and_notify(interaction, member, cost, item_name, description, review_message, source_thread_id=source_thread_id)
    if success:
        await interaction.followup.send(f"<:white_black_staff_badge:1499471650532360254> **{item_name}** обработана.", ephemeral=True)


async def process_warn_remove(interaction, member, review_message, source_thread_id=None):
    guild = interaction.guild
    member_role_ids = [r.id for r in member.roles]
    warn_count = sum(1 for rid in WARN_ROLES if rid in member_role_ids)

    if warn_count == 0:
        await interaction.followup.send("<:dnd_badge:1499472489112273077> У игрока нет варнов.", ephemeral=True)
        return

    role_to_remove = guild.get_role(WARN_ROLES[warn_count - 1])
    if role_to_remove:
        await member.remove_roles(role_to_remove)

    new_count = warn_count - 1
    success = await deduct_and_notify(
        interaction, member, 70, "🚫 Снятие варна", "",
        review_message,
        extra_fields=[("Варны после покупки", f"{new_count}/3")],
        source_thread_id=source_thread_id
    )
    if success:
        announce_ch = bot.get_channel(WARN_ANNOUNCE_CHANNEL)
        if announce_ch:
            embed = discord.Embed(title="🚫 Покупка снятия варна", color=0xED4245)
            embed.add_field(name="Варны", value=f"{new_count}/3", inline=True)
            await announce_ch.send(content=member.mention, embed=embed)
        
        # Обновляем лидерборд варнов
        await update_warn_leaderboard()
        
        await interaction.followup.send("<:white_black_staff_badge:1499471650532360254> Варн снят.", ephemeral=True)


async def process_mute_remove(interaction, member, review_message, source_thread_id=None):
    guild = interaction.guild
    member_role_ids = [r.id for r in member.roles]
    mute_count = sum(1 for rid in MUTE_ROLES if rid in member_role_ids)

    if mute_count == 0:
        await interaction.followup.send("<:dnd_badge:1499472489112273077> У игрока нет устников.", ephemeral=True)
        return

    role_to_remove = guild.get_role(MUTE_ROLES[mute_count - 1])
    if role_to_remove:
        await member.remove_roles(role_to_remove)

    new_count = mute_count - 1
    success = await deduct_and_notify(
        interaction, member, 40, "🔇 Снятие устника", "",
        review_message,
        extra_fields=[("Устники после покупки", f"{new_count}/2")],
        source_thread_id=source_thread_id
    )
    if success:
        announce_ch = bot.get_channel(WARN_ANNOUNCE_CHANNEL)
        if announce_ch:
            embed = discord.Embed(title="🔇 Покупка снятия устника", color=0xF1C40F)
            embed.add_field(name="Устники", value=f"{new_count}/2", inline=True)
            await announce_ch.send(content=member.mention, embed=embed)
        await interaction.followup.send("<:white_black_staff_badge:1499471650532360254> Устник снят.", ephemeral=True)


async def process_promotion(interaction, member, review_message, source_thread_id=None):
    guild = interaction.guild
    member_role_ids = [r.id for r in member.roles]

    current_idx = -1
    for i, rid in enumerate(STAFF_ROLES):
        if rid in member_role_ids:
            current_idx = i

    if current_idx == -1:
        await interaction.followup.send("<:dnd_badge:1499472489112273077> У игрока нет штабной роли.", ephemeral=True)
        return
    if current_idx >= len(STAFF_ROLES) - 1:
        await interaction.followup.send("<:dnd_badge:1499472489112273077> У игрока максимальная роль.", ephemeral=True)
        return

    old_role = guild.get_role(STAFF_ROLES[current_idx])
    new_role = guild.get_role(STAFF_ROLES[current_idx + 1])

    if old_role:
        await member.remove_roles(old_role)
    if new_role:
        await member.add_roles(new_role)

    success = await deduct_and_notify(
        interaction, member, 0, "⬆️ Повышение без нормы", "",
        review_message,
        extra_fields=[("Новая роль", new_role.mention if new_role else STAFF_NAMES[current_idx + 1])],
        source_thread_id=source_thread_id
    )
    if success:
        promo_ch = bot.get_channel(PROMOTION_CHANNEL)
        if promo_ch:
            await promo_ch.send(
                f"{member.mention} Был повышен до {new_role.mention if new_role else STAFF_NAMES[current_idx + 1]}\n"
                f"Поздравим его! 🎉🎉🎉"
            )
        await interaction.followup.send("<:white_black_staff_badge:1499471650532360254> Повышение выполнено.", ephemeral=True)


async def process_bonus(interaction, member, role_id, item_name, cost, review_message, source_thread_id=None):
    guild = interaction.guild
    role = guild.get_role(role_id)
    if role:
        await member.add_roles(role)
    success = await deduct_and_notify(interaction, member, cost, item_name, "", review_message, source_thread_id=source_thread_id)
    if success:
        await interaction.followup.send(f"<:white_black_staff_badge:1499471650532360254> **{item_name}** выдан.", ephemeral=True)


# ─── HELPERS ──────────────────────────────────────────────────────────────────

async def post_to_forum(guild, embed, thread_name):
    forum = discord.utils.get(guild.forums, name="заявки")
    fallback = discord.utils.get(guild.text_channels, name="заявки")
    if forum:
        await forum.create_thread(name=thread_name[:100], embed=embed)
    elif fallback:
        await fallback.send(embed=embed)
    else:
        await bot.get_channel(REVIEW_CHANNEL).send(embed=embed)


async def disable_buttons(message: discord.Message):
    try:
        await message.edit(view=discord.ui.View())
        print(f"[disable_buttons] Кнопки отключены для сообщения {message.id}")
    except Exception as e:
        print(f"[disable_buttons] Ошибка отключения кнопок: {e}")
        import traceback
        traceback.print_exc()


# ─── SALARY APPLICATION VIEWS ─────────────────────────────────────────────────

class SalaryReviewView(discord.ui.View):
    def __init__(self, author_id: int, source_thread_id: int):
        super().__init__(timeout=None)
        self.author_id = author_id
        self.source_thread_id = source_thread_id

    @discord.ui.button(label="<:white_black_staff_badge:1499471650532360254> Одобрить", style=discord.ButtonStyle.success)
    async def approve(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)

        guild = interaction.guild
        member = guild.get_member(self.author_id)

        # Уведомление в треде
        await notify_in_thread(
            SALARY_FORUM,
            self.source_thread_id,
            self.author_id,
            approved=True,
            title="<:white_black_staff_badge:1499471650532360254> Заявка на зарплату одобрена",
            details="Для выдачи зарплаты обратитесь к администрации.",
            admin_name=str(interaction.user)
        )

        await disable_buttons(interaction.message)
        await interaction.followup.send("<:white_black_staff_badge:1499471650532360254> Заявка на зарплату одобрена.", ephemeral=True)

    @discord.ui.button(label="<:dnd_badge:1499472489112273077> Отклонить", style=discord.ButtonStyle.danger)
    async def reject(self, interaction: discord.Interaction, button: discord.ui.Button):
        modal = SalaryRejectModal(
            author_id=self.author_id,
            review_message=interaction.message,
            source_thread_id=self.source_thread_id
        )
        await interaction.response.send_modal(modal)


class SalaryRejectModal(discord.ui.Modal, title="Причина отклонения"):
    reason = discord.ui.TextInput(label="Причина", style=discord.TextStyle.paragraph)

    def __init__(self, author_id: int, review_message: discord.Message, source_thread_id: int):
        super().__init__()
        self.author_id = author_id
        self.review_message = review_message
        self.source_thread_id = source_thread_id

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)

        await notify_in_thread(
            SALARY_FORUM,
            self.source_thread_id,
            self.author_id,
            approved=False,
            title="<:dnd_badge:1499472489112273077> Заявка на зарплату отклонена",
            details=str(self.reason),
            admin_name=str(interaction.user)
        )

        await disable_buttons(self.review_message)
        await interaction.followup.send("<:white_black_staff_badge:1499471650532360254> Заявка отклонена.", ephemeral=True)


# ─── DAY OFF APPLICATION VIEWS ────────────────────────────────────────────────

class DayoffReviewView(discord.ui.View):
    def __init__(self, author_id: int, source_thread_id: int):
        super().__init__(timeout=None)
        self.author_id = author_id
        self.source_thread_id = source_thread_id

    @discord.ui.button(label="<:white_black_staff_badge:1499471650532360254> Одобрить", style=discord.ButtonStyle.success)
    async def approve(self, interaction: discord.Interaction, button: discord.ui.Button):
        modal = DayoffApproveModal(
            author_id=self.author_id,
            review_message=interaction.message,
            source_thread_id=self.source_thread_id
        )
        await interaction.response.send_modal(modal)

    @discord.ui.button(label="<:dnd_badge:1499472489112273077> Отклонить", style=discord.ButtonStyle.danger)
    async def reject(self, interaction: discord.Interaction, button: discord.ui.Button):
        modal = DayoffRejectModal(
            author_id=self.author_id,
            review_message=interaction.message,
            source_thread_id=self.source_thread_id
        )
        await interaction.response.send_modal(modal)


class DayoffApproveModal(discord.ui.Modal, title="Одобрение отгула"):
    days = discord.ui.TextInput(
        label="Количество дней",
        style=discord.TextStyle.short,
        placeholder="Например: 7"
    )

    def __init__(self, author_id: int, review_message: discord.Message, source_thread_id: int):
        super().__init__()
        self.author_id = author_id
        self.review_message = review_message
        self.source_thread_id = source_thread_id

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        
        print(f"[DayoffApproveModal] Начало обработки для user_id={self.author_id}")

        try:
            days_count = int(str(self.days))
        except ValueError:
            await interaction.followup.send("<:dnd_badge:1499472489112273077> Введите число.", ephemeral=True)
            return

        if days_count <= 0:
            await interaction.followup.send("<:dnd_badge:1499472489112273077> Количество дней должно быть больше 0.", ephemeral=True)
            return

        guild = interaction.guild
        member = guild.get_member(self.author_id)

        if not member:
            await interaction.followup.send("<:dnd_badge:1499472489112273077> Игрок не найден на сервере.", ephemeral=True)
            return

        print(f"[DayoffApproveModal] Выдаем роль отгула для {member}")

        # Выдаем роль отгула
        dayoff_role = guild.get_role(DAYOFF_ROLE)
        if dayoff_role:
            await member.add_roles(dayoff_role)
            print(f"[DayoffApproveModal] Роль выдана")

        # Вычисляем даты
        from datetime import datetime, timedelta
        start_date = datetime.now()
        end_date = start_date + timedelta(days=days_count)
        
        start_str = start_date.strftime("%d.%m.%Y")
        end_str = end_date.strftime("%d.%m.%Y")

        # Сохраняем в БД
        db.set_dayoff(self.author_id, start_str, end_str, days_count)
        print(f"[DayoffApproveModal] Сохранено в БД")

        # Отключаем кнопки ПЕРЕД отправкой уведомлений
        print(f"[DayoffApproveModal] Отключаем кнопки для сообщения {self.review_message.id}")
        await disable_buttons(self.review_message)

        # Уведомление в треде
        print(f"[DayoffApproveModal] Отправляем уведомление в тред")
        await notify_in_thread(
            DAYOFF_FORUM,
            self.source_thread_id,
            self.author_id,
            approved=True,
            title="<:white_black_staff_badge:1499471650532360254> Заявка на отгул одобрена",
            details=f"Отгул выдан на **{days_count} дней**\nС {start_str} по {end_str}",
            admin_name=str(interaction.user)
        )
        
        # Обновляем лидерборд отгулов
        print(f"[DayoffApproveModal] Обновляем лидерборд")
        await update_dayoff_leaderboard()

        # Планируем снятие роли
        print(f"[DayoffApproveModal] Планируем снятие роли через {days_count} дней")
        asyncio.create_task(schedule_dayoff_removal(self.author_id, days_count))

        await interaction.followup.send(f"<:white_black_staff_badge:1499471650532360254> Отгул одобрен на **{days_count} дней** (до {end_str}). Роль выдана.", ephemeral=True)
        print(f"[DayoffApproveModal] Завершено успешно")


class DayoffRejectModal(discord.ui.Modal, title="Причина отклонения"):
    reason = discord.ui.TextInput(label="Причина", style=discord.TextStyle.paragraph)

    def __init__(self, author_id: int, review_message: discord.Message, source_thread_id: int):
        super().__init__()
        self.author_id = author_id
        self.review_message = review_message
        self.source_thread_id = source_thread_id

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)

        await notify_in_thread(
            DAYOFF_FORUM,
            self.source_thread_id,
            self.author_id,
            approved=False,
            title="<:dnd_badge:1499472489112273077> Заявка на отгул отклонена",
            details=str(self.reason),
            admin_name=str(interaction.user)
        )

        await disable_buttons(self.review_message)
        await interaction.followup.send("<:white_black_staff_badge:1499471650532360254> Заявка отклонена.", ephemeral=True)


# ─── PROMOTION APPLICATION VIEWS ──────────────────────────────────────────────

class PromotionAppReviewView(discord.ui.View):
    def __init__(self, author_id: int, source_thread_id: int):
        super().__init__(timeout=None)
        self.author_id = author_id
        self.source_thread_id = source_thread_id

    @discord.ui.button(label="<:white_black_staff_badge:1499471650532360254> Одобрить", style=discord.ButtonStyle.success)
    async def approve(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)

        guild = interaction.guild
        member = guild.get_member(self.author_id)

        if not member:
            await interaction.followup.send("<:dnd_badge:1499472489112273077> Игрок не найден на сервере.", ephemeral=True)
            return

        member_role_ids = [r.id for r in member.roles]
        current_idx = -1
        for i, rid in enumerate(STAFF_ROLES):
            if rid in member_role_ids:
                current_idx = i

        if current_idx == -1:
            await interaction.followup.send("<:dnd_badge:1499472489112273077> У игрока нет штабной роли.", ephemeral=True)
            return
        if current_idx >= len(STAFF_ROLES) - 1:
            await interaction.followup.send("<:dnd_badge:1499472489112273077> У игрока максимальная роль.", ephemeral=True)
            return

        old_role = guild.get_role(STAFF_ROLES[current_idx])
        new_role = guild.get_role(STAFF_ROLES[current_idx + 1])

        if old_role:
            await member.remove_roles(old_role)
        if new_role:
            await member.add_roles(new_role)

        # Объявление в канал повышений (БЕЗ информации кто повысил)
        promo_ch = bot.get_channel(PROMOTION_CHANNEL)
        if promo_ch:
            await promo_ch.send(
                f"{member.mention} Был повышен до {new_role.mention if new_role else STAFF_NAMES[current_idx + 1]}\n"
                f"Поздравим его! 🎉🎉🎉"
            )

        # Уведомление в треде
        await notify_in_thread(
            PROMO_APP_FORUM,
            self.source_thread_id,
            self.author_id,
            approved=True,
            title="<:white_black_staff_badge:1499471650532360254> Заявка на повышение одобрена",
            details=f"Вы повышены до {new_role.mention if new_role else STAFF_NAMES[current_idx + 1]}!",
            admin_name=str(interaction.user)
        )

        await disable_buttons(interaction.message)
        await interaction.followup.send(f"<:white_black_staff_badge:1499471650532360254> {member.mention} повышен до **{new_role.mention if new_role else STAFF_NAMES[current_idx + 1]}**!", ephemeral=True)

    @discord.ui.button(label="<:dnd_badge:1499472489112273077> Отклонить", style=discord.ButtonStyle.danger)
    async def reject(self, interaction: discord.Interaction, button: discord.ui.Button):
        modal = PromotionAppRejectModal(
            author_id=self.author_id,
            review_message=interaction.message,
            source_thread_id=self.source_thread_id
        )
        await interaction.response.send_modal(modal)


class PromotionAppRejectModal(discord.ui.Modal, title="Причина отклонения"):
    reason = discord.ui.TextInput(label="Причина", style=discord.TextStyle.paragraph)

    def __init__(self, author_id: int, review_message: discord.Message, source_thread_id: int):
        super().__init__()
        self.author_id = author_id
        self.review_message = review_message
        self.source_thread_id = source_thread_id

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)

        await notify_in_thread(
            PROMO_APP_FORUM,
            self.source_thread_id,
            self.author_id,
            approved=False,
            title="<:dnd_badge:1499472489112273077> Заявка на повышение отклонена",
            details=str(self.reason),
            admin_name=str(interaction.user)
        )

        await disable_buttons(self.review_message)
        await interaction.followup.send("<:white_black_staff_badge:1499471650532360254> Заявка отклонена.", ephemeral=True)


# ─── HELPER FOR THREAD NOTIFICATIONS ──────────────────────────────────────────

async def notify_in_thread(forum_id: int, thread_id: int, author_id: int, approved: bool, title: str, details: str, admin_name: str):
    """Отправляет уведомление в тред форума"""
    if not thread_id:
        return

    channel = bot.get_channel(forum_id)
    if not channel:
        return

    thread = None
    if isinstance(channel, discord.ForumChannel):
        try:
            thread = channel.get_thread(thread_id)
            if not thread:
                thread = await bot.fetch_channel(thread_id)
        except Exception:
            return
    else:
        return

    if approved:
        embed = discord.Embed(
            title=title,
            description=f"<@{author_id}>, твоя заявка была **одобрена**. 🎉",
            color=0x57F287
        )
        embed.add_field(name="📌 Детали", value=details or "—", inline=False)
        embed.set_footer(text=f"Обработал: {admin_name}")
    else:
        embed = discord.Embed(
            title=title,
            description=f"<@{author_id}>, твоя заявка была **отклонена**.",
            color=0xED4245
        )
        embed.add_field(name="📌 Причина", value=details or "Причина не указана", inline=False)
        embed.set_footer(text=f"Обработал: {admin_name}")

    try:
        await thread.send(embed=embed)
    except Exception as e:
        print(f"[notify_in_thread] Ошибка: {e}")


# ─── LEADERBOARD ──────────────────────────────────────────────────────────────

async def update_leaderboard():
    """Обновляет сообщение с таблицей баллов всех игроков"""
    try:
        channel = bot.get_channel(LEADERBOARD_CHANNEL)
        if not channel:
            print(f"[update_leaderboard] Канал {LEADERBOARD_CHANNEL} не найден")
            return

        guild = channel.guild
        all_points = db.get_all_points()
        
        print(f"[update_leaderboard] Найдено {len(all_points)} записей в БД")

        # Группируем игроков по ролям
        role_groups = {}
        for user_id, points in all_points.items():
            member = guild.get_member(user_id)
            if not member:
                continue

            # Определяем роль игрока (берем самую высокую штабную роль)
            member_role_ids = [r.id for r in member.roles]
            role_name = "Без роли"
            
            for i, rid in enumerate(STAFF_ROLES):
                if rid in member_role_ids:
                    role_name = STAFF_NAMES[i]
                    break

            if role_name not in role_groups:
                role_groups[role_name] = []
            
            role_groups[role_name].append((member, points))

        # Сортируем каждую группу по баллам
        for role_name in role_groups:
            role_groups[role_name].sort(key=lambda x: x[1], reverse=True)

        # Формируем embed
        embed = discord.Embed(
            title="🏆 Таблица баллов",
            description="Список всех игроков с баллами, сгруппированных по ролям",
            color=0xF1C40F
        )

        # Порядок ролей (от высшей к низшей)
        role_order = STAFF_NAMES[::-1]  # Разворачиваем, чтобы высшие были сверху

        has_players = False
        for role_name in role_order:
            if role_name not in role_groups:
                continue

            players_list = []
            for member, points in role_groups[role_name]:
                players_list.append(f"{member.mention} — **{points}** 🪙")

            if players_list:
                has_players = True
                embed.add_field(
                    name=f"**{role_name}**",
                    value="\n".join(players_list),
                    inline=False
                )

        # Добавляем игроков без роли в конце
        if "Без роли" in role_groups:
            players_list = []
            for member, points in role_groups["Без роли"]:
                players_list.append(f"{member.mention} — **{points}** 🪙")

            if players_list:
                has_players = True
                embed.add_field(
                    name="**Без роли**",
                    value="\n".join(players_list),
                    inline=False
                )

        # Если нет игроков, добавляем заглушку
        if not has_players:
            embed.add_field(
                name="Пусто",
                value="Пока нет игроков с баллами",
                inline=False
            )

        embed.set_footer(text="Обновляется автоматически")

        # Ищем существующее сообщение или создаем новое
        messages = [msg async for msg in channel.history(limit=10)]
        bot_messages = [msg for msg in messages if msg.author == bot.user and msg.embeds and msg.embeds[0].title == "🏆 Таблица баллов"]

        if bot_messages:
            # Обновляем последнее сообщение бота
            await bot_messages[0].edit(embed=embed)
            print(f"[update_leaderboard] Лидерборд обновлен")
        else:
            # Создаем новое сообщение
            await channel.send(embed=embed)
            print(f"[update_leaderboard] Лидерборд создан")
    
    except Exception as e:
        print(f"[update_leaderboard] Ошибка: {e}")
        import traceback
        traceback.print_exc()


async def update_dayoff_leaderboard():
    """Обновляет сообщение с таблицей отгулов"""
    try:
        channel = bot.get_channel(DAYOFF_LEADERBOARD_CHANNEL)
        if not channel:
            print(f"[update_dayoff_leaderboard] Канал {DAYOFF_LEADERBOARD_CHANNEL} не найден")
            return

        guild = channel.guild
        all_dayoffs = db.get_all_dayoffs()
        
        print(f"[update_dayoff_leaderboard] Найдено {len(all_dayoffs)} отгулов в БД")

        if not all_dayoffs:
            # Если нет отгулов, удаляем старое сообщение если есть
            messages = [msg async for msg in channel.history(limit=10)]
            bot_messages = [msg for msg in messages if msg.author == bot.user and msg.embeds and msg.embeds[0].title == "🏖️ Список отгулов"]
            if bot_messages:
                await bot_messages[0].delete()
                print(f"[update_dayoff_leaderboard] Сообщение удалено (нет отгулов)")
            return

        # Формируем embed
        embed = discord.Embed(
            title="🏖️ Список отгулов",
            description="Игроки, находящиеся в отгуле",
            color=0x3498DB
        )

        dayoff_list = []
        for user_id, dayoff_info in all_dayoffs.items():
            member = guild.get_member(user_id)
            if not member:
                continue

            start_date = dayoff_info.get("start_date", "?")
            end_date = dayoff_info.get("end_date", "?")
            
            dayoff_list.append(f"{member.mention}\n📅 С **{start_date}** по **{end_date}**")

        if dayoff_list:
            embed.add_field(
                name="Игроки в отгуле",
                value="\n\n".join(dayoff_list),
                inline=False
            )
        else:
            embed.add_field(
                name="Пусто",
                value="Нет игроков в отгуле",
                inline=False
            )

        embed.set_footer(text="Обновляется автоматически")

        # Ищем существующее сообщение или создаем новое
        messages = [msg async for msg in channel.history(limit=10)]
        bot_messages = [msg for msg in messages if msg.author == bot.user and msg.embeds and msg.embeds[0].title == "🏖️ Список отгулов"]

        if bot_messages:
            # Обновляем последнее сообщение бота
            await bot_messages[0].edit(embed=embed)
            print(f"[update_dayoff_leaderboard] Лидерборд отгулов обновлен")
        else:
            # Создаем новое сообщение
            await channel.send(embed=embed)
            print(f"[update_dayoff_leaderboard] Лидерборд отгулов создан")
    
    except Exception as e:
        print(f"[update_dayoff_leaderboard] Ошибка: {e}")
        import traceback
        traceback.print_exc()


async def update_warn_leaderboard():
    """Обновляет сообщение со списком варнов"""
    try:
        channel = bot.get_channel(WARN_LEADERBOARD_CHANNEL)
        if not channel:
            print(f"[update_warn_leaderboard] Канал {WARN_LEADERBOARD_CHANNEL} не найден")
            return

        guild = channel.guild
        
        # Собираем всех игроков с варнами
        warn_players = []
        for member in guild.members:
            if member.bot:
                continue
            
            member_role_ids = [r.id for r in member.roles]
            warn_count = sum(1 for rid in WARN_ROLES if rid in member_role_ids)
            
            if warn_count > 0:
                warn_players.append((member, warn_count))
        
        print(f"[update_warn_leaderboard] Найдено {len(warn_players)} игроков с варнами")

        # Формируем embed
        embed = discord.Embed(
            title="🚫 Список варнов",
            description="Игроки с активными варнами",
            color=0xED4245
        )

        if warn_players:
            # Сортируем по количеству варнов (больше варнов - выше)
            warn_players.sort(key=lambda x: x[1], reverse=True)
            
            warn_list = []
            for member, warn_count in warn_players:
                warn_emoji = "🔴" * warn_count
                warn_list.append(f"{member.mention} — {warn_emoji} **{warn_count}/3**")
            
            embed.add_field(
                name="Игроки с варнами",
                value="\n".join(warn_list),
                inline=False
            )
        else:
            embed.add_field(
                name="Пусто",
                value="Нет игроков с варнами",
                inline=False
            )

        embed.set_footer(text="Обновляется автоматически")

        # Ищем существующее сообщение или создаем новое
        messages = [msg async for msg in channel.history(limit=10)]
        bot_messages = [msg for msg in messages if msg.author == bot.user and msg.embeds and msg.embeds[0].title == "🚫 Список варнов"]

        if bot_messages:
            # Обновляем последнее сообщение бота
            await bot_messages[0].edit(embed=embed)
            print(f"[update_warn_leaderboard] Лидерборд варнов обновлен")
        else:
            # Создаем новое сообщение
            await channel.send(embed=embed)
            print(f"[update_warn_leaderboard] Лидерборд варнов создан")
    
    except Exception as e:
        print(f"[update_warn_leaderboard] Ошибка: {e}")
        import traceback
        traceback.print_exc()


async def schedule_dayoff_removal(user_id: int, days: int):
    """Планирует снятие роли отгула через указанное количество дней"""
    await asyncio.sleep(days * 24 * 60 * 60)  # Конвертируем дни в секунды

    # Снимаем роль
    for guild in bot.guilds:
        member = guild.get_member(user_id)
        if member:
            dayoff_role = guild.get_role(DAYOFF_ROLE)
            if dayoff_role and dayoff_role in member.roles:
                await member.remove_roles(dayoff_role)
                print(f"[schedule_dayoff_removal] Роль отгула снята у {member}")

    # Удаляем из БД
    db.remove_dayoff(user_id)

    # Обновляем лидерборд
    await update_dayoff_leaderboard()


async def restore_dayoff_timers():
    """Восстанавливает таймеры для отгулов при перезапуске бота"""
    from datetime import datetime
    
    all_dayoffs = db.get_all_dayoffs()
    current_date = datetime.now()

    for user_id, dayoff_info in all_dayoffs.items():
        try:
            end_date_str = dayoff_info.get("end_date", "")
            end_date = datetime.strptime(end_date_str, "%d.%m.%Y")
            
            # Вычисляем оставшееся время
            time_left = (end_date - current_date).total_seconds()
            
            if time_left <= 0:
                # Отгул уже истек, снимаем роль сразу
                for guild in bot.guilds:
                    member = guild.get_member(user_id)
                    if member:
                        dayoff_role = guild.get_role(DAYOFF_ROLE)
                        if dayoff_role and dayoff_role in member.roles:
                            await member.remove_roles(dayoff_role)
                            print(f"[restore_dayoff_timers] Роль отгула снята у {member} (истек)")
                
                db.remove_dayoff(user_id)
            else:
                # Планируем снятие роли
                days_left = time_left / (24 * 60 * 60)
                asyncio.create_task(schedule_dayoff_removal(user_id, days_left))
                print(f"[restore_dayoff_timers] Восстановлен таймер для user_id={user_id}, осталось {days_left:.2f} дней")
        
        except Exception as e:
            print(f"[restore_dayoff_timers] Ошибка для user_id={user_id}: {e}")

    await update_dayoff_leaderboard()


bot.run(os.getenv("DISCORD_TOKEN"))
