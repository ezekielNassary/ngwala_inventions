import utime as time
import _thread
import gc
import json
import asyncio
from machine import UART, I2C, Pin, WDT
from flow_meter import FlowMeter
from mfrc522 import MFRC522
from pico_i2c_lcd import I2cLcd
from keypad_unit import KeypadUnit
from menu_routine import Menu
from display_unit import DisplayUnit
from db_manager import DbManager


class App:
    def __init__(self):

        self.wdt = WDT(timeout=8000)
        self.dc = _thread.allocate_lock()

        # modules
        self.dsp = DisplayUnit(sda=14, scl=15)
        self.kpd = KeypadUnit()
        self.dbm = DbManager()
        self.flow_meter = FlowMeter()

        self.rfd = MFRC522(spi_id=0, sck=2, miso=4, mosi=3, cs=1, rst=0)
        self.gprs = UART(0, baudrate=9600, rx=Pin(17),
                         tx=Pin(16))
        self.gw = self.gprs.write
        self.gr = self.gprs.read

        # platform
        self.tsp = time.sleep
        self.pt = time.time()

        # from db
        self.url = ""
        self.calfactor = 7
        self.lvl = 10
        self.api = ""
        self.ppl = ""

        # gpios
        self.sensor_pin = Pin(19, Pin.IN, Pin.PULL_DOWN)
        self.led = Pin(20, Pin.OUT)
        self.reset_pin = Pin(21, Pin.IN, Pin.PULL_UP)
        self.pump = Pin(22, Pin.OUT)
        self.charge = Pin(27, Pin.OUT)
        self.buzzer = Pin(28, Pin.OUT)  # 28

        # variables
        self.stage = 0
        self.fl_frq = 0
        self.previous = 0
        self.balance = 0.0
        self.amount_entered = ""
        self.user_card = ""
        self.ph = ""
        self.ppl = 0.0
        self.data = {}
        self.card_in = False
        self.method = "GET"
        self.amt = 0.0
        self.postData = {}

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
            "AT"
        ]
        self.delays = [1, 3, 3, 2, 2, 2, 4, 4, 6, 5, 10, 10, 2, 2, 180]

        # initial starts
        self.pump(0)
        self.led(1)
        # self.initGsm()
        self.dsp.lcr()
        self.dsp.printtxt(0, 0, "     NG'WALA     ")
        self.dsp.printtxt(0, 1, "   INVENTIONS   ")
        self.tsp(2)
        self.dsp.lbf()
        gc.collect()

    async def init(self):
        self.url = await self.dbm.r_d()["url"]
        self.calfactor = await self.dbm.r_d()["calbrate"]
        self.lvl = await self.dbm.r_d()["level"]
        self.api = await self.dbm.r_d()["api"]
        self.ppl = await self.dbm.r_d()["ppl"]

    def initGsm(self):
        i = 0
        vl = 0
        strs = ""
        while 1:
            self.wdt.feed()
            self.dsp.lmt(i, 1)
            self.dsp.pts("-")
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
                        self.dsp.printtxt(0, 0, "Mtandao: " +
                                          str(rpsl[2].split(",")[2].replace('"', "")))
                        self.gw("AT+CSQ\r")
                        self.wdt.feed()
                        self.tsp(2)
                        strs = self.gr().decode().split()
                        vl = int(
                            strs[strs.index("+CSQ:") + 1].split(",")[0]) / 31
                        vl = vl * 100
                        self.dsp.printtxt(0, 1, "Nguvu  : " +
                                          str("{:.2f}".format(vl)) + "%")

                    except Exception as e:
                        print(str(e))
                    self.wdt.feed()
                    self.tsp(3)
                    del strs, vl, rpsl
                    break

            if i < 19:
                self.dsp.lmt(i, 1)
                self.dsp.pts("_")
                print(".")
                i = i + 1
            else:
                i = 0
            self.tsp(1)
            del rpsl

    def reset_pico(self, pin):
        machine.reset(pin)

    async def get_gprs(self):
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
                            db = self.dbm.r_d()
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
        local_data = self.dbm.r_d()
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

    def dispensePaste(self, bal):
        self.lcr()
        self.dsp.printtxt(0, 0, "Kiasi: ")
        self.dsp.printtxt(0, 1, "Chotwa: ")
        count = 0.00
        loop = True
        start = 0
        end = 0
        tt = 0
        balance = 0
        data = self.dbm.r_d()
        lt = 0.0
        lt = bal / self.ppl
        self.buzzer(0)
        self.pump(1)
        while loop:
            self.wdt.feed()
            try:
                start = time.time()
                flow_rate = self.flow_meter.start_measurement(self.calfactor)
                print(f"The flow is: {flow_rate:.3f} Liter/min")
                self.dsp.printtxt(6, 0, "%.2f L" % (lt))
                count += flow_rate / 60
                self.dsp.printtxt(7, 1, "%.2f L" % (count))
                balance = self.balance - (count * int(self.ppl))
                if count >= (lt+0.055) or count >= (lt-0.055):
                    self.pump(0)
                    print("Kiasi: "+str(lt)+" Hela: " +
                          str(bal) + " Salio: "+str(balance))
                    self.dsp.printtxt(7, 1, "%.2f L " % (lt))
                    dbbal = self.lvl-count
                    data['level'] = dbbal
                    self.w_d(data)
                    self.lvl = self.dbm.r_d()["level"]
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
                    self.dsp.printtxt(0, 2, "Pesa:" +
                                      str("{:.1f}".format(int(bal))) + "TZS")
                    self.dsp.printtxt(0, 3, "ahsante karibu tena")
                    self.tsp(2)
                    self.lcr()
                    loop = False
                elif tt > 5:
                    print("Balance saved: "+str(balance))
                    self.sv_bal(balance, self.user_card)
                    tt = 0
                end = time.time()
                tt += (end - start)
                gc.collect()
            except KeyboardInterrupt:
                print("\nkeyboard interrupt!")

    def scancard(self):
        crd = None
        flg = False
        try:
            (stat, tag_type) = self.rfd.request(self.rfd.REQIDL)
            if stat == self.rfd.OK:
                (stat, uid) = self.rfd.SelectTagSN()
                if stat == self.rfd.OK:
                    self.buzzer(1)
                    crd = str(int.from_bytes(bytes(uid), "little", False))
                    crd = str(crd)
                    gc.collect()
                    flg = True

        except KeyboardInterrupt:
            print("\nkeyboard interrupt!")
        return crd, flg

    async def run(self):
        await self.init()
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
                    print(crd)
                    self.card_in = True
                    self.user_card = str(crd)
                    self.dsp.lbo()
                    self.dsp.printtxt(0, 0, str(crd))
                    db = await self.dbm.r_d()
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
                        found = False
                        self.buzzer(0)
                        # self.charge(1)
                        if (self.balance - 0.2) > 0:
                            self.dsp.printtxt(0, 0, "Kadi  " +
                                              str(crd)[:4] + "*****")
                            self.dsp.printtxt(0, 1, "Salio: %.1fTzs" %
                                              (self.balance))
                            self.tsp(2)
                            self.lvl = self.dbm.r_d()["level"]
                            lvl = float(self.lvl)
                            if lvl > 1:
                                self.MenuEvent()
                            else:
                                self.dsp.printtxt(0, 0, "     Samahani  ")
                                self.dsp.printtxt(0, 1, " mashine iko nje ya")
                                self.dsp.printtxt(0, 2, "     huduma ")
                                self.dsp.printtxt(0, 3, "PIGA: 0754689034")
                                self.tsp(3)

                        else:
                            self.dsp.printtxt(0, 0, "Kadi  " +
                                              str(crd)[:4] + "*****")
                            self.dsp.printtxt(0, 1, "Haina Salio")
                            self.tsp(1.5)
                        self.lcr()
                        self.lbf()

                    else:
                        self.buzzer(0)
                        self.data = ""
                        self.lcr()
                        self.dsp.printtxt(0, 0, "Kadi haijasajiliwa")
                        self.dsp.printtxt(0, 1, "Tafadhali wasiliana")
                        self.dsp.printtxt(0, 2, "nasi kwa namba:    ")
                        self.dsp.printtxt(0, 3, "     0754689034   ")
                        self.tsp(3)
                        self.lcr()
                        self.lbf()
                        self.user_card = ""
                gc.collect()
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
_thread.start_new_thread(asyncio.run, (app.get_gprs(),))
asyncio.run(app.run())
