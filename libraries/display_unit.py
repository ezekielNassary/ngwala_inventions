from pico_i2c_lcd import I2cLcd
from machine import I2C, Pin


class DisplayUnit:
    def __init__(self, sda, scl):
        self.sd = sda
        self.sc = scl
        self.row = 4
        self.col = 20
        self.addr = 1
        self.lcd = self.init_lcd()

    def lco(self):
        self.lcd.backlight_on()

    def lbf(self):
        self.lcd.clear()
        self.lcd.backlight_off()

    def printtxt(self, r, c, t):
        self.lcd.move_to(r, c)
        self.lcd.putstr(t)

    def lcr(self):
        self.lcd.clear()

    def lmt(self):
        self.lmt = self.lcd.move_to

    def pts(self):
        self.pts = self.lcd.putstr

    def init_lcd(self):
        try:
            return I2cLcd(I2C(self.addr, sda=Pin(self.sd), scl=Pin(self.sc), freq=400000), 0x27, self.row, self.col)
        except:
            return I2cLcd(I2C(self.addr, sda=Pin(self.sd), scl=Pin(self.sc), freq=400000), 0x3F, self.row, self.col)
