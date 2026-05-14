import discord
from discord.ext import commands
from discord import app_commands
import asyncio
import os
from dotenv import load_dotenv
from db import DBManager

try:
    from groq import Groq
    GROQ_AVAILABLE = True
except ImportError:
    GROQ_AVAILABLE = False
    print("⚠️ groq не установлен — автопроверка заявок отключена")

load_dotenv()

intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)
db = DBManager()
groq_client = Groq(api_key=os.getenv("GROQ_API_KEY")) if GROQ_AVAILABLE else None

# Channel IDs
WATCH_CHANNEL = 1429899592824258590
REVIEW_CHANNEL = 1499473605535203358
WARN_ANNOUNCE_CHANNEL = 1429895979863113832
PROMOTION_CHANNEL = 1493355826138583061

# GIF URLs для уведомлений
APPROVED_GIF = "https://raw.githubusercontent.com/mihailzn2011-ui/fringemarket/main/assets/gifs/odobreno.gif"
REJECTED_GIF = "https://raw.githubusercontent.com/mihailzn2011-ui/fringemarket/main/assets/gifs/otkazano.gif"

# Salary application channels
SALARY_FORUM = 1429899084331876494
SALARY_REVIEW = 1499473776067350538

# Day off application channels
DAYOFF_FORUM = 1429895980177821772
DAYOFF_REVIEW = 1499473645863571637
DAYOFF_ROLE = 1493325741444563198

# Promotion application channels
PROMO_APP_FORUM = 1429895980177821773
PROMO_APP_REVIEW = 1499473570617753700

# Leaderboard channel
LEADERBOARD_CHANNEL = 1441724727910469633
DAYOFF_LEADERBOARD_CHANNEL = 1496230104756523099
WARN_LEADERBOARD_CHANNEL = 1473657044899856414
MUTE_LEADERBOARD_CHANNEL = 1499487138792870018
ROSTER_LEADERBOARD_CHANNEL = 1501263934752297030

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
    1429895978931978273,  # 1/3
    1429895978931978274,  # 2/3
    1429895978931978275,  # 3/3
]

