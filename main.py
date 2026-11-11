from microbit import *
from ssd1306 import screen, set_address, initialize, clear_oled, draw_screen
from ssd1306_text import add_text
from gameplay import GAME, INFO, PUSH, CENTRE_ZONE, clear, draw_flag, write, read_stick, stick_centre, forget_buttons, get_button, buzz, solo
 
options = ["SOLO", "MULTIPLAYER", "CONTROLS"]
 
 
def draw_menu(selected):
	clear()
	add_text(1, 0, "MAIN MENU", 0)
	for i in range(3):
		x = (12 - len(options[i])) // 2
		add_text(x, i + 1, options[i], 0)
	start = 1 + (selected + 1) * 128
	for i in range(start, start + 128):
		screen[i] = screen[i] ^ 0xFF
	draw_screen()
 
 
def draw_title():
	set_address(INFO)
	clear()
	add_text(0, 0, "FAIRWAY", 0)
	add_text(0, 1, "FRIENDS", 0)
	add_text(0, 3, "A TO SELECT", 0)
	draw_flag(54)
	draw_screen()
	set_address(GAME)
 
 
def menu(middle):
	selected = 0
	draw_menu(selected)
	draw_title()
	forget_buttons()
	ready = True
	up_before = 1
	down_before = 1
	while True:
		step = 0
		move = read_stick(pin1) - middle
		if ready and abs(move) >= PUSH:
			ready = False
			if move > 0:
				step = -1
			else:
				step = 1
		elif abs(move) <= CENTRE_ZONE:
			ready = True
		up = pin13.read_digital()
		down = pin15.read_digital()
		if up == 0 and up_before == 1:
			step = -1
		if down == 0 and down_before == 1:
			step = 1
		up_before = up
		down_before = down
		if step != 0:
			buzz()
			selected = (selected + step) % 3
			draw_menu(selected)
		b = get_button()
		if b == "A":
			if selected == 0:
				return
			if selected == 1:
				write(INFO, "MULTIPLAYER||COMING SOON|B: BACK")
			if selected == 2:
				write(INFO, "STICK: AIM|UP/DN: CLUB|A: OK / HIT|B: BACK")
		if b == "B":
			draw_title()
		sleep(20)
 
 
pin13.set_pull(pin13.PULL_UP)
pin15.set_pull(pin15.PULL_UP)
for oled in (INFO, GAME):
	set_address(oled)
	initialize()
	clear_oled()
middle_y = stick_centre(pin1)
while True:
	menu(middle_y)
	solo()
