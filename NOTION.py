import os
import discord
from discord.ext import commands, tasks
import datetime
from notion_client import Client
from dotenv import load_dotenv

# .env 파일에서 환경 변수를 로드합니다.
load_dotenv()

# 환경 변수 가져오기
discord_bot_token = os.getenv("DISCORD_BOT_TOKEN")
notification_channel_id = int(os.getenv("DISCORD_CHANNEL_ID"))
notion_api_key = os.getenv("NOTION_API_KEY")
notion_database_id = os.getenv("NOTION_DATABASE_ID")

intents = discord.Intents.default()
intents.message_content = True

# !를 명령어 접두사(prefix)로 설정합니다.
bot = commands.Bot(command_prefix='!', intents=intents)
notion = Client(auth=notion_api_key)

# 봇이 준비되었을 때 실행됩니다.
@bot.event
async def on_ready():
    """봇이 온라인 상태가 되면 실행됩니다."""
    print(f'{bot.user} 봇이 온라인 상태입니다! 🎉')
    # 주기적 일정 확인 작업을 시작합니다.
    check_notion_schedule.start()

# 24시간마다 노션 일정을 확인하는 작업
@tasks.loop(hours=24)
async def check_notion_schedule():
    """노션 데이터베이스에서 D-Day 일정을 찾아 알림을 보냅니다."""
    channel = bot.get_channel(notification_channel_id)
    if not channel:
        print(f"경고: 채널 ID {notification_channel_id}를 찾을 수 없습니다.")
        return

    today = datetime.date.today()

    try:
        results = notion.databases.query(database_id=notion_database_id)
        
        for item in results['results']:
            date_info = item['properties'].get('날짜', {}).get('date')
            if not date_info:
                continue

            event_date = datetime.datetime.fromisoformat(date_info['start']).date()
            
            if event_date == today:
                title_prop = item['properties'].get('이름', {}).get('title')
                title = title_prop[0]['plain_text'] if title_prop and title_prop[0] else '제목 없음'
                
                await channel.send(f"🗓️ **D-Day 알림!** 오늘 일정: **{title}**")

    except Exception as e:
        print(f"노션 일정 확인 중 오류 발생: {e}")
        await channel.send("노션 일정을 가져오는 데 실패했습니다. 😅")

# 사용자가 !일정 명령어를 입력했을 때 실행됩니다.
@bot.command(name='일정')
async def show_schedule(ctx):
    """오늘의 노션 일정을 수동으로 가져와 보여줍니다."""
    await ctx.send("📅 노션 캘린더에서 일정을 불러오는 중...")
    today = datetime.date.today()

    try:
        results = notion.databases.query(database_id=notion_database_id)
        
        schedule_list = []
        for item in results['results']:
            date_info = item['properties'].get('날짜', {}).get('date')
            if not date_info:
                continue

            event_date = datetime.datetime.fromisoformat(date_info['start']).date()
            if event_date == today:
                title_prop = item['properties'].get('이름', {}).get('title')
                title = title_prop[0]['plain_text'] if title_prop and title_prop[0] else '제목 없음'
                schedule_list.append(title)
        
        if schedule_list:
            response = "✨ **오늘의 일정**\n" + "\n".join([f"- {s}" for s in schedule_list])
            await ctx.send(response)
        else:
            await ctx.send("✅ 오늘 예정된 일정이 없습니다.")

    except Exception as e:
        await ctx.send(f"노션 일정을 가져오는 데 실패했습니다: {e}")

# 봇을 실행합니다.
bot.run(discord_bot_token)
