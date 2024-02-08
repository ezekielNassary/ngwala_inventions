from display_unit import DisplayUnit
import gc
import utime
from keypad_unit import KeypadUnit as keypad


class Menu:
    def __init__(self):
        self.tsp = utime.sleep
        self.dsp = DisplayUnit(14, 15)

    def MenuEvent(self, delay_ms=300):
        self.dsp.lcr()
        self.dsp.printtxt(0, 0, "A. Dawa")
        self.dsp.printtxt(0, 1, "B. Chaji")
        loop = True
        while loop:
            x = keypad.scankeys()
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
        self.dsp.lcr()
        self.dsp.printtxt(0, 0, "A. Pata Dawa")
        self.dsp.printtxt(0, 1, "B. Salio")
        loop = True
        while loop:
            x = keypad.scankeys()
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
        self.dsp.lcr()
        self.dsp.printtxt(0, 0, "Weka kiasi")
        self.dsp.printtxt(0, 1, "Kiasi:")
        loop = True
        i = 6
        custkeys = ["#", "A", "B", "C", "D", "*"]
        self.amount_entered = ""
        while loop:
            x = keypad.scankeys().replace(" ", "")
            if x != "":
                if x in custkeys:
                    if x == "*":
                        self.amount_entered = ""
                        self.dsp.lcr()
                        self.dsp.printtxt(0, 0, "Weka kiasi")
                        self.dsp.printtxt(0, 1, "Kiasi:")
                        i = 6
                        self.amount_entered = ""
                    if x == "#":
                        if self.amount_entered == "0000":
                            self.mpangilio()
                            loop = False
                        elif int(self.amount_entered) < self.ppl:
                            self.dsp.lcr()
                            self.dsp.printtxt(0, 0, "Tafahali weka ")
                            self.dsp.printtxt(0, 1, "Kuanzia  " +
                                              str("{:.2f}".format(self.ppl)))
                            self.tsp(3)
                            self.amount_entered = ""
                            self.subMenuEvent1()
                        elif self.balance > int(self.amount_entered):
                            loop = False
                            self.dispensePaste(int(self.amount_entered))

                        elif self.balance < int(self.amount_entered):
                            self.dsp.lcr()
                            self.dsp.printtxt(0, 0, "Kiasi ulichoweka")
                            self.dsp.printtxt(4, 1, "Kimezidi")
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
        self.dsp.lcr()
        self.dsp.printtxt(0, 0, "Salio lako ni")
        self.dsp.printtxt(4, 1, "%.2f Tzs" % (self.balance))
        self.tsp(3)

    def subMenuEvent3(self):
        v = 0.0
        bal = 15
        loop = True
        start = 0
        end = 0
        tsec = 0
        tmin = 0
        tt = 0
        self.dsp.lcr()
        self.dsp.printtxt(0, 0, "Chaji Simu Yako")
        self.dsp.printtxt(0, 1, "Dakika: %.2f " % (bal))
        while loop:
            self.wdt.feed()
            try:
                if time.time() - self.previous >= 1:
                    start = time.time()
                    # self.charge(1)
                    self.tsp(1)
                    end = time.time()
                    tt += (end - start)
                    if tt == 60:
                        tmin += 1
                        tt = 0
                    self.dsp.printtxt(0, 2, "Dakka: %.0f " % (tmin))
                    self.dsp.printtxt(0, 3, "Sek  : %.0f " % (tt))
                    if tmin >= bal:
                        # self.charge(0)
                        self.dsp.lcr()
                        self.dsp.printtxt(0, 0, "ahsante karibu tena")
                        self.tsp(2)
                        loop = False
                    gc.collect()
            except KeyboardInterrupt:
                print("\nkeyboard interrupt!")
                loop = False

    def mpangilio(self):
        custkeys = ["#", "A", "B", "C", "D", "*"]
        number = ""
        data = self.r_d()
        self.dsp.lcr()
        self.dsp.printtxt(0, 0, "Level Setting")
        self.dsp.printtxt(0, 2, "Weka Kiasi")
        self.dsp.printtxt(0, 3, "Kiasi:")
        data = self.r_d()
        self.dsp.printtxt(0, 1, "Balance:%.2f L " % (data['level']))
        i = 6
        loop = True
        while loop:
            x = keypad.scankeys().replace(" ", "")
            if x != "":
                if x in custkeys:
                    if x == "*":
                        number = ""
                        self.dsp.lcr()
                        self.dsp.printtxt(0, 0, "Weka Kiasi")
                        self.dsp.printtxt(0, 1, "Kiasi:")
                        i = 6
                    if x == "#" and number != "":
                        n_level = self.lvl + float(number)
                        data['level'] = n_level
                        self.lvl = n_level
                        self.w_d(data)
                        self.dsp.lcr()
                        self.dsp.printtxt(0, 0, "Level Updated ")
                        self.dsp.printtxt(0, 1, "Succesful")
                        time.sleep(1)
                        self.dsp.lbf()
                        del (n_level)
                        gc.collect()
                        loop = False
                    if x == "C":
                        self.dsp.lbf()
                        loop = False
                else:
                    buton = str(x)
                    number += buton
                    self.dsp.printtxt(i, 3, buton)
                    i += 1
                    if i > 16:
                        i = 6
                        self.amount_entered = ""
        del (custkeys, number, loop, i)
        gc.collect()
