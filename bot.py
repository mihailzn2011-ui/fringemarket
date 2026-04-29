import discord
from discord.ext import commands
from discord import app_commands
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
WATCH_CHANNEL = 1499110010976997508
REVIEW_CHANNEL = 1499110318117486654
WARN_ANNOUNCE_CHANNEL = 1499106932752126107
PROMOTION_CHANNEL = 1499106965173960815

# Warn role IDs
WARN_ROLES = [
    1499106669278400642,  # 1 варн
    1499106668334682193,  # 2 варн
    1499106667378376715,  # 3 варн
]

# Mute role IDs
MUTE_ROLES = [
    1499106671157444871,  # 1 устник
    1499106670180044900,  # 2 устник
]

# Staff role IDs (от низшего к высшему)
STAFF_ROLES = [
    1499106642216882376,  # хелпер
    1499106641298325554,  # ст хелпер
    1499106640182513715,  # мл модер
    1499106638764834857,  # модер
    1499106637284380693,  # модер+
    1499106634734108855,  # ст модер
    1499106633970880652,  # гл модер
]

STAFF_NAMES = ["Хелпер", "Ст. Хелпер", "Мл. Модер", "Модер", "Модер+", "Ст. Модер", "Гл. Модер"]

BONUS_SALARY_ROLE = 1499106656884232344
BONUS_POINTS_ROLE = 1499106655802097795


@bot.event
async def on_ready():
    print(f"Бот {bot.user} запущен!")
    await bot.tree.sync()


@bot.event
async def on_message(message):
    if message.channel.id == WATCH_CHANNEL and not message.author.bot:
        review_channel = bot.get_channel(REVIEW_CHANNEL)
        if review_channel:
            embed = discord.Embed(
                title="📋 Новая заявка",
                description=message.content or "*Без текста*",
                color=0x5865F2
            )
            embed.set_author(name=str(message.author), icon_url=message.author.display_avatar.url)
            embed.set_footer(text=f"ID автора: {message.author.id}")

            if message.attachments:
                embed.set_image(url=message.attachments[0].url)

            view = ReviewView(author_id=message.author.id)
            await review_channel.send(embed=embed, view=view)

    await bot.process_commands(message)


@bot.tree.command(name="выдать", description="Выдать баллы игроку вручную")
@app_commands.describe(игрок="Упомяните игрока", количество="Количество баллов")
async def give_points(interaction: discord.Interaction, игрок: discord.Member, количество: int):
    if interaction.channel_id != REVIEW_CHANNEL:
        await interaction.response.send_message("❌ Только в канале проверки.", ephemeral=True)
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


# ─── VIEWS ────────────────────────────────────────────────────────────────────

class ReviewView(discord.ui.View):
    def __init__(self, author_id: int):
        super().__init__(timeout=None)
        self.author_id = author_id

    @discord.ui.button(label="✅ Одобрить", style=discord.ButtonStyle.success)
    async def approve(self, interaction: discord.Interaction, button: discord.ui.Button):
        view = SelectTypeView(author_id=self.author_id, review_message=interaction.message)
        await interaction.response.send_message("Выберите тип:", view=view, ephemeral=True)

    @discord.ui.button(label="❌ Отклонить", style=discord.ButtonStyle.danger)
    async def reject(self, interaction: discord.Interaction, button: discord.ui.Button):
        modal = RejectModal(author_id=self.author_id, review_message=interaction.message)
        await interaction.response.send_modal(modal)


class RejectModal(discord.ui.Modal, title="Причина отклонения"):
    reason = discord.ui.TextInput(label="Причина", style=discord.TextStyle.paragraph)

    def __init__(self, author_id: int, review_message: discord.Message):
        super().__init__()
        self.author_id = author_id
        self.review_message = review_message

    async def on_submit(self, interaction: discord.Interaction):
        guild = interaction.guild
        member = guild.get_member(self.author_id)

        embed = discord.Embed(title="❌ Заявка отклонена", color=0xED4245)
        embed.add_field(name="Игрок", value=member.mention if member else f"<@{self.author_id}>", inline=True)
        embed.add_field(name="Причина", value=str(self.reason), inline=False)
        embed.set_footer(text=f"Отклонил: {interaction.user}")

        await post_to_forum(guild, embed, f"Отклонено — {member or self.author_id}")
        await disable_buttons(self.review_message)
        await interaction.response.send_message("✅ Заявка отклонена.", ephemeral=True)


