from microbit import *
import math
import random
import music
from ssd1306 import screen, set_address, draw_screen
from ssd1306_text import add_text

GAME = 0x3C
INFO = 0x3D

TURN_STEP = 5
PUSH = 300
CENTRE_ZONE = 90

CLUB_NAMES = ["DRIVER", "IRON", "WEDGE", "PUTTER"]
CLUB_RANGE = [40, 24, 12, 5]
CUP_SIZE = 1.6
MAX_STROKES = 6
SENS = 2.5
MIN_SWING = 80

power = 0
holes = 1
cup_x = 30
cup_y = 10


def buzz(ms=20):
	pin8.write_digital(1)
	sleep(ms)
	pin8.write_digital(0)


def set_led(green=0, blue=0):
	pin14.write_digital(1 - green)
	pin16.write_digital(1 - blue)


def clear():
	for i in range(1, 513):
		screen[i] = 0


def dot(x, y):
	x = int(x)
	y = int(y)
	if x < 0 or x > 63 or y < 0 or y > 31:
		return
	i = 1 + (y // 8) * 128 + x * 2
	bit = 1 << (y % 8)
	screen[i] = screen[i] | bit
	screen[i + 1] = screen[i + 1] | bit


def write(oled, text, slow=False):
	set_address(oled)
	clear()
	if slow:
		draw_screen()
	lines = text.split("|")
	for row in range(len(lines)):
		line = lines[row]
		if slow:
			for col in range(len(line)):
				if line[col] != " ":
					add_text(col, row, line[col])
					sleep(40)
		else:
			add_text(0, row, line, 0)
	if not slow:
		draw_screen()
	set_address(GAME)


def draw_flag(x, y=10):
	for i in range(1, 10):
		dot(x, y - i)
	for i in range(1, 5):
		dot(x + i, y - 8)
	for i in range(1, 3):
		dot(x + i, y - 9)
		dot(x + i, y - 7)
	for i in range(-2, 3):
		dot(x + i, y)


def draw_ball(x, y):
	for i in range(4):
		for j in range(4):
			corner = (i == 0 or i == 3) and (j == 0 or j == 3)
			if not corner:
				dot(x - 1 + i, y - 1 + j)


def draw_course(bx, by, angle=None):
	clear()
	draw_flag(cup_x)
	if angle is not None:
		draw_arrow(bx + 0.5, by + 0.5, angle)
	draw_ball(bx, by)
	draw_screen()


def draw_arrow(ox, oy, angle):
	a = math.radians(angle)
	sx = math.sin(a)
	sy = -math.cos(a)
	tip_x = ox + sx * 15
	tip_y = oy + sy * 15
	x1 = int(min(ox, tip_x)) - 5
	x2 = int(max(ox, tip_x)) + 5
	y1 = int(min(oy, tip_y)) - 5
	y2 = int(max(oy, tip_y)) + 5
	for y in range(max(0, y1), min(32, y2)):
		for x in range(max(0, x1), min(64, x2)):
			dx = x - ox
			dy = y - oy
			along = dx * sx + dy * sy
			side = abs(dy * sx - dx * sy)
			if along >= 4 and along <= 9 and side <= 1:
				dot(x, y)
			elif along > 9 and along <= 15 and side <= (15 - along) * 3.5 / 6:
				dot(x, y)


def read_stick(p):
	total = 0
	for i in range(4):
		total += p.read_analog()
	return total // 4


def stick_centre(p):
	total = 0
	for i in range(8):
		total += read_stick(p)
		sleep(5)
	c = total // 8
	if abs(c - 511) > 200:
		c = 511
	return c


def forget_buttons():
	button_a.was_pressed()
	button_b.was_pressed()


def get_button():
	if button_a.was_pressed():
		buzz()
		return "A"
	if button_b.was_pressed():
		buzz()
		return "B"
	return None


def wait_button(timeout=0):
	forget_buttons()
	start = running_time()
	while True:
		b = get_button()
		if b:
			return b
		if timeout and running_time() - start > timeout:
			return "B"
		sleep(20)


def get_ready():
	set_led()
	sleep(500)
	set_led(green=1)


def read_swing():
	biggest = 0
	start = running_time()
	while running_time() - start < 2000:
		x, y, z = accelerometer.get_values()
		size = x * x + y * y + z * z
		if size > biggest:
			biggest = size
	set_led()
	result = int(math.sqrt(biggest)) - 1000
	if result < 0:
		result = 0
	return result


def calibrate():
	global power
	try:
		accelerometer.set_range(8000)
	except AttributeError:
		pass
	set_led()
	write(GAME, "CALIBRATE|SWING|PRESS A TO|CALIBRATE")
	write(INFO, "SWING WITH|YOUR MAXIMUM|POWER")
	forget_buttons()
	while get_button() != "A":
		sleep(20)
	best = 0
	while True:
		write(GAME, "GET IN|POSITION|WAIT FOR|GREEN LED")
		write(INFO, "HOLD STILL|THEN SWING|WHEN GREEN")
		get_ready()
		s = read_swing()
		if s > best:
			best = s
		write(GAME, "SWING " + str(s) + "|BEST  " + str(best) + "|CAN YOU DO|BETTER?")
		write(INFO, "A: TRY AGAIN|B: PLAY")
		if wait_button() == "B":
			power = max(best, 300)
			return


def story():
	write(INFO, "")
	write(GAME, "YOU WERE|ALONE IN A|GOLF PARK.", True)
	sleep(1000)
	write(INFO, "YOU SEE|SOMEONE|FAMILIAR.", True)
	sleep(1000)
	write(INFO, "")
	write(GAME, "HIS NAME IS|JEFF AND HE|INVITES YOU|TO PLAY.", True)
	sleep(3000)


def draw_number(n):
	clear()
	digit = Image(str(n))
	for row in range(5):
		for col in range(5):
			if digit.get_pixel(col, row) > 0:
				for i in range(3):
					for j in range(3):
						dot(24 + col * 3 + i, 4 + row * 3 + j)
	for i in range(6):
		for y in range(11 - i, 12 + i):
			if n > 1:
				dot(10 + i, y)
			if n < 7:
				dot(53 - i, y)
	add_text(0, 3, "A:OK  B:MENU", 0)
	draw_screen()


def choose_holes():
	write(INFO, "JEFF:|HOW MANY|HOLES YOU|WANNA PLAY?")
	middle = stick_centre(pin0)
	n = 1
	draw_number(n)
	ready = True
	forget_buttons()
	while True:
		move = read_stick(pin0) - middle
		if ready and abs(move) >= PUSH:
			ready = False
			buzz()
			if move > 0 and n < 7:
				n += 1
				draw_number(n)
			elif move < 0 and n > 1:
				n -= 1
				draw_number(n)
		elif abs(move) <= CENTRE_ZONE:
			ready = True
		b = get_button()
		if b == "A":
			return n
		if b == "B":
			return 0
		sleep(20)


def aim(bx, by, middle, strokes, hole):
	angle = math.degrees(math.atan2(cup_x - bx, by - cup_y))
	angle = int(round(angle / TURN_STEP)) * TURN_STEP
	distance = math.sqrt((cup_x - bx) ** 2 + (cup_y - by) ** 2)
	if distance > 30:
		club = 0
	elif distance > 16:
		club = 1
	elif distance > 7:
		club = 2
	else:
		club = 3
	up_before = 1
	down_before = 1
	changed = True
	forget_buttons()
	while True:
		if changed:
			draw_course(bx, by, angle)
			write(INFO, "HOLE " + str(hole) + " OF " + str(holes) + "|STROKE " + str(strokes + 1) + "|CLUB " + CLUB_NAMES[club] + "|A:HIT B:MENU")
			changed = False
		move = read_stick(pin0) - middle
		if abs(move) >= PUSH:
			if move > 0:
				angle += TURN_STEP
			else:
				angle -= TURN_STEP
			if angle > 180:
				angle -= 360
			if angle <= -180:
				angle += 360
			buzz(10)
			draw_course(bx, by, angle)
		up = pin13.read_digital()
		down = pin15.read_digital()
		if up == 0 and up_before == 1:
			club = (club - 1) % 4
			buzz()
			changed = True
		if down == 0 and down_before == 1:
			club = (club + 1) % 4
			buzz()
			changed = True
		up_before = up
		down_before = down
		b = get_button()
		if b == "B":
			return None
		if b == "A":
			write(INFO, "HOLD STILL|THEN SWING|WHEN GREEN")
			get_ready()
			return angle, club, read_swing()
		sleep(20)


def hit_ball(bx, by, angle, club, swing):
	strength = SENS * max(0, swing - MIN_SWING) / power
	wobble = 3 + 15 * max(0, strength - 1)
	length = CLUB_RANGE[club] * min(strength, 1.2) * random.uniform(0.9, 1.1)
	a = math.radians(angle + random.uniform(-wobble, wobble))
	end_x = min(61, max(1, bx + math.sin(a) * length))
	end_y = min(29, max(1, by - math.cos(a) * length))
	pin8.write_digital(1)
	music.pitch(220, 60, pin12, False)
	sleep(60)
	pin8.write_digital(0)
	for i in range(1, 9):
		f = 1 - (1 - i / 8) ** 2
		draw_course(bx + (end_x - bx) * f, by + (end_y - by) * f)
	gap = math.sqrt((end_x - cup_x) ** 2 + (end_y - cup_y) ** 2)
	return end_x, end_y, gap <= CUP_SIZE


def play_hole(hole, middle):
	global cup_x
	cup_x = random.randint(2, 58)
	bx = 31
	by = 28
	strokes = 0
	while strokes < MAX_STROKES:
		shot = aim(bx, by, middle, strokes, hole)
		if shot is None:
			return None
		strokes += 1
		bx, by, in_hole = hit_ball(bx, by, shot[0], shot[1], shot[2])
		if in_hole:
			set_led(green=1)
			music.play(music.BA_DING, pin12, False)
			draw_course(cup_x, cup_y)
			write(INFO, "IN THE HOLE!|STROKES " + str(strokes))
			buzz(150)
			sleep(1500)
			set_led()
			return strokes
		set_led(blue=1)
		sleep(400)
		set_led()
	write(INFO, "OUT OF|STROKES|SCORE " + str(MAX_STROKES))
	buzz(150)
	sleep(1500)
	return MAX_STROKES


def play():
	middle = stick_centre(pin0)
	while True:
		you = 0
		jeff = 0
		for hole in range(1, holes + 1):
			score = play_hole(hole, middle)
			if score is None:
				return
			jeff_score = random.randint(3, 5)
			you += score
			jeff += jeff_score
			write(GAME, "HOLE " + str(hole) + " DONE|YOU  " + str(score) + "|JEFF " + str(jeff_score) + "|LOW WINS")
			if hole < holes:
				write(INFO, "TOTAL|YOU  " + str(you) + "|JEFF " + str(jeff) + "|A: NEXT")
				if wait_button() == "B":
					return
			else:
				write(INFO, "TOTAL|YOU  " + str(you) + "|JEFF " + str(jeff))
				sleep(2500)
		if you < jeff:
			result = "YOU WIN!"
			set_led(green=1)
			music.play(music.POWER_UP, pin12, False)
		elif you > jeff:
			result = "JEFF WINS"
			music.play(music.POWER_DOWN, pin12, False)
		else:
			result = "A TIE!"
			music.play(music.BA_DING, pin12, False)
		buzz(300)
		write(GAME, result + "|YOU  " + str(you) + "|JEFF " + str(jeff))
		write(INFO, "GAME OVER|A:PLAY AGAIN|B: MENU")
		b = wait_button(60000)
		set_led()
		if b == "B":
			return


def solo():
	global holes
	calibrate()
	story()
	holes = choose_holes()
	if holes > 0:
		play()
