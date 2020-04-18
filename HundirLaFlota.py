# LET'S SINK THE FLOAT
import machine
import pyb
import framebuf
import time
import math

#Literals representing screen size
SCREEN_WIDTH = 64
SCREEN_HEIGHT = 32

torpedo_shooted = False
cannon_angle = 0
slope = 0.0

#Declare the trigger for shooting
trigger = pyb.Switch()

#Declare servo motor for cannon accuracy
servo = pyb.Servo(1)

#Declare torpedo hit LED
y12 = machine.Pin('Y12')

#Declare ADC slider input
y4 = machine.Pin('Y4')
adc = pyb.ADC(y4)

#Declare I2C screen
scl = machine.Pin('X9')
sda = machine.Pin('X10')
i2c = machine.I2C(scl=scl, sda=sda)

#Declare screen buffer
fbuf = framebuf.FrameBuffer(bytearray(SCREEN_WIDTH * SCREEN_HEIGHT // 8), SCREEN_WIDTH, SCREEN_HEIGHT, framebuf.MONO_HLSB)

tick = time.ticks_ms()


#Same function as map() in arduino but in Python
def arduino_map(x, in_min, in_max, out_min, out_max):
    return (x - in_min) * (out_max - out_min) / (in_max - in_min) + out_min

#Declare classes for diferent elements in the game
class Entity:
    def __init__(self, x, y, w, h, vx, vy):
        self.x = x;
        self.y = y;
        self.w = w;
        self.h = h;
        self.vx = vx;
        self.vy = vy;

    def draw(self, fbuf):
        fbuf.fill_rect(int(self.x), int(self.y), self.w, self.h, 1)

class Player(Entity):
    pass

class Torpedo(Entity):
    def update(self, portaaviones):
        global cannon_angle
        global slope
        global torpedo_shooted
        global torpedo_strike
        
        shoot_angle = arduino_map(cannon_angle, -90, 90, 0, 180)
        slope = math.tan(shoot_angle)
        
        if (cannon_angle < 0):
            self.x = self.x + (1 / slope) * - self.vx
        else:
            self.x = self.x + (1 / slope) * + self.vx

        self.y = self.y - self.vy 
        
        if (self.y <= 0 or self.x < 0 or self.x > SCREEN_WIDTH):
            self.x = 31
            self.y = 31
            torpedo_shooted = False
            return

        if ((self.y - 2) == portaaviones.y):
            if (self.x >= portaaviones.x and self.x <= portaaviones.x + portaaviones.w):
                fbuf.fill(0)
                fbuf.text('SCORE', 12, 14)
                i2c.writeto(8, fbuf)
                for i in range(5):
                    y12(1)
                    time.sleep(500)
                    y12(0)
                    time.sleep(500)
                self.x = 31
                self.y = 31
                torpedo_shooted = False
        
class Boat(Entity):
    def update(self):
        self.x += self.vx
        if (self.x <= 0):
            self.x = 0
            self.vx = -self.vx
        if (self.x >= SCREEN_WIDTH - self.w):
            self.x = SCREEN_WIDTH - self.w
            self.vx = -self.vx

class Portaviones(Boat):
    pass

class Fragata(Boat):
    pass

class Corbeta(Boat):
    pass

#Declare boats types, cannon and torpedo
torpedo = Torpedo(31, 31, 1, 1, 2, 2)
player = Player(31, 31, 1, 1, 0, 0)
portaaviones = Portaviones(30, 1, 10, 1, 1, 0)
y12(0)

def update_cannon():
    global cannon_angle
    adc_read = adc.read()
    cannon_angle = arduino_map(adc_read, 0, 255, -90, 90)
    servo.angle(int(cannon_angle), 500)
    time.sleep(1)

def update_torpedo_flag():
    global torpedo_shooted
    if pyb.Switch().value():
        torpedo_shooted = True

#Main loop
while True:
    if not torpedo_shooted:
        update_cannon()
    
    update_torpedo_flag()
    
    if torpedo_shooted:
        torpedo.update(portaaviones)
    
    portaaviones.update()
    fbuf.fill(0)
    portaaviones.draw(fbuf)
    torpedo.draw(fbuf)
    player.draw(fbuf)
    i2c.writeto(8, fbuf)