class SelectTypeView(discord.ui.View):
    def __init__(self, author_id: int, review_message: discord.Message):
        super().__init__(timeout=120)
        self.author_id = author_id
        self.review_message = review_message

    @discord.ui.button(label="📥 Зачисление", style=discord.ButtonStyle.primary)
    async def accrual(self, interaction: discord.Interaction, button: discord.ui.Button):
        modal = AccrualModal(author_id=self.author_id, review_message=self.review_message)
        await interaction.response.send_modal(modal)

    @discord.ui.button(label="🛒 Покупка", style=discord.ButtonStyle.secondary)
    async def purchase(self, interaction: discord.Interaction, button: discord.ui.Button):
        view = ShopSelectView(author_id=self.author_id, review_message=self.review_message)
        await interaction.response.send_message("Выберите товар:", view=view, ephemeral=True)


class AccrualModal(discord.ui.Modal, title="Зачисление баллов"):
    punishments = discord.ui.TextInput(label="Количество наказаний", placeholder="Например: 10")

    def __init__(self, author_id: int, review_message: discord.Message):
        super().__init__()
        self.author_id = author_id
        self.review_message = review_message

    async def on_submit(self, interaction: discord.Interaction):
        try:
            count = int(str(self.punishments))
        except ValueError:
            await interaction.response.send_message("❌ Введите число.", ephemeral=True)
            return

        points = round(count * 1.5)
        guild = interaction.guild
        member = guild.get_member(self.author_id)

        current = db.get_points(self.author_id)
        new_total = current + points
        db.set_points(self.author_id, new_total, str(member) if member else "")

        # Форум
        embed_forum = discord.Embed(title="🪙 Зачисление Fcoin", color=0xF1C40F)
        embed_forum.add_field(name="Зачислено", value=f"{points} 🪙 пользователю {member.mention if member else f'<@{self.author_id}>'}", inline=False)
        embed_forum.add_field(name="💰 Новый баланс", value=f"{new_total} 🪙", inline=False)
        embed_forum.set_footer(text=f"Администратор: {interaction.user.name}")
        await post_to_forum(guild, embed_forum, f"Зачисление — {member or self.author_id}")

        # Канал проверки
        embed_review = discord.Embed(title="✅ Баллы начислены", color=0x57F287)
        embed_review.add_field(name="Игрок", value=member.mention if member else f"<@{self.author_id}>", inline=True)
        embed_review.add_field(name="Наказаний", value=str(count), inline=True)
        embed_review.add_field(name="Начислено", value=f"+{points} 🪙", inline=True)
        embed_review.add_field(name="Новый баланс", value=f"{new_total} 🪙", inline=True)
        embed_review.set_footer(text=f"Обработал: {interaction.user}")
        await bot.get_channel(REVIEW_CHANNEL).send(embed=embed_review)

        await disable_buttons(self.review_message)
        await interaction.response.send_message("✅ Баллы начислены!", ephemeral=True)


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
    def __init__(self, author_id: int, review_message: discord.Message):
        super().__init__(timeout=120)
        self.author_id = author_id
        self.review_message = review_message

        select = discord.ui.Select(placeholder="Выберите товар...", options=SHOP_ITEMS)
        select.callback = self.select_callback
        self.add_item(select)

    async def select_callback(self, interaction: discord.Interaction):
        value = interaction.data["values"][0]
        guild = interaction.guild
        member = guild.get_member(self.author_id)

        if value == "warn_remove":
            await process_warn_remove(interaction, member, self.review_message)
        elif value == "mute_remove":
            await process_mute_remove(interaction, member, self.review_message)
        elif value == "donate_helper":
            await process_simple(interaction, member, 80, "💎 Донат Helper на твинк", "Для выдачи доната обратитесь к администрации.", self.review_message)
        elif value == "kit":
            await process_simple(interaction, member, 65, "🎁 Кит", "Для выдачи кита обратитесь к администрации.", self.review_message)
        elif value == "case_relic":
            modal = QuantityModal("📦 Кейс с Рилликами", "Количество кейсов", self.author_id, self.review_message, item_type="case_relic")
            await interaction.response.send_modal(modal)
        elif value == "relics":
            modal = QuantityModal("✨ Рилики", "Количество риликов (20 шт = 1 балл)", self.author_id, self.review_message, item_type="relics")
            await interaction.response.send_modal(modal)
        elif value == "promote":
            await process_promotion(interaction, member, self.review_message)
        elif value == "bonus_salary":
            await process_bonus(interaction, member, BONUS_SALARY_ROLE, "💸 Бонус к зарплате", 200, self.review_message)
        elif value == "bonus_points":
            await process_bonus(interaction, member, BONUS_POINTS_ROLE, "⭐ Бонус к баллам", 200, self.review_message)