# Mute role IDs
MUTE_ROLES = [
    1469416711798390927,  # 1/2
    1469416666772406335,  # 2/2
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

# Categories for staff report channels (same order as STAFF_ROLES)
STAFF_CATEGORIES = [
    1498310733971198052,  # Хелпер
    1498312806116626543,  # Ст. Хелпер
    1498313628259192892,  # Мл. Модер
    1498315899768279050,  # Модер
    1498316703757504522,  # Модер+
    1498317376641302679,  # Ст. Модер
    1498318061449515029,  # Гл. Модер
]

BONUS_SALARY_ROLE = 1466142358549823672
BONUS_POINTS_ROLE = 1466142620580450439

# Forum thread tags
# 1. WATCH_CHANNEL (баллы)
TAGS_POINTS = {
    "pending":  1500498742476800000,
    "approved": 1436827449529995335,
    "rejected": 1436827472422375686,
}
# 2. SALARY_FORUM (зарплата)
TAGS_SALARY = {
    "pending":  1429899644368064623,
    "approved": 1429899577208733807,
    "rejected": 1429899618258387028,
}
# 3. DAYOFF_FORUM (отгулы)
TAGS_DAYOFF = {
    "pending":  1429897264343679237,
    "approved": 1429897193057288243,
    "rejected": 1429897219825205310,
}
# 4. PROMO_APP_FORUM (повышение)
TAGS_PROMO = {
    "pending":  1429896854568435827,
    "approved": 1429896774008442910,
    "rejected": 1429896817914675241,
}
# 5. APPEAL_FORUM (обжалование варнов/устников)
APPEAL_FORUM = 1503423212179034253
APPEAL_REVIEW = 1503425294764085379
TAGS_APPEAL = {
    "pending":  1503423824962519072,
    "approved": 1503423655315767487,
    "rejected": 1503423727096955010,
}


@bot.event
async def on_ready():
    print(f"Бот {bot.user} запущен!")
    print(f"Подключен к {len(bot.guilds)} серверам")
    
    try:
        synced = await bot.tree.sync()
        print(f"✅ Синхронизировано {len(synced)} команд!")
        for cmd in synced:
            print(f"  - /{cmd.name}")
    except Exception as e:
        print(f"❌ Ошибка синхронизации команд: {e}")
        import traceback
        traceback.print_exc()
    
    try:
        await update_leaderboard()
        print("✅ Лидерборд баллов обновлен!")
    except Exception as e:
        print(f"❌ Ошибка обновления лидерборда баллов: {e}")
    
    try:
        await update_dayoff_leaderboard()
        print("✅ Лидерборд отгулов обновлен!")
    except Exception as e:
        print(f"❌ Ошибка обновления лидерборда отгулов: {e}")
    
    try:
        await update_warn_leaderboard()
        print("✅ Лидерборд варнов обновлен!")
    except Exception as e:
        print(f"❌ Ошибка обновления лидерборда варнов: {e}")
    
    try:
        await update_mute_leaderboard()
        print("✅ Лидерборд устников обновлен!")
    except Exception as e:
        print(f"❌ Ошибка обновления лидерборда устников: {e}")

    try:
        await update_roster_leaderboard()
        print("✅ Список состава обновлен!")
    except Exception as e:
        print(f"❌ Ошибка обновления списка состава: {e}")
    
    try:
        await restore_dayoff_timers()
        print("✅ Таймеры отгулов восстановлены!")
    except Exception as e:
        print(f"❌ Ошибка восстановления таймеров: {e}")

    asyncio.create_task(daily_scheduler())


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
    if thread.parent_id == WATCH_CHANNEL:
        await handle_points_thread(thread)
    elif thread.parent_id == SALARY_FORUM:
        await handle_salary_thread(thread)
    elif thread.parent_id == DAYOFF_FORUM:
        await handle_dayoff_thread(thread)
    elif thread.parent_id == PROMO_APP_FORUM:
        await handle_promotion_thread(thread)
    elif thread.parent_id == APPEAL_FORUM:
        await handle_appeal_thread(thread)


# ─── ОБНОВЛЕНИЕ ТАБЛИЦ ПРИ РУЧНОМ ИЗМЕНЕНИИ РОЛЕЙ ────────────────────────────

@bot.event
async def on_member_update(before: discord.Member, after: discord.Member):
    before_ids = {r.id for r in before.roles}
    after_ids = {r.id for r in after.roles}
    changed = before_ids.symmetric_difference(after_ids)

    warn_changed = any(rid in WARN_ROLES for rid in changed)
    mute_changed = any(rid in MUTE_ROLES for rid in changed)
    staff_changed = any(rid in STAFF_ROLES for rid in changed)
    points_changed = staff_changed  # таблица баллов группируется по стаф-ролям

    if warn_changed:
        try:
            await update_warn_leaderboard()
        except Exception as e:
            print(f"[on_member_update] Ошибка обновления варнов: {e}")

    if mute_changed:
        try:
            await update_mute_leaderboard()
        except Exception as e:
            print(f"[on_member_update] Ошибка обновления устников: {e}")

    if points_changed:
        try:
            await update_leaderboard()
        except Exception as e:
            print(f"[on_member_update] Ошибка обновления баллов: {e}")

    # Перемещение канала при смене штатной роли
    if staff_changed:
        try:
            await move_staff_channel(before, after)
        except Exception as e:
            print(f"[on_member_update] Ошибка перемещения канала: {e}")
        try:
            await update_roster_leaderboard()
        except Exception as e:
            print(f"[on_member_update] Ошибка обновления состава: {e}")

    # Dayoff роль
    if DAYOFF_ROLE in changed:
        try:
            await update_dayoff_leaderboard()
        except Exception as e:
            print(f"[on_member_update] Ошибка обновления отгулов: {e}")


# ─── THREAD HANDLERS ──────────────────────────────────────────────────────────

async def move_staff_channel(before: discord.Member, after: discord.Member):
    """При смене штатной роли ищет канал участника в старой категории и перемещает в новую."""
    before_ids = {r.id for r in before.roles}
    after_ids = {r.id for r in after.roles}

    # Определяем индекс роли до и после
    old_idx = -1
    new_idx = -1
    for i, rid in enumerate(STAFF_ROLES):
        if rid in before_ids:
            old_idx = i
        if rid in after_ids:
            new_idx = i

    # Нет смысла двигать если роль не изменилась или нет штатной роли
    if old_idx == new_idx or old_idx == -1 or new_idx == -1:
        return

    old_category_id = STAFF_CATEGORIES[old_idx]
    new_category_id = STAFF_CATEGORIES[new_idx]

    if old_category_id == new_category_id:
        return

    guild = after.guild
    old_category = guild.get_channel(old_category_id)
    new_category = guild.get_channel(new_category_id)

    if not old_category or not new_category:
        print(f"[move_staff_channel] Категория не найдена: old={old_category_id}, new={new_category_id}")
        return

    # Ищем канал по display_name участника в старой категории
    # Ник на сервере формата "ник | имя" — берём только часть до "|"
    display_name = after.display_name.split("|")[0].strip().lower()
    target_channel = None
    for ch in old_category.channels:
        if display_name in ch.name.lower():
            target_channel = ch
            break

    if not target_channel:
        print(f"[move_staff_channel] Канал для '{after.display_name}' не найден в категории '{old_category.name}'")
        return

    await target_channel.edit(category=new_category)
    print(f"[move_staff_channel] Канал '{target_channel.name}' перемещён из '{old_category.name}' в '{new_category.name}'")


async def set_thread_tag(forum_id: int, thread_id: int, tags: dict, status: str):
    """Меняет тег треда на нужный статус: 'pending', 'approved', 'rejected'."""
    try:
        forum = bot.get_channel(forum_id)
        if not isinstance(forum, discord.ForumChannel):
            return

        thread = forum.get_thread(thread_id)
        if not thread:
            thread = await bot.fetch_channel(thread_id)

        tag_id = tags.get(status)
        if not tag_id:
            return

        # Находим объект тега по ID
        target_tag = discord.utils.get(forum.available_tags, id=tag_id)
        if not target_tag:
            return

        # Убираем все теги из нашего набора, добавляем нужный
        tag_ids_set = set(tags.values())
        current_tags = [t for t in thread.applied_tags if t.id not in tag_ids_set]
        current_tags.append(target_tag)

        await thread.edit(applied_tags=current_tags)
    except Exception as e:
        print(f"[set_thread_tag] Ошибка: {e}")


# ─── AUTO CHECK POINTS APPLICATION ───────────────────────────────────────────

# Список товаров магазина с номерами и стоимостью
SHOP_ITEMS_MAP = {
    "1": ("warn_remove",   "🚫 Снятие варна",           None),
    "2": ("mute_remove",   "🔇 Снятие устника",          None),
    "3": ("donate_helper", "💎 Донат Helper на твинк",   80),
    "4": ("kit",           "🎁 Кит",                     65),
    "5": ("case_relic",    "📦 Кейс с Рилликами",        None),
    "6": ("relics",        "✨ Рилики",                   None),
    "7": ("promote",       "⬆️ Повышение без нормы",     None),
    "8": ("bonus_salary",  "💸 Бонус к зарплате",        200),
    "9": ("bonus_points",  "⭐ Бонус к баллам",           200),
}


async def detect_application_type(text: str) -> str:
    """Определяет тип заявки по структуре текста без Claude."""
    import re
    # Ищем пункты вида "1.", "2.", "3." и т.д.
    points = re.findall(r'^\s*\d+[\.\)]\s*.+', text, re.MULTILINE)
    if len(points) >= 3:
        return "accrual"
    elif len(points) == 2:
        return "purchase"
    return "unknown"


async def auto_check_purchase_application(text: str, author, guild) -> dict | None:
    """Парсит заявку на покупку через Groq и обрабатывает если возможно."""
    if not groq_client:
        return None
    try:
        response = await asyncio.to_thread(
            lambda: groq_client.chat.completions.create(
                model="llama-3.1-70b-versatile",
                messages=[{"role": "user", "content": (
                    "Из текста заявки на покупку извлеки:\n"
                    "- nickname: ник игрока\n"
                    "- item_number: номер товара (цифра)\n"
                    "Ответь ТОЛЬКО валидным JSON без пояснений:\n"
                    '{"nickname": "...", "item_number": "1"}\n\n'
                    f"Текст:\n{text}"
                )}],
                max_tokens=100
            )
        )
        import json
        parsed = json.loads(response.choices[0].message.content.strip())
    except Exception as e:
        print(f"[auto_check_purchase] Groq ошибка: {e}")
        return None

    nickname = parsed.get("nickname")
    item_number = str(parsed.get("item_number", "")).strip()

    if not nickname or item_number not in SHOP_ITEMS_MAP:
        return {"success": False, "error": f"Не удалось определить товар (номер: {item_number}) — проверьте вручную"}

    item_value, item_name, item_cost = SHOP_ITEMS_MAP[item_number]

    # Товары которые требуют доп. данных или ручной обработки
    manual_items = {"warn_remove", "mute_remove", "case_relic", "relics", "promote"}
    if item_value in manual_items:
        return {"success": False, "error": f"Товар **{item_name}** требует ручной обработки"}

    if item_cost is None:
        return {"success": False, "error": f"Стоимость товара **{item_name}** не определена"}

    # Ищем участника по нику
    member = None
    if author:
        member = guild.get_member(author.id)

    if not member:
        return {"success": False, "error": f"Игрок не найден на сервере"}

    # Проверяем баланс
    current = db.get_points(member.id)
    if current < item_cost:
        return {
            "success": False,
            "error": f"Недостаточно баллов для **{item_name}**\nНужно: **{item_cost} 🪙** | Баланс: **{current} 🪙**"
        }

    # Списываем баллы
    new_total = current - item_cost
    db.set_points(member.id, new_total, str(member))

    return {
        "success": True,
        "details": (
            f"Товар: **{item_name}**\n"
            f"Списано: **-{item_cost} 🪙**\n"
            f"Новый баланс: **{new_total} 🪙**\n"
            f"Для выдачи товара обратитесь к администрации."
        )
    }


async def auto_check_points_application(text: str, author, guild) -> dict | None:
    """
    Парсит заявку на баллы через Groq, находит канал игрока,
    считает сообщения за период и сравнивает с заявленным числом.
    Возвращает dict с ключами: match, claimed, actual, points, summary
    """
    if not groq_client:
        return None
    from datetime import datetime, timezone

    # 1. Парсим заявку через Groq
    prompt = f"""Ты парсер заявок на баллы для Discord бота. Из текста заявки извлеки:
- nickname: ник игрока (строка)
- count: количество наказаний (целое число)  
- date_from: дата начала периода в формате DD.MM.YYYY
- date_to: дата конца периода в формате DD.MM.YYYY

Сегодня: {datetime.now().strftime('%d.%m.%Y')}

Правила:
- "за сегодня" = сегодняшняя дата для обоих полей
- "за неделю" = последние 7 дней
- если одна дата = она же для date_from и date_to
- если не можешь определить поле = null

Ответь ТОЛЬКО валидным JSON без пояснений:
{{"nickname": "...", "count": 0, "date_from": "DD.MM.YYYY", "date_to": "DD.MM.YYYY"}}

Текст заявки:
{text}"""

    try:
        response = await asyncio.to_thread(
            lambda: groq_client.chat.completions.create(
                model="llama-3.1-70b-versatile",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=200
            )
        )
        import json
        parsed = json.loads(response.choices[0].message.content.strip())
    except Exception as e:
        print(f"[auto_check] Groq ошибка парсинга: {e}")
        return None

    nickname = parsed.get("nickname")
    claimed_count = parsed.get("count")
    date_from_str = parsed.get("date_from")
    date_to_str = parsed.get("date_to")

    if not all([nickname, claimed_count is not None, date_from_str, date_to_str]):
        return None

    # 2. Парсим даты
    try:
        date_from = datetime.strptime(date_from_str, "%d.%m.%Y").replace(tzinfo=timezone.utc)
        date_to = datetime.strptime(date_to_str, "%d.%m.%Y").replace(
            hour=23, minute=59, second=59, tzinfo=timezone.utc
        )
    except Exception:
        return None

    # 3. Ищем канал игрока по нику во всех штатных категориях
    target_channel = None
    nick_lower = nickname.lower()
    for cat_id in STAFF_CATEGORIES:
        category = guild.get_channel(cat_id)
        if not category:
            continue
        for ch in category.channels:
            if nick_lower in ch.name.lower():
                target_channel = ch
                break
        if target_channel:
            break

    if not target_channel:
        return {
            "match": False,
            "claimed": claimed_count,
            "actual": None,
            "points": round(claimed_count * 1.5),
            "summary": (
                f"Ник: **{nickname}** | Заявлено: **{claimed_count}** наказаний\n"
                f"Период: {date_from_str} — {date_to_str}\n"
                f"⚠️ Канал игрока не найден — проверьте вручную"
            )
        }

    # 4. Считаем сообщения за период
    actual_count = 0
    try:
        async for msg in target_channel.history(limit=2000, after=date_from, before=date_to):
            if msg.author == author or (author and msg.author.id == author.id):
                actual_count += 1
    except Exception as e:
        print(f"[auto_check] Ошибка чтения истории: {e}")
        return None

    # 5. Сравниваем
    match = actual_count == claimed_count
    points = round(actual_count * 1.5)

    if match:
        summary = (
            f"Ник: **{nickname}** | Период: {date_from_str} — {date_to_str}\n"
            f"Заявлено: **{claimed_count}** | Найдено: **{actual_count}** ✅\n"
            f"К начислению: **{points} 🪙**"
        )
    else:
        summary = (
            f"Ник: **{nickname}** | Период: {date_from_str} — {date_to_str}\n"
            f"Заявлено: **{claimed_count}** | Найдено в канале: **{actual_count}** ⚠️\n"
            f"Расхождение! К начислению по факту: **{points} 🪙**"
        )

    return {
        "match": match,
        "claimed": claimed_count,
        "actual": actual_count,
        "points": points,
        "summary": summary,
        "channel": target_channel.name
    }


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

    # Определяем тип заявки через Groq и пробуем автообработать
    if content:
        try:
            print(f"[auto_check] groq доступен: {groq_client is not None}, content: {content[:50]!r}")
            app_type = await detect_application_type(content)
            print(f"[auto_check] тип заявки: {app_type}")

            if app_type == "accrual":
                result = await auto_check_points_application(content, author, thread.guild)
                print(f"[auto_check] результат accrual: {result}")
                if result and result["match"] and result["actual"] is not None:
                    # Всё сошлось — автоначисляем без отправки в канал
                    member = thread.guild.get_member(thread.owner_id)
                    points = result["points"]
                    current = db.get_points(thread.owner_id)
                    new_total = current + points
                    db.set_points(thread.owner_id, new_total, str(member) if member else "")
                    await set_thread_tag(WATCH_CHANNEL, thread.id, TAGS_POINTS, "approved")
                    await notify_author_in_thread(
                        thread.id, thread.owner_id,
                        approved=True,
                        details=f"Автопроверка прошла ✅\nНачислено **+{points} 🪙**\nНовый баланс: **{new_total} 🪙**",
                        admin_name="Автосистема"
                    )
                    await update_leaderboard()
                    print(f"[auto_check] Заявка {thread.id} автоодобрена: {points} баллов")
                    return  # не отправляем в канал проверки

                # Расхождение или канал не найден — отправляем в канал с пометкой
                embed = discord.Embed(title=f"📋 {thread.name}", description=content or "*Без текста*", color=0x5865F2)
                if author:
                    embed.set_author(name=str(author), icon_url=author.display_avatar.url)
                embed.set_footer(text=f"ID автора: {thread.owner_id} | Тред: {thread.id}")
                if attachment_url:
                    embed.set_image(url=attachment_url)
                if result:
                    embed.add_field(name="⚠️ Автопроверка", value=result["summary"], inline=False)
                else:
                    embed.add_field(name="⚠️ Автопроверка", value="Не удалось распарсить заявку — проверьте вручную", inline=False)
                view = ReviewView(author_id=thread.owner_id, source_thread_id=thread.id)
                await review_channel.send(embed=embed, view=view)
                await set_thread_tag(WATCH_CHANNEL, thread.id, TAGS_POINTS, "pending")
                return

            elif app_type == "purchase":
                result = await auto_check_purchase_application(content, author, thread.guild)
                if result and result.get("success"):
                    # Автопокупка прошла
                    await set_thread_tag(WATCH_CHANNEL, thread.id, TAGS_POINTS, "approved")
                    await notify_author_in_thread(
                        thread.id, thread.owner_id,
                        approved=True,
                        details=f"Автопроверка прошла ✅\n{result['details']}",
                        admin_name="Автосистема"
                    )
                    await update_leaderboard()
                    print(f"[auto_check] Покупка {thread.id} автоодобрена")
                    return

                # Не смогли обработать — в канал
                embed = discord.Embed(title=f"📋 {thread.name}", description=content or "*Без текста*", color=0x5865F2)
                if author:
                    embed.set_author(name=str(author), icon_url=author.display_avatar.url)
                embed.set_footer(text=f"ID автора: {thread.owner_id} | Тред: {thread.id}")
                if attachment_url:
                    embed.set_image(url=attachment_url)
                if result and result.get("error"):
                    embed.add_field(name="⚠️ Автопроверка", value=result["error"], inline=False)
                else:
                    embed.add_field(name="⚠️ Автопроверка", value="Не удалось распарсить заявку — проверьте вручную", inline=False)
                view = ReviewView(author_id=thread.owner_id, source_thread_id=thread.id)
                await review_channel.send(embed=embed, view=view)
                await set_thread_tag(WATCH_CHANNEL, thread.id, TAGS_POINTS, "pending")
                return

        except Exception as e:
            print(f"[handle_points_thread] Ошибка автопроверки: {e}")
            import traceback
            traceback.print_exc()

    # Fallback — стандартная отправка в канал
    embed = discord.Embed(title=f"📋 {thread.name}", description=content or "*Без текста*", color=0x5865F2)
    if author:
        embed.set_author(name=str(author), icon_url=author.display_avatar.url)
    embed.set_footer(text=f"ID автора: {thread.owner_id} | Тред: {thread.id}")
    if attachment_url:
        embed.set_image(url=attachment_url)
    view = ReviewView(author_id=thread.owner_id, source_thread_id=thread.id)
    await review_channel.send(embed=embed, view=view)
    await set_thread_tag(WATCH_CHANNEL, thread.id, TAGS_POINTS, "pending")


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
    await set_thread_tag(SALARY_FORUM, thread.id, TAGS_SALARY, "pending")


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
    await set_thread_tag(DAYOFF_FORUM, thread.id, TAGS_DAYOFF, "pending")


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
    await set_thread_tag(PROMO_APP_FORUM, thread.id, TAGS_PROMO, "pending")


async def handle_appeal_thread(thread: discord.Thread):
    await asyncio.sleep(1.5)
    try:
        starter = await thread.fetch_message(thread.id)
    except Exception:
        starter = None

    review_channel = bot.get_channel(APPEAL_REVIEW)
    if not review_channel:
        return

    author = thread.owner
    content = starter.content if starter else ""
    attachment_url = starter.attachments[0].url if starter and starter.attachments else None

    embed = discord.Embed(
        title=f"⚖️ Обжалование: {thread.name}",
        description=content or "*Без текста*",
        color=0xE67E22
    )
    if author:
        embed.set_author(name=str(author), icon_url=author.display_avatar.url)
    embed.set_footer(text=f"ID автора: {thread.owner_id} | Тред: {thread.id}")
    if attachment_url:
        embed.set_image(url=attachment_url)

    view = AppealReviewView(author_id=thread.owner_id, source_thread_id=thread.id)
    await review_channel.send(embed=embed, view=view)
    await set_thread_tag(APPEAL_FORUM, thread.id, TAGS_APPEAL, "pending")


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
            title="✅ Заявка одобрена",
            description=f"<@{author_id}>, твоя заявка была **одобрена**. 🎉",
            color=0x57F287
        )
        embed.add_field(name="📌 Детали", value=details or "—", inline=False)
        embed.set_footer(text=f"Обработал: {admin_name}" if admin_name else "Обработано администрацией")
        embed.set_thumbnail(url=APPROVED_GIF)
    else:
        embed = discord.Embed(
            title="❌ Заявка отклонена",
            description=f"<@{author_id}>, твоя заявка была **отклонена**.",
            color=0xED4245
        )
        embed.add_field(name="📌 Причина", value=details or "Причина не указана", inline=False)
        embed.set_footer(text=f"Обработал: {admin_name}" if admin_name else "Обработано администрацией")
        embed.set_thumbnail(url=REJECTED_GIF)

    try:
        await thread.send(embed=embed)
    except Exception as e:
        print(f"[notify_author_in_thread] Ошибка: {e}")


# ─── SLASH COMMANDS ───────────────────────────────────────────────────────────

@bot.tree.command(name="выдать", description="Выдать баллы игроку вручную")
@app_commands.describe(игрок="Упомяните игрока", количество="Количество баллов")
async def give_points(interaction: discord.Interaction, игрок: discord.Member, количество: int):
    user_role_ids = [role.id for role in interaction.user.roles]
    if not any(role_id in ALLOWED_COMMAND_ROLES for role_id in user_role_ids):
        await interaction.response.send_message("❌ У вас нет прав для использования этой команды.", ephemeral=True)
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
    user_role_ids = [role.id for role in interaction.user.roles]
    if not any(role_id in ALLOWED_COMMAND_ROLES for role_id in user_role_ids):
        await interaction.response.send_message("❌ У вас нет прав для использования этой команды.", ephemeral=True)
        return
    
    await interaction.response.defer(ephemeral=True)
    
    guild = interaction.guild
    member_role_ids = [r.id for r in игрок.roles]
    warn_count = sum(1 for rid in WARN_ROLES if rid in member_role_ids)

    if warn_count >= 3:
        await interaction.followup.send("❌ У игрока уже максимум варнов (3/3).", ephemeral=True)
        return

    role_to_add = guild.get_role(WARN_ROLES[warn_count])
    if role_to_add:
        await игрок.add_roles(role_to_add)

    new_count = warn_count + 1

    # Цветные кружки для варнов
    if new_count == 1:
        warn_emoji = "🟢"
    elif new_count == 2:
        warn_emoji = "🟡"
    else:
        warn_emoji = "🔴"

    # Цвет embed по количеству варнов
    if new_count == 1:
        embed_color = 0x57F287   # зеленый
    elif new_count == 2:
        embed_color = 0xFEE75C   # желтый
    else:
        embed_color = 0xED4245   # красный

    # Визуальная полоска варнов: заполненные и пустые кружки
    filled = warn_emoji * new_count
    empty = "⚫" * (3 - new_count)
    warn_bar = filled + empty  # например 🟢⚫⚫ или 🟡🟡⚫

    announce_ch = bot.get_channel(WARN_ANNOUNCE_CHANNEL)
    if announce_ch:
        embed_announce = discord.Embed(
            title="⚠️ Выдача варна",
            description=f"{игрок.mention} получил варн!",
            color=embed_color
        )
        embed_announce.add_field(name="👤 Игрок", value=игрок.mention, inline=True)
        embed_announce.add_field(name="🛡️ Выдал", value=interaction.user.mention, inline=True)
        embed_announce.add_field(name=f"Варны {warn_bar} {new_count}/3", value=f"", inline=False)
        embed_announce.add_field(name="📋 Причина", value=причина, inline=False)
        embed_announce.set_thumbnail(url=игрок.display_avatar.url)
        embed_announce.set_footer(text=f"ID: {игрок.id}")
        if скриншот:
            embed_announce.set_image(url=скриншот)
        await announce_ch.send(embed=embed_announce)

    await update_warn_leaderboard()
    await interaction.followup.send(f"✅ Варн выдан {игрок.mention}. Варны: **{new_count}/3**", ephemeral=True)


