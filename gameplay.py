from microbit import*
import math,random,music
from ssd1306 import screen,set_address,draw_screen
from ssd1306_text import add_text
MUSIC=True
SOUNDS=True
GAME=60
INFO=61
TURN_STEP=5
PUSH=300
CENTRE=90
CLUBS=['DRIVER','IRON','WEDGE','PUTTER']
RANGE=[40,24,12,5]
CUP_SIZE=3
MAX_STROKES=6
SENS=2.5
MIN_SWING=80
YARDS=5
EDGE=4
CALM='E4:4 G4:4 C5:8 B4:4 G4:4 A4:8 F4:4 E4:4 D4:8 C4:4 E4:4 G4:8 r:8'.split()
FAST='A3:2 C4 E4 A4 G4 E4 C4 E4 F3 A3 C4 F4 E4 C4 B3 G#3'.split()
power=300
holes=1
cup_x=30
y_mid=511
def tune(notes,bpm):
	if MUSIC:music.set_tempo(ticks=4,bpm=bpm);music.play(notes,pin12,False,True)
def sound(effect):
	if SOUNDS:music.play(effect,pin12,False)
def buzz(ms=20):pin8.write_digital(1);sleep(ms);pin8.write_digital(0)
def set_led(green=0,blue=0):pin14.write_digital(1-green);pin16.write_digital(1-blue)
def clear():
	for i in range(1,513):screen[i]=0
def dot(x,y):
	x=int(x);y=int(y)
	if 0<=x<64 and 0<=y<32:i=1+y//8*128+x*2;screen[i]|=1<<y%8;screen[i+1]=screen[i]
def write(oled,text,slow=False):
	set_address(oled);clear();draw_screen();row=0
	for line in text.split('|'):
		if slow:
			for col in range(len(line)):
				if line[col]!=' ':add_text(col,row,line[col]);sleep(40)
		else:add_text(0,row,line)
		row+=1
	set_address(GAME)
