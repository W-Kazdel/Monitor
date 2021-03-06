# coding=utf-8
import json
import time
import datetime
import shutil
import re
import os
from mcdreforged.api.all import *

PLUGIN_METADATA = {
    'id': 'monitor',
    'version': '2.2.1',
    'name': 'Monitor',
    'description': 'A plugin to record player coordinates, pseudo-peace notification.',
    'author': 'W_Kazdel',
    'link': 'https://github.com/W-Kazdel/Monitor',
    'dependencies': {
        'minecraft_data_api': '>=1.1.0'
    }
}

sleep = 15

json_filename = "./records/record_list.json"
site_info = "./config/site.json"
records = "./records"

online_player = []
bot_list = []
record_list = []
site_list = {}

help_msg = '''----------- §aMCDR 监控插件帮助信息 §f-----------
§b!!mr add [坐标名] [x] [y] [z] [次元] §f- §c次元：world nether end
§b!!mr list §f- §c显示所有已有监控
§b!!mr reload §f- §c重载监控坐标，联系管理员更改后操作该指令
§e为防止随意删除更改监控点，删除监控请联系管理，玩家仅有添加权限
-----------------Monitor-----------------'''

ISOTIMEFORMAT = '%Y-%m-%d %H.%M.%S'
pre = " 危 "

status = 0

def on_info(server, info):
    global bot_list
    if info.is_player == 1:
        if info.content.startswith('!!mr'):
            args = info.content.split(' ')
            if len(args) == 1:
                for line in help_msg.splitlines():
                    server.tell(info.player, line)
            elif args[1] == 'add':
                add_site(server, args, info)
                saveSite()
            elif args[1] == 'list':
                show_site(server)
            elif args[1] == 'reload':
                load_site(site_info)
                server.say("§a监控坐标已重载")
            else:
                server.tell(info.player, "§7[§aMonitor§f/§cWARN§7] §c参数错误，请输入!!mr 查看帮助信息")
    elif info.source == 0 and not info.is_player:
        botinfo = joined_info(info.content)
        if botinfo[0] and botinfo[1] == 'bot' and botinfo[2] not in bot_list:
            bot_list.append(botinfo[2])

def on_load(server, old):
    global online_player
    server.register_help_message('!!mr', '监控插件')
    if not os.path.exists(records):
        os.makedirs(records)
    apart()
    load_site(site_info)
    if old is not None and old.online_player is not None:
        online_player = old.online_player
    else:
        online_player = []

# 分割文件
def apart():
    theTime = datetime.datetime.now().strftime(ISOTIMEFORMAT)
    try:
        shutil.copy(json_filename, './records/' + str(theTime) + '.json')
    except:
        saveJson()

# 保存坐标记录
def saveJson():
    with open(json_filename, 'w+', encoding='utf-8') as f:
        json.dump(record_list, f, ensure_ascii=False, indent=4)

# 保存监控点
@new_thread('mr')
def saveSite():
    with open(site_info, 'w') as f:
        json.dump(site_list, f, ensure_ascii=False, indent=4)

# 重载监控点
@new_thread('mr')
def load_site(site_info):
    global site_list
    try:
        with open(site_info) as f:
            site_list = json.load(f, encoding='utf-8')
    except:
        saveSite()

# 判断整数
def is_instance(str):
    try:
        str = int(str)
        return isinstance(str,int)
    except ValueError:
        return False

# 判断bot
def joined_info(msg):
    joined_player = re.match(
        r'(\w+)\[([0-9\.:]+|local)\] logged in with entity id', msg)
    if joined_player:
        if joined_player.group(2) == 'local':
            return [True, 'bot', joined_player.group(1)]
        else:
            return [True, 'player', joined_player.group(1)]
    return [False]

# 添加监控点
@new_thread('mr')
def add_site(server, args, info):
    if len(args) == 7:
        if args[2] in site_list:
            server.tell(info.player, "§7[§aMonitor§f/§cWARN§7] §c监控点已存在")
        elif is_instance(args[3])==0 or is_instance(args[4])==0 or is_instance(args[5])==0:
            server.tell(info.player, "§7[§aMonitor§f/§cWARN§7] §c参数[x] [y] [z]必须为整数")
        elif args[6]=='world' or args[6]=='nether' or args[6]=='end':
            site_list[args[2]] = [args[3], args[4], args[5], args[6]]
            server.say(f"§b{info.player} 添加了新的监控坐标 §e{args[2]}")
        else:
            server.tell(info.player, "§7[§aMonitor§f/§cWARN§7] §c参数[次元]错误")
    else:
        server.tell(info.player, "§7[§aMonitor§f/§cWARN§7] §c缺少参数，请输入!!mr 查看帮助信息")

# 打印监控点
@new_thread('mr')
def show_site(server):
    server.say("§b[监控坐标点列表]")
    for key, values in site_list.items():
        x = int(values[0])
        y = int(values[1])
        z = int(values[2])
        dim = values[3]
        server.say(f"§a{key} §b次元: {dim}  §a{x}, {y}, {z}")

# 控制坐标监控开关
def on_player_joined(server, player, info):
    global status
    if player not in online_player and player not in bot_list:
        online_player.append(player)
    if len(online_player) == 1 and player in online_player:
        status = 1
        monitor(server)

def on_player_left(server, player):
    global status
    if player in online_player:
        online_player.remove(player)
        if len(online_player) == 0:
            status = 0
    if player in bot_list:
        bot_list.remove(player)

# 监控
@new_thread('Monitor')
def monitor(server):
    global record_list
    MinecraftDataAPI = server.get_plugin_instance('minecraft_data_api')
    while True:
        if status == 1:
            time.sleep(3)
            try:
                for i in range(len(online_player)):
                    pos = MinecraftDataAPI.get_player_coordinate(online_player[i])
                    x = int(pos[0])
                    y = int(pos[1])
                    z = int(pos[2])
                    dim = MinecraftDataAPI.get_player_dimension(online_player[i])
                    if dim==0:
                        dim = "world"
                    elif dim==-1:
                        dim = "nether"
                    elif dim==1:
                        dim = "end"
                    for key, values in site_list.items():
                        fp_x = int(values[0])
                        fp_y = int(values[1])
                        fp_z = int(values[2])
                        fp_dim = values[3]
                        if fp_x-50<=x<=fp_x+50 and fp_z-50<z<fp_z+50 and fp_y-10<=y<=fp_y+10 and dim==fp_dim:
                            server.say("§7[§aMonitor§f/§cWARNING§7]§c" + pre + online_player[i] + pre + "在 " + key + " 附近游荡！！！")
                            record_list.append("[Monitor/WARNING]" + pre + online_player[i] + pre + "在 " + key + " 附近游荡！！！")
                    theTime = datetime.datetime.now().strftime(ISOTIMEFORMAT)
                    info = str(theTime) + " " + str(online_player[i]) + " " + str(dim) + " x:" + str(x)+ " y:" + str(y)+ " z:" + str(z)
                    record_list.append(info)
                    saveJson()
            except:
                continue
            time.sleep(sleep - 3)
        elif status == 0:
            break

def on_unload(server):
    saveJson()
    saveSite()

def on_server_stop(server, return_code):
    global online_player
    online_player = []
