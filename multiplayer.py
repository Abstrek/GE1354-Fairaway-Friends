from microbit import *
import radio
import random
import gameplay
from gameplay import GAME, INFO, GAME_SONG, write, buzz, wait_button, calibrate, choose_holes, play_hole, stick_centre, play_song, final_result

RADIO_GROUP = 23

inbox = []
seen = []
my_id = 0
other_id = 0


def check_radio():
	global other_id
	try:
		message = radio.receive()
	except ValueError:
		return None
	if message is None:
		return None
	if message.startswith("K"):
		return message
	radio.send("K" + message)
	if message.startswith("P"):
		other_id = int(message[1:])
		radio.send("R%s:%d" % (message[1:], my_id))
		return None
	if message in seen:
		return None
	seen.append(message)
	for i in range(3):
		sleep(20)
		radio.send("K" + message)
	return message


def quit_game():
	buzz()
	for i in range(5):
		radio.send("Q")
		sleep(50)


def send(message):
	last_sent = -1000
	start = running_time()
	button_b.was_pressed()
	while running_time() - start < 120000:
		if running_time() - last_sent > 200:
			radio.send(message)
			last_sent = running_time()
		reply = check_radio()
		if reply == "K" + message:
			return True
		if reply == "Q" or button_b.was_pressed():
			quit_game()
			return False
		if reply and not reply.startswith("K") and not reply.startswith("R"):
			inbox.append(reply)
			return True
		sleep(10)
	return False


def wait_for(start_text):
	button_b.was_pressed()
	while True:
		if len(inbox) > 0:
			message = inbox.pop(0)
		else:
			message = check_radio()
		if message == "Q" or button_b.was_pressed():
			quit_game()
			return None
		if message and message.startswith(start_text):
			return message
		sleep(10)


def connect():
	global my_id
	my_id = random.randint(1, 30000)
	write(GAME, "SEARCHING|FOR PLAYER 2|...|B: CANCEL")
	write(INFO, "THE OTHER|PLAYER MUST|PICK MULTI-|PLAYER TOO")
	they_heard_me = False
	last_sent = -1000
	button_b.was_pressed()
	while other_id == 0 or not they_heard_me:
		if running_time() - last_sent > 300:
			radio.send("P%d" % my_id)
			last_sent = running_time()
		message = check_radio()
		if message and message.startswith("R%d:" % my_id):
			they_heard_me = True
		if button_b.was_pressed():
			buzz()
			return None
		sleep(10)
	start = running_time()
	while running_time() - start < 1500:
		check_radio()
		sleep(10)
	buzz(100)
	return my_id > other_id


def connection_lost():
	write(GAME, "CONNECTION|LOST OR|PLAYER LEFT")
	write(INFO, "A OR B:|MAIN MENU")
	buzz(300)
	wait_button(60000)


def agree_on_holes(host, me, them):
	pick = choose_holes("YOU ARE %s|HOW MANY|HOLES DO|YOU WANT?" % me)
	if pick == 0:
		quit_game()
		return []
	write(GAME, "YOU PICKED %d|WAITING FOR|%s...|B: QUIT" % (pick, them))
	if host:
		message = wait_for("N")
		if message is None:
			return None
		their_pick = int(message[1:])
		holes = random.choice([pick, their_pick])
		cups = []
		message = "G%d:%d" % (pick, holes)
		for i in range(holes):
			cup = random.randint(2, 58)
			cups.append(cup)
			message += ":%d" % cup
		if not send(message):
			return None
	else:
		if not send("N%d" % pick):
			return None
		message = wait_for("G")
		if message is None:
			return None
		numbers = []
		for part in message[1:].split(":"):
			numbers.append(int(part))
		their_pick = numbers[0]
		holes = numbers[1]
		cups = numbers[2:]
	write(INFO, "%s PICKED %d|%s PICKED %d|P1 CHOSE ONE|AT RANDOM" % (me, pick, them, their_pick))
	write(GAME, "WE PLAY|%d HOLES" % holes)
	buzz(100)
	sleep(3000)
	return cups


def game():
	global other_id
	other_id = 0
	inbox.clear()
	seen.clear()
	calibrate()
	host = connect()
	if host is None:
		return
	if host:
		me = "P1"
		them = "P2"
	else:
		me = "P2"
		them = "P1"
	write(GAME, "CONNECTED!|YOU ARE|" + me)
	write(INFO, "")
	sleep(2000)
	cups = agree_on_holes(host, me, them)
	if cups is None:
		connection_lost()
		return
	if len(cups) == 0:
		return
	gameplay.holes = len(cups)
	middle = stick_centre(pin0)
	my_total = 0
	their_total = 0
	for hole in range(1, len(cups) + 1):
		for turn in range(2):
			my_turn = (turn == 0 and host) or (turn == 1 and not host)
			if my_turn:
				write(GAME, "YOUR TURN|HOLE %d" % hole)
				buzz(200)
				sleep(1500)
				score = play_hole(hole, middle, cups[hole - 1])
				if score is None:
					quit_game()
					return
				my_total += score
				if not send("S%d:%d" % (hole, score)):
					connection_lost()
					return
			else:
				write(GAME, "WAITING FOR|%s TO FINISH|HOLE %d|B: QUIT" % (them, hole))
				write(INFO, "TOTAL|%s  %d|%s  %d" % (me, my_total, them, their_total))
				play_song(GAME_SONG, 150)
				message = wait_for("S%d:" % hole)
				if message is None:
					connection_lost()
					return
				score = int(message.split(":")[1])
				their_total += score
				write(INFO, "%s SCORED %d|ON HOLE %d" % (them, score, hole))
				buzz(100)
				sleep(2000)
		write(GAME, "HOLE %d DONE|%s  %d|%s  %d|LOW WINS" % (hole, me, my_total, them, their_total))
		write(INFO, "")
		sleep(2500)
	final_result(me, them, my_total, their_total, "|A OR B:|MAIN MENU")


def multiplayer():
	radio.config(group=RADIO_GROUP, power=7)
	radio.on()
	game()
	radio.off()