def draw_list(lines,row):
	clear()
	for i in range(len(lines)):add_text((12-len(lines[i]))//2,i,lines[i],0)
	for i in range(1+row*128,129+row*128):screen[i]^=255
	draw_screen()
def draw_flag(x,y=10):
	for i in range(1,10):dot(x,y-i)
	for i in range(1,5):
		dot(x+i,y-8)
		if i<3:dot(x+i,y-9);dot(x+i,y-7)
	for i in range(-2,3):dot(x+i,y)
def draw_course(bx,by,angle=None):
	clear();draw_flag(cup_x)
	if angle is not None:
		sx=math.sin(math.radians(angle));sy=-math.cos(math.radians(angle))
		for y in range(int(by)-16,int(by)+17):
			for x in range(int(bx)-16,int(bx)+17):
				dx=x-bx-.5;dy=y-by-.5;along=dx*sx+dy*sy;side=abs(dy*sx-dx*sy)
				if 4<=along<=9 and side<=1 or 9<along<=15 and side<=(15-along)*.58:dot(x,y)
	for i in range(16):
		if i not in(0,3,12,15):dot(bx-1+i%4,by-1+i//4)
	draw_screen()
def read_stick(p):return(p.read_analog()+p.read_analog()+p.read_analog()+p.read_analog())//4
def stick_centre(p):
	total=0
	for i in range(8):total+=read_stick(p);sleep(5)
	c=total//8
	if abs(c-511)>200:c=511
	return c
class UpDown:
	def __init__(self):self.ready=True;self.keys=1,1
	def step(self):
		step=0;move=read_stick(pin1)-y_mid
		if self.ready and abs(move)>=PUSH:self.ready=False;step=-1 if move>0 else 1
		elif abs(move)<=CENTRE:self.ready=True
		keys=pin13.read_digital(),pin15.read_digital()
		if keys[0]<self.keys[0]:step=-1
		if keys[1]<self.keys[1]:step=1
		self.keys=keys;return step
def forget_buttons():button_a.was_pressed();button_b.was_pressed()
def get_button():
	if button_a.was_pressed():buzz();return'A'
	if button_b.was_pressed():buzz();return'B'
def wait_button(timeout=0):
	forget_buttons();start=running_time()
	while True:
		b=get_button()
		if b:return b
		if timeout and running_time()-start>timeout:return'B'
		sleep(20)
def read_swing():
	set_led();sleep(500);set_led(1);biggest=0;start=running_time()
	while running_time()-start<2000:x,y,z=accelerometer.get_values();biggest=max(biggest,x*x+y*y+z*z)
	set_led();return max(0,int(math.sqrt(biggest))-1000)
def calibrate():
	global power
	try:accelerometer.set_range(8000)
	except AttributeError:0
	set_led();write(GAME,'CALIBRATE|SWING|PRESS A TO|CALIBRATE');write(INFO,'SWING WITH|YOUR MAXIMUM|POWER')
	while wait_button()!='A':0
	best=0
	while True:
		write(GAME,'GET IN|POSITION|WAIT FOR|GREEN LED');write(INFO,'HOLD STILL|THEN SWING|WHEN GREEN');s=read_swing();best=max(best,s);write(GAME,'SWING %d|BEST  %d|CAN YOU DO|BETTER?'%(s,best));write(INFO,'A: TRY AGAIN|B: PLAY')
		if wait_button()=='B':power=max(best,300);return
def story():write(INFO,'');write(GAME,'YOU WERE|ALONE IN A|GOLF PARK.',True);sleep(1000);write(INFO,'YOU SEE|SOMEONE|FAMILIAR.',True);sleep(1000);write(INFO,'');write(GAME,'HIS NAME IS|JEFF AND HE|INVITES YOU|TO PLAY.',True);sleep(3000)
def choose_holes(question='JEFF:|HOW MANY|HOLES YOU|WANNA PLAY?'):
	write(INFO,question);middle=stick_centre(pin0);n=0;ready=True;forget_buttons()
	while True:
		move=read_stick(pin0)-middle;step=0
		if ready and abs(move)>=PUSH:ready=False;buzz();step=1 if move>0 else-1
		elif abs(move)<=CENTRE:ready=True
		if n==0 or 1<=n+step<=7 and step:
			n=max(1,n+step);clear();digit=Image(str(n))
			for i in range(225):
				if digit.get_pixel(i%15//3,i//45):dot(24+i%15,4+i//15)
			for i in range(6):
				for y in range(11-i,12+i):
					if n>1:dot(10+i,y)
					if n<7:dot(53-i,y)
			add_text(0,3,'A:OK  B:MENU',0);draw_screen()
		b=get_button()
		if b=='A':return n
		if b=='B':return 0
		sleep(20)
def draw_clubs(club):draw_list(['%-6s %3d'%(CLUBS[i],RANGE[i]*YARDS)for i in range(4)],club)
def hole_screens(bx,by,hole,strokes,club,aiming):
	away='%d YDS AWAY'%int(math.sqrt((cup_x-bx)**2+(10-by)**2)*YARDS)
	if aiming:write(INFO,'%s|CLUB %s|STICK: AIM|A:HIT B:CLUB'%(away,CLUBS[club]))
	else:write(INFO,'%s|HOLE %d OF %d|STROKE %d|A:OK B:MENU'%(away,hole,holes,strokes+1));draw_clubs(club)
def start_angle(bx,by):
	right=(bx<1+EDGE)-(bx>61-EDGE);down=(by<1+EDGE)-(by>29-EDGE)
	if right==0 and down==0:return 0
	return int(round(math.degrees(math.atan2(right,-down))/TURN_STEP))*TURN_STEP
def take_shot(bx,by,middle,hole,strokes,club):
	nav=UpDown();aiming=False;angle=start_angle(bx,by);hole_screens(bx,by,hole,strokes,club,aiming);forget_buttons()
	while True:
		if aiming:
			mx=read_stick(pin0)-middle;my=read_stick(pin1)-y_mid
			if mx*mx+my*my>=PUSH*PUSH:
				turn=(math.degrees(math.atan2(mx,my))-angle+180)%360-180
				if abs(turn)>=TURN_STEP:angle=(angle+(TURN_STEP if turn>0 else-TURN_STEP)+180)%360-180;buzz(10);draw_course(bx,by,angle)
		else:
			step=nav.step()
			if step:buzz();club=(club+step)%4;draw_clubs(club)
		b=get_button()
		if b=='B'and not aiming:return
		if b=='B'or b=='A'and not aiming:
			aiming=not aiming;angle=start_angle(bx,by);hole_screens(bx,by,hole,strokes,club,aiming)
			if aiming:draw_course(bx,by,angle)
		elif b=='A':write(INFO,'HOLD STILL|THEN SWING|WHEN GREEN');return angle,club,read_swing()
		sleep(20)
def hit_ball(bx,by,angle,club,swing):
	strength=SENS*max(0,swing-MIN_SWING)/power;length=RANGE[club]*min(strength,1.2)*random.uniform(.9,1.1);a=math.radians(angle);dx=math.sin(a);dy=-math.cos(a)
	while length>0 and not(1<=bx+dx*length<=61 and 1<=by+dy*length<=29):length-=.5
	length=max(0,length);ex=bx+dx*length;ey=by+dy*length
	if SOUNDS:music.pitch(220,60,pin12,False)
	buzz(60)
	for i in range(1,9):f=1-(1-i/8)**2;draw_course(bx+(ex-bx)*f,by+(ey-by)*f)
	return ex,ey,math.sqrt((ex-cup_x)**2+(ey-10)**2)<=CUP_SIZE
def play_hole(hole,middle,cup=None):
	global cup_x;cup_x=random.randint(2,58)if cup is None else cup;bx=31;by=28;strokes=0;club=0
	while strokes<MAX_STROKES:
		tune(FAST,150);shot=take_shot(bx,by,middle,hole,strokes,club)
		if shot is None:return
		strokes+=1;club=shot[1];bx,by,holed=hit_ball(bx,by,shot[0],club,shot[2])
		if holed:set_led(1);sound(music.BA_DING);draw_course(cup_x,10);write(INFO,'IN THE HOLE!|STROKES %d'%strokes);buzz(150);sleep(1500);set_led();return strokes
		set_led(0,1);sleep(400);set_led()
	write(INFO,'OUT OF|STROKES|SCORE %d'%MAX_STROKES);buzz(150);sleep(1500);return MAX_STROKES
def final_result(me,them,a,b,menu_text):
	if a<b:result='YOU WIN!';set_led(1);sound(music.POWER_UP)
	elif a>b:result=them+' WINS';sound(music.POWER_DOWN)
	else:result='A TIE!';sound(music.BA_DING)
	buzz(300);write(GAME,'%s|%s  %d|%s  %d'%(result,me,a,them,b));write(INFO,'GAME OVER|'+menu_text);b=wait_button(60000);set_led();return b
def play():
	middle=stick_centre(pin0)
	while True:
		you=0;jeff=0
		for hole in range(1,holes+1):
			score=play_hole(hole,middle)
			if score is None:return
			j=random.randint(3,5);you+=score;jeff+=j;write(GAME,'HOLE %d DONE|YOU  %d|JEFF %d|LOW WINS'%(hole,score,j));write(INFO,'TOTAL|YOU  %d|JEFF %d|A: NEXT'%(you,jeff))
			if wait_button(5000 if hole==holes else 0)=='B'and hole<holes:return
		if final_result('YOU','JEFF',you,jeff,'A:PLAY AGAIN|B: MENU')=='B':return
def solo():
	global holes;calibrate();story();holes=choose_holes()
	if holes:play()