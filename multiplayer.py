from microbit import*
import radio,random,gameplay
from gameplay import GAME,INFO,write,buzz,calibrate,choose_holes,play_hole,stick_centre,tune,FAST,final_result
GROUP=23
inbox=[]
seen=[]
me_id=0
other_id=0
def poll():
	global other_id
	try:m=radio.receive()
	except ValueError:return
	if not m or m[0]=='K':return m
	radio.send('K'+m)
	if m[0]=='P':other_id=int(m[1:]);radio.send('R%s:%d'%(m[1:],me_id))
	elif m not in seen:
		seen.append(m)
		for i in range(3):sleep(20);radio.send('K'+m)
		return m
def give_up():
	buzz()
	for i in range(5):radio.send('Q');sleep(50)
def send(msg):
	last=-999;start=running_time();button_b.was_pressed()
	while running_time()-start<120000:
		if running_time()-last>200:radio.send(msg);last=running_time()
		m=poll()
		if m=='K'+msg:return True
		if m=='Q'or button_b.was_pressed():give_up();return False
		if m and m[0]not in'KR':inbox.append(m);return True
		sleep(10)
	return False
def wait_for(start):
	button_b.was_pressed()
	while True:
		m=inbox.pop(0)if inbox else poll()
		if m=='Q'or button_b.was_pressed():give_up();return
		if m and m.startswith(start):return m
		sleep(10)
def connect():
	global me_id;me_id=random.randint(1,30000);write(GAME,'SEARCHING|FOR PLAYER 2|...|B: CANCEL');write(INFO,'THE OTHER|PLAYER MUST|PICK MULTI-|PLAYER TOO');heard=False;last=-999;button_b.was_pressed()
	while not(other_id and heard):
		if running_time()-last>300:radio.send('P%d'%me_id);last=running_time()
		m=poll()
		if m and m.startswith('R%d:'%me_id):heard=True
		if button_b.was_pressed():buzz();return
		sleep(10)
	start=running_time()
	while running_time()-start<1500:poll();sleep(10)
	buzz(100);return me_id>other_id
def lost():write(GAME,'CONNECTION|LOST OR|PLAYER LEFT');write(INFO,'A OR B:|MAIN MENU');buzz(300);gameplay.wait_button(60000)
def game():
	global other_id;other_id=0;inbox.clear();seen.clear();calibrate();host=connect()
	if host is None:return
	me,them=('P1','P2')if host else('P2','P1');write(GAME,'CONNECTED!|YOU ARE|'+me);write(INFO,'');sleep(2000);pick=choose_holes('YOU ARE %s|HOW MANY|HOLES DO|YOU WANT?'%me)
	if pick==0:give_up();return
	write(GAME,'YOU PICKED %d|WAITING FOR|%s...|B: QUIT'%(pick,them))
	if host:
		m=wait_for('N')
		if m is None:return lost()
		their_pick=int(m[1:]);holes=random.choice([pick,their_pick]);cups=[random.randint(2,58)for i in range(holes)]
		if not send('G%d:%d:'%(pick,holes)+':'.join([str(c)for c in cups])):return lost()
	else:
		if not send('N%d'%pick):return lost()
		m=wait_for('G')
		if m is None:return lost()
		parts=[int(p)for p in m[1:].split(':')];their_pick=parts[0];holes=parts[1];cups=parts[2:]
	write(INFO,'%s PICKED %d|%s PICKED %d|P1 CHOSE ONE|AT RANDOM'%(me,pick,them,their_pick));write(GAME,'WE PLAY|%d HOLES'%holes);buzz(100);sleep(3000);gameplay.holes=holes;middle=stick_centre(pin0);mine=0;theirs=0
	for hole in range(1,holes+1):
		for turn in range(2):
			if(turn==0)==host:
				write(GAME,'YOUR TURN|HOLE %d'%hole);buzz(200);sleep(1500);score=play_hole(hole,middle,cups[hole-1])
				if score is None:give_up();return
				mine+=score
				if not send('S%d:%d'%(hole,score)):return lost()
			else:
				write(GAME,'WAITING FOR|%s TO FINISH|HOLE %d|B: QUIT'%(them,hole));write(INFO,'TOTAL|%s  %d|%s  %d'%(me,mine,them,theirs));tune(FAST,150);m=wait_for('S%d:'%hole)
				if m is None:return lost()
				score=int(m.split(':')[1]);theirs+=score;write(INFO,'%s SCORED %d|ON HOLE %d'%(them,score,hole));buzz(100);sleep(2000)
		write(GAME,'HOLE %d DONE|%s  %d|%s  %d|LOW WINS'%(hole,me,mine,them,theirs));write(INFO,'');sleep(2500)
	final_result(me,them,mine,theirs,'|A OR B:|MAIN MENU')
def multiplayer():radio.config(group=GROUP,power=7);radio.on();game();radio.off()