@bot.tree.command(name="снятьварн", description="Снять варн игроку")
@app_commands.describe(игрок="Упомяните игрока")
async def remove_warn(interaction: discord.Interaction, игрок: discord.Member):
    user_role_ids = [role.id for role in interaction.user.roles]
    if not any(role_id in ALLOWED_COMMAND_ROLES for role_id in user_role_ids):
        await interaction.response.send_message("❌ У вас нет прав для использования этой команды.", ephemeral=True)
        return
    
    await interaction.response.defer(ephemeral=True)
    
    guild = interaction.guild
    member_role_ids = [r.id for r in игрок.roles]
    warn_count = sum(1 for rid in WARN_ROLES if rid in member_role_ids)

    if warn_count == 0:
        await interaction.followup.send("❌ У игрока нет варнов.", ephemeral=True)
        return

    # Удаляем последний варн (самый высокий)
    role_to_remove = guild.get_role(WARN_ROLES[warn_count - 1])
    if role_to_remove:
        await игрок.remove_roles(role_to_remove)

    new_count = warn_count - 1

    # Цветные кружки для варнов
    if new_count == 0:
        warn_emoji = "⚫"
        warn_bar = "⚫⚫⚫"
        embed_color = 0x57F287
    elif new_count == 1:
        warn_emoji = "🟢"
        warn_bar = "🟢⚫⚫"
        embed_color = 0x57F287
    elif new_count == 2:
        warn_emoji = "🟡"
        warn_bar = "🟡🟡⚫"
        embed_color = 0xFEE75C
    else:
        warn_emoji = "🔴"
        warn_bar = "🔴🔴🔴"
        embed_color = 0xED4245

    announce_ch = bot.get_channel(WARN_ANNOUNCE_CHANNEL)
    if announce_ch:
        embed_announce = discord.Embed(
            title="✅ Снятие варна",
            description=f"{игрок.mention} получил снятие варна!",
            color=embed_color
        )
        embed_announce.add_field(name="👤 Игрок", value=игрок.mention, inline=True)
        embed_announce.add_field(name="🛡️ Снял", value=interaction.user.mention, inline=True)
        embed_announce.add_field(name=f"Варны {warn_bar} {new_count}/3", value=f"", inline=False)
        embed_announce.set_thumbnail(url=игрок.display_avatar.url)
        embed_announce.set_footer(text=f"ID: {игрок.id}")
        await announce_ch.send(embed=embed_announce)

    await update_warn_leaderboard()
    await interaction.followup.send(f"✅ Варн снят у {игрок.mention}. Варны: **{new_count}/3**", ephemeral=True)


@bot.tree.command(name="выдатьустник", description="Выдать устник игроку")
@app_commands.describe(игрок="Упомяните игрока", причина="Причина выдачи устника", скриншот="Ссылка на скриншот (опционально)")
async def give_mute(interaction: discord.Interaction, игрок: discord.Member, причина: str, скриншот: str = None):
    user_role_ids = [role.id for role in interaction.user.roles]
    if not any(role_id in ALLOWED_COMMAND_ROLES for role_id in user_role_ids):
        await interaction.response.send_message("❌ У вас нет прав для использования этой команды.", ephemeral=True)
        return
    
    await interaction.response.defer(ephemeral=True)
    
    guild = interaction.guild
    member_role_ids = [r.id for r in игрок.roles]
    mute_count = sum(1 for rid in MUTE_ROLES if rid in member_role_ids)

    if mute_count >= 2:
        await interaction.followup.send("❌ У игрока уже максимум устников (2/2).", ephemeral=True)
        return

    role_to_add = guild.get_role(MUTE_ROLES[mute_count])
    if role_to_add:
        await игрок.add_roles(role_to_add)

    new_count = mute_count + 1

    # Цветные кружки для устников
    if new_count == 1:
        mute_emoji = "🟡"
    else:
        mute_emoji = "🟠"

    # Цвет embed по количеству устников
    if new_count == 1:
        embed_color = 0xFEE75C   # желтый
    else:
        embed_color = 0xE67E22   # оранжевый

    # Визуальная полоска устников
    filled = mute_emoji * new_count
    empty = "⚫" * (2 - new_count)
    mute_bar = filled + empty  # например 🟡⚫ или 🟠🟠

    announce_ch = bot.get_channel(WARN_ANNOUNCE_CHANNEL)
    if announce_ch:
        embed_announce = discord.Embed(
            title="🔇 Выдача устника",
            description=f"{игрок.mention} получил устник!",
            color=embed_color
        )
        embed_announce.add_field(name="👤 Игрок", value=игрок.mention, inline=True)
        embed_announce.add_field(name="🛡️ Выдал", value=interaction.user.mention, inline=True)
        embed_announce.add_field(name=f"Устники {mute_bar} {new_count}/2", value="", inline=False)
        embed_announce.add_field(name="📋 Причина", value=причина, inline=False)
        embed_announce.set_thumbnail(url=игрок.display_avatar.url)
        embed_announce.set_footer(text=f"ID: {игрок.id}")
        if скриншот:
            embed_announce.set_image(url=скриншот)
        await announce_ch.send(embed=embed_announce)

    await update_mute_leaderboard()
    await interaction.followup.send(f"✅ Устник выдан {игрок.mention}. Устники: **{new_count}/2**", ephemeral=True)


@bot.tree.command(name="мультиварн", description="Выдать варн сразу нескольким игрокам")
@app_commands.describe(
    игроки="Упомяните игроков через пробел (@игрок1 @игрок2 ...)",
    причина="Причина (будет заголовком embed)"
)
async def multi_warn(interaction: discord.Interaction, игроки: str, причина: str):
    user_role_ids = [role.id for role in interaction.user.roles]
    if not any(role_id in ALLOWED_COMMAND_ROLES for role_id in user_role_ids):
        await interaction.response.send_message("❌ У вас нет прав для использования этой команды.", ephemeral=True)
        return

    await interaction.response.defer(ephemeral=True)

    guild = interaction.guild

    # Парсим упомянутых участников из строки
    import re
    member_ids = re.findall(r"<@!?(\d+)>", игроки)
    if not member_ids:
        await interaction.followup.send("❌ Не удалось найти упоминания игроков. Используй @упоминание.", ephemeral=True)
        return

    members = []
    for mid in member_ids:
        m = guild.get_member(int(mid))
        if m:
            members.append(m)

    if not members:
        await interaction.followup.send("❌ Ни один из упомянутых игроков не найден на сервере.", ephemeral=True)
        return

    announce_ch = bot.get_channel(WARN_ANNOUNCE_CHANNEL)
    players_lines = []

    for игрок in members:
        member_role_ids = [r.id for r in игрок.roles]
        warn_count = sum(1 for rid in WARN_ROLES if rid in member_role_ids)

        if warn_count >= 3:
            players_lines.append(f"⛔ {игрок.mention} — уже 3/3")
            continue

        role_to_add = guild.get_role(WARN_ROLES[warn_count])
        if role_to_add:
            await игрок.add_roles(role_to_add)

        new_count = warn_count + 1

        if new_count == 1:
            warn_emoji = "🟢"
        elif new_count == 2:
            warn_emoji = "🟡"
        else:
            warn_emoji = "🔴"

        filled = warn_emoji * new_count
        empty = "⚫" * (3 - new_count)
        warn_bar = filled + empty

        players_lines.append(f"{игрок.mention} {warn_bar} **{new_count}/3**")

    # Одно общее сообщение на всех
    if announce_ch and players_lines:
        embed_announce = discord.Embed(
            title=f"⚠️ {причина}",
            color=0xED4245
        )
        embed_announce.add_field(
            name="👥 Игроки",
            value="\n".join(players_lines),
            inline=False
        )
        embed_announce.add_field(name="🛡️ Выдал", value=interaction.user.mention, inline=False)
        await announce_ch.send(embed=embed_announce)

    await update_warn_leaderboard()
    await interaction.followup.send(f"✅ Мультиварн выдан на **{len(members)}** игроков.", ephemeral=True)


@bot.tree.command(name="снятьбаллы", description="Снять баллы у игрока")
@app_commands.describe(игрок="Упомяните игрока", количество="Количество баллов для снятия")
async def remove_points(interaction: discord.Interaction, игрок: discord.Member, количество: int):
    user_role_ids = [role.id for role in interaction.user.roles]
    if not any(role_id in ALLOWED_COMMAND_ROLES for role_id in user_role_ids):
        await interaction.response.send_message("❌ У вас нет прав для использования этой команды.", ephemeral=True)
        return
    
    await interaction.response.defer(ephemeral=True)
    
    current = db.get_points(игрок.id)
    new_total = max(0, current - количество)
    db.set_points(игрок.id, new_total, str(игрок))

    embed_review = discord.Embed(title="💸 Баллы сняты", color=0xE74C3C)
    embed_review.add_field(name="Игрок", value=игрок.mention, inline=True)
    embed_review.add_field(name="Снято", value=f"-{количество} 🪙", inline=True)
    embed_review.add_field(name="Новый баланс", value=f"{new_total} 🪙", inline=True)
    embed_review.set_footer(text=f"Снял: {interaction.user}")
    await bot.get_channel(REVIEW_CHANNEL).send(embed=embed_review)

    await interaction.followup.send(f"✅ Снято **{количество} 🪙** у {игрок.mention}. Новый баланс: **{new_total} 🪙**", ephemeral=True)
    await update_leaderboard()


@bot.tree.command(name="выдатьповышение", description="Повысить игрока")
@app_commands.describe(игрок="Упомяните игрока")
async def give_promotion(interaction: discord.Interaction, игрок: discord.Member):
    user_role_ids = [role.id for role in interaction.user.roles]
    if not any(role_id in ALLOWED_COMMAND_ROLES for role_id in user_role_ids):
        await interaction.response.send_message("❌ У вас нет прав для использования этой команды.", ephemeral=True)
        return
    
    await interaction.response.defer(ephemeral=True)
    
    guild = interaction.guild
    member_role_ids = [r.id for r in игрок.roles]

    current_idx = -1
    for i, rid in enumerate(STAFF_ROLES):
        if rid in member_role_ids:
            current_idx = i

    if current_idx == -1:
        await interaction.followup.send("❌ У игрока нет штабной роли.", ephemeral=True)
        return
    if current_idx >= len(STAFF_ROLES) - 1:
        await interaction.followup.send("❌ У игрока максимальная роль.", ephemeral=True)
        return

    old_role = guild.get_role(STAFF_ROLES[current_idx])
    new_role = guild.get_role(STAFF_ROLES[current_idx + 1])

    if old_role:
        await игрок.remove_roles(old_role)
    if new_role:
        await игрок.add_roles(new_role)

    # Если повышают до Модератора (индекс 3) — выдаём доп. роль
    MODER_ROLE_ID = 1500525783456809101
    if current_idx + 1 == 3:
        moder_extra = guild.get_role(MODER_ROLE_ID)
        if moder_extra:
            await игрок.add_roles(moder_extra)

    # Очищаем канал отчётов игрока
    nick_lower = игрок.display_name.split("|")[0].strip().lower()
    for cat_id in STAFF_CATEGORIES:
        category = guild.get_channel(cat_id)
        if not category:
            continue
        for ch in category.channels:
            if nick_lower in ch.name.lower():
                try:
                    await ch.purge(limit=None)
                    print(f"[give_promotion] Канал {ch.name} очищен")
                except Exception as e:
                    print(f"[give_promotion] Ошибка очистки канала: {e}")
                break

    promo_ch = bot.get_channel(PROMOTION_CHANNEL)
    if promo_ch:
        embed = discord.Embed(title="⬆️ Повышение", color=0x9B59B6)
        embed.add_field(name="Новая роль", value=new_role.mention if new_role else STAFF_NAMES[current_idx + 1], inline=True)
        embed.set_footer(text=f"Выдал: {interaction.user.name}")
        await promo_ch.send(
            content=f"{игрок.mention} Был повышен до {new_role.mention if new_role else STAFF_NAMES[current_idx + 1]}\nПоздравим его! 🎉🎉🎉",
            embed=embed
        )

    await interaction.followup.send(f"✅ {игрок.mention} повышен до **{new_role.mention if new_role else STAFF_NAMES[current_idx + 1]}**!", ephemeral=True)


