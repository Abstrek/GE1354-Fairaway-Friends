from microbit import Image,i2c
import ssd1306
from ssd1306 import screen,set_zoom,set_pos
def add_text(x,y,text,draw=1):
	A=text
	if not A or x>=12:return
	for C in range(min(len(A),12-x)):
		G=Image(A[C])
		for D in range(5):
			E=0
			for F in range(1,6):
				if G.get_pixel(D,F-1):E|=1<<F
			B=x*10+y*128+C*10+D*2+1;screen[B]=screen[B+1]=E
	if draw:set_zoom(1);set_pos(x*5,y);i2c.write(ssd1306.ADDR,b'@'+screen[x*10+y*128+1:B+1])