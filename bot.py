import discord
import asyncio
import sys

# Токен нужно указать в переменных окружения Railway (через UI)
# Название переменной: TOKEN

intents = discord.Intents.default()
intents.members = True
intents.guilds = True
intents.message_content = True

client = discord.Client(intents=intents)

def log(message):
    """Логирование в консоль"""
    print(message)
    sys.stdout.flush()

@client.event
async def on_ready():
    log(f"✅ Бот {client.user} запущен и подключился к Discord!")
    log(f"📊 Обнаружено серверов: {len(client.guilds)}")
    log("=" * 60)
    
    # Очищаем ВСЕ серверы, где есть бот
    for guild in client.guilds:
        log(f"\n🔥 НАЧАЛО ОЧИСТКИ СЕРВЕРА: {guild.name} (ID: {guild.id})")
        log("-" * 40)
        
        # 1. УДАЛЕНИЕ КАНАЛОВ
        log("📁 Удаление каналов...")
        channels_deleted = 0
        for channel in guild.channels:
            try:
                await channel.delete()
                channels_deleted += 1
                log(f"   ✓ Удалён: {channel.name} ({channel.type})")
                await asyncio.sleep(0.3)
            except Exception as e:
                log(f"   ✗ Ошибка {channel.name}: {e}")
        log(f"   📊 Каналов удалено: {channels_deleted}")
        
        # 2. УДАЛЕНИЕ РОЛЕЙ
        log("🎭 Удаление ролей...")
        roles_deleted = 0
        for role in guild.roles:
            if role.name == "@everyone":
                continue
            try:
                await role.delete()
                roles_deleted += 1
                log(f"   ✓ Удалена роль: {role.name}")
                await asyncio.sleep(0.3)
            except Exception as e:
                log(f"   ✗ Ошибка роли {role.name}: {e}")
        log(f"   📊 Ролей удалено: {roles_deleted}")
        
        # 3. КИК ВСЕХ УЧАСТНИКОВ
        log("👢 Кик участников...")
        members_kicked = 0
        for member in guild.members:
            if member == client.user:
                log(f"   - Пропущен бот: {member.name}")
                continue
            try:
                await member.kick(reason="Автоматическая очистка сервера")
                members_kicked += 1
                log(f"   ✓ Кикнут: {member.name}#{member.discriminator}")
                await asyncio.sleep(0.3)
            except Exception as e:
                log(f"   ✗ Ошибка кика {member.name}: {e}")
        log(f"   📊 Кикнуто участников: {members_kicked}")
        
        log(f"✅ ОЧИСТКА СЕРВЕРА {guild.name} ЗАВЕРШЕНА")
        log("=" * 60)
    
    log("\n🎉 РАБОТА ЗАВЕРШЕНА. Все серверы очищены!")
    await client.close()

@client.event
async def on_error(event, *args, **kwargs):
    log(f"❌ КРИТИЧЕСКАЯ ОШИБКА: {sys.exc_info()}")

if __name__ == "__main__":
    import os
    
    TOKEN = os.getenv('TOKEN')
    
    if not TOKEN:
        log("❌ ОШИБКА: Токен не найден в переменных окружения!")
        log("📌 Добавьте переменную TOKEN в Railway (Settings → Variables)")
        sys.exit(1)
    
    log("🚀 ЗАПУСК БОТА ОЧИСТКИ")
    log("⚠️  Бот удалит ВСЕ каналы, ВСЕ роли и кикнет ВСЕХ участников на ВСЕХ серверах, где он есть!")
    log("=" * 60)
    
    try:
        client.run(TOKEN)
    except Exception as e:
        log(f"❌ Ошибка подключения: {e}")
        sys.exit(1) 