@bot.tree.command(name="понизить", description="Понизить игрока")
@app_commands.describe(игрок="Упомяните игрока")
async def demote(interaction: discord.Interaction, игрок: discord.Member):
    user_role_ids = [role.id for role in interaction.user.roles]
    if not any(role_id in ALLOWED_COMMAND_ROLES for role_id in user_role_ids):
        await interaction.response.send_message("❌ У вас нет прав для использования этой команды.", ephemeral=True)
        return

    await interaction.response.defer(ephemeral=True)

    guild = interaction.guild
    member_role_ids = [r.id for r in игрок.roles]

    current_idx = -1
    for i, rid in enumerate(STAFF_ROLES):
        if rid in member_role_ids:
            current_idx = i

    if current_idx == -1:
        await interaction.followup.send("❌ У игрока нет штабной роли.", ephemeral=True)
        return
    if current_idx == 0:
        await interaction.followup.send("❌ У игрока минимальная роль.", ephemeral=True)
        return

    old_role = guild.get_role(STAFF_ROLES[current_idx])
    new_role = guild.get_role(STAFF_ROLES[current_idx - 1])

    if old_role:
        await игрок.remove_roles(old_role)
    if new_role:
        await игрок.add_roles(new_role)

    # Если понижают с Модератора (индекс 3) — снимаем доп. роль
    MODER_ROLE_ID = 1500525783456809101
    if current_idx == 3:
        moder_extra = guild.get_role(MODER_ROLE_ID)
        if moder_extra and moder_extra in игрок.roles:
            await игрок.remove_roles(moder_extra)

    # Очищаем канал отчётов игрока
    nick_lower = игрок.display_name.split("|")[0].strip().lower()
    for cat_id in STAFF_CATEGORIES:
        category = guild.get_channel(cat_id)
        if not category:
            continue
        for ch in category.channels:
            if nick_lower in ch.name.lower():
                try:
                    await ch.purge(limit=None)
                    print(f"[demote] Канал {ch.name} очищен")
                except Exception as e:
                    print(f"[demote] Ошибка очистки канала: {e}")
                break

    promo_ch = bot.get_channel(PROMOTION_CHANNEL)
    if promo_ch:
        embed = discord.Embed(title="⬇️ Понижение", color=0xE74C3C)
        embed.add_field(name="Игрок", value=игрок.mention, inline=True)
        embed.add_field(name="Новая роль", value=new_role.mention if new_role else STAFF_NAMES[current_idx - 1], inline=True)
        embed.set_footer(text=f"Понизил: {interaction.user.name}")
        await promo_ch.send(
            content=f"{игрок.mention} был понижен до {new_role.mention if new_role else STAFF_NAMES[current_idx - 1]}",
            embed=embed
        )

    await update_roster_leaderboard()
    await interaction.followup.send(f"✅ {игрок.mention} понижен до **{new_role.mention if new_role else STAFF_NAMES[current_idx - 1]}**!", ephemeral=True)


# ─── АТТЕСТАЦИЯ ───────────────────────────────────────────────────────────────

ATTEST_CHANNEL = 1504472739250176070
ATTEST_PASS_CHANNEL = 1504483633657020416
ATTEST_ROLE_REMOVE = 1500525783456809101
ATTEST_ROLE_ADD = 1476242135748448276
ATTEST_PING_ROLE = 1198613123561685104

# Счётчик попыток аттестации: {user_id: count}
attest_attempts: dict[int, int] = {}


@bot.tree.command(name="аттестация", description="Провести аттестацию игрока")
@app_commands.describe(
    игрок="Упомяните игрока",
    вердикт="Одобрено или Отказано",
    вредоносных="Сколько нашел вредоносных ПО (1-10)",
)
@app_commands.choices(вердикт=[
    app_commands.Choice(name="Одобрено", value="approved"),
    app_commands.Choice(name="Отказано", value="rejected"),
])
async def attestation(
    interaction: discord.Interaction,
    игрок: discord.Member,
    вердикт: app_commands.Choice[str],
    вредоносных: app_commands.Range[int, 1, 10],
):
    user_role_ids = [role.id for role in interaction.user.roles]
    if not any(role_id in ALLOWED_COMMAND_ROLES + HIRE_HELPER_ROLES for role_id in user_role_ids):
        await interaction.response.send_message("❌ У вас нет прав.", ephemeral=True)
        return

    await interaction.response.send_message(
        "📎 Отправь скриншот с аттестации в этот канал в течение **60 секунд**.\nЕсли скриншота нет — напиши `-`",
        ephemeral=False
    )

    # Ждём скриншот от пользователя
    def check(m):
        return m.author.id == interaction.user.id and m.channel.id == interaction.channel_id

    try:
        msg = await bot.wait_for("message", timeout=60.0, check=check)
        screenshot_url = msg.attachments[0].url if msg.attachments else None
        # Удаляем сообщение со скриншотом и подсказку
        try:
            await msg.delete()
        except Exception:
            pass
    except asyncio.TimeoutError:
        await interaction.channel.send("⏰ Время вышло, аттестация отменена.", delete_after=5)
        return

    guild = interaction.guild

    # Считаем попытки
    attest_attempts[игрок.id] = attest_attempts.get(игрок.id, 0) + 1
    attempts = attest_attempts[игрок.id]
    attempts_left = max(0, 3 - attempts + 1)

    approved = вердикт.value == "approved"
    вердикт_текст = "✅ Одобрено" if approved else "❌ Отказано"

    # Пишем в канал аттестации
    attest_ch = bot.get_channel(ATTEST_CHANNEL)
    if attest_ch:
        embed = discord.Embed(
            title="📋 Аттестация",
            color=0x57F287 if approved else 0xED4245
        )
        embed.add_field(name="1. Никнейм", value=игрок.mention, inline=False)
        embed.add_field(name="2. Вердикт", value=вердикт_текст, inline=True)
        embed.add_field(name="3. Вредоносных ПО", value=f"**{вредоносных}**", inline=True)
        embed.add_field(name="4. Осталось попыток", value=f"**{attempts_left}/3**", inline=True)
        embed.add_field(name="5. Провёл аттестацию", value=interaction.user.mention, inline=False)
        embed.set_footer(text=f"ID игрока: {игрок.id}")
        if screenshot_url:
            embed.set_image(url=screenshot_url)
        await attest_ch.send(embed=embed)

    if approved:
        role_remove = guild.get_role(ATTEST_ROLE_REMOVE)
        role_add = guild.get_role(ATTEST_ROLE_ADD)
        if role_remove and role_remove in игрок.roles:
            await игрок.remove_roles(role_remove)
        if role_add:
            await игрок.add_roles(role_add)
        attest_attempts.pop(игрок.id, None)

        pass_ch = bot.get_channel(ATTEST_PASS_CHANNEL)
        if pass_ch:
            await pass_ch.send(f"<@&{ATTEST_PING_ROLE}> {игрок.mention} был аттестирован ✅")

    await interaction.channel.send(f"✅ Аттестация для {игрок.mention} записана.", delete_after=5)


# ─── HELPER ROLES ─────────────────────────────────────────────────────────────

HELPER_ROLES_ALWAYS = [
    1499821941647872061,
    1429895978931978278,  # Хелпер (штатная роль)
    1476242632031080623,
    1467285060523790528,
    1467284797692055657,
    1467285307064848468,
    1467284992873861192,
]
HELPER_ROLE_GRIEF_1 = 1434471470326747146
HELPER_ROLE_GRIEF_2 = 1471547081196835018
HELPER_ROLE_REMOVE  = 1429895978931978276  # роль которая снимается

# Роли с доступом к команде /хелпер (помимо ALLOWED_COMMAND_ROLES)
HIRE_HELPER_ROLES = [1452006848570982551]


@bot.tree.command(name="хелпер", description="Принять игрока на должность хелпера")
@app_commands.describe(
    игрок="Упомяните игрока",
    ник="Ник в Minecraft",
    имя="Имя (отображается в нике)",
    гриф="Тип грифа: 1 или 2"
)
@app_commands.choices(гриф=[
    app_commands.Choice(name="1", value=1),
    app_commands.Choice(name="2", value=2),
])
async def hire_helper(
    interaction: discord.Interaction,
    игрок: discord.Member,
    ник: str,
    имя: str,
    гриф: app_commands.Choice[int]
):
    user_role_ids = [role.id for role in interaction.user.roles]
    allowed = ALLOWED_COMMAND_ROLES + HIRE_HELPER_ROLES
    if not any(role_id in allowed for role_id in user_role_ids):
        await interaction.response.send_message("❌ У вас нет прав для использования этой команды.", ephemeral=True)
        return

    await interaction.response.defer(ephemeral=True)
    guild = interaction.guild
    errors = []

    # 1. Снять роль
    role_to_remove = guild.get_role(HELPER_ROLE_REMOVE)
    if role_to_remove and role_to_remove in игрок.roles:
        try:
            await игрок.remove_roles(role_to_remove)
        except Exception as e:
            errors.append(f"Не удалось снять роль {HELPER_ROLE_REMOVE}: {e}")

    # 2. Выдать постоянные роли
    for rid in HELPER_ROLES_ALWAYS:
        role = guild.get_role(rid)
        if role:
            try:
                await игрок.add_roles(role)
            except Exception as e:
                errors.append(f"Не удалось выдать роль {rid}: {e}")

    # 3. Выдать роль грифа
    grief_role_id = HELPER_ROLE_GRIEF_1 if гриф.value == 1 else HELPER_ROLE_GRIEF_2
    grief_role = guild.get_role(grief_role_id)
    if grief_role:
        try:
            await игрок.add_roles(grief_role)
        except Exception as e:
            errors.append(f"Не удалось выдать роль грифа: {e}")

    # 4. Сменить никнейм
    new_nick = f"{ник} | {имя}"
    try:
        await игрок.edit(nick=new_nick)
    except Exception as e:
        errors.append(f"Не удалось сменить ник: {e}")

    # 5. Создать канал в категории хелперов
    helper_category = guild.get_channel(STAFF_CATEGORIES[0])  # категория Хелперов
    new_channel = None
    if helper_category and isinstance(helper_category, discord.CategoryChannel):
        try:
            # Права: игрок видит и пишет, остальные — по умолчанию категории
            overwrites = dict(helper_category.overwrites)
            overwrites[игрок] = discord.PermissionOverwrite(
                view_channel=True,
                send_messages=True,
                read_message_history=True
            )
            new_channel = await guild.create_text_channel(
                name=ник,
                category=helper_category,
                overwrites=overwrites
            )
        except Exception as e:
            errors.append(f"Не удалось создать канал: {e}")
    else:
        errors.append("Категория хелперов не найдена.")

    # 6. Пингануть игрока в новом канале
    if new_channel:
        try:
            await new_channel.send(f"{игрок.mention}, добро пожаловать в команду! 🎉")
        except Exception as e:
            errors.append(f"Не удалось отправить сообщение в канал: {e}")

    # Итог
    if errors:
        err_text = "\n".join(f"⚠️ {e}" for e in errors)
        await interaction.followup.send(
            f"✅ Хелпер **{new_nick}** принят, но возникли ошибки:\n{err_text}",
            ephemeral=True
        )
    else:
        await interaction.followup.send(
            f"✅ **{игрок.mention}** принят как хелпер!\n"
            f"Ник: `{new_nick}` | Гриф: **{гриф.value}**\n"
            f"Канал: {new_channel.mention if new_channel else '—'}",
            ephemeral=True
        )


@bot.tree.command(name="посчитать", description="Посчитать наказания игрока по скриншотам в канале")
@app_commands.describe(игрок="Упомяните игрока", с_даты="С какого числа считать (формат: ДД.ММ.ГГГГ)")
async def count_punishments(interaction: discord.Interaction, игрок: discord.Member, с_даты: str):
    user_role_ids = [role.id for role in interaction.user.roles]
    if not any(role_id in ALLOWED_COMMAND_ROLES for role_id in user_role_ids):
        await interaction.response.send_message("❌ У вас нет прав для использования этой команды.", ephemeral=True)
        return

    await interaction.response.defer(ephemeral=False)

    from datetime import datetime, timezone
    try:
        date_from = datetime.strptime(с_даты, "%d.%m.%Y").replace(tzinfo=timezone.utc)
    except ValueError:
        await interaction.followup.send("❌ Неверный формат даты. Используй: ДД.ММ.ГГГГ (например 01.05.2026)", ephemeral=True)
        return

    # Ищем канал по display_name игрока (часть до |)
    target_channel = None
    nick_lower = игрок.display_name.split("|")[0].strip().lower()
    for cat_id in STAFF_CATEGORIES:
        category = interaction.guild.get_channel(cat_id)
        if not category:
            continue
        for ch in category.channels:
            if nick_lower in ch.name.lower():
                target_channel = ch
                break
        if target_channel:
            break

    if not target_channel:
        await interaction.followup.send(f"❌ Канал игрока **{игрок.display_name}** не найден.", ephemeral=True)
        return

    # Считаем сообщения со скриншотами (вложениями)
    count = 0
    try:
        async for msg in target_channel.history(limit=5000, after=date_from):
            if msg.attachments:
                count += len(msg.attachments)
    except Exception as e:
        await interaction.followup.send(f"❌ Ошибка при чтении канала: {e}", ephemeral=True)
        return

    embed = discord.Embed(title="📊 Подсчёт наказаний", color=0x5865F2)
    embed.add_field(name="👤 Игрок", value=игрок.mention, inline=True)
    embed.add_field(name="� С даты", value=f"**{с_даты}**", inline=True)
    embed.add_field(name="⚠️ Наказаний", value=f"**{count}**", inline=True)
    embed.add_field(name="� Канал", value=target_channel.mention, inline=False)
    embed.set_footer(text=f"Проверил: {interaction.user}")
    await interaction.followup.send(embed=embed)


