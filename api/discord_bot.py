import json
import os, re, time, discord, requests
from datetime import datetime

os_path_slash = "\\" # default Windows
if os.name == 'posix':
    os.environ['TZ'] = 'Asia/Taipei'
    time.tzset()
    os_path_slash = "/" # unix

__dir__ = os.path.dirname(os.path.abspath(__file__)) + os_path_slash

def convertMinuteToHumanReadTime(minutes):
    result = ''

    years = int(minutes / 60 / 24 / 365)
    if years >= 1:
        result += ' %d 年'%(years)
        minutes -= years * 60 * 24 * 365

    months = int(minutes / 60 / 24 / 30)
    if months >= 1:
        result += ' %d 月'%(months)
        minutes -= months * 60 * 24 * 30

    days = int(minutes / 60 / 24)
    if days >= 1:
        result += ' %d 日'%(days)
        minutes -= days * 60 * 24

    hours = int(minutes / 60)
    if hours >= 1:
        result += ' %d 時'%(hours)
        minutes -= hours * 60

    if minutes >= 1:
        result += ' %d 分'%(minutes)

    if result == '':
       result = '不用等待'

    return result.strip()

def readenv():
    if not os.path.isfile(__dir__ + '.env'):
        return {}
    
    result = {}
    file_object = open(__dir__ + '.env', 'r', encoding="utf-8")
    while True:
        line = file_object.readline()
        if not line:
            break

        center_point = line.find('=')
        name = line[0:center_point]
        value = line[(center_point + 1):].strip()
        
        result[name] = value

    file_object.close()
    return result

def storeLog(content):
    global time
    now_time = time.time()
    format_date = datetime.fromtimestamp(now_time).strftime('%Y-%m-%d')
    format_time = datetime.fromtimestamp(now_time).strftime('%H:%M:%S')
    file_object = open(__dir__ + '/logs/discord_bot_%s.log'%(format_date), 'a', encoding="utf-8")
    file_object.write('[%s] %s\n'%(format_time, content))
    file_object.close()

def getWorldInfoByWorldName(world_name):
    url = "https://firstlight.newworldstatus.com/ext/v1/worlds/%s"%(world_name)
    headers = {
        'Authorization': 'Bearer %s'%(envs['NEW_WORLD_STATUS_API_SECRET_KEY']),
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.81 Safari/537.36',
        'Accept': '*/*',
        'Connection': 'keep-alive',
    }
    response = requests.request("GET", url, headers=headers)
    
    if response.status_code != 200:
        storeLog('呼叫 API 無法正確取得資料，status code: %d'%(response.status_code))
        return {}

    result = response.json()

    if not result['success']:
        storeLog('呼叫 API 無法正確取得資料，success: %s'%(result['success']))
        return {}

    return result['message']

def getWorldTerritories(world_name):
    try:
        file_object = open(__dir__ + '/territories.json', 'r', encoding="utf-8")
        json_data = file_object.read()
        file_object.close()
    except:
        url = "https://nwmaps.info"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.81 Safari/537.36',
            'Accept': '*/*',
            'Connection': 'keep-alive',
        }
        response = requests.request("GET", url, headers=headers)

        json_search = re.search('<script id="__NEXT_DATA__" type="application/json">(.*)</script></body></html>', response.text())
        if not json_search:
            return []
        json_data = json_search[1]

        file_object = open(__dir__ + '/territories.json', 'w', encoding="utf-8")
        file_object.write(json_data)
        file_object.close()
    else:
        json_data = json.loads(json_data)
        worlds = json_data['props']['pageProps']['serverList']['servers']
        for world in worlds:
            if world['name'].lower().replace(' ', '-') == world_name:
                return world

envs = readenv()

# client 是我們與Discord連結的橋樑
client = discord.Client()

#調用event函式庫
@client.event
#當機器人完成啟動時
async def on_ready():
    print('目前登入身份：', client.user)
    activity = discord.Activity(name="!Server Riallaro 查詢伺服器狀態", type=discord.ActivityType.listening)
    await client.change_presence(status=discord.Status.online, activity=activity)

@client.event
# 當有訊息時
async def on_message(message):
    catch_time = time.time()
    # 排除自己的訊息，避免陷入無限循環
    if message.author == client.user:
        return

    # match 指令 !server
    match_objs = re.match('^!(S|s)erver (.*)$', message.content)
    if not match_objs:
        return

    game_server_name = match_objs[2]
    discord_message = await message.channel.send('查詢 ' + game_server_name + ' 的伺服器狀態中...')
    if isinstance(message.channel, discord.TextChannel):
        msg_log = '伺服器: %s, 群組: %s, 頻道: %s, 查詢者: %s, 內容: %s'%(message.channel.guild, message.channel.category, message.channel, message.author.name, message.content)
    else:
        msg_log = '查詢者: %s, 內容: %s'%(message.author.name, message.content)
    print(msg_log)
    storeLog(msg_log)

    # 這邊打 API 取得必要資訊
    result = getWorldInfoByWorldName(game_server_name.lower().replace(' ', '-'))
    territory = getWorldTerritories(game_server_name.lower().replace(' ', '-'))

    if not result:
        msg = '找不到指定世界 %s 的資料'%(game_server_name)
        print(msg)
        storeLog(msg)
        await discord_message.edit(content=msg)
        return

    if territory:
        world_name = territory['name']
    else:
        world_name = ''
        for part in game_server_name.replace('-', ' ').split(' '):
            world_name += part.capitalize() + ' '
        world_name = world_name.strip()
    now_players = result['players_current']
    in_queue = result['queue_current']
    average_wait = convertMinuteToHumanReadTime(int(result['queue_wait_time_minutes']))
    world_status = result['status_enum']

    if world_status == 'ENUM_FAILED_BITBANG_UNPACK':
        average_wait = '不明的伺服器狀態，無法預估'

    # 處理嵌入內容
    embed = discord.Embed()
    if territory:
        embed.set_image(url=territory['mapImage'])
    embed.set_author(name='New World Server Status & Population', url='https://newworldstatus.com/', icon_url='http://i.imgur.com/lDF4O4s.jpg') # https://imgur.com/a/paxI6xX
    embed.title = '%s 的伺服器狀態'%(world_name)
    embed.url = 'https://newworldstatus.com/worlds/%s'%(game_server_name.lower().replace(' ', '-'))

    embed.add_field(name='狀態', value=world_status, inline=True)
    embed.add_field(name='線上人數', value=str(now_players), inline=True)
    embed.add_field(name='排隊人數', value=str(in_queue), inline=True)
    embed.add_field(name='預估等待時間', value=average_wait, inline=True)

    embed.timestamp = datetime.utcnow()
    embed.set_footer(text='查詢耗時 %.2f 秒'%((time.time() - catch_time)))
    embed.color = 15548997 # red
    if int(now_players) >= 1750:
        embed.color = 16705372 # yellow
    if world_status == 'ACTIVE':
        embed.color = 5763719 # green
    if world_status == 'UNKNOWN':
        embed.color = 9807270 # grey

    content = "查詢耗時: %.2f 秒, %s 狀態 [%s], 遊玩人數: %s, 排隊人數: %s, 預估時間: %s"%((time.time() - catch_time), world_name, world_status, str(now_players), str(in_queue), average_wait)
    print(content)
    storeLog(content)
    await discord_message.delete()
    await message.channel.send(embed=embed)

client.run(envs['DISCORD_BOT_TOKEN']) # from env