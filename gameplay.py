from microbit import *
import math
import random
import music
from ssd1306 import screen, set_address, draw_screen
from ssd1306_text import add_text

MUSIC = True
SOUNDS = True

GAME = 0x3C
INFO = 0x3D

STICK_PUSH = 300
STICK_CENTRE = 90
TURN_STEP = 5

CLUBS = ["DRIVER", "IRON", "WEDGE", "PUTTER"]
CLUB_RANGE = [40, 24, 12, 5]
YARDS_PER_PIXEL = 5

CUP_Y = 10
CUP_SIZE = 3
MAX_STROKES = 6
SENSITIVITY = 2.5
MIN_SWING = 80
EDGE = 4

LEFT = 1
RIGHT = 61
TOP = 1
BOTTOM = 29

CALM_SONG = "E4:4 G4:4 C5:8 B4:4 G4:4 A4:8 F4:4 E4:4 D4:8 C4:4 E4:4 G4:8 r:8".split()
GAME_SONG = "A3:2 C4 E4 A4 G4 E4 C4 E4 F3 A3 C4 F4 E4 C4 B3 G#3".split()

power = 300
holes = 1
cup_x = 30
y_centre = 511


def play_song(song, bpm):
	if MUSIC:
		music.set_tempo(ticks=4, bpm=bpm)
		music.play(song, pin12, False, True)


def play_sound(effect):
	if SOUNDS:
		music.play(effect, pin12, False)


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
	screen[i] = screen[i] | (1 << (y % 8))
	screen[i + 1] = screen[i]


def write(oled, text, slow=False):
	set_address(oled)
	clear()
	draw_screen()
	lines = text.split("|")
	for row in range(len(lines)):
		line = lines[row]
		if not slow:
			add_text(0, row, line)
			continue
		for col in range(len(line)):
			if line[col] != " ":
				add_text(col, row, line[col])
				sleep(40)
	set_address(GAME)


def draw_list(lines, selected):
	clear()
	for row in range(len(lines)):
		x = (12 - len(lines[row])) // 2
		add_text(x, row, lines[row], 0)
	start = 1 + selected * 128
	for i in range(start, start + 128):
		screen[i] = screen[i] ^ 255
	draw_screen()


def draw_flag(x, y=CUP_Y):
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
	for row in range(4):
		for col in range(4):
			corner = (row == 0 or row == 3) and (col == 0 or col == 3)
			if not corner:
				dot(x - 1 + col, y - 1 + row)


def draw_arrow(bx, by, angle):
	ax = math.sin(math.radians(angle))
	ay = -math.cos(math.radians(angle))
	for y in range(int(by) - 16, int(by) + 17):
		for x in range(int(bx) - 16, int(bx) + 17):
			dx = x - bx - 0.5
			dy = y - by - 0.5
			along = dx * ax + dy * ay
			side = abs(dy * ax - dx * ay)
			if along >= 4 and along <= 9 and side <= 1:
				dot(x, y)
			elif along > 9 and along <= 15 and side <= (15 - along) * 0.58:
				dot(x, y)


def draw_course(bx, by, angle=None):
	clear()
	draw_flag(cup_x)
	if angle is not None:
		draw_arrow(bx, by, angle)
	draw_ball(bx, by)
	draw_screen()


def read_stick(pin):
	total = 0
	for i in range(4):
		total += pin.read_analog()
	return total // 4


def stick_centre(pin):
	total = 0
	for i in range(8):
		total += read_stick(pin)
		sleep(5)
	centre = total // 8
	if abs(centre - 511) > 200:
		centre = 511
	return centre


class UpDown:
	def __init__(self):
		self.ready = True
		self.up_before = 1
		self.down_before = 1

	def step(self):
		step = 0
		move = read_stick(pin1) - y_centre
		if self.ready and abs(move) >= STICK_PUSH:
			self.ready = False
			if move > 0:
				step = -1
			else:
				step = 1
		elif abs(move) <= STICK_CENTRE:
			self.ready = True
		up = pin13.read_digital()
		down = pin15.read_digital()
		if up == 0 and self.up_before == 1:
			step = -1
		if down == 0 and self.down_before == 1:
			step = 1
		self.up_before = up
		self.down_before = down
		return step


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
		button = get_button()
		if button:
			return button
		if timeout > 0 and running_time() - start > timeout:
			return "B"
		sleep(20)


