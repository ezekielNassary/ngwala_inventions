from machine import Pin, WDT
import utime


class KeypadUnit:
    def __init__(self):
        self.wdt = WDT(timeout=8000)
        self.buzzer = Pin(28, Pin.OUT)
        self.tsp = utime.sleep
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