class QuantityModal(discord.ui.Modal):
    def __init__(self, title: str, label: str, author_id: int, review_message: discord.Message, item_type: str):
        super().__init__(title=title)
        self.author_id = author_id
        self.review_message = review_message
        self.item_type = item_type
        self.qty_input = discord.ui.TextInput(label=label, placeholder="Введите число")
        self.add_item(self.qty_input)

    async def on_submit(self, interaction: discord.Interaction):
        try:
            qty = int(str(self.qty_input))
        except ValueError:
            await interaction.response.send_message("❌ Введите число.", ephemeral=True)
            return

        guild = interaction.guild
        member = guild.get_member(self.author_id)

        if self.item_type == "case_relic":
            cost = qty * 20
            item_name = f"📦 Кейс с Рилликами x{qty}"
            description = f"{qty} кейс(ов)"
        else:
            cost = max(1, qty // 20)
            item_name = f"✨ Рилики x{qty}"
            description = f"{qty} риликов"

        success = await deduct_and_notify(interaction, member, cost, item_name, description, self.review_message)
        if success:
            await interaction.response.send_message(f"✅ **{item_name}** — списано {cost} 🪙", ephemeral=True)


# ─── HANDLERS ─────────────────────────────────────────────────────────────────

async def deduct_and_notify(interaction, member, cost, item_name, description, review_message, extra_fields=None):
    current = db.get_points(member.id)
    if cost > 0 and current < cost:
        await interaction.response.send_message(f"❌ Недостаточно баллов. Нужно: {cost}, есть: {current}", ephemeral=True)
        return False

    new_total = current - cost
    db.set_points(member.id, new_total, str(member))

    guild = interaction.guild

    # Форум
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

    # Канал проверки
    embed_review = discord.Embed(title=f"✅ Покупка: {item_name}", color=0x57F287)
    embed_review.add_field(name="Игрок", value=member.mention, inline=True)
    embed_review.add_field(name="Списано", value=f"-{cost} 🪙", inline=True)
    embed_review.add_field(name="Новый баланс", value=f"{new_total} 🪙", inline=True)
    embed_review.set_footer(text=f"Обработал: {interaction.user}")
    await bot.get_channel(REVIEW_CHANNEL).send(embed=embed_review)

    await disable_buttons(review_message)
    return True


async def process_simple(interaction, member, cost, item_name, description, review_message):
    success = await deduct_and_notify(interaction, member, cost, item_name, description, review_message)
    if success:
        await interaction.response.send_message(f"✅ **{item_name}** обработана.", ephemeral=True)


async def process_warn_remove(interaction, member, review_message):
    guild = interaction.guild
    member_role_ids = [r.id for r in member.roles]
    warn_count = sum(1 for rid in WARN_ROLES if rid in member_role_ids)

    if warn_count == 0:
        await interaction.response.send_message("❌ У игрока нет варнов.", ephemeral=True)
        return

    role_to_remove = guild.get_role(WARN_ROLES[warn_count - 1])
    if role_to_remove:
        await member.remove_roles(role_to_remove)

    new_count = warn_count - 1
    success = await deduct_and_notify(
        interaction, member, 70, "🚫 Снятие варна", "",
        review_message, extra_fields=[("Варны после покупки", f"{new_count}/3")]
    )
    if success:
        announce_ch = bot.get_channel(WARN_ANNOUNCE_CHANNEL)
        if announce_ch:
            embed = discord.Embed(title="🚫 Покупка снятия варна", color=0xED4245)
            embed.add_field(name="Варны", value=f"{new_count}/3", inline=True)
            await announce_ch.send(content=member.mention, embed=embed)
        await interaction.response.send_message("✅ Варн снят.", ephemeral=True)


async def process_mute_remove(interaction, member, review_message):
    guild = interaction.guild
    member_role_ids = [r.id for r in member.roles]
    mute_count = sum(1 for rid in MUTE_ROLES if rid in member_role_ids)

    if mute_count == 0:
        await interaction.response.send_message("❌ У игрока нет устников.", ephemeral=True)
        return

    role_to_remove = guild.get_role(MUTE_ROLES[mute_count - 1])
    if role_to_remove:
        await member.remove_roles(role_to_remove)

    new_count = mute_count - 1
    success = await deduct_and_notify(
        interaction, member, 40, "🔇 Снятие устника", "",
        review_message, extra_fields=[("Устники после покупки", f"{new_count}/2")]
    )
    if success:
        announce_ch = bot.get_channel(WARN_ANNOUNCE_CHANNEL)
        if announce_ch:
            embed = discord.Embed(title="🔇 Покупка снятия устника", color=0xF1C40F)
            embed.add_field(name="Устники", value=f"{new_count}/2", inline=True)
            await announce_ch.send(content=member.mention, embed=embed)
        await interaction.response.send_message("✅ Устник снят.", ephemeral=True)


async def process_promotion(interaction, member, review_message):
    guild = interaction.guild
    member_role_ids = [r.id for r in member.roles]

    current_idx = -1
    for i, rid in enumerate(STAFF_ROLES):
        if rid in member_role_ids:
            current_idx = i

    if current_idx == -1:
        await interaction.response.send_message("❌ У игрока нет штабной роли.", ephemeral=True)
        return
    if current_idx >= len(STAFF_ROLES) - 1:
        await interaction.response.send_message("❌ У игрока максимальная роль.", ephemeral=True)
        return

    old_role = guild.get_role(STAFF_ROLES[current_idx])
    new_role = guild.get_role(STAFF_ROLES[current_idx + 1])

    if old_role:
        await member.remove_roles(old_role)
    if new_role:
        await member.add_roles(new_role)

    success = await deduct_and_notify(
        interaction, member, 0, "⬆️ Повышение без нормы", "",
        review_message, extra_fields=[("Новая роль", new_role.mention if new_role else STAFF_NAMES[current_idx + 1])]
    )
    if success:
        promo_ch = bot.get_channel(PROMOTION_CHANNEL)
        if promo_ch:
            await promo_ch.send(
                f"{member.mention} Был повышен до {new_role.mention if new_role else STAFF_NAMES[current_idx + 1]}\n"
                f"Поздравим его! 🎉🎉🎉"
            )
        await interaction.response.send_message("✅ Повышение выполнено.", ephemeral=True)


async def process_bonus(interaction, member, role_id, item_name, cost, review_message):
    guild = interaction.guild
    role = guild.get_role(role_id)
    if role:
        await member.add_roles(role)
    success = await deduct_and_notify(interaction, member, cost, item_name, "", review_message)
    if success:
        await interaction.response.send_message(f"✅ **{item_name}** выдан.", ephemeral=True)


# ─── HELPERS ──────────────────────────────────────────────────────────────────

async def post_to_forum(guild, embed, thread_name):
    forum = discord.utils.get(guild.forums, name="заявки")
    fallback = discord.utils.get(guild.text_channels, name="заявки")
    if forum:
        await forum.create_thread(name=thread_name[:100], embed=embed)
    elif fallback:
        await fallback.send(embed=embed)
    else:
        # Если канала нет — шлём в канал проверки
        await bot.get_channel(REVIEW_CHANNEL).send(embed=embed)


async def disable_buttons(message: discord.Message):
    try:
        await message.edit(view=discord.ui.View())
    except Exception:
        pass


bot.run(os.getenv("DISCORD_TOKEN"))
