from microbit import i2c
ADDR_3C=60
ADDR_3D=61
ADDR=ADDR_3C
screen=bytearray(513)
screen[0]=64
zoom=1
def set_address(addr):
	global ADDR,zoom
	if addr!=ADDR:zoom=-1
	ADDR=addr
def command(c):i2c.write(ADDR,b'\x00'+bytearray(c))
def initialize():
	for A in([174],[164],[213,240],[168,63],[211,0],[0],[141,20],[32,0],[33,0,127],[34,0,63],[161],[200],[218,18],[129,207],[217,241],[219,64],[166],[214,1],[175]):command(A)
def set_pos(col=0,page=0):command([176|page]);command([col*2&15]);command([16|col>>3])
def clear_oled(c=0):
	set_pos()
	for A in range(1,513):screen[A]=0
	draw_screen()
def set_zoom(v):
	global zoom
	if zoom!=v:command([214,v]);command([167-v]);zoom=v
def draw_screen():set_zoom(1);set_pos();i2c.write(ADDR,screen)