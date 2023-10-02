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
        self.url = self.r_d()["url"]
        self.calfactor = self.r_d()["calbrate"]
        self.gw = self.gprs.write
        self.gr = self.gprs.read
        self.pt = time.time()
        self.stage = 0
        self.flow = Pin(18, Pin.IN)
        self.fl_frq = 0
        self.previous = 0
        self.balance = 0.0

        self.sensor_pin = Pin(19, Pin.IN, Pin.PULL_DOWN)

        self.amount_entered = ""
        self.user_card = ""
        self.ph = ""
        self.ppl = 0.0
        self.data = []

        self.led = Pin(20, Pin.OUT)
        self.buzzer = Pin(28, Pin.OUT)
        self.valve = Pin(22, Pin.OUT)
        self.pump = Pin(22, Pin.OUT)
        self.button = machine.Pin(21, machine.Pin.IN, machine.Pin.PULL_UP)
        self.charge = Pin(27, Pin.OUT)

        # Create a map between keypad buttons and characters
        self.matrix_keys = [
            ['1', '2', '3', 'A'],
            ['4', '5', '6', 'B'],
            ['7', '8', '9', 'C'],
            ['*', '0', '#', 'D'],
        ]
        # PINs according to schematic - Change the pins to match with your connections
        self.keypad_rows = [8, 7, 6, 5]
        self.keypad_columns = [12, 11, 10, 9]

        # Create two empty lists to set up pins ( Rows output and columns input )
        self.col_pins = []
        self.row_pins = []

        # Loop to assign GPIO pins and setup input and outputs
        for x in range(0, 4):
            self.row_pins.append(Pin(self.keypad_rows[x], Pin.OUT))
            self.row_pins[x].value(1)
            self.col_pins.append(
                Pin(self.keypad_columns[x], Pin.IN, Pin.PULL_DOWN))
            self.col_pins[x].value(0)

        self.lbo = self.lcd.backlight_on
        self.lbf = self.lcd.backlight_off
        self.pts = self.lcd.putstr
        self.lmt = self.lcd.move_to
        self.lcr = self.lcd.clear
        self.rd = MFRC522(spi_id=0, sck=2, miso=4, mosi=3, cs=1, rst=0)
        self.gprs = UART(0, baudrate=58000, rx=Pin(17), tx=Pin(16))
        self.lcr()
        self.lmt(0, 0)
        self.lmt(0, 0)
        self.pts("Inapakia...")
        self.led(1)
        self.lmt(8, 0)
        i = 0

        self.gprswitch = False
        self.amt = 0.0
        self.postData = {}

        while 1:
            self.wdt.feed()
            self.lmt(i, 1)
            self.pts("-")
            self.gw("AT+COPS?\r")
            rpsl = ""
            try:
                self.led(1)
                rpsl = self.gr().decode().split()
            except:
                pass
            if len(rpsl) >= 4:
                if rpsl[2] == "0":
                    pass
                else:
                    self.lcr()
                    self.pts("Mtandao: " +
                             str(rpsl[2].split(",")[2].replace('"', "")))
                    self.gw("AT+CSQ\r")
                    self.wdt.feed()
                    self.tsp(2)
                    self.lmt(0, 1)
                    strs = self.gr().decode().split()
                    vl = int(strs[strs.index("+CSQ:") + 1].split(",")[0]) / 31
                    vl = vl * 100
                    self.pts("Nguvu  : " + str("{:.2f}".format(vl)) + "%")
                    self.wdt.feed()
                    self.tsp(3)
                    del strs, vl, rpsl
                    break

            if i < 19:
                self.lmt(i, 1)
                self.pts("_")
                i = i + 1
                self.led(0)
            else:
                i = 0
            del rpsl
        self.gr()
        del i
        gc.collect()
        self.lcr()
        self.printtxt(0, 0, "     NG'WALA     ")
        self.printtxt(0, 1, "   INVENTIONS   ")
        self.tsp(2)
        self.lcr()
        self.lbf()
        self.led(1)

    def level(self):
        ll = self.sensor_pin.value()
        return bool(ll)

    def MenuEvent(self):
        self.lcr()
        self.printtxt(0, 0, "A. Dawa")
        self.printtxt(0, 1, "B. Lugha")

        loop = True
        while loop:
            x = self.scankeys()
            if x == "A":
                loop = False
                self.menuEvent1()
            if x == "B":
                print("lugha")
                loop = False
            if x == "C":
                print("Token")
                loop = False
            if x == "D":
                loop = False
            if self.button.value() == 0:
                machine.reset()
            del x
            gc.collect()
        del loop
        gc.collect()

    def menuEvent1(self):
        self.lcr()
        self.lmt(0, 0)
        self.pts("A. Pata Dawa")
        self.lmt(0, 1)
        self.pts("B. Salio")
        self.lmt(0, 2)
        self.pts("C. Chaji")
        self.lmt(0, 3)
        loop = True
        while loop:
            x = self.scankeys()
            if x == "A":
                loop = False
                self.subMenuEvent1()
            if x == "B":
                loop = False
                self.subMenuEvent2()
            if x == "C":
                loop = False
                self.subMenuEvent3()
            if x == "*":
                loop = False
                self.MenuEvent()
            if self.button.value() == 0:
                machine.reset()

    def subMenuEvent1(self):
        self.lcr()
        self.lmt(0, 0)
        self.pts("Weka kiasi")
        self.lmt(0, 1)
        self.pts("Kiasi: ")
        loop = True
        i = 6
        custkeys = ["#", "A", "B", "C", "D", "*"]
        self.amount_entered = ""
        while loop:
            x = self.scankeys().replace(" ", "")
            if x != "":
                if x in custkeys:
                    if x == "*":
                        self.amount_entered = ""
                        self.lcr()
                        self.lmt(0, 0)
                        self.pts("Weka Kiasi")
                        self.lmt(0, 1)
                        self.pts("Kiasi: ")
                        i = 6
                        self.amount_entered = ""
                    if x == "#":
                        if int(self.amount_entered) < 100:
                            self.lcr()
                            self.lmt(0, 0)
                            self.pts("Tafahali weka ")
                            self.lmt(0, 1)
                            self.pts("kuanzia sh 100")
                            self.tsp(3)
                            self.amount_entered = ""
                            self.subMenuEvent1()
                        elif self.balance > int(self.amount_entered):
                            self.dispensePaste(int(self.amount_entered))
                            loop = False
                        elif self.balance < int(self.amount_entered):
                            print(self.amount_entered)
                            self.lcr()
                            self.lmt(0, 0)
                            self.pts("Kiasi ulichoweka ")
                            self.lmt(4, 1)
                            self.pts("Kimezidi ")
                            self.tsp(3)
                            self.amount_entered = ""
                            self.subMenuEvent1()
                    if x == "D":
                        loop = False

                else:
                    buton = str(x)
                    self.amount_entered += buton
                    self.lmt(i, 1)
                    self.pts(buton)
                    i += 1
                    if i > 16:
                        i = 6
                        self.amount_entered = ""

    def nambayasimu(self):
        self.lcr()
        self.printtxt(0, 0, "Je unataka risiti")
        self.printtxt(0, 1, "A. Ndiyo")
        self.printtxt(0, 2, "B. Hapana")
        if self.button.value() == 0:
            machine.reset()
        loop = True
        i = 0
        ctk = ["#", "A", "B", "C", "D", "*"]
        nos = ""
        y = False
        while loop:
            x = self.scankeys().replace(" ", "")
            if self.button.value() == 0:
                machine.reset()
            if x != "":
                if x in ctk:
                    if x == "A":
                        self.lcr()
                        self.printtxt(0, 0, "ingiza namba ya simu")
                        nos = ""
                        y = True
                    if x == "B":
                        loop = False
                        self.lcr()
                        self.printtxt(0, 0, "Ahsante karibu tena")
                        nos = ""
                        y = False
                    if x == "*":
                        self.lcr()
                        self.printtxt(0, 0, "weka namba ya simu")
                        self.printtxt(0, 1, "bonyeza # kuhakiki")
                        self.printtxt(0, 2, "bonyeza * kufuta")
                        i = 0
                        nos = ""
                    if x == "#":
                        if len(nos) < 10 or not nos.startswith('0'):
                            self.lcr()
                            self.printtxt(0, 0, "ingiza namba sahihi")
                            self.printtxt(0, 1, "namba iwe ianze na 0")
                            self.printtxt(0, 2, "iwe na tarakimu 10")
                            self.tsp(3)
                            nos = ""
                            self.nambayasimu()
                            loop = False
                        else:
                            loop = False
                            return nos

                    if x == "D":
                        loop = False
                        return ''

                else:
                    if y:
                        p = str(x)
                        nos += p
                        self.lmt(i, 3)
                        self.pts(p)
                        i += 1
                        if i > 20:
                            i = 0
                            nos = ""

    def subMenuEvent3(self):
        v = 0.0
        bal = 15*60
        loop = True
        self.lcr()
        while loop:
            self.wdt.feed()
            try:
                if time.time() - self.previous >= 1:
                    self.charge(1)
                    self.flow.irq(trigger=Pin.IRQ_RISING,
                                  handler=self.countPulse)
                    liters = bal / self.ppl
                    self.printtxt(0, 0, "Dakika: %.2f M" % (liters))
                    self.previous = time.time()
                    v = (
                        (self.fl_frq / self.calfactor) / 60
                    ) + v  # flowrate in L/hour= (Pulse frequency x 60 min) / 7.5
                    # print("The flow is: %.3f Liter" % (self.fl_frq))
                    self.fl_frq = 0
                    self.printtxt(0, 2, "Zilizosalia: %.2f M" % (v))
                    time.sleep(0.5)
                    gc.collect()
                    if v >= (liters - 0.0001):
                        self.charge(0)
                        self.balance = self.balance - (v * int(self.ppl))
                        db = self.r_d()
                        for u in db["users"]:
                            if str(self.user_card) in u:
                                u[self.user_card] = self.balance
                                break

                        self.printtxt(0, 2, "Pesa:" +
                                      str("{:.1f}".format(int(bal))) + "TZS")
                        self.printtxt(0, 3, "ahsante karibu tena")
                        self.w_d(db)
                        del db
                        self.tsp(4)
                        self.lcr()
                        liters = 0
                        loop = False
                        gc.collect()
                    gc.collect()
            except KeyboardInterrupt:
                print("\nkeyboard interrupt!")
                loop = False

            self.amount_entered = ""
            gc.collect()

        v = 0.0
        del v
        gc.collect()

    def subMenuEvent2(self):
        self.lcr()
        self.lmt(0, 0)
        self.pts("Salio lako ni")
        self.lmt(0, 1)
        self.pts("%.2f Tzs" % (self.balance))
        self.tsp(3)

    def printtxt(self, c, r, t):
        self.lmt(c, r)
        self.pts(t)

    def scankeys(self):
        keypressed = ""
        self.wdt.feed()
        for row in range(4):
            for col in range(4):
                self.row_pins[row].high()
                key = None
                if self.col_pins[col].value() == 1:
                    self.buzzer(1)
                    keypressed = self.matrix_keys[row][col]
                    self.tsp(0.3)
                    self.buzzer(0)
            self.row_pins[row].low()
        return keypressed

    def countPulse(self, channel):
        self.fl_frq += 1

    def svdt(self, dt, crd):
        db = self.r_d()
        # print(dt)
        # print(crd)
        for u in db["users"]:
            if str(crd) in u:
                print(crd, dt)
                u[crd] = float(dt)
                # dt = float(u[crd])
                break
        self.w_d(db)
        del db

    def ctrv(self, state):
        if state:
            self.valve(state)
            self.pump(state)
        else:
            self.pump(state)
            self.valve(state)

    def send_command(self, cmdstr, delay=1):
        cmdstr = cmdstr + "\r\n"
        print(cmdstr)
        result = ""
        try:
            if self.gprs.any():
                res = self.convert_to_string(self.gprs.read())
                print(res)
                try:
                    ext = ""
                    i = 0
                    for x in res:
                        if x == "[":
                            i += 1
                            ext += x
                        elif x == "]":
                            i -= 1
                            ext += x
                            if i == 0:
                                self.data = ext
                                print("Data: ", self.data)
                        elif i > 0:
                            ext += x
                except Exception as e:
                    print(e)

                if res == "OK":
                    res = "OK"
                else:
                    result += res
            self.gw(cmdstr)

            buf = self.gprs.readline()
            buf = self.gprs.readline()
            if not buf:
                return None
            result += self.convert_to_string(buf)
            return result
        except Exception as e:
            return e

    def convert_to_string(self, buf):
        tt = buf.decode("utf-8").strip()
        return tt

    def send_sms(self, msgtext):
        self.ph = ""
        self.ph = '0759082262'  # self.nambayasimu()
        self.lcr()
        self.printtxt(0, 0, "inatuma risiti")
        self.printtxt(0, 1, "subiri........")
        cmd = ['AT', 'AT+CMGF=1',
               'AT+CMGS="{}"\n'.format(self.ph), (msgtext+'\x1A')]
        tmd = [1, 2, 5, 5]
        loop = True
        end = 0
        i = 0
        while loop:
            self.wdt.feed()
            try:
                if (time.time() - end) >= tmd[i]:
                    rs = self.send_command(cmd[i], tmd[i])
                    if rs == "" or rs == None:
                        i -= 1
                    else:
                        print(rs)
                        i += 1
                    if i == len(cmd):
                        loop = False
                        i = 0
                        self.lcr()

                    end = time.time()
            except Exception as e:
                print(e)
        self.lcr()
        self.printtxt(0, 0, "risiti imetumwa ")
        self.printtxt(0, 1, "kwenye namba ")
        self.printtxt(0, 2, self.ph)
        self.tsp(3)
        self.lcr()

    def dispensePaste(self, bal):
        v = 0.0
        count = 0.00
        loop = True
        self.lcr()
        self.ctrv(1)
        self.printtxt(0, 0, "Kiasi: ")
        self.printtxt(0, 1, "Chotwa: ")
        while loop:
            self.wdt.feed()
            try:
                if time.time() - self.previous >= 1:
                    self.flow.irq(trigger=Pin.IRQ_RISING,
                                  handler=self.countPulse)
                    lt = bal / self.ppl
                    self.printtxt(6, 0, "%.2f L" % (lt))
                    self.previous = time.time()
                    count += 0.055
                    self.fl_frq = 0
                    self.printtxt(7, 1, "%.2f L" % (count))
                    time.sleep(0.5)
                    gc.collect()

                    if count >= (lt - 0.055):
                        self.ctrv(0)
                        balance = self.balance - (lt * int(self.ppl))
                        self.svdt(balance, self.user_card)
                        self.printtxt(0, 2, "Pesa:" +
                                      str("{:.1f}".format(int(bal))) + "TZS")
                        self.printtxt(0, 3, "ahsante karibu tena")
                        self.tsp(2)
                        self.lcr()
                        self.postData = json.dumps(
                            {
                                "uid": str(self.user_card),
                                "api": "AjGjIYTUIiojkN",
                                "amt": str(bal),
                                "bal": str(balance),
                                "level": str(self.level()),
                            }
                        )
                        print(self.postData)
                        lt = 0
                        self.gprswitch = True
                        loop = False
                        gc.collect()
                    gc.collect()
            except KeyboardInterrupt:
                print("\nkeyboard interrupt!")
                loop = False

            self.amount_entered = ""
            gc.collect()

        v = 0.0

        del v
        gc.collect()

    def searchcard(self, crd):
        i = 0
        end = time.time()
        url = ""
        url = "http://development-ngwala-sys.herokuapp.com/api/v1/get_user/?uid=" + \
            str(crd)
        loop = True
        self.buzzer(0)
        response = ""
        self.lmt(0, 3)
        self.pts("              ")

        cmdlst = [
            "AT",
            'AT+SAPBR=3,1,"Contype","GPRS"',
            'AT+SAPBR=3,1,"APN","internet"',
            "AT+SAPBR=1,1",
            "AT+SAPBR=2,1",
            "AT+HTTPINIT",
            'AT+HTTPPARA="CID",1',
            'AT+HTTPPARA="URL","' + url + '"',
            'AT+HTTPPARA="CONTENT","application/json"',
            # "AT+HTTPDATA=" + str(len(bdy)) + ",100000",
            # bdy,
            "AT+HTTPACTION=0",
            "AT+HTTPREAD",
            "AT+HTTPREAD",
            "AT+HTTPTERM",
            "AT+SAPBR=0,1",
        ]
        tmd = [1, 3, 3, 5, 3, 3, 3, 3, 5, 6, 5, 5, 5, 5]
        data = self.r_d()
        while loop:
            self.wdt.feed()
            self.lmt(i, 3)
            self.pts(".")
            self.led(1)
            try:
                if (time.time() - end) >= tmd[i]:
                    cmd = cmdlst[i]
                    rs = self.send_command(cmd, tmd[i])
                    rs = rs.replace(" ", "")
                    self.led(0)
                    if rs == "" or rs == None:
                        response = ""
                    else:
                        rs = self.data
                    i += 1
                    if i == len(cmdlst):
                        i = 0
                        self.lmt(i, 3)
                        self.pts("               ")
                        loop = False
                    end = time.time()
            except Exception as e:
                print(e)
            if self.data != "" and cmd == "AT+SAPBR=0,1":
                try:
                    js = json.loads(self.data)
                    new = js[0]['users']
                    data["users"].extend(new)
                    self.w_d(data)
                    self.data = ""
                    data["users"].clear()
                    data = self.r_d()
                    print(data["users"])
                    for user in data['users']:
                        usrlst = list(user[0])
                        crd = usrlst[0]
                        if crd in user:
                            self.balance = float(user[crd])
                            print(crd[:4] + "*****")
                except Exception as e:
                    print("error:", e)

    def dispensePost(self):
        i = 0
        end = time.time()
        url = "http://development-ngwala-sys.herokuapp.com/api/v1/get_user/"
        loop = True
        response = ""
        cmdlst = [
            "AT",
            'AT+SAPBR=3,1,"Contype","GPRS"',
            'AT+SAPBR=3,1,"APN","internet"',
            "AT+SAPBR=1,1",
            "AT+SAPBR=2,1",
            "AT+HTTPINIT",
            'AT+HTTPPARA="CID",1',
            'AT+HTTPPARA="URL","' + url + '"',
            'AT+HTTPPARA="CONTENT","application/json"',
            "AT+HTTPDATA=" + str(len(self.postData)) + ",100000",
            self.postData,
            "AT+HTTPACTION=1",
            "AT+HTTPREAD",
            "AT+HTTPREAD",
            "AT+HTTPTERM",
            "AT+SAPBR=0,1",
        ]
        tmd = [1, 3, 3, 5, 3, 3, 3, 3, 5, 6, 6, 6, 5, 5, 5, 5]
        data = self.r_d()
        while loop:
            self.wdt.feed()
            try:
                if (time.time() - end) >= tmd[i]:
                    cmd = cmdlst[i]
                    rs = self.send_command(cmd, tmd[i])
                    rs = rs.replace(" ", "")
                    if rs == "" or rs == None:
                        response = ""
                    else:
                        rs = self.data
                    i += 1
                    if i == len(cmdlst):
                        i = 0
                        loop = False
                        self.gprswitch = False
                    end = time.time()
            except Exception as e:
                print(e)
            if self.data != "" and cmd == "AT+SAPBR=0,1":
                try:
                    js = json.loads(self.data)
                    new = js[0]['users']
                    data["users"].extend(new)
                    self.w_d(data)
                    self.data = ""
                    data["users"].clear()
                    data = self.r_d()
                    print(data["users"])
                    for user in data['users']:
                        usrlst = list(user[0])
                        crd = usrlst[0]
                        if crd in user:
                            self.balance = float(user[crd])
                        print((crd)[:4] + "*****")
                except Exception as e:
                    print("error:", e)

    def switch_post():
        if self.gprswitch:
            self.dispensePost()
        else:
            self.get_gprs()

    def get_gprs(self):
        # url = "http://easydigital2.000webhostapp.com/users.php"
        cms = [
            "AT",
            'AT+SAPBR=3,1,"Contype","GPRS"',
            'AT+SAPBR=3,1,"APN","internet"',
            "AT+SAPBR=1,1",
            "AT+SAPBR=2,1",
            "AT+HTTPINIT",
            'AT+HTTPPARA="CID",1',
            'AT+HTTPPARA="URL","' + self.url + '"',
            'AT+HTTPPARA="CONTENT","application/json"',
            "AT+HTTPACTION=0",
            "AT+HTTPREAD",
            "AT+HTTPREAD",
            "AT+HTTPTERM",
            "AT+SAPBR=0,1",
        ]

        cd = [1, 3, 3, 6, 6, 4, 4, 4, 6, 5, 5, 10, 10, 5, 5]
        cl = len(cms)
        self.data = ""
        data = self.r_d()
        ct = 0
        pt = 0

        while 1:
            self.wdt.feed()
            self.dc.acquire()
            # self.led(1)
            # if self.gprswitch:
            #     try:
            #         if (time.time() - pt) >= cd[ct]:
            #             strcmd = cmdlst[ct]
            #             rs = self.send_command(strcmd, tmd[ct])
            #             print("Dispense: ", rs)
            #             ct += 1
            #             if ct == len(tmd):
            #                 ct = 0
            #                 self.gprswitch = False
            #             pt = time.time()
            #     except Exception as e:
            #         print(e)

            # else:
            try:
                if (time.time() - self.pt) >= cd[self.stage]:
                    cmdstr = cms[self.stage]
                    rs = self.send_command(cmdstr, cd[self.stage])
                    print("Fetch: ", rs)
                    self.led(0)
                    self.stage += 1
                    if self.stage == cl:
                        self.stage = 0
                    self.pt = time.time()
            except Exception as e:
                print(e)
            if self.data != "" and cmdstr == "AT+SAPBR=0,1":
                try:
                    js = json.loads(self.data)
                    new = js[0]['users']
                    users = data["users"]
                    added = []
                    exist = []
                    bal = 0
                    # print('new', new)
                    # print('indb', users)
                    for x in new:
                        uid = list(x.keys())[1]
                        if uid == 'ver':
                            uid = list(x.keys())[0]
                        n_ver = x['ver']
                        for y in users:
                            if uid in y:
                                l_ver = y['ver']
                                if int(n_ver) > int(l_ver):
                                    # bal=float(y[uid])
                                    # bal2=float(x[uid])
                                    # bal+=bal2
                                    # x[uid]=str(bal)
                                    users.remove(y)
                            if x == y:
                                exist.append(x)
                            else:
                                if x not in exist:
                                    if x not in added:
                                        added.append(x)
                    users.extend(added)
                    skp = []
                    for v in added:
                        for u in users:
                            if list(v) == list(u):
                                v1 = int(v['ver'])
                                v2 = int(u['ver'])
                                if v1 < v2:
                                    users.remove(v)
                                elif v2 > v1:
                                    skp.append(v)
                                    #   prev.insert(1,u)
                    users.extend(skp)
                    seen = set()
                    result = []
                    for d in users:
                        items = tuple(d.items())
                        if items not in seen:
                            seen.add(items)
                            result.append(d)

                    users = result
                    self.w_d(data)
                    self.data = ""
                    skp.clear()
                    added.clear()
                    exist.clear()
                except Exception as e:
                    print("error:", e)

            gc.collect()
            self.dc.release()
        self.tsp(300)
        return 0

    def r_d(self):
        with open("database.json", "r") as f:
            data = json.load(f)
        gc.collect()
        return data

    def w_d(self, data):
        with open("database.json", "w") as f:
            json.dump(data, f)
            gc.collect()

    def run(self):
        start = 0
        end = 0
        while 1:
            self.wdt.feed()
            self.dc.acquire()
            start = time.time
            try:
                (stat, tag_type) = self.rd.request(self.rd.REQIDL)
                if stat == self.rd.OK:
                    (stat, uid) = self.rd.SelectTagSN()
                    self.balance
                    if stat == self.rd.OK:
                        self.buzzer(1)

                        crd = str(int.from_bytes(bytes(uid), "little", False))
                        self.user_card = str(crd)
                        self.lbo()
                        self.lmt(0, 0)
                        self.pts(str(crd))
                        print(str(crd))
                        print(str(crd)[:4] + "*****")
                        db = self.r_d()
                        print(db['users'])
                        found = False
                        for user in db['users']:
                            if str(crd) in user:
                                self.balance = float(user[crd])
                                found = True
                                break
                            else:
                                found = False
                                self.balance = 0.0
                        print(self.balance)
                        self.ppl = db["ppl"]
                        if found:
                            self.buzzer(0)
                            self.charge(1)
                            if (self.balance - 0.2) > 0:
                                self.printtxt(0, 0, "Kadi  " +
                                              str(crd)[:4] + "*****")
                                self.printtxt(0, 1, "Salio: %.1fTzs" %
                                              (self.balance))
                                self.tsp(2)
                                lvl = self.level()
                                # self.MenuEvent()
                                if lvl:
                                    self.MenuEvent()
                                else:
                                    self.printtxt(0, 0, "     Samahani  ")
                                    self.printtxt(0, 1, " mashine iko nje ya")
                                    self.printtxt(0, 2, "     huduma ")
                                    self.printtxt(0, 3, "PIGA: 0754689034")
                                    self.tsp(3)

                            else:
                                self.printtxt(0, 0, "Kadi  " +
                                              str(crd)[:4] + "*****")
                                self.printtxt(0, 1, "Haina Salio")
                                self.tsp(1.5)
                            self.lcr()
                            self.lbf()

                        else:
                            self.buzzer(0)
                            self.data = ""
                            self.lcr()
                            self.printtxt(0, 0, "Kadi haijasajiliwa")
                            self.printtxt(0, 1, "Tafadhali wasiliana")
                            self.printtxt(0, 2, "nasi kwa namba:    ")
                            self.printtxt(0, 3, "     0754689034   ")
                            self.tsp(3)
                            self.lcr()
                            self.lbf()
                            self.user_card = ""
                        gc.collect()
            except KeyboardInterrupt:
                print("\nkeyboard interrupt!")
                break
            end = time.time
            gc.collect()
            self.dc.release()
        return 0


app = App()
_thread.start_new_thread(app.get_gprs, ())
app.run()
