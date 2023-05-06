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
                I2C(0, sda=Pin(12), scl=Pin(13), freq=400000), 0x27, 2, 16
            )
        except:
            self.lcd = I2cLcd(
                I2C(0, sda=Pin(12), scl=Pin(13), freq=400000), 0x3F, 2, 16
            )
        self.rd = MFRC522(spi_id=0, sck=2, miso=4, mosi=3, cs=1, rst=0)
        self.gprs = UART(0, baudrate=9600, rx=Pin(17), tx=Pin(16))

        self.timer = time.time()
        self.tsp = time.sleep
        # ?uid=886490451&amount=100
        self.url="http://development-ngwala-sys.herokuapp.com/api/v1/amount/" 
        # self.url="http://worldtimeapi.org/api/timezone/Africa/Dar_es_Salaam" 
        self.gw = self.gprs.write   
        self.gr = self.gprs.read
        self.pt = time.time()
        self.stage = 0
        
        # flow rate sensor
        self.flow = Pin(21 , Pin.IN)
        self.flow_frequency = 0
        self.previous = 0
        self.calfactor=7.5
        self.balance=""

        self.menu_mode=True
        self.amount_entered=""
        self.user_card=""

        self.pausebtn = Pin(27 , Pin.OUT)
        self.leds = Pin(26, Pin.OUT)
        self.buzzer = Pin(6, Pin.OUT)
        self.valve = Pin(15, Pin.OUT)
        self.pump = Pin(25, Pin.OUT)

        # Create a map between keypad buttons and characters
        self.matrix_keys = [['1', '4', '7', '*'],
                            ['2', '5', '8', '0'],
                            ['3', '6', '9', '#'],
                            ['A', 'B', 'C', 'D']]
        # PINs according to schematic - Change the pins to match with your connections
        self.keypad_rows = [15,14,11,10]
        self.keypad_columns = [9,8,7,6]

        # Create two empty lists to set up pins ( Rows output and columns input )
        self.col_pins = []
        self.row_pins = []

        # Loop to assign GPIO pins and setup input and outputs
        for x in range(0,4):
            self.row_pins.append(Pin(self.keypad_rows[x], Pin.OUT))
            self.row_pins[x].value(1)
            self.col_pins.append(Pin(self.keypad_columns[x], Pin.IN, Pin.PULL_DOWN))
            self.col_pins[x].value(0)

        self.lbo = self.lcd.backlight_on
        self.lbf = self.lcd.backlight_off
        self.pts = self.lcd.putstr
        self.lmt = self.lcd.move_to
        self.lcr = self.lcd.clear

        self.rd = MFRC522(spi_id=0, sck=2, miso=4, mosi=3, cs=1, rst=0)
        self.gprs = UART(0, baudrate=9600, rx=Pin(17), tx=Pin(16))
        self.lcr()
        self.lmt(0,0)       #self.lmt(8,0) 
        self.pts("GETTING READY...")
        self.tsp(4)
        self.lcr()
        i=0
        while 0:
            self.wdt.feed()
            self.lmt(0,0)       #self.lmt(8,0) 
            self.pts("Intializing..")
            self.wdt.feed()
            self.lmt(i,1)
            self.pts(".")
            self.tsp(0.4)
            self.gw("AT+COPS?\r")
            rpsl= ""
            try:
                rpsl= self.gr().decode().split()
            except:
                pass
            if (len(rpsl) >= 4):
                if rpsl[2] == "0":
                    pass
                else:
                    try:
                        self.lcr()
                        self.lmt(0,0)
                        self.pts("Net:")
                        self.pts(str(rpsl[2].split(",")[2].replace('"', "")))
                        self.gw("AT+CSQ\r")
                        self.wdt.feed()
                        self.tsp(2)
                        strs = self.gr().decode().split()
                        vl = int(strs[strs.index('+CSQ:')+1].split(",")[0]) / 31
                        vl = vl*100 
                        self.lmt(0,1) 
                        self.pts(str("Strength: {:.2f}".format(vl))+"%")
                        self.wdt.feed()
                        self.tsp(3)
                        del strs, vl, rpsl
                        break
                    except:
                        pass
            if i < 16:
                self.lmt(i, 1)
                self.pts(".")
                i = i + 1
            else:
                i = 0
                
        self.tsp(1)
        self.lbf()
        
    def MenuEvent(self):
        self.lcr()
        self.lmt(0,0)
        self.pts("A. Dawa")
        self.lmt(0,1)
        self.pts("B. Lugha")
        # self.lmt(0,2)
        # self.pts("C. Token")
        loop=True
        while loop:
            x=self.scankeys()
            if x=="A":
                loop=False
                self.menuEvent1()
            if x=="B":
                print("lugha")
                loop=False
            if x=="C":
                print("Token")
                loop=False
            if x=="D":
                loop=False

    def menuEvent1(self):
        self.lcr()
        self.lmt(0,0)
        self.pts("A. Pata Dawa")
        self.lmt(0,1)
        self.pts("B. Salio")
        self.lmt(0,2)
        loop=True
        while loop:
            x=self.scankeys()
            if x == "A":
                loop=False
                self.subMenuEvent1()
            if x == "B":
                print("Salio")
                loop=False
            if x == "*":
                loop=False
                self.MenuEvent()
        
    def subMenuEvent1(self):
        self.lcr()
        self.lmt(0,0)
        self.pts("Weka kiasi")
        self.lmt(0,1)
        self.pts("Kiasi: ")
        
        loop=True
        i=6
        custkeys=['#','A','B','C','D','*']
        while loop:
             x=self.scankeys().replace(" ", "")
             if x != "":
                if (x in custkeys):
                    if x == '*':
                        self.amount_entered=""
                        self.lcr()
                        self.lmt(0,0)
                        self.pts("Enter Amount")
                        self.lmt(0,1)
                        self.pts("Amount: ")
                        i=6
                        self.amount_entered=""
                    if x == '#':
                        if self.balance > int(self.amount_entered):
                            self.dispensePaste(int(self.amount_entered))
                            loop=False
                        else:
                            self.lcr()
                            self.lmt(0,0)
                            self.pts("Kiasi ulichoweka ")
                            self.lmt(4,1)
                            self.pts("Kimezidi ")
                            self.tsp(3)
                            self.subMenuEvent1()
                    if x == 'D':
                        loop=False
                            
                else:
                    buton = str(x)
                    self.amount_entered += buton
                    self.lmt(i,1)
                    self.pts(buton)
                    i+=1
                    if i>16:
                        i=6
                        self.amount_entered=""
                    x=""
    def subMenuEvent2(self):
        self.lcr()
        self.lmt(0,0)
        self.pts("Your balance is:")
        self.lmt(0, 1)
        self.pts("%.2fL" % (self.balance))


    def scankeys(self): 
        keypressed=""
        self.wdt.feed() 
        for row in range(4):
            for col in range(4):
                self.row_pins[row].high()
                key = None
                if self.col_pins[col].value() == 1:
                    print("You have pressed:", self.matrix_keys[row][col])
                    keypressed = self.matrix_keys[row][col]
                    self.tsp(0.3)
            self.row_pins[row].low()
        return keypressed
            

        
    def countPulse(self,channel):
        self.flow_frequency += 1   
        
    def dispensePaste(self,bal):
        v=0.0
        loop=True
        # self.lbf()
        self.lcr()
        self.flow.irq(trigger=Pin.IRQ_RISING, handler=self.countPulse)
        while loop:
            self.wdt.feed()
            try:
                if time.time() - self.previous >= 1:
                    newbalance=bal-v
                    self.lmt(0,0)
                    self.pts("Req: %.2f L" % (bal))
                    self.previous = time.time()
                    v = ((self.flow_frequency  / self.calfactor)/60)+v  #flowrate in L/hour= (Pulse frequency x 60 min) / 7.5 
                    self.flow_frequency = 0  # Pulse frequency (Hz) = 7.5Q, Q is flow rate in L/min.
                    print("The flow is: %.3f Liter" % (v))
                    self.lmt(0,1)
                    self.pts("Cons: %.2f L" % (v))
                    time.sleep(0.5)
                    gc.collect()
                    if v >= (bal-0.2):
                        self.balance=self.balance-v
                       
                        db["users"][self.user_card] = self.balance
                        self.lcr()
                        self.lmt(0, 0)
                        self.pts("Cons: %.2f L" % (v))
                        self.lmt(3, 1)
                        self.pts("" + str("{:.1f}".format(v*self.ppl)) + "TZS")
                        self.wj(db)                        
                        del (v, newbalance,db)
                        loop=False
                        gc.collect()
                        self.tsp(4)
                    gc.collect()
            except KeyboardInterrupt:
                print('\nkeyboard interrupt!')
                loop=False
                break
            gc.collect()
    def rj(self):
        dt = None
        db_file = open("database.json", "r")
        dt = json.loads(db_file.read())
        db_file.close()
        del db_file
        gc.collect()
        return dt

    def wj(self, dt):
        res = False
        db_file = open("database.json", "w+")
        try:
            json.dump(dt, db_file)
            res = True
        except Exception as E:
            print(E)
        db_file.close()
        del db_file
        gc.collect()
        return res
    def get_gprs(self,id):
        self.wdt.feed() 
        # self.dc.acquire()
        # cmd = ["AT+SAPBR=1,1\r","AT+HTTPINIT\r","AT+HTTPPARA=\"URL\","+self.url+"\r","AT+HTTPACTION=1\r","AT+HTTPREAD\r","AT+HTTPTERM\r" ]
        cmd = [
            "AT\r",
            "AT+SAPBR=3,1,\"Contype\",\"GPRS\"\r",
            "AT+SAPBR=3,1,\"APN\",\"internet\"\r",
            "AT+SAPBR=1,1\r",
            "AT+SAPBR=2,1\r",
            "AT+HTTPINIT\r",
            "AT+HTTPPARA=\"CID\",1\r",
            'AT+HTTPPARA=\"URL\",\"'+self.url+'"\r',
            "AT+HTTPPARA=\"CONTENT\",\"application/json\"\r",
            " data-lenght",
            "data-itself",
            "AT+HTTPACTION=1\r",
            "AT+HTTPREAD\r",
            "AT+HTTPTERM\r", 
            "AT+SAPBR=0,1\r"
            ]
        
        delay = [0.3, 6, 6, 6, 6, 6, 6, 4, 4, 6, 6, 10 ,5 ,5 , 5]
        cl = len(cmd)
        if time.time() - self.pt >= delay[self.stage]:
            payload=self.gr()
            if payload != None:
                rec_data=payload.decode()
                print(rec_data)

        self.gw(cmd[self.stage])
        # time.sleep(delay[self.stage])

        time.sleep(delay[self.stage])
        self.stage += 1
        if self.stage == cl:
            self.stage=0
        bdy = json.dumps({ "uid": id, "amount": "100" })
        if self.stage == (cl-5) or self.stage == (cl-6):
            if self.stage == (cl-5):
                print(self.stage)
                self.gw(bdy+"\r") 
            else:
                print(self.stage)
                self.gw("AT+HTTPDATA=" + str(len(bdy))+ ",100000\r")
        # else:
        #     self.gw(cmd[self.stage])
        gc.collect()
        # self.dc.release()
        return True
    



    def run(self):
        while 1:
            self.wdt.feed()
            try:
                (stat, tag_type) = self.rd.request(self.rd.REQIDL)
                if stat == self.rd.OK:
                    (stat, uid) = self.rd.SelectTagSN()
                    if stat == self.rd.OK:
                        crd = str(int.from_bytes(bytes(uid), "little", False))
                        self.user_card=str(crd)
                        self.lbo()
                        self.lmt(0, 0)
                        self.pts(str(crd))
                        print(str(crd))
                        db = self.rj()
                        self.ppl = db["ppl"]
                        if crd in db["users"]:
                            self.balance = db["users"][crd]
                            if (self.balance-0.2) > 0:
                                self.lmt(0, 0)
                                self.pts("Card " + str(crd))
                                self.lmt(0, 1)
                                self.pts("Balance: %.2fL" % (self.balance))
                                self.tsp(2)
                                self.MenuEvent()
                            else:
                                self.lmt(0, 0)
                                self.pts("Card  " + str(crd))
                                self.lmt(0, 1)
                                self.pts("No balance")
                                self.tsp(1.5)
                            self.lcr()
                            self.lbf()

                        else: 
                            self.lmt(0, 0)
                            self.pts("Card  " + str(crd))
                            self.lmt(0, 1)
                            self.pts("Not registered")
                            self.tsp(1.5)
                            self.lcr()
                            self.lbf()
                        
                        gc.collect()
            except KeyboardInterrupt:
                print('\nkeyboard interrupt!')
                break
                gc.collect()

app=App()
# _thread.start_new_thread(app.get_gprs, ())
app.run()


# self.lmt(0,0)     #self.lmt(0,0) 
# self.pts("1st row ")
# self.lmt(-4,3)    #self.lmt(-4,3) 
# self.pts("2nd row")
# self.lmt(8,0)       #self.lmt(8,0) 
# self.pts("3rd row")
# self.lmt(4,3)       #self.lmt(4,3) 
# self.pts("4th row")