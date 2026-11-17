from microbit import *
import music
import gameplay
from ssd1306 import set_address, initialize, clear_oled, draw_screen
from ssd1306_text import add_text
from gameplay import GAME, INFO, CALM_SONG, UpDown, clear, draw_flag, draw_list, write, play_song, stick_centre, forget_buttons, get_button, buzz, solo
from multiplayer import multiplayer

MENU = ["MAIN MENU", "SOLO", "MULTIPLAYER", "CONTROLS"]


def draw_title():
	set_address(INFO)
	clear()
	add_text(0, 0, "FAIRWAY", 0)
	add_text(0, 1, "FRIENDS", 0)
	add_text(0, 3, "A TO SELECT", 0)
	draw_flag(54)
	draw_screen()
	set_address(GAME)


def main_menu():
	choice = 1
	draw_list(MENU, choice)
	draw_title()
	play_song(CALM_SONG, 70)
	nav = UpDown()
	forget_buttons()
	while True:
		step = nav.step()
		if step != 0:
			buzz()
			choice = choice + step
			if choice < 1:
				choice = 3
			if choice > 3:
				choice = 1
			draw_list(MENU, choice)
		button = get_button()
		if button == "A":
			if MENU[choice] == "CONTROLS":
				write(INFO, "UP/DN: CLUB|STICK: AIM|A: OK / HIT|B: BACK")
			else:
				music.stop(pin12)
				return MENU[choice]
		if button == "B":
			draw_title()
		sleep(20)


pin13.set_pull(pin13.PULL_UP)
pin15.set_pull(pin15.PULL_UP)
for oled in (INFO, GAME):
	set_address(oled)
	initialize()
	clear_oled()
gameplay.y_centre = stick_centre(pin1)

while True:
	if main_menu() == "SOLO":
		solo()
	else:
		multiplayer()
