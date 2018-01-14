# Rested Experience by MiB
from config.manager import ConfigManager
from restedexp.restedexpfunctions import pickle
from commands.say import SayCommand
from commands.client import ClientCommand
from commands.server import ServerCommand
from listeners.tick import Repeat
from listeners import OnLevelInit
from events import Event
from players.entity import Player
from filters.players import PlayerIter
from time import time

from menus import PagedMenu
from menus import PagedOption
from menus import SimpleMenu
from menus import SimpleOption
from menus import Text

import wcs

addon_config = ConfigManager('restedxp')
toggle = addon_config.cvar("wcs_restedexp_cfg_toggle",1)
timer = addon_config.cvar("wcs_restedexp_cfg_timer",60)
tickaxp = addon_config.cvar("wcs_restedexp_cfg_a_tickxp",1)
tickoxp = addon_config.cvar("wcs_restedexp_cfg_o_tickxp",0)
gainxp = addon_config.cvar("wcs_restedexp_cfg_gainxp",5)
addon_config.write()


db = pickle.getDict()

joined = set()

def exptick():
	for player in PlayerIter():
		steamid = player.steamid
		if steamid == 'BOT':
			steamid = 'BOT_'+player.name.upper()
		if tickoxp.get_int():
			db[steamid]["exp"] += int(tickoxp)
		db[steamid]["left"] = time()
		
		
repeat = Repeat(exptick)
repeat.start(timer.get_int())

def player_menu_select(menu, index, choice):
	userid = choice.value
	player = Player.from_userid(userid)
	
	steamid = player.steamid
	if steamid == 'BOT':
		steamid = 'BOT_'+player.name.upper()
	check(steamid)
	exp = int(db[steamid]["exp"])
	if player.index == index:
		wcs.wcs.tell(Player(index).userid,"\x04[WCS]\x05 You currently have %s rested experience."%int(exp))
	else:
		wcs.wcs.tell(Player(index).userid,"\x04[WCS]\x05 %s currently has %s rested experience."%(player.name,int(exp)))
	restedexp_menu.send(index)
		
		
def player_menu_build(menu, index):
	menu.clear()
	for player in PlayerIter():
		option = PagedOption('%s' % str(player.name), player.userid)
		menu.append(option)


player_menu = PagedMenu(select_callback=player_menu_select, build_callback=player_menu_build)


def restedexp_menu_select(menu, index, choice):
	if choice.choice_index == 1:
		if int(toggle.get_int()):
			steamid = Player(index).steamid
			if db[steamid]["gaintrig"]:
				db[steamid]["gaintrig"] = 0
				wcs.wcs.tell(Player(index).userid,"\x04[WCS]\x05 You toggled your collect per kill off.")
			else:
				db[steamid]["gaintrig"] = 1
				wcs.wcs.tell(Player(index).userid,"\x04[WCS]\x05 You toggled your collect per kill on.")
		else:
			wcs.wcs.tell(Player(index).userid,"\x04[WCS]\x05 Cannot toggle your collect per kill since server settings currently has it off.")
		restedexp_menu.send(index)
	elif choice.choice_index == 2:
		player_menu.send(index)
	
def restedexp_menu_build(menu, index):
	player = Player(index)
	steamid = player.steamid
	menu.clear()
	menu.append(Text('Rested Experience - Main Menu'))
	menu.append(Text('-----------------------------'))
	menu.append(Text('Current Rested Experience: %s'%int(db[steamid]["exp"])))
	if db[steamid]["gaintrig"] and int(toggle.get_int()):
		menu.append(Text("Collect Per Kill: On"))
	else:
		if not db[steamid]["gaintrig"] and int(toggle.get_int()):
		   menu.append(Text("Collect Per Kill: Off"))
		else:
		   menu.append(Text("Collect Per Kill: Off (Server Setting)"))
	menu.append(Text("Collected Per Kill: %s (Server Setting)"%gainxp.get_int()))
	menu.append(Text("-----------------------------"))
	menu.append(Text("Gain Amount (Online): %s"%tickoxp.get_int()))
	menu.append(Text("Gain Amount (Offline): %s"%tickaxp.get_int()))
	menu.append(Text("Gain Tick Rate: %s"%timer.get_int()))
	menu.append(Text("-----------------------------"))
	menu.append(SimpleOption(1, 'Toggle Collect Per Kill', 'toggle'))
	menu.append(SimpleOption(2, "Check Other Player's Rested Experience", 'check'))
	menu.append(Text("-----------------------------"))
	menu.append(SimpleOption(9, 'Close', highlight=False))



restedexp_menu = SimpleMenu(select_callback=restedexp_menu_select, build_callback=restedexp_menu_build)


@SayCommand('restedxp')
@SayCommand('restedexp')
@ClientCommand('restedxp')
@ClientCommand('restedexp')
def rested_exp_cmd(command,index,team=None):
	restedexp_menu.send(index)
	
	
@ServerCommand('saverestedxp')
@ServerCommand('saverestedexp')
def save_rested_cmd(args):
	pickle.save()

@OnLevelInit
def level_init_listener(mapname):
	pickle.save()

def check(steamid):
	if not steamid in db:
		db[steamid] = {}
	if not "gaintrig" in db[steamid]:
		db[steamid]["gaintrig"] = 1
	if not "exp" in db[steamid]:
		db[steamid]["exp"] = 0
	if not "left" in db[steamid]:
		db[steamid]["left"] = 0
		
@Event('round_end')
def round_end(ev):
	pickle.save()
		
@Event('player_disconnect')		
def player_disconnect(ev):
	player = Player.from_userid(ev['userid'])
	steamid = player.steamid
	if steamid == "BOT":
		steamid = "BOT_%s"%player.name.upper()
	check(steamid)
	db[steamid]["left"] = time()
	if not steamid in joined:
		return
	joined.discard(steamid)
	
@Event('player_activate')
def player_activate(ev):
	player = Player.from_userid(ev['userid'])
	steamid = player.steamid
	if steamid == "BOT":
		steamid = "BOT_%s"%player.name.upper()
	if steamid in joined:
		return
	joined.add(steamid)
	if steamid:
		check(steamid)
		left = db[steamid]["left"]
		if left:
			gained = int(round(time() - left))
			if gained < 0:
				gained *= -1
			gained = (gained / int(timer.get_int())) * tickaxp.get_int()
			if gained:
				wcs.wcs.tell(ev["userid"],"\x04[WCS]\x05 You gained %s rested experience while offline."%gained)
				db[steamid]["exp"] += gained
		db[steamid]["left"] = time()


@Event('player_death')		
def player_death(ev):
	atk_play = Player.from_userid(ev['attacker'])
	vic_play = Player.from_userid(ev['userid'])
	steamid = atk_play.steamid
	if steamid == "BOT":
		steamid = "BOT_%s"%atk_play.name.upper()
	if not steamid:
		return
	uid = atk_play.userid
	if uid:
		check(steamid)
		if vic_play.team == atk_play.team:
			return
		exp = db[steamid]["exp"]
		gxp = int(gainxp.get_int())
		if exp and db[steamid]["gaintrig"] and int(toggle.get_int()):
			if gxp > exp:
				gxp = exp
			db[steamid]["exp"] -= gxp
			player = wcs.wcs.getPlayer(uid)
			player.giveXp(gxp,"rested experience")