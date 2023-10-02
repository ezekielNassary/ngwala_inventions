from machine import UART, I2C, Pin, WDT
from mfrc522 import MFRC522
from pico_i2c_lcd import I2cLcd
import time
import _thread
import gc
import machine
import json


class App:
    def __init__(self):
        self.wdt = WDT(timeout=8000)
        self.dc = _thread.allocate_lock()
        self.lcd = None
        try:
            self.lcd = I2cLcd(
                I2C(1, sda=Pin(14), scl=Pin(15), freq=400000), 0x27, 4, 20
            )
        except:
            self.lcd = I2cLcd(
                I2C(1, sda=Pin(14), scl=Pin(15), freq=400000), 0x3F, 4, 20
            )
        self.rd = MFRC522(spi_id=0, sck=2, miso=4, mosi=3, cs=1, rst=0)
        self.gprs = UART(0, baudrate=9600, rx=Pin(17),
                         tx=Pin(16), timeout=2000)
        self.tsp = time.sleep

        self.flow = Pin(18, Pin.IN)
        self.sensor_pin = Pin(19, Pin.IN)
        self.led = Pin(20, Pin.OUT)
        self.buzzer = Pin(28, Pin.OUT)
        self.valve = Pin(22, Pin.OUT)
        self.pump = Pin(22, Pin.OUT)
        self.button = machine.Pin(21, machine.Pin.IN, machine.Pin.PULL_UP)
        self.charge = Pin(27, Pin.OUT)