def read_swing():
	set_led()
	sleep(500)
	set_led(green=1)
	biggest = 0
	start = running_time()
	while running_time() - start < 2000:
		x, y, z = accelerometer.get_values()
		biggest = max(biggest, x * x + y * y + z * z)
	set_led()
	return max(0, int(math.sqrt(biggest)) - 1000)


def calibrate():
	global power
	try:
		accelerometer.set_range(8000)
	except AttributeError:
		pass
	set_led()
	write(GAME, "CALIBRATE|SWING|PRESS A TO|CALIBRATE")
	write(INFO, "SWING WITH|YOUR MAXIMUM|POWER")
	while wait_button() != "A":
		pass
	best = 0
	while True:
		write(GAME, "GET IN|POSITION|WAIT FOR|GREEN LED")
		write(INFO, "HOLD STILL|THEN SWING|WHEN GREEN")
		swing = read_swing()
		best = max(best, swing)
		write(GAME, "SWING %d|BEST  %d|CAN YOU DO|BETTER?" % (swing, best))
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


def draw_holes(n):
	clear()
	digit = Image(str(n))
	for row in range(15):
		for col in range(15):
			if digit.get_pixel(col // 3, row // 3) > 0:
				dot(24 + col, 4 + row)
	for i in range(6):
		for y in range(11 - i, 12 + i):
			if n > 1:
				dot(10 + i, y)
			if n < 7:
				dot(53 - i, y)
	add_text(0, 3, "A:OK  B:MENU", 0)
	draw_screen()


def choose_holes(question="JEFF:|HOW MANY|HOLES YOU|WANNA PLAY?"):
	write(INFO, question)
	middle = stick_centre(pin0)
	n = 1
	draw_holes(n)
	ready = True
	forget_buttons()
	while True:
		move = read_stick(pin0) - middle
		if ready and abs(move) >= STICK_PUSH:
			ready = False
			buzz()
			if move > 0 and n < 7:
				n += 1
				draw_holes(n)
			elif move < 0 and n > 1:
				n -= 1
				draw_holes(n)
		elif abs(move) <= STICK_CENTRE:
			ready = True
		button = get_button()
		if button == "A":
			return n
		if button == "B":
			return 0
		sleep(20)


def yards_to_cup(bx, by):
	pixels = math.sqrt((cup_x - bx) ** 2 + (CUP_Y - by) ** 2)
	return int(pixels * YARDS_PER_PIXEL)


def keep_angle_in_range(angle):
	while angle > 180:
		angle -= 360
	while angle <= -180:
		angle += 360
	return angle


def start_angle(bx, by):
	right = 0
	down = 0
	if bx < LEFT + EDGE:
		right = 1
	if bx > RIGHT - EDGE:
		right = -1
	if by < TOP + EDGE:
		down = 1
	if by > BOTTOM - EDGE:
		down = -1
	if right == 0 and down == 0:
		return 0
	angle = math.degrees(math.atan2(right, -down))
	return int(round(angle / TURN_STEP)) * TURN_STEP


def pick_club(bx, by, hole, strokes, club):
	write(INFO, "%d YDS AWAY|HOLE %d OF %d|STROKE %d|A:OK B:MENU" % (yards_to_cup(bx, by), hole, holes, strokes + 1))
	labels = []
	for i in range(4):
		labels.append("%-6s %3d" % (CLUBS[i], CLUB_RANGE[i] * YARDS_PER_PIXEL))
	draw_list(labels, club)
	nav = UpDown()
	forget_buttons()
	while True:
		step = nav.step()
		if step != 0:
			buzz()
			club = (club + step) % 4
			draw_list(labels, club)
		button = get_button()
		if button == "A":
			return club
		if button == "B":
			return None
		sleep(20)


def aim(bx, by, middle, club):
	write(INFO, "%d YDS AWAY|CLUB %s|STICK: AIM|A:HIT B:CLUB" % (yards_to_cup(bx, by), CLUBS[club]))
	angle = start_angle(bx, by)
	draw_course(bx, by, angle)
	forget_buttons()
	while True:
		mx = read_stick(pin0) - middle
		my = read_stick(pin1) - y_centre
		if mx * mx + my * my >= STICK_PUSH * STICK_PUSH:
			target = math.degrees(math.atan2(mx, my))
			turn = keep_angle_in_range(target - angle)
			if abs(turn) >= TURN_STEP:
				if turn > 0:
					angle = keep_angle_in_range(angle + TURN_STEP)
				else:
					angle = keep_angle_in_range(angle - TURN_STEP)
				buzz(10)
				draw_course(bx, by, angle)
		button = get_button()
		if button == "B":
			return None
		if button == "A":
			write(INFO, "HOLD STILL|THEN SWING|WHEN GREEN")
			return angle
		sleep(20)


def hit_ball(bx, by, angle, club, swing):
	strength = SENSITIVITY * max(0, swing - MIN_SWING) / power
	length = CLUB_RANGE[club] * min(strength, 1.2) * random.uniform(0.9, 1.1)
	dx = math.sin(math.radians(angle))
	dy = -math.cos(math.radians(angle))
	while length > 0:
		end_x = bx + dx * length
		end_y = by + dy * length
		if LEFT <= end_x <= RIGHT and TOP <= end_y <= BOTTOM:
			break
		length -= 0.5
	length = max(0, length)
	end_x = bx + dx * length
	end_y = by + dy * length
	if SOUNDS:
		music.pitch(220, 60, pin12, False)
	buzz(60)
	for i in range(1, 9):
		f = 1 - (1 - i / 8) ** 2
		draw_course(bx + (end_x - bx) * f, by + (end_y - by) * f)
	gap = math.sqrt((end_x - cup_x) ** 2 + (end_y - CUP_Y) ** 2)
	return end_x, end_y, gap <= CUP_SIZE


def play_hole(hole, middle, cup=None):
	global cup_x
	if cup is None:
		cup = random.randint(2, 58)
	cup_x = cup
	bx = 31
	by = 28
	strokes = 0
	club = 0
	while strokes < MAX_STROKES:
		play_song(GAME_SONG, 150)
		club = pick_club(bx, by, hole, strokes, club)
		if club is None:
			return None
		angle = aim(bx, by, middle, club)
		if angle is None:
			continue
		swing = read_swing()
		strokes += 1
		bx, by, in_hole = hit_ball(bx, by, angle, club, swing)
		if in_hole:
			set_led(green=1)
			play_sound(music.BA_DING)
			draw_course(cup_x, CUP_Y)
			write(INFO, "IN THE HOLE!|STROKES %d" % strokes)
			buzz(150)
			sleep(1500)
			set_led()
			return strokes
		set_led(blue=1)
		sleep(400)
		set_led()
	write(INFO, "OUT OF|STROKES|SCORE %d" % MAX_STROKES)
	buzz(150)
	sleep(1500)
	return MAX_STROKES


def final_result(me, them, my_score, their_score, menu_text):
	if my_score < their_score:
		result = "YOU WIN!"
		set_led(green=1)
		play_sound(music.POWER_UP)
	elif my_score > their_score:
		result = them + " WINS"
		play_sound(music.POWER_DOWN)
	else:
		result = "A TIE!"
		play_sound(music.BA_DING)
	buzz(300)
	write(GAME, "%s|%s  %d|%s  %d" % (result, me, my_score, them, their_score))
	write(INFO, "GAME OVER|" + menu_text)
	button = wait_button(60000)
	set_led()
	return button


def play():
	middle = stick_centre(pin0)
	while True:
		my_total = 0
		jeff_total = 0
		for hole in range(1, holes + 1):
			score = play_hole(hole, middle)
			if score is None:
				return
			jeff_score = random.randint(3, 5)
			my_total += score
			jeff_total += jeff_score
			write(GAME, "HOLE %d DONE|YOU  %d|JEFF %d|LOW WINS" % (hole, score, jeff_score))
			write(INFO, "TOTAL|YOU  %d|JEFF %d|A: NEXT" % (my_total, jeff_total))
			if hole < holes:
				if wait_button() == "B":
					return
			else:
				wait_button(5000)
		if final_result("YOU", "JEFF", my_total, jeff_total, "A:PLAY AGAIN|B: MENU") == "B":
			return


def solo():
	global holes
	calibrate()
	story()
	holes = choose_holes()
	if holes > 0:
		play()