@bot.tree.command(name="обновитьлидерборд", description="Обновить таблицу баллов вручную")
async def update_leaderboard_command(interaction: discord.Interaction):
    user_role_ids = [role.id for role in interaction.user.roles]
    if not any(role_id in ALLOWED_COMMAND_ROLES for role_id in user_role_ids):
        await interaction.response.send_message("❌ У вас нет прав для использования этой команды.", ephemeral=True)
        return
    await interaction.response.defer(ephemeral=True)
    await update_leaderboard()
    await interaction.followup.send("✅ Таблица баллов обновлена!", ephemeral=True)


@bot.tree.command(name="отгулы_обновить", description="Обновить таблицу отгулов вручную")
async def update_dayoff_leaderboard_command(interaction: discord.Interaction):
    user_role_ids = [role.id for role in interaction.user.roles]
    if not any(role_id in ALLOWED_COMMAND_ROLES for role_id in user_role_ids):
        await interaction.response.send_message("❌ У вас нет прав для использования этой команды.", ephemeral=True)
        return
    await interaction.response.defer(ephemeral=True)
    await update_dayoff_leaderboard()
    await interaction.followup.send("✅ Таблица отгулов обновлена!", ephemeral=True)


@bot.tree.command(name="варны_обновить", description="Обновить список варнов вручную")
async def update_warn_leaderboard_command(interaction: discord.Interaction):
    user_role_ids = [role.id for role in interaction.user.roles]
    if not any(role_id in ALLOWED_COMMAND_ROLES for role_id in user_role_ids):
        await interaction.response.send_message("❌ У вас нет прав для использования этой команды.", ephemeral=True)
        return
    await interaction.response.defer(ephemeral=True)
    await update_warn_leaderboard()
    await interaction.followup.send("✅ Список варнов обновлен!", ephemeral=True)


@bot.tree.command(name="устники_обновить", description="Обновить список устников вручную")
async def update_mute_leaderboard_command(interaction: discord.Interaction):
    user_role_ids = [role.id for role in interaction.user.roles]
    if not any(role_id in ALLOWED_COMMAND_ROLES for role_id in user_role_ids):
        await interaction.response.send_message("❌ У вас нет прав для использования этой команды.", ephemeral=True)
        return
    await interaction.response.defer(ephemeral=True)
    await update_mute_leaderboard()
    await interaction.followup.send("✅ Список устников обновлен!", ephemeral=True)


@bot.tree.command(name="состав_обновить", description="Обновить список состава вручную")
async def update_roster_command(interaction: discord.Interaction):
    user_role_ids = [role.id for role in interaction.user.roles]
    if not any(role_id in ALLOWED_COMMAND_ROLES for role_id in user_role_ids):
        await interaction.response.send_message("❌ У вас нет прав для использования этой команды.", ephemeral=True)
        return
    await interaction.response.defer(ephemeral=True)
    await update_roster_leaderboard()
    await interaction.followup.send("✅ Список состава обновлен!", ephemeral=True)


@bot.tree.command(name="отгул_снять", description="Снять отгул у игрока досрочно")
@app_commands.describe(игрок="Упомяните игрока")
async def remove_dayoff_command(interaction: discord.Interaction, игрок: discord.Member):
    user_role_ids = [role.id for role in interaction.user.roles]
    if not any(role_id in ALLOWED_COMMAND_ROLES for role_id in user_role_ids):
        await interaction.response.send_message("❌ У вас нет прав для использования этой команды.", ephemeral=True)
        return
    await interaction.response.defer(ephemeral=True)
    
    guild = interaction.guild
    dayoff_role = guild.get_role(DAYOFF_ROLE)
    if dayoff_role and dayoff_role in игрок.roles:
        await игрок.remove_roles(dayoff_role)
    
    db.remove_dayoff(игрок.id)
    await update_dayoff_leaderboard()
    await interaction.followup.send(f"✅ Отгул снят у {игрок.mention}.", ephemeral=True)


@bot.tree.command(name="отгул_выдать", description="Выдать отгул игроку")
@app_commands.describe(игрок="Упомяните игрока", дни="Количество дней отгула")
async def give_dayoff_command(interaction: discord.Interaction, игрок: discord.Member, дни: int):
    user_role_ids = [role.id for role in interaction.user.roles]
    if not any(role_id in ALLOWED_COMMAND_ROLES for role_id in user_role_ids):
        await interaction.response.send_message("❌ У вас нет прав для использования этой команды.", ephemeral=True)
        return
    await interaction.response.defer(ephemeral=True)
    
    if дни <= 0:
        await interaction.followup.send("❌ Количество дней должно быть больше 0.", ephemeral=True)
        return
    
    guild = interaction.guild
    dayoff_role = guild.get_role(DAYOFF_ROLE)
    if dayoff_role:
        await игрок.add_roles(dayoff_role)
    
    from datetime import datetime, timedelta
    start_date = datetime.now()
    end_date = start_date + timedelta(days=дни)
    start_str = start_date.strftime("%d.%m.%Y")
    end_str = end_date.strftime("%d.%m.%Y")
    
    db.set_dayoff(игрок.id, start_str, end_str, дни)
    await update_dayoff_leaderboard()
    asyncio.create_task(schedule_dayoff_removal(игрок.id, дни))
    
    await interaction.followup.send(
        f"✅ Отгул выдан {игрок.mention} на **{дни} дней** (до {end_str}).\n"
        f"Роль будет автоматически снята через {дни} дней.",
        ephemeral=True
    )


@bot.tree.command(name="тест_лидерборд", description="Тестовая команда для проверки лидербордов")
async def test_leaderboard(interaction: discord.Interaction):
    user_role_ids = [role.id for role in interaction.user.roles]
    if not any(role_id in ALLOWED_COMMAND_ROLES for role_id in user_role_ids):
        await interaction.response.send_message("❌ У вас нет прав для использования этой команды.", ephemeral=True)
        return
    await interaction.response.defer(ephemeral=True)
    
    channel = bot.get_channel(LEADERBOARD_CHANNEL)
    if not channel:
        await interaction.followup.send(f"❌ Канал {LEADERBOARD_CHANNEL} не найден!", ephemeral=True)
        return
    
    await interaction.followup.send(f"✅ Канал найден: {channel.name}\nОбновляю лидерборды...", ephemeral=True)
    await update_leaderboard()
    await update_dayoff_leaderboard()
    await interaction.followup.send("✅ Лидерборды обновлены!", ephemeral=True)


@bot.tree.command(name="создать_лидерборд", description="Принудительно создать лидерборд с тестовыми данными")
async def force_create_leaderboard(interaction: discord.Interaction):
    user_role_ids = [role.id for role in interaction.user.roles]
    if not any(role_id in ALLOWED_COMMAND_ROLES for role_id in user_role_ids):
        await interaction.response.send_message("❌ У вас нет прав для использования этой команды.", ephemeral=True)
        return
    await interaction.response.defer(ephemeral=True)
    
    channel = bot.get_channel(LEADERBOARD_CHANNEL)
    if not channel:
        await interaction.followup.send(f"❌ Канал {LEADERBOARD_CHANNEL} не найден!", ephemeral=True)
        return
    
    embed = discord.Embed(
        title="🏆 Таблица баллов",
        description="Список всех игроков с баллами, сгруппированных по ролям",
        color=0xF1C40F
    )
    embed.add_field(name="Пусто", value="Пока нет игроков с баллами", inline=False)
    embed.set_footer(text="Обновляется автоматически")
    msg = await channel.send(embed=embed)
    await interaction.followup.send(f"✅ Лидерборд создан в канале {channel.mention}!\nID сообщения: {msg.id}", ephemeral=True)


# ─── VIEWS ────────────────────────────────────────────────────────────────────

class ReviewView(discord.ui.View):
    def __init__(self, author_id: int, source_thread_id: int | None = None):
        super().__init__(timeout=None)
        self.author_id = author_id
        self.source_thread_id = source_thread_id

    @discord.ui.button(label="✅ Одобрить", style=discord.ButtonStyle.success)
    async def approve(self, interaction: discord.Interaction, button: discord.ui.Button):
        view = SelectTypeView(
            author_id=self.author_id,
            review_message=interaction.message,
            source_thread_id=self.source_thread_id
        )
        await interaction.response.send_message("Выберите тип:", view=view, ephemeral=True)

    @discord.ui.button(label="❌ Отклонить", style=discord.ButtonStyle.danger)
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
        await interaction.response.defer(ephemeral=True)
        guild = interaction.guild
        member = guild.get_member(self.author_id)

        embed = discord.Embed(title="❌ Заявка отклонена", color=0xED4245)
        embed.add_field(name="Игрок", value=member.mention if member else f"<@{self.author_id}>", inline=True)
        embed.add_field(name="Причина", value=str(self.reason), inline=False)
        embed.set_footer(text=f"Отклонил: {interaction.user}")

        await post_to_forum(guild, embed, f"Отклонено — {member or self.author_id}")
        await disable_buttons(self.review_message)
        await set_thread_tag(WATCH_CHANNEL, self.source_thread_id, TAGS_POINTS, "rejected")
        await notify_author_in_thread(
            self.source_thread_id, self.author_id,
            approved=False, details=str(self.reason), admin_name=str(interaction.user)
        )
        await interaction.followup.send("✅ Заявка отклонена.", ephemeral=True)


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
        await interaction.response.defer(ephemeral=True)
        try:
            count = int(str(self.punishments))
        except ValueError:
            await interaction.followup.send("❌ Введите число.", ephemeral=True)
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

        embed_review = discord.Embed(title="✅ Баллы начислены", color=0x57F287)
        embed_review.add_field(name="Игрок", value=member.mention if member else f"<@{self.author_id}>", inline=True)
        embed_review.add_field(name="Наказаний", value=str(count), inline=True)
        embed_review.add_field(name="Начислено", value=f"+{points} 🪙", inline=True)
        embed_review.add_field(name="Новый баланс", value=f"{new_total} 🪙", inline=True)
        embed_review.set_footer(text=f"Обработал: {interaction.user}")
        await bot.get_channel(REVIEW_CHANNEL).send(embed=embed_review)

        await disable_buttons(self.review_message)
        await set_thread_tag(WATCH_CHANNEL, self.source_thread_id, TAGS_POINTS, "approved")
        await notify_author_in_thread(
            self.source_thread_id, self.author_id,
            approved=True,
            details=f"Начислено **+{points} 🪙**\nНовый баланс: **{new_total} 🪙**",
            admin_name=str(interaction.user)
        )
        await interaction.followup.send("✅ Баллы начислены!", ephemeral=True)
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
            await interaction.response.send_message("❌ Не удалось найти игрока на сервере.", ephemeral=True)
            return

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
                await interaction.followup.send(f"❌ Произошла ошибка: `{e}`", ephemeral=True)
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
        await interaction.response.defer(ephemeral=True)
        try:
            qty = int(str(self.qty_input))
        except ValueError:
            await interaction.followup.send("❌ Введите число.", ephemeral=True)
            return

        guild = interaction.guild
        member = guild.get_member(self.author_id)
        if member is None:
            await interaction.followup.send("❌ Не удалось найти игрока на сервере.", ephemeral=True)
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
                await interaction.followup.send(f"✅ **{item_name}** — списано {cost} 🪙", ephemeral=True)
        except Exception as e:
            print(f"[QuantityModal] Ошибка: {e}")
            await interaction.followup.send(f"❌ Ошибка: `{e}`", ephemeral=True)


# ─── HANDLERS ─────────────────────────────────────────────────────────────────

async def deduct_and_notify(interaction, member, cost, item_name, description, review_message, extra_fields=None, source_thread_id=None):
    current = db.get_points(member.id)
    if cost > 0 and current < cost:
        await interaction.followup.send(f"❌ Недостаточно баллов. Нужно: {cost}, есть: {current}", ephemeral=True)
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

    embed_review = discord.Embed(title=f"✅ Покупка: {item_name}", color=0x57F287)
    embed_review.add_field(name="Игрок", value=member.mention, inline=True)
    embed_review.add_field(name="Списано", value=f"-{cost} 🪙", inline=True)
    embed_review.add_field(name="Новый баланс", value=f"{new_total} 🪙", inline=True)
    embed_review.set_footer(text=f"Обработал: {interaction.user}")
    await bot.get_channel(REVIEW_CHANNEL).send(embed=embed_review)

    await disable_buttons(review_message)
    await set_thread_tag(WATCH_CHANNEL, source_thread_id, TAGS_POINTS, "approved")

    details_parts = [f"**{item_name}**"]
    if description:
        details_parts.append(description)
    if extra_fields:
        for name, value in extra_fields:
            details_parts.append(f"{name}: {value}")
    details_parts.append(f"Списано: **-{cost} 🪙** | Баланс: **{new_total} 🪙**")

    await notify_author_in_thread(
        source_thread_id, member.id,
        approved=True,
        details="\n".join(details_parts),
        admin_name=str(interaction.user)
    )
    await update_leaderboard()
    return True


