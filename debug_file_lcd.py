from machine import UART, I2C, Pin, WDT
from flow_meter import FlowMeter
from mfrc522 import MFRC522
from pico_i2c_lcd import I2cLcd
import utime as time
import _thread
import gc
import json


class App:
    def __init__(self):

        self.wdt = WDT(timeout=8000)
        self.dc = _thread.allocate_lock()
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
                         tx=Pin(16))

        self.gw = self.gprs.write
        self.gr = self.gprs.read
        self.tsp = time.sleep
        self.pt = time.time()
        self.url = self.r_d()["url"]
        self.calfactor = self.r_d()["calbrate"]
        self.lvl = self.r_d()["level"]
        self.api = self.r_d()["api"]
        self.ppl = self.r_d()["ppl"]
        self.stage = 0
        self.fl_frq = 0
        self.previous = 0
        self.balance = 0.0
        self.amount_entered = ""
        self.user_card = ""
        self.ph = ""
        self.ppl = 0.0
        self.data = {}
        self.flow_meter = FlowMeter()
        self.sensor_pin = Pin(19, Pin.IN, Pin.PULL_DOWN)
        self.led = Pin(20, Pin.OUT)
        self.reset_pin = Pin(21, Pin.IN, Pin.PULL_UP)
        self.valve = Pin(22, Pin.OUT)
        self.pump = Pin(22, Pin.OUT)
        self.charge = Pin(27, Pin.OUT)
        self.buzzer = Pin(28, Pin.OUT)  # 28
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

        self.method = "GET"

        self.amt = 0.0
        self.postData = {}
        self.led(1)
        self.commands = [
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
        self.delays = [1, 3, 3, 2, 2, 2, 4, 4, 6, 5, 10, 10, 2, 2]
        self.initGsm()
        self.lcr()
        self.printtxt(0, 0, "     NG'WALA     ")
        self.printtxt(0, 1, "   INVENTIONS   ")
        self.tsp(2)
        self.lcr()
        self.lbf()
        gc.collect()

    def initGsm(self):
        i = 0
        while 1:
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

    def printtxt(self, c, r, t):
        self.lmt(c, r)
        self.pts(t)

    def reset_pico(self, pin):
        machine.reset(pin)

    def r_d(self):
        with open("db.json", "r") as f:
            data = json.load(f)
        gc.collect()
        return data

    def w_d(self, data):
        with open("db.json", "w") as f:
            json.dump(data, f)
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

    def sv_bal(self, dt, crd):
        try:
            db = self.r_d()
            users = db.get("users", [])
            for u in users:
                if str(crd) in u:
                    u[crd] = dt
                    break
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
            print("Removed "+str(data))
            gc.collect()
        except Exception as e:
            print("Error", e)

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

    def get_gprs(self):
        stg = 0
        length = len(self.commands)
        prev_time = time.time()
        error = True
        while 1:
            self.wdt.feed()
            self.dc.acquire()
            method = self.method

            try:
                if ((time.time()-prev_time) >= self.delays[stg]):
                    cmd = self.commands[stg]
                    delay = self.delays[stg]
                    if "URL" in cmd and method == "POST":
                        p_url = "http://ngwalainventions-a7e0b65f6e46.herokuapp.com/api/machine-data-getmethod/"
                        self.postData = self.rd_trx()
                        if self.postData == None:
                            cmd = 'AT+HTTPPARA="URL","' + self.url + '"'
                            method = 'POST'
                        else:
                            params = "&".join(
                                f"{key}={value}" for key, value in self.postData.items())
                            api_url = f"{p_url}?{params}"
                            cmd = 'AT+HTTPPARA="URL","' + api_url + '"'
                        print(cmd)

                    res = self.send_command(
                        cmd, delay)
                    print(method, res)
                    if "+HTTPACTION: 0,200" in res:
                        error = False
                    if cmd == "AT+SAPBR=0,1" and self.data != "":
                        if method == "GET":
                            server = json.loads(self.data)
                            merged_data = self.merge_data(server)
                            print("Updated", merged_data)
                            db = self.r_d()
                            db["users"] = merged_data
                            self.w_d(db)
                            chktrx = self.rd_trx()
                            if chktrx != None:
                                self.method = "POST"
                        if method == "POST":
                            if "success" in self.data:
                                trx = self.rd_trx()
                                self.rm_trx(trx)
                            else:
                                pass
                            self.method = "GET"
                    else:
                        pass

                    stg += 1
                    if stg == length:
                        stg = 0
                    prev_time = time.time()
            except Exception as e:
                print(e)

            gc.collect()
            self.dc.release()
            # Adjust sleep period based on your requirements
            self.tsp(self.delays[stg])

    def merge_data(self, server_data):
        local_data = self.r_d()
        local_users = local_data["users"]
        server_users = server_data.get("user", [])
        all_users = local_users + server_users
        updated_list = []
        uid_list = []
        for u in all_users:
            uid = list(u.keys())[0]
            if uid == "ver":
                uid = list(u.keys())[1]
            ver0 = int(u['ver'])
            if uid not in uid_list:
                uid_list.append(uid)
                updated_list.append(u)
            else:
                for v in updated_list:
                    if uid in v:
                        ver1 = int(v["ver"])
                        if ver0 > ver1:
                            updated_list.remove(v)
                            updated_list.append(u)
                        else:
                            pass
        local_data["users"] = updated_list
        return local_data["users"]

    def send_command(self, cmdstr, delay=1):
        cmdstr = cmdstr + "\r\n"
        # print(cmdstr)
        # "+HTTPACTION: 0,200,132"
        result = ""
        try:
            if self.gprs.any():
                gread = self.gprs.read()
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
                                print("data", self.data)
                        elif i > 0:
                            ext += x
                except Exception as e:
                    print(e)
                if res == "OK":
                    res = "OK"
                else:
                    result += res
            self.gw(cmdstr)
            lines = result.split("\r\n")
            if len(lines) > 1:
                result = lines[-1]
            return result
            gc.collect()
        except Exception as e:
            print("Exception occured: ", e)
            return None

    def convert_to_string(self, buf):
        tt = buf.decode("utf-8").strip()
        return tt

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
                # self.subMenuEvent3()
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
                        if self.amount_entered == "0000":
                            self.mpangilio()
                            loop = False
                        elif int(self.amount_entered) < self.ppl:
                            self.lcr()
                            self.printtxt(0, 0, "Tafahali weka ")
                            self.printtxt(0, 1, "Kuanzia  " +
                                          str("{:.2f}".format(self.ppl)))
                            self.tsp(3)
                            self.amount_entered = ""
                            self.subMenuEvent1()
                        elif self.balance > int(self.amount_entered):
                            loop = False
                            self.dispensePaste(int(self.amount_entered))

                        elif self.balance < int(self.amount_entered):
                            self.lcr()
                            self.printtxt(0, 0, "Kiasi ulichoweka")
                            self.printtxt(4, 1, "Kimezidi")
                            self.tsp(3)
                            self.amount_entered = ""
                            self.subMenuEvent1()
                    if x == "C":
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

    def subMenuEvent2(self):
        self.lcr()
        self.lmt(0, 0)
        self.pts("Salio lako ni")
        self.lmt(0, 1)
        self.pts("%.2f Tzs" % (self.balance))
        self.tsp(3)

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

    def ctrv(self, state):
        if state:
            self.valve(state)
            self.pump(state)
        else:
            self.pump(state)
            self.valve(state)

    def dispensePaste(self, bal):
        self.lcr()
        self.printtxt(0, 0, "Kiasi: ")
        self.printtxt(0, 1, "Chotwa: ")
        # self.ctrv(1)
        count = 0.00
        loop = True
        start = 0
        end = 0
        tt = 0
        balance = 0
        data = self.r_d()
        lt = 0.0
        lt = bal / self.ppl
        self.buzzer(0)

        while loop:
            self.wdt.feed()
            try:
                start = time.time()
                flow_rate = self.flow_meter.start_measurement()
                print(f"The flow is: {flow_rate:.3f} Liter/min")
                self.printtxt(6, 0, "%.2f L" % (lt))
                count += flow_rate / 60
                count += 0.055
                self.printtxt(7, 1, "%.2f L" % (count))
                balance = self.balance - (count * int(self.ppl))-100
                if count >= (lt+0.055) or count >= (lt-0.055):
                    print("Kiasi: "+str(lt)+" Hela: " +
                          str(bal) + " Salio: "+str(balance))
                    self.printtxt(7, 1, "%.2f L " % (lt))
                    dbbal = self.lvl-count
                    data['level'] = dbbal
                    self.w_d(data)
                    self.lvl = self.r_d()["level"]
                    fmt_bal = "{:.2f}".format(balance)
                    # self.svdt(balance, self.user_card)
                    self.sv_bal(balance, self.user_card)
                    level = round(float(self.lvl), 2)
                    fmt_lt = round(float(lt), 2)
                    data = {
                        "uid": str(self.user_card),
                        "api": self.api,
                        "amt": str(bal),
                        "bal": str(balance),
                        "level": str(fmt_lt),
                        "tank": str(level)
                    }
                    self.add_trx(data)
                    self.method = "POST"
                    self.printtxt(0, 2, "Pesa:" +
                                        str("{:.1f}".format(int(bal))) + "TZS")
                    self.printtxt(0, 3, "ahsante karibu tena")
                    self.tsp(2)
                    self.lcr()
                    loop = False
                elif tt > 5:
                    print("Balance saved: "+str(balance))
                    self.sv_bal(balance, self.user_card)
                    self.scancard()
                    self.buzzer(0)
                    crd, scanned = self.scancard()
                    if scanned and crd != None:
                        print(
                            "Card yako ipo............................................")
                        self.buzzer(0)
                    else:
                        self.ctrv(0)  # turn to 1
                        self.buzzer(0)
                    tt = 0
                end = time.time()
                tt += (end - start)
                gc.collect()
            except KeyboardInterrupt:
                print("\nkeyboard interrupt!")

    def mpangilio(self):

        custkeys = ["#", "A", "B", "C", "D", "*"]
        number = ""
        data = self.r_d()
        self.lcr()
        self.printtxt(0, 0, "Level Setting")
        self.printtxt(0, 2, "Weka Kiasi")
        self.printtxt(0, 3, "Kiasi:")
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

    def run(self):
        self.tsp(2)
        start = 0
        end = 0
        while 1:
            start = time.time()
            self.wdt.feed()
            self.dc.acquire()
            try:
                crd, scanned = self.scancard()
                if scanned and crd != None:
                    self.card_in = True
                    self.user_card = str(crd)
                    self.lbo()
                    self.printtxt(0, 0, str(crd))
                    db = self.r_d()
                    found = False
                    users = db['users']
                    for user in users:
                        if str(crd) in user:
                            print(user)
                            self.balance = float(user[crd])
                            found = True
                            break
                        else:
                            found = False
                            self.balance = 0.0
                    self.ppl = db["ppl"]
                    if found:
                        self.buzzer(0)
                        # self.charge(1)
                        if (self.balance - 0.2) > 0:
                            self.printtxt(0, 0, "Kadi  " +
                                          str(crd)[:4] + "*****")
                            self.printtxt(0, 1, "Salio: %.1fTzs" %
                                          (self.balance))
                            self.tsp(2)
                            self.MenuEvent()
                            self.lvl = self.r_d()["level"]
                            lvl = float(self.lvl)
                            if lvl > 1:
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
                # x = self.scankeys().replace(" ", "")
                # if x != "":
                #     if x == "#":
                #         self.lbo()
                #         self.mpangilio()  129355 everist mgenyi
            except Exception as e:
                print(e)
            end = time.time()
            elapsed_time = end - start
            # print(elapsed_time)
            gc.collect()
            self.tsp(1)
            self.dc.release()
        return 0


app = App()
_thread.start_new_thread(app.get_gprs, ())
app.run()
