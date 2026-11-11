from microbit import*
import music,gameplay
from ssd1306 import set_address,initialize,clear_oled,draw_screen
from ssd1306_text import add_text
from gameplay import*
from multiplayer import multiplayer
options=['MAIN MENU','SOLO','MULTIPLAYER','CONTROLS']
def draw_title():set_address(INFO);clear();add_text(0,0,'FAIRWAY',0);add_text(0,1,'FRIENDS',0);add_text(0,3,'A TO SELECT',0);draw_flag(54);draw_screen();set_address(GAME)
def menu():
	selected=0;draw_list(options,1);draw_title();tune(CALM,70);nav=UpDown();forget_buttons()
	while True:
		step=nav.step()
		if step:buzz();selected=(selected+step)%3;draw_list(options,selected+1)
		b=get_button()
		if b=='A'and selected<2:music.stop(pin12);return selected
		if b=='A':write(INFO,'UP/DN: CLUB|STICK: AIM|A: OK / HIT|B: BACK')
		if b=='B':draw_title()
		sleep(20)
pin13.set_pull(pin13.PULL_UP)
pin15.set_pull(pin15.PULL_UP)
for oled in(INFO,GAME):set_address(oled);initialize();clear_oled()
gameplay.y_mid=stick_centre(pin1)
while True:
	if menu()==0:solo()
	else:multiplayer()