async def process_simple(interaction, member, cost, item_name, description, review_message, source_thread_id=None):
    success = await deduct_and_notify(interaction, member, cost, item_name, description, review_message, source_thread_id=source_thread_id)
    if success:
        await interaction.followup.send(f"✅ **{item_name}** обработана.", ephemeral=True)


async def process_warn_remove(interaction, member, review_message, source_thread_id=None):
    guild = interaction.guild
    member_role_ids = [r.id for r in member.roles]
    warn_count = sum(1 for rid in WARN_ROLES if rid in member_role_ids)

    if warn_count == 0:
        await interaction.followup.send("❌ У игрока нет варнов.", ephemeral=True)
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
            embed = discord.Embed(
                description=f"{member.mention} снял варн 🚫 **{new_count}/3** | Покупка в магазине",
                color=0xED4245
            )
            embed.set_author(name="🚫 Снятие варна")
            await announce_ch.send(embed=embed)
        await update_warn_leaderboard()
        await interaction.followup.send("✅ Варн снят.", ephemeral=True)


async def process_mute_remove(interaction, member, review_message, source_thread_id=None):
    guild = interaction.guild
    member_role_ids = [r.id for r in member.roles]
    mute_count = sum(1 for rid in MUTE_ROLES if rid in member_role_ids)

    if mute_count == 0:
        await interaction.followup.send("❌ У игрока нет устников.", ephemeral=True)
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
            embed = discord.Embed(
                description=f"{member.mention} снял устник 🔇 **{new_count}/2** | Покупка в магазине",
                color=0xF1C40F
            )
            embed.set_author(name="🔇 Снятие устника")
            await announce_ch.send(embed=embed)
        await update_mute_leaderboard()
        await interaction.followup.send("✅ Устник снят.", ephemeral=True)


async def process_promotion(interaction, member, review_message, source_thread_id=None):
    guild = interaction.guild
    member_role_ids = [r.id for r in member.roles]

    current_idx = -1
    for i, rid in enumerate(STAFF_ROLES):
        if rid in member_role_ids:
            current_idx = i

    if current_idx == -1:
        await interaction.followup.send("❌ У игрока нет штабной роли.", ephemeral=True)
        return
    if current_idx >= len(STAFF_ROLES) - 1:
        await interaction.followup.send("❌ У игрока максимальная роль.", ephemeral=True)
        return

    old_role = guild.get_role(STAFF_ROLES[current_idx])
    new_role = guild.get_role(STAFF_ROLES[current_idx + 1])

    if old_role:
        await member.remove_roles(old_role)
    if new_role:
        await member.add_roles(new_role)

    success = await deduct_and_notify(
        interaction, member, 500, "⬆️ Повышение без нормы", "",
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
        await interaction.followup.send("✅ Повышение выполнено.", ephemeral=True)


async def process_bonus(interaction, member, role_id, item_name, cost, review_message, source_thread_id=None):
    guild = interaction.guild
    role = guild.get_role(role_id)
    if role:
        await member.add_roles(role)
    success = await deduct_and_notify(interaction, member, cost, item_name, "", review_message, source_thread_id=source_thread_id)
    if success:
        await interaction.followup.send(f"✅ **{item_name}** выдан.", ephemeral=True)


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

    @discord.ui.button(label="✅ Одобрить", style=discord.ButtonStyle.success)
    async def approve(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)
        await notify_in_thread(
            SALARY_FORUM, self.source_thread_id, self.author_id,
            approved=True,
            title="✅ Заявка на зарплату одобрена",
            details="Для выдачи зарплаты обратитесь к администрации.",
            admin_name=str(interaction.user)
        )
        await disable_buttons(interaction.message)
        await set_thread_tag(SALARY_FORUM, self.source_thread_id, TAGS_SALARY, "approved")
        await interaction.followup.send("✅ Заявка на зарплату одобрена.", ephemeral=True)

    @discord.ui.button(label="❌ Отклонить", style=discord.ButtonStyle.danger)
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
            SALARY_FORUM, self.source_thread_id, self.author_id,
            approved=False,
            title="❌ Заявка на зарплату отклонена",
            details=str(self.reason),
            admin_name=str(interaction.user)
        )
        await disable_buttons(self.review_message)
        await set_thread_tag(SALARY_FORUM, self.source_thread_id, TAGS_SALARY, "rejected")
        await interaction.followup.send("✅ Заявка отклонена.", ephemeral=True)


# ─── DAY OFF APPLICATION VIEWS ────────────────────────────────────────────────

class DayoffReviewView(discord.ui.View):
    def __init__(self, author_id: int, source_thread_id: int):
        super().__init__(timeout=None)
        self.author_id = author_id
        self.source_thread_id = source_thread_id

    @discord.ui.button(label="✅ Одобрить", style=discord.ButtonStyle.success)
    async def approve(self, interaction: discord.Interaction, button: discord.ui.Button):
        modal = DayoffApproveModal(
            author_id=self.author_id,
            review_message=interaction.message,
            source_thread_id=self.source_thread_id
        )
        await interaction.response.send_modal(modal)

    @discord.ui.button(label="❌ Отклонить", style=discord.ButtonStyle.danger)
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
            await interaction.followup.send("❌ Введите число.", ephemeral=True)
            return

        if days_count <= 0:
            await interaction.followup.send("❌ Количество дней должно быть больше 0.", ephemeral=True)
            return

        guild = interaction.guild
        member = guild.get_member(self.author_id)
        if not member:
            await interaction.followup.send("❌ Игрок не найден на сервере.", ephemeral=True)
            return

        dayoff_role = guild.get_role(DAYOFF_ROLE)
        if dayoff_role:
            await member.add_roles(dayoff_role)

        from datetime import datetime, timedelta
        start_date = datetime.now()
        end_date = start_date + timedelta(days=days_count)
        start_str = start_date.strftime("%d.%m.%Y")
        end_str = end_date.strftime("%d.%m.%Y")

        db.set_dayoff(self.author_id, start_str, end_str, days_count)
        await disable_buttons(self.review_message)
        await set_thread_tag(DAYOFF_FORUM, self.source_thread_id, TAGS_DAYOFF, "approved")
        await notify_in_thread(
            DAYOFF_FORUM, self.source_thread_id, self.author_id,
            approved=True,
            title="✅ Заявка на отгул одобрена",
            details=f"Отгул выдан на **{days_count} дней**\nС {start_str} по {end_str}",
            admin_name=str(interaction.user)
        )
        await update_dayoff_leaderboard()
        asyncio.create_task(schedule_dayoff_removal(self.author_id, days_count))
        await interaction.followup.send(f"✅ Отгул одобрен на **{days_count} дней** (до {end_str}). Роль выдана.", ephemeral=True)
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
            DAYOFF_FORUM, self.source_thread_id, self.author_id,
            approved=False,
            title="❌ Заявка на отгул отклонена",
            details=str(self.reason),
            admin_name=str(interaction.user)
        )
        await disable_buttons(self.review_message)
        await set_thread_tag(DAYOFF_FORUM, self.source_thread_id, TAGS_DAYOFF, "rejected")
        await interaction.followup.send("✅ Заявка отклонена.", ephemeral=True)


# ─── PROMOTION APPLICATION VIEWS ──────────────────────────────────────────────

class PromotionAppReviewView(discord.ui.View):
    def __init__(self, author_id: int, source_thread_id: int):
        super().__init__(timeout=None)
        self.author_id = author_id
        self.source_thread_id = source_thread_id

    @discord.ui.button(label="✅ Одобрить", style=discord.ButtonStyle.success)
    async def approve(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)
        guild = interaction.guild
        member = guild.get_member(self.author_id)

        if not member:
            await interaction.followup.send("❌ Игрок не найден на сервере.", ephemeral=True)
            return

        member_role_ids = [r.id for r in member.roles]
        current_idx = -1
        for i, rid in enumerate(STAFF_ROLES):
            if rid in member_role_ids:
                current_idx = i

        if current_idx == -1:
            await interaction.followup.send("❌ У игрока нет штабной роли.", ephemeral=True)
            return
        if current_idx >= len(STAFF_ROLES) - 1:
            await interaction.followup.send("❌ У игрока максимальная роль.", ephemeral=True)
            return

        old_role = guild.get_role(STAFF_ROLES[current_idx])
        new_role = guild.get_role(STAFF_ROLES[current_idx + 1])

        if old_role:
            await member.remove_roles(old_role)
        if new_role:
            await member.add_roles(new_role)

        promo_ch = bot.get_channel(PROMOTION_CHANNEL)
        if promo_ch:
            await promo_ch.send(
                f"{member.mention} Был повышен до {new_role.mention if new_role else STAFF_NAMES[current_idx + 1]}\n"
                f"Поздравим его! 🎉🎉🎉"
            )

        await notify_in_thread(
            PROMO_APP_FORUM, self.source_thread_id, self.author_id,
            approved=True,
            title="✅ Заявка на повышение одобрена",
            details=f"Вы повышены до {new_role.mention if new_role else STAFF_NAMES[current_idx + 1]}!",
            admin_name=str(interaction.user)
        )
        await disable_buttons(interaction.message)
        await set_thread_tag(PROMO_APP_FORUM, self.source_thread_id, TAGS_PROMO, "approved")
        await interaction.followup.send(f"✅ {member.mention} повышен до **{new_role.mention if new_role else STAFF_NAMES[current_idx + 1]}**!", ephemeral=True)

    @discord.ui.button(label="❌ Отклонить", style=discord.ButtonStyle.danger)
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
            PROMO_APP_FORUM, self.source_thread_id, self.author_id,
            approved=False,
            title="❌ Заявка на повышение отклонена",
            details=str(self.reason),
            admin_name=str(interaction.user)
        )
        await disable_buttons(self.review_message)
        await set_thread_tag(PROMO_APP_FORUM, self.source_thread_id, TAGS_PROMO, "rejected")
        await interaction.followup.send("✅ Заявка отклонена.", ephemeral=True)


# ─── APPEAL VIEWS ─────────────────────────────────────────────────────────────

class AppealReviewView(discord.ui.View):
    def __init__(self, author_id: int, source_thread_id: int):
        super().__init__(timeout=None)
        self.author_id = author_id
        self.source_thread_id = source_thread_id

    @discord.ui.button(label="✅ Одобрить", style=discord.ButtonStyle.success)
    async def approve(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Показываем выбор: снять варн или устник
        view = AppealApproveTypeView(
            author_id=self.author_id,
            review_message=interaction.message,
            source_thread_id=self.source_thread_id
        )
        await interaction.response.send_message("Что снять?", view=view, ephemeral=True)

    @discord.ui.button(label="❌ Отклонить", style=discord.ButtonStyle.danger)
    async def reject(self, interaction: discord.Interaction, button: discord.ui.Button):
        modal = AppealRejectModal(
            author_id=self.author_id,
            review_message=interaction.message,
            source_thread_id=self.source_thread_id
        )
        await interaction.response.send_modal(modal)


class AppealApproveTypeView(discord.ui.View):
    def __init__(self, author_id: int, review_message: discord.Message, source_thread_id: int):
        super().__init__(timeout=60)
        self.author_id = author_id
        self.review_message = review_message
        self.source_thread_id = source_thread_id

    @discord.ui.button(label="⚠️ Снять варн", style=discord.ButtonStyle.primary)
    async def remove_warn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)
        guild = interaction.guild
        member = guild.get_member(self.author_id)
        if not member:
            await interaction.followup.send("❌ Игрок не найден.", ephemeral=True)
            return

        member_role_ids = [r.id for r in member.roles]
        warn_count = sum(1 for rid in WARN_ROLES if rid in member_role_ids)
        if warn_count == 0:
            await interaction.followup.send("❌ У игрока нет варнов.", ephemeral=True)
            return

        role_to_remove = guild.get_role(WARN_ROLES[warn_count - 1])
        if role_to_remove:
            await member.remove_roles(role_to_remove)
        new_count = warn_count - 1

        warn_ch = bot.get_channel(WARN_ANNOUNCE_CHANNEL)
        if warn_ch:
            embed = discord.Embed(
                title="⚖️ Обжалование варна одобрено",
                description=f"{member.mention} — варн снят по обжалованию",
                color=0x57F287
            )
            embed.add_field(name="Варны", value=f"**{new_count}/3**", inline=True)
            embed.add_field(name="Снял", value=interaction.user.mention, inline=True)
            embed.set_thumbnail(url=member.display_avatar.url)
            await warn_ch.send(embed=embed)

        await notify_in_thread(
            APPEAL_FORUM, self.source_thread_id, self.author_id,
            approved=True,
            title="✅ Обжалование одобрено",
            details=f"Варн снят. Текущие варны: **{new_count}/3**",
            admin_name=str(interaction.user)
        )
        await disable_buttons(self.review_message)
        await set_thread_tag(APPEAL_FORUM, self.source_thread_id, TAGS_APPEAL, "approved")
        await update_warn_leaderboard()
        await interaction.followup.send(f"✅ Варн снят. Варны: **{new_count}/3**", ephemeral=True)

    @discord.ui.button(label="🔇 Снять устник", style=discord.ButtonStyle.secondary)
    async def remove_mute(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)
        guild = interaction.guild
        member = guild.get_member(self.author_id)
        if not member:
            await interaction.followup.send("❌ Игрок не найден.", ephemeral=True)
            return

        member_role_ids = [r.id for r in member.roles]
        mute_count = sum(1 for rid in MUTE_ROLES if rid in member_role_ids)
        if mute_count == 0:
            await interaction.followup.send("❌ У игрока нет устников.", ephemeral=True)
            return

        role_to_remove = guild.get_role(MUTE_ROLES[mute_count - 1])
        if role_to_remove:
            await member.remove_roles(role_to_remove)
        new_count = mute_count - 1

        mute_ch = bot.get_channel(WARN_ANNOUNCE_CHANNEL)
        if mute_ch:
            embed = discord.Embed(
                title="⚖️ Обжалование устника одобрено",
                description=f"{member.mention} — устник снят по обжалованию",
                color=0x57F287
            )
            embed.add_field(name="Устники", value=f"**{new_count}/2**", inline=True)
            embed.add_field(name="Снял", value=interaction.user.mention, inline=True)
            embed.set_thumbnail(url=member.display_avatar.url)
            await mute_ch.send(embed=embed)

        await notify_in_thread(
            APPEAL_FORUM, self.source_thread_id, self.author_id,
            approved=True,
            title="✅ Обжалование одобрено",
            details=f"Устник снят. Текущие устники: **{new_count}/2**",
            admin_name=str(interaction.user)
        )
        await disable_buttons(self.review_message)
        await set_thread_tag(APPEAL_FORUM, self.source_thread_id, TAGS_APPEAL, "approved")
        await update_mute_leaderboard()
        await interaction.followup.send(f"✅ Устник снят. Устники: **{new_count}/2**", ephemeral=True)


