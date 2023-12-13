from machine import UART, I2C, Pin, WDT
from mfrc522 import MFRC522
from pico_i2c_lcd import I2cLcd
import time
import _thread
import gc
import uasyncio as asyncio
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
        self.gw = self.gprs.write
        self.gr = self.gprs.read
        self.tsp = time.sleep
        self.url = self.r_d()["url"]
        self.calfactor = self.r_d()["calbrate"]
        self.lvl = self.r_d()["level"]
        self.api = self.r_d()["api"]
        self.pt = time.time()
        self.stage = 0
        self.flow = Pin(18, Pin.IN)
        self.fl_frq = 0
        self.previous = 0
        self.balance = 0.0
        self.sensor_pin = Pin(19, Pin.IN, Pin.PULL_DOWN)
        self.reset_pin = Pin(21, Pin.IN, Pin.PULL_UP)
        self.amount_entered = ""
        self.user_card = ""
        self.ph = ""
        self.ppl = 0.0
        self.data = {}
        self.led = Pin(20, Pin.OUT)
        self.led(1)
        self.buzzer = Pin(28, Pin.OUT)
        self.valve = Pin(22, Pin.OUT)
        self.pump = Pin(22, Pin.OUT)
        self.charge = Pin(27, Pin.OUT)
        self.card_in = False

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
        self.lcr()
        self.lmt(0, 0)
        self.lmt(0, 0)
        self.pts("Inapakia...")
        self.lmt(8, 0)
        i = 0

        self.method = "GET"
        self.amt = 0.0
        self.postData = {}
        self.led(1)

        # trx = self.rd_trx()
        # if trx != None:
        #     self.method = "POST"
        while 0:
            self.wdt.feed()
            self.lmt(i, 1)
            self.pts("-")
            self.gw("AT+COPS?\r")
            rpsl = ""
            try:

                rpsl = self.gr().decode().split()
            except:
                pass
            if len(rpsl) >= 4:
                if rpsl[2] == "0":
                    pass
                else:
                    self.lcr()
                    try:
                        self.pts("Mtandao: " +
                                 str(rpsl[2].split(",")[2].replace('"', "")))
                        self.gw("AT+CSQ\r")
                        self.wdt.feed()
                        self.tsp(2)
                        self.lmt(0, 1)
                        strs = self.gr().decode().split()
                        vl = int(
                            strs[strs.index("+CSQ:") + 1].split(",")[0]) / 31
                        vl = vl * 100
                        self.pts("Nguvu  : " + str("{:.2f}".format(vl)) + "%")

                    except:
                        pass
                    self.wdt.feed()
                    self.tsp(3)
                    del strs, vl, rpsl
                    break

            if i < 19:
                self.lmt(i, 1)
                self.pts("_")
                print(".")
                i = i + 1

            else:
                i = 0
            del rpsl
        self.lcr()
        self.printtxt(0, 0, "     NG'WALA     ")
        self.printtxt(0, 1, "   INVENTIONS   ")
        self.tsp(2)
        self.lcr()
        self.lbf()
        gc.collect()

    def getLevel(self):
        ll = self.sensor_pin.value()
        level = bool(ll)
        gc.collect()
        return level

    def MenuEvent(self, delay_ms=300):
        self.lcr()
        self.printtxt(0, 0, "A. Dawa")
        self.printtxt(0, 1, "B. Chaji")
        loop = True
        while loop:
            x = self.scankeys()
            if x == "A":
                loop = False
                self.menuEvent1()
            if x == "B":
                loop = False
                self.subMenuEvent3()
            if x == "C":
                loop = False
        gc.collect()

    def menuEvent1(self):
        self.lcr()
        self.printtxt(0, 0, "A. Pata Dawa")
        self.printtxt(0, 1, "B. Salio")
        loop = True
        while loop:
            x = self.scankeys()
            if x == "A":
                loop = False
                self.subMenuEvent1()
            if x == "B":
                loop = False
                self.subMenuEvent2()
            if x == "*":
                loop = False
                self.MenuEvent()

    def mpangilio(self):
        self.lcr()
        self.printtxt(0, 0, "Level Setting")
        self.printtxt(0, 2, "Weka Kiasi")
        self.printtxt(0, 3, "Kiasi:")
        custkeys = ["#", "A", "B", "C", "D", "*"]
        number = ""
        data = self.r_d()
        self.printtxt(0, 1, "Balance:%.2f L " % (data['level']))
        i = 6
        loop = True
        while loop:
            x = self.scankeys().replace(" ", "")
            if x != "":
                if x in custkeys:
                    if x == "*":
                        number = ""
                        self.lcr()
                        self.printtxt(0, 0, "Weka Kiasi")
                        self.printtxt(0, 1, "Kiasi:")
                        i = 6
                    if x == "#" and number != "":
                        n_level = self.lvl + float(number)
                        data['level'] = n_level
                        self.lvl = n_level
                        self.w_d(data)
                        self.lcr()
                        self.printtxt(0, 0, "Level Updated ")
                        self.printtxt(0, 1, "Succesful")
                        time.sleep(1)
                        self.lcr()
                        self.lbf()
                        del (n_level)
                        gc.collect()
                        loop = False
                    if x == "C":
                        self.lcr()
                        self.lbf()
                        loop = False
                else:
                    buton = str(x)
                    number += buton
                    self.printtxt(i, 3, buton)
                    i += 1
                    if i > 16:
                        i = 6
                        self.amount_entered = ""
        del (custkeys, number, loop, i)
        gc.collect()

    def subMenuEvent1(self):
        self.lcr()
        self.printtxt(0, 0, "Weka kiasi")
        self.printtxt(0, 1, "Kiasi:")
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
                        self.printtxt(0, 0, "Weka kiasi")
                        self.printtxt(0, 1, "Kiasi:")
                        i = 6
                        self.amount_entered = ""
                    if x == "#":
                        if int(self.amount_entered) < 2500:
                            self.lcr()
                            self.printtxt(0, 0, "Tafahali weka ")
                            self.printtxt(0, 1, "kuanzia sh 2500")
                            self.tsp(3)
                            self.amount_entered = ""
                            self.subMenuEvent1()
                        elif self.balance > int(self.amount_entered):
                            self.dispensePaste(int(self.amount_entered))
                            loop = False
                        elif self.balance < int(self.amount_entered):
                            print(self.amount_entered)
                            self.lcr()
                            self.printtxt(0, 0, "Kiasi ulichoweka")
                            self.printtxt(4, 1, "Kimezidi")
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
        result = ""
        try:
            if self.gprs.any():
                gread = self.gprs.read()
                print(gread)
                res = self.convert_to_string(gread)
                try:
                    ext = ""
                    i = 0
                    for x in res:
                        if x == "{":
                            i += 1
                            ext += x
                        elif x == "}":
                            i -= 1
                            ext += x
                            if i == 0:
                                self.data = ext
                                # print("Data: ", self.data)
                        elif i > 0:
                            ext += x
                except Exception as e:
                    print(e)

                if res == "OK":
                    res = "OK"
                else:
                    result += res
            self.gw(cmdstr)
            # self.tsp(delay)
            buf = self.gprs.readline()
            # print('discard linefeed:{}'.format(buf))
            buf = self.gprs.readline()
            # print('next linefeed:{}'.format(buf))
            if not buf:
                return None
            result += self.convert_to_string(buf)

            # result=str(buf)
            return result
        except Exception as e:
            return e

    def convert_to_string(self, buf):
        tt = buf.decode("utf-8").strip()
        return tt

    def dispensePaste(self, bal):
        v = 0.0
        count = 0.00
        dbbal = 0.0
        loop = True
        self.lcr()
        crd, scanned = self.scancard()
        self.ctrv(1)
        self.printtxt(0, 0, "Kiasi: ")
        self.printtxt(0, 1, "Chotwa: ")
        data = self.r_d()
        lt = bal / self.ppl
        print(str(self.lvl))
        self.buzzer(0)
        while loop:
            self.wdt.feed()
            try:
                if self.lvl > lt:
                    if time.time() - self.previous >= 1:
                        self.flow.irq(trigger=Pin.IRQ_RISING,
                                      handler=self.countPulse)

                        self.printtxt(6, 0, "%.2f L" % (lt))
                        self.previous = time.time()
                        count += 0.055
                        self.fl_frq = 0
                        self.printtxt(7, 1, "%.2f L" % (count))
                        time.sleep(0.5)
                        gc.collect()
                        if count >= (lt+0.055):
                            self.printtxt(7, 1, "%.2f L " % (lt))
                            self.ctrv(0)
                            balance = self.balance - (lt * int(self.ppl))
                            dbbal = self.lvl-count
                            data['level'] = dbbal
                            self.w_d(data)
                            self.lvl = self.r_d()["level"]
                            self.svdt(balance, self.user_card)
                            self.printtxt(0, 2, "Pesa:" +
                                          str("{:.1f}".format(int(bal))) + "TZS")
                            self.printtxt(0, 3, "ahsante karibu tena")
                            self.tsp(2)
                            self.lcr()
                            data = {
                                "uid": str(self.user_card),
                                "api": self.api,
                                "amt": str(bal),
                                "bal": str(balance),
                                "level": str(self.lvl),
                            }
                            self.add_trx(data)
                            # self.postData = json.dumps(data)
                            # trc = self.r_d()
                            # trc["transactions"].append(data)
                            # trc.append(data)
                            # self.w_d(trc)

                            # self.dispensePost()

                            lt = 0
                            loop = False
                            self.method = "POST"
                            gc.collect()
                else:
                    self.lcr()
                    self.printtxt(0, 0, "Kiasi ulichoweka kimezid ")
                    self.printtxt(0, 1, "weka kiasi chini ya ")
                    self.printtxt(0, 2,
                                  str("{:.1f}".format(int(self.lvl))) + "")
                    time.sleep(3)
                    loop = False
                    gc.collect()
            except KeyboardInterrupt:
                print("\nkeyboard interrupt!")
                loop = False

            self.amount_entered = ""
            gc.collect()

            v = 0.0

            del v
            gc.collect()

    def rd_trx(self):
        try:
            db = self.r_d()
            trx = db.get("transactions", [])
            gc.collect()
            if not trx:
                return None
            else:
                return trx[0]
        except Exception as e:
            print("reading transaction failed", e)

    def add_trx(self, data):
        try:
            db = self.r_d()
            trx = db.get("transactions", [])
            if data not in trx:
                trx.append(data)
            db["transactions"] = trx
            self.w_d(db)
            gc.collect()
        except Exception as e:
            return None

    def rm_trx(self, data):
        try:
            db = self.r_d()
            trx = db.get("transactions", [])
            if data in trx:
                trx.remove(data)
                db["transactions"] = trx
                self.w_d(db)
            gc.collect()
        except Exception as e:
            print("Error", e)

    def merge_data(self, local_data, server_data):
        local_users = local_data.get("users", [])
        server_users = server_data.get("user", [])
        updated_users = []
        for server_user in server_users:
            server_uid = list(server_user.keys())[0]
            # print("server", server_uid)
            server_ver = int(server_user['ver'])
            local_user = None
            for u in local_users:
                l_uid = list(u.keys())[0]
                # print("local", l_uid)
                if server_uid in u:
                    local_user = u
                else:
                    local_user = None
            if local_user:
                local_ver = int(local_user['ver'])
                if server_ver > local_ver:
                    local_users.remove(local_user)
                elif server_ver == local_ver:
                    pass
            else:
                if server_user not in local_users:
                    updated_users.append(server_user)
        local_users.extend(updated_users)

        local_data["users"] = local_users
        return local_data

    def get_gprs(self):
        self.data = ""

        cmd = [
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
        cmd_del = [1, 3, 3, 6, 6, 4, 4, 4, 6, 5, 5, 5, 10, 10, 5, 5]
        g_len = len(cmd)
        g_stage = 0
        p_stage = 0
        g_prev = time.time()
        p_prev = time.time()
        while 1:
            self.wdt.feed()
            self.dc.acquire()
            method = self.method
            if method == 'GET':
                p_stage = 0
                try:
                    if (time.time() - g_prev) >= cmd_del[g_stage]:
                        cmdstr = cmd[g_stage]
                        if "URL" in cmdstr:
                            url = self.url
                            cmdstr = 'AT+HTTPPARA="URL","' + url + '"'
                            print(cmdstr)
                        rs = self.send_command(cmdstr, cmd_del[g_stage])
                        print("GET", rs)
                        g_stage += 1
                        if g_stage == g_len:
                            g_stage = 0
                        g_prev = time.time()
                except Exception as e:
                    print("get error", e)
                if self.data != "" and cmdstr == "AT+SAPBR=0,1":
                    try:
                        local = self.r_d()
                        server = json.loads(self.data)
                        merged_data = self.merge_data(local, server)
                        self.w_d(merged_data)
                    except Exception as e:
                        print("error:", e)
                gc.collect()
            elif method == "POST":
                p_url = "http://ngwalainventions-a7e0b65f6e46.herokuapp.com/api/machine-data-getmethod/"
                g_stage = 0
                try:
                    if (time.time() - p_prev) >= cmd_del[p_stage]:
                        cmdstr = cmd[p_stage]
                        delay = cmd_del[p_stage]
                        if "URL" in cmdstr:
                            self.postData = self.rd_trx()
                            params = "&".join(
                                f"{key}={value}" for key, value in self.postData.items())
                            api_url = f"{p_url}?{params}"
                            cmdstr = 'AT+HTTPPARA="URL","' + api_url + '"'
                            print(cmdstr)
                        rs = self.send_command(cmdstr, delay)
                        print("POST", rs)
                        if rs == "" or rs == None:
                            pass
                        else:
                            rs = rs.replace(" ", "")
                        p_stage += 1
                        if p_stage == g_len:
                            p_stage = 0
                        p_prev = time.time()
                except Exception as e:
                    print(e)
                if "AT+SAPBR=0,1" in cmdstr:
                    print("Last=>", self.data)
                    res = self.rd_trx()

                    if res == None:
                        self.method = "GET"
                    else:
                        self.rm_trx(res)
                        res = self.rd_trx()
                        if res == None:
                            self.method = "GET"

                    gc.collect()
            gc.collect()
            self.dc.release()
        return 0

    def r_d(self):
        with open("db.json", "r") as f:
            data = json.load(f)
        gc.collect()
        return data

    def w_d(self, data):
        with open("db.json", "w") as f:
            json.dump(data, f)
            gc.collect()

    def chk_card(self):
        (stat, tag_type) = self.rd.request(self.rd.REQIDL)
        if stat == self.rd.OK:
            (stat, uid) = self.rd.SelectTagSN()
            self.balance
            if stat == self.rd.OK:
                return True
            else:
                return False

    def reset_pico(self, pin):
        machine.reset(pin)

    def scancard(self):
        card_value = None
        card_scanned = False
        try:
            (stat, tag_type) = self.rd.request(self.rd.REQIDL)
            if stat == self.rd.OK:
                (stat, uid) = self.rd.SelectTagSN()
                if stat == self.rd.OK:
                    self.buzzer(1)
                    crd = str(int.from_bytes(bytes(uid), "little", False))
                    card_value = str(crd)
                    gc.collect()
                    card_scanned = True
        except KeyboardInterrupt:
            print("\nkeyboard interrupt!")
        return card_value, card_scanned

    def run(self):
        start = 0
        end = 0
        while 1:
            self.wdt.feed()
            self.dc.acquire()
            start = time.time
            try:
                crd, scanned = self.scancard()
                if scanned and crd != None:
                    self.card_in = True
                    self.user_card = str(crd)
                    self.lbo()
                    self.lmt(0, 0)
                    self.pts(str(crd))
                    print(str(crd))
                    print(str(crd)[:4] + "*****")
                    db = self.r_d()
                    print(db['users'])
                    trx = db.get("transactions", [])
                    print(trx)
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
                            lvl = self.getLevel()
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
                    x = self.scankeys().replace(" ", "")
                    if x != "":
                        if x == "#":
                            self.lbo()
                            self.mpangilio()
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