class AppealRejectModal(discord.ui.Modal, title="Причина отклонения"):
    reason = discord.ui.TextInput(label="Причина", style=discord.TextStyle.paragraph)

    def __init__(self, author_id: int, review_message: discord.Message, source_thread_id: int):
        super().__init__()
        self.author_id = author_id
        self.review_message = review_message
        self.source_thread_id = source_thread_id

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        await notify_in_thread(
            APPEAL_FORUM, self.source_thread_id, self.author_id,
            approved=False,
            title="❌ Обжалование отклонено",
            details=str(self.reason),
            admin_name=str(interaction.user)
        )
        await disable_buttons(self.review_message)
        await set_thread_tag(APPEAL_FORUM, self.source_thread_id, TAGS_APPEAL, "rejected")
        await interaction.followup.send("✅ Заявка отклонена.", ephemeral=True)


# ─── HELPER FOR THREAD NOTIFICATIONS ──────────────────────────────────────────

async def notify_in_thread(forum_id: int, thread_id: int, author_id: int, approved: bool, title: str, details: str, admin_name: str):
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
        embed = discord.Embed(title=title, description=f"<@{author_id}>, твоя заявка была **одобрена**. 🎉", color=0x57F287)
        embed.add_field(name="📌 Детали", value=details or "—", inline=False)
        embed.set_footer(text=f"Обработал: {admin_name}")
        embed.set_thumbnail(url=APPROVED_GIF)
    else:
        embed = discord.Embed(title=title, description=f"<@{author_id}>, твоя заявка была **отклонена**.", color=0xED4245)
        embed.add_field(name="📌 Причина", value=details or "Причина не указана", inline=False)
        embed.set_footer(text=f"Обработал: {admin_name}")
        embed.set_thumbnail(url=REJECTED_GIF)

    try:
        await thread.send(embed=embed)
    except Exception as e:
        print(f"[notify_in_thread] Ошибка: {e}")


# ─── LEADERBOARD ──────────────────────────────────────────────────────────────

async def update_roster_leaderboard():
    """Обновляет список состава — все участники со штатными ролями, сгруппированные по ролям."""
    try:
        channel = bot.get_channel(ROSTER_LEADERBOARD_CHANNEL)
        if not channel:
            print(f"[update_roster_leaderboard] Канал {ROSTER_LEADERBOARD_CHANNEL} не найден")
            return

        guild = channel.guild

        # Собираем участников по штатным ролям (от высшей к низшей)
        role_groups = {}
        for i, rid in enumerate(STAFF_ROLES):
            role = guild.get_role(rid)
            if not role:
                continue
            members = [m for m in role.members]
            if members:
                role_groups[i] = (role, members)

        embed = discord.Embed(
            title="👥 Состав команды",
            color=0x5865F2
        )

        # От высшей роли к низшей
        for i in reversed(range(len(STAFF_ROLES))):
            if i not in role_groups:
                continue
            role, members = role_groups[i]
            lines = [f"{idx + 1}. {m.mention}" for idx, m in enumerate(members)]
            embed.add_field(
                name=f"**{STAFF_NAMES[i]}** — {len(members)} чел.",
                value="\n".join(lines) or "—",
                inline=False
            )

        if not role_groups:
            embed.description = "Штат пуст."

        embed.set_footer(text="Обновляется автоматически")

        messages = [msg async for msg in channel.history(limit=10)]
        bot_messages = [
            msg for msg in messages
            if msg.author == bot.user and msg.embeds and msg.embeds[0].title == "👥 Состав команды"
        ]

        if bot_messages:
            try:
                await bot_messages[0].delete()
            except discord.errors.NotFound:
                pass
        await channel.send(embed=embed)
        print("[update_roster_leaderboard] Состав обновлён")

    except Exception as e:
        print(f"[update_roster_leaderboard] Ошибка: {e}")
        import traceback
        traceback.print_exc()


async def update_leaderboard():
    try:
        channel = bot.get_channel(LEADERBOARD_CHANNEL)
        if not channel:
            print(f"[update_leaderboard] Канал {LEADERBOARD_CHANNEL} не найден")
            return

        guild = channel.guild
        all_points = db.get_all_points()
        print(f"[update_leaderboard] Найдено {len(all_points)} записей в БД")

        role_groups = {}
        for user_id, points in all_points.items():
            member = guild.get_member(user_id)
            if not member:
                continue

            member_role_ids = [r.id for r in member.roles]
            role_name = "Без роли"
            for i, rid in enumerate(STAFF_ROLES):
                if rid in member_role_ids:
                    role_name = STAFF_NAMES[i]
                    break

            if role_name not in role_groups:
                role_groups[role_name] = []
            role_groups[role_name].append((member, points))

        for role_name in role_groups:
            role_groups[role_name].sort(key=lambda x: x[1], reverse=True)

        embed = discord.Embed(
            title="🏆 Таблица баллов",
            description="Список всех игроков с баллами, сгруппированных по ролям",
            color=0xF1C40F
        )

        role_order = STAFF_NAMES[::-1]
        has_players = False

        for role_name in role_order:
            if role_name not in role_groups:
                continue
            players_list = [f"{m.mention} — **{p}** 🪙" for m, p in role_groups[role_name]]
            if players_list:
                has_players = True
                embed.add_field(name=f"**{role_name}**", value="\n".join(players_list), inline=False)

        if "Без роли" in role_groups:
            players_list = [f"{m.mention} — **{p}** 🪙" for m, p in role_groups["Без роли"]]
            if players_list:
                has_players = True
                embed.add_field(name="**Без роли**", value="\n".join(players_list), inline=False)

        if not has_players:
            embed.add_field(name="Пусто", value="Пока нет игроков с баллами", inline=False)

        embed.set_footer(text="Обновляется автоматически")

        messages = [msg async for msg in channel.history(limit=10)]
        bot_messages = [msg for msg in messages if msg.author == bot.user and msg.embeds and msg.embeds[0].title == "🏆 Таблица баллов"]

        if bot_messages:
            await bot_messages[0].edit(embed=embed)
            print("[update_leaderboard] Лидерборд обновлен")
        else:
            await channel.send(embed=embed)
            print("[update_leaderboard] Лидерборд создан")

    except Exception as e:
        print(f"[update_leaderboard] Ошибка: {e}")
        import traceback
        traceback.print_exc()


async def update_dayoff_leaderboard():
    try:
        channel = bot.get_channel(DAYOFF_LEADERBOARD_CHANNEL)
        if not channel:
            print(f"[update_dayoff_leaderboard] Канал {DAYOFF_LEADERBOARD_CHANNEL} не найден")
            return

        guild = channel.guild
        all_dayoffs = db.get_all_dayoffs()
        print(f"[update_dayoff_leaderboard] Найдено {len(all_dayoffs)} отгулов в БД")

        if not all_dayoffs:
            messages = [msg async for msg in channel.history(limit=10)]
            bot_messages = [msg for msg in messages if msg.author == bot.user and msg.embeds and msg.embeds[0].title == "🏖️ Список отгулов"]
            if bot_messages:
                try:
                    await bot_messages[0].delete()
                except discord.errors.NotFound:
                    pass
            return

        embed = discord.Embed(title="🏖️ Список отгулов", description="Игроки, находящиеся в отгуле", color=0x3498DB)

        dayoff_list = []
        for user_id, dayoff_info in all_dayoffs.items():
            member = guild.get_member(user_id)
            if not member:
                continue
            start_date = dayoff_info.get("start_date", "?")
            end_date = dayoff_info.get("end_date", "?")
            dayoff_list.append(f"{member.mention}\n📅 С **{start_date}** по **{end_date}**")

        if dayoff_list:
            embed.add_field(name="Игроки в отгуле", value="\n\n".join(dayoff_list), inline=False)
        else:
            embed.add_field(name="Пусто", value="Нет игроков в отгуле", inline=False)

        embed.set_footer(text="Обновляется автоматически")

        messages = [msg async for msg in channel.history(limit=10)]
        bot_messages = [msg for msg in messages if msg.author == bot.user and msg.embeds and msg.embeds[0].title == "🏖️ Список отгулов"]

        if bot_messages:
            await bot_messages[0].edit(embed=embed)
        else:
            await channel.send(embed=embed)

    except Exception as e:
        print(f"[update_dayoff_leaderboard] Ошибка: {e}")
        import traceback
        traceback.print_exc()


async def update_warn_leaderboard():
    try:
        channel = bot.get_channel(WARN_LEADERBOARD_CHANNEL)
        if not channel:
            print(f"[update_warn_leaderboard] Канал {WARN_LEADERBOARD_CHANNEL} не найден")
            return

        guild = channel.guild
        warn_players = []
        for member in guild.members:
            if member.bot:
                continue
            member_role_ids = [r.id for r in member.roles]
            warn_count = sum(1 for rid in WARN_ROLES if rid in member_role_ids)
            if warn_count > 0:
                warn_players.append((member, warn_count))

        print(f"[update_warn_leaderboard] Найдено {len(warn_players)} игроков с варнами")

        embed = discord.Embed(title="🚫 Список варнов", description="Игроки с активными варнами", color=0xED4245)

        if warn_players:
            warn_players.sort(key=lambda x: x[1], reverse=True)
            warn_list = []
            for member, warn_count in warn_players:
                if warn_count == 1:
                    warn_emoji = "🟢"
                elif warn_count == 2:
                    warn_emoji = "🟡"
                else:
                    warn_emoji = "🔴"
                warn_list.append(f"{member.mention} — {warn_emoji} **{warn_count}/3**")
            embed.add_field(name="Игроки с варнами", value="\n".join(warn_list), inline=False)
        else:
            embed.add_field(name="Пусто", value="Нет игроков с варнами", inline=False)

        embed.set_footer(text="Обновляется автоматически")

        messages = [msg async for msg in channel.history(limit=10)]
        bot_messages = [msg for msg in messages if msg.author == bot.user and msg.embeds and msg.embeds[0].title == "🚫 Список варнов"]

        if bot_messages:
            await bot_messages[0].edit(embed=embed)
        else:
            await channel.send(embed=embed)

    except Exception as e:
        print(f"[update_warn_leaderboard] Ошибка: {e}")
        import traceback
        traceback.print_exc()


async def update_mute_leaderboard():
    try:
        channel = bot.get_channel(MUTE_LEADERBOARD_CHANNEL)
        if not channel:
            print(f"[update_mute_leaderboard] Канал {MUTE_LEADERBOARD_CHANNEL} не найден")
            return

        guild = channel.guild
        mute_players = []
        for member in guild.members:
            if member.bot:
                continue
            member_role_ids = [r.id for r in member.roles]
            mute_count = sum(1 for rid in MUTE_ROLES if rid in member_role_ids)
            if mute_count > 0:
                mute_players.append((member, mute_count))

        print(f"[update_mute_leaderboard] Найдено {len(mute_players)} игроков с устниками")

        embed = discord.Embed(title="🔇 Список устников", description="Игроки с активными устниками", color=0xF1C40F)

        if mute_players:
            mute_players.sort(key=lambda x: x[1], reverse=True)
            mute_list = []
            for member, mute_count in mute_players:
                mute_emoji = "🟡" if mute_count == 1 else "🟠"
                mute_list.append(f"{member.mention} — {mute_emoji} **{mute_count}/2**")
            embed.add_field(name="Игроки с устниками", value="\n".join(mute_list), inline=False)
        else:
            embed.add_field(name="Пусто", value="Нет игроков с устниками", inline=False)

        embed.set_footer(text="Обновляется автоматически")

        messages = [msg async for msg in channel.history(limit=10)]
        bot_messages = [msg for msg in messages if msg.author == bot.user and msg.embeds and msg.embeds[0].title == "🔇 Список устников"]

        if bot_messages:
            await bot_messages[0].edit(embed=embed)
        else:
            await channel.send(embed=embed)

    except Exception as e:
        print(f"[update_mute_leaderboard] Ошибка: {e}")
        import traceback
        traceback.print_exc()


async def schedule_dayoff_removal(user_id: int, days: int):
    await asyncio.sleep(days * 24 * 60 * 60)
    for guild in bot.guilds:
        member = guild.get_member(user_id)
        if member:
            dayoff_role = guild.get_role(DAYOFF_ROLE)
            if dayoff_role and dayoff_role in member.roles:
                await member.remove_roles(dayoff_role)
                print(f"[schedule_dayoff_removal] Роль отгула снята у {member}")
    db.remove_dayoff(user_id)
    await update_dayoff_leaderboard()


async def restore_dayoff_timers():
    from datetime import datetime
    all_dayoffs = db.get_all_dayoffs()
    current_date = datetime.now()

    for user_id, dayoff_info in all_dayoffs.items():
        try:
            end_date_str = dayoff_info.get("end_date", "")
            end_date = datetime.strptime(end_date_str, "%d.%m.%Y")
            time_left = (end_date - current_date).total_seconds()
            if time_left > 0:
                days_left = time_left / 86400
                asyncio.create_task(schedule_dayoff_removal(user_id, days_left))
                print(f"[restore_dayoff_timers] Восстановлен таймер для user_id={user_id}, осталось {days_left:.1f} дней")
            else:
                guild = None
                for g in bot.guilds:
                    guild = g
                    break
                if guild:
                    member = guild.get_member(user_id)
                    if member:
                        dayoff_role = guild.get_role(DAYOFF_ROLE)
                        if dayoff_role and dayoff_role in member.roles:
                            await member.remove_roles(dayoff_role)
                db.remove_dayoff(user_id)
                print(f"[restore_dayoff_timers] Отгул истёк для user_id={user_id}, роль снята")
        except Exception as e:
            print(f"[restore_dayoff_timers] Ошибка для user_id={user_id}: {e}")

    await update_dayoff_leaderboard()
    await update_dayoff_leaderboard()


# ─── РАСПИСАНИЕ ПРОВЕРОК ──────────────────────────────────────────────────────

REPORT_CHECK_CHANNEL = 1429895979657859163
auto_check_disabled_date = None  # дата когда отключена автопроверка

# Роли грифов
GRIEF_1_ROLE = 1471547081196835018
GRIEF_2_ROLE = 1434471945893576714
# Анка — все кто не гриф 1 и не гриф 2 считаются анкой

# Норма наказаний для грифа 1 (индекс совпадает с STAFF_ROLES)
NORM_GRIEF1 = [15, 20, 15, 25, 30, 35, 40]
# Гриф 2 и анка — норма в 2 раза меньше
NORM_GRIEF2 = [n // 2 for n in NORM_GRIEF1]

# Расписание: 0=Пн, 1=Вт, 2=Ср, 3=Чт, 4=Пт, 5=Сб, 6=Вс
# True = с нормой, False = без нормы, None = выходной
SCHEDULE = {0: False, 1: True, 2: False, 3: True, 4: False, 5: True, 6: None}


def get_today_check_type():
    from datetime import datetime
    import pytz
    msk = pytz.timezone("Europe/Moscow")
    weekday = datetime.now(msk).weekday()
    return SCHEDULE.get(weekday)


async def send_daily_reminder():
    """Отправляет напоминание в 10:00 МСК."""
    channel = bot.get_channel(REPORT_CHECK_CHANNEL)
    if not channel:
        return
    check_type = get_today_check_type()
    if check_type is None:
        return  # Воскресенье — отдых
    if check_type is False:
        await channel.send("@everyone Сегодня проверка отчётов без нормы, не будет отчёта до 00:00 ПО МСК - варн")
    else:
        await channel.send("@everyone Сегодня проверка отчётов с нормой, не будет отчёта до 00:00 ПО МСК - варн")


async def get_member_norm(member: discord.Member) -> int | None:
    """Возвращает норму наказаний для участника или None если нет штатной роли."""
    member_role_ids = [r.id for r in member.roles]
    staff_idx = -1
    for i, rid in enumerate(STAFF_ROLES):
        if rid in member_role_ids:
            staff_idx = i
    if staff_idx == -1:
        return None
    if GRIEF_1_ROLE in member_role_ids:
        return NORM_GRIEF1[staff_idx]
    else:
        return NORM_GRIEF2[staff_idx]


async def check_reports(with_norm: bool, guild: discord.Guild):
    """Проверяет отчёты всех штатных игроков и выдаёт варны/устники."""
    from datetime import datetime, timezone
    import pytz
    msk = pytz.timezone("Europe/Moscow")
    now = datetime.now(msk)
    # Начало вчерашнего дня в МСК → UTC (проверка идёт в 00:00, значит смотрим вчера)
    yesterday = now.replace(hour=0, minute=0, second=0, microsecond=0)
    from datetime import timedelta
    day_start = msk.localize(yesterday.replace(tzinfo=None) - timedelta(days=1)).astimezone(timezone.utc)
    day_end = msk.localize(yesterday.replace(tzinfo=None)).astimezone(timezone.utc)

    violators = []

    for member in guild.members:
        if member.bot:
            continue
        member_role_ids = [r.id for r in member.roles]
        if not any(rid in member_role_ids for rid in STAFF_ROLES):
            continue
        if DAYOFF_ROLE in member_role_ids:
            continue

        # Ищем канал игрока
        nick_lower = member.display_name.split("|")[0].strip().lower()
        target_channel = None
        for cat_id in STAFF_CATEGORIES:
            category = guild.get_channel(cat_id)
            if not category:
                continue
            for ch in category.channels:
                if nick_lower in ch.name.lower():
                    target_channel = ch
                    break
            if target_channel:
                break

        if not target_channel:
            continue

        # Считаем вложения за вчера
        count = 0
        try:
            async for msg in target_channel.history(limit=2000, after=day_start, before=day_end):
                count += len(msg.attachments)
        except Exception:
            continue

        if not with_norm:
            if count == 0:
                violators.append((member, count, None))
        else:
            norm = await get_member_norm(member)
            if norm is None:
                continue
            if count < norm:
                violators.append((member, count, norm))

    if not violators:
        print(f"[check_reports] Нарушителей нет")
        return

    # Выдаём варны/устники одним сообщением в канал варнов
    warn_lines = []
    mute_lines = []

    for member, count, norm in violators:
        member_role_ids = [r.id for r in member.roles]
        warn_count = sum(1 for rid in WARN_ROLES if rid in member_role_ids)
        mute_count = sum(1 for rid in MUTE_ROLES if rid in member_role_ids)
        reason = "Нет отчёта" if not with_norm else f"норма {count}/{norm}"

        if warn_count >= 2:
            if mute_count < len(MUTE_ROLES):
                role_to_add = guild.get_role(MUTE_ROLES[mute_count])
                if role_to_add:
                    await member.add_roles(role_to_add)
                mute_lines.append(f"{member.mention} — 🔇 устник ({reason})")
        elif warn_count < len(WARN_ROLES):
            role_to_add = guild.get_role(WARN_ROLES[warn_count])
            if role_to_add:
                await member.add_roles(role_to_add)
            new_warn = warn_count + 1
            warn_lines.append(f"{member.mention} — ⚠️ {new_warn}/3 ({reason})")

    warn_ch = bot.get_channel(WARN_ANNOUNCE_CHANNEL)
    if warn_ch and (warn_lines or mute_lines):
        check_label = "без нормы" if not with_norm else "с нормой"
        embed_w = discord.Embed(
            title=f"📋 Проверка отчётов ({check_label})",
            color=0xED4245
        )
        if warn_lines:
            embed_w.add_field(name="⚠️ Варны", value="\n".join(warn_lines), inline=False)
        if mute_lines:
            embed_w.add_field(name="� Устники", value="\n".join(mute_lines), inline=False)
        embed_w.set_footer(text=now.strftime("%d.%m.%Y"))
        await warn_ch.send(embed=embed_w)

    await update_warn_leaderboard()
    await update_mute_leaderboard()
    print(f"[check_reports] Завершено, нарушителей: {len(violators)}")


async def daily_scheduler():
    """Фоновая задача — запускает напоминание в 10:00 и проверку в 00:00 МСК."""
    import pytz
    from datetime import datetime, timedelta
    msk = pytz.timezone("Europe/Moscow")

    await bot.wait_until_ready()
    print("[scheduler] Планировщик запущен")

    while not bot.is_closed():
        now = datetime.now(msk)
        # Следующие 10:00 МСК
        next_10 = msk.localize(datetime(now.year, now.month, now.day, 10, 0, 0))
        if now >= next_10:
            next_10 += timedelta(days=1)
        # Следующие 00:00 МСК
        next_midnight = msk.localize(datetime(now.year, now.month, now.day + 1, 0, 0, 0))

        # Ждём ближайшее событие
        next_event = min(next_10, next_midnight)
        wait_seconds = (next_event - now).total_seconds()
        await asyncio.sleep(wait_seconds)

        now = datetime.now(msk)
        guild = None
        for g in bot.guilds:
            guild = g
            break

        if now.hour == 10 and now.minute < 5:
            await send_daily_reminder()
        elif now.hour == 0 and now.minute < 5:
            check_type = get_today_check_type()
            # Проверяем вчерашний день (уже наступила полночь)
            yesterday = (now.weekday() - 1) % 7
            check_type = SCHEDULE.get(yesterday)
            if check_type is not None and guild:
                # Проверяем не отключена ли автопроверка на сегодня
                global auto_check_disabled_date
                today_str = now.strftime("%d.%m.%Y")
                if auto_check_disabled_date == today_str:
                    print("[scheduler] Автопроверка отключена на сегодня")
                else:
                    await check_reports(with_norm=check_type, guild=guild)


@bot.tree.command(name="подсчитать_норму", description="Вручную запустить проверку отчётов")
@app_commands.describe(тип="Тип проверки: без_нормы или с_нормой")
@app_commands.choices(тип=[
    app_commands.Choice(name="без нормы", value="no_norm"),
    app_commands.Choice(name="с нормой", value="with_norm"),
])
async def manual_check_norm(interaction: discord.Interaction, тип: app_commands.Choice[str]):
    user_role_ids = [role.id for role in interaction.user.roles]
    if not any(role_id in ALLOWED_COMMAND_ROLES for role_id in user_role_ids):
        await interaction.response.send_message("❌ У вас нет прав.", ephemeral=True)
        return
    await interaction.response.defer(ephemeral=False)
    with_norm = тип.value == "with_norm"
    await check_reports(with_norm=with_norm, guild=interaction.guild)
    await interaction.followup.send("✅ Проверка завершена.", ephemeral=True)


@bot.tree.command(name="отключитьавтопроверку", description="Отключить автопроверку отчётов на сегодня")
async def disable_auto_check(interaction: discord.Interaction):
    user_role_ids = [role.id for role in interaction.user.roles]
    if not any(role_id in ALLOWED_COMMAND_ROLES for role_id in user_role_ids):
        await interaction.response.send_message("❌ У вас нет прав.", ephemeral=True)
        return
    global auto_check_disabled_date
    import pytz
    from datetime import datetime
    msk = pytz.timezone("Europe/Moscow")
    today_str = datetime.now(msk).strftime("%d.%m.%Y")
    auto_check_disabled_date = today_str
    await interaction.response.send_message(f"✅ Автопроверка отключена на **{today_str}**.", ephemeral=True)


@bot.tree.command(name="проверка_с_нормой", description="Запустить проверку с нормой (удаляет старое сообщение)")
async def check_with_norm_cmd(interaction: discord.Interaction):
    user_role_ids = [role.id for role in interaction.user.roles]
    if not any(role_id in ALLOWED_COMMAND_ROLES for role_id in user_role_ids):
        await interaction.response.send_message("❌ У вас нет прав.", ephemeral=True)
        return
    await interaction.response.defer(ephemeral=True)
    # Удаляем старое сообщение бота в канале проверок
    report_ch = bot.get_channel(REPORT_CHECK_CHANNEL)
    if report_ch:
        async for msg in report_ch.history(limit=20):
            if msg.author == bot.user and msg.embeds and "Результаты проверки" in (msg.embeds[0].title or ""):
                try:
                    await msg.delete()
                except discord.errors.NotFound:
                    pass
                break
    await check_reports(with_norm=True, guild=interaction.guild)
    await interaction.followup.send("✅ Проверка с нормой завершена.", ephemeral=True)


@bot.tree.command(name="проверка_без_нормы", description="Запустить проверку без нормы (удаляет старое сообщение)")
async def check_without_norm_cmd(interaction: discord.Interaction):
    user_role_ids = [role.id for role in interaction.user.roles]
    if not any(role_id in ALLOWED_COMMAND_ROLES for role_id in user_role_ids):
        await interaction.response.send_message("❌ У вас нет прав.", ephemeral=True)
        return
    await interaction.response.defer(ephemeral=True)
    # Удаляем старое сообщение бота в канале проверок
    report_ch = bot.get_channel(REPORT_CHECK_CHANNEL)
    if report_ch:
        async for msg in report_ch.history(limit=20):
            if msg.author == bot.user and msg.embeds and "Результаты проверки" in (msg.embeds[0].title or ""):
                try:
                    await msg.delete()
                except discord.errors.NotFound:
                    pass
                break
    await check_reports(with_norm=False, guild=interaction.guild)
    await interaction.followup.send("✅ Проверка без нормы завершена.", ephemeral=True)


bot.run(os.getenv("DISCORD_TOKEN"))
