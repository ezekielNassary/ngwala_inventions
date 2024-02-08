from machine import Pin
import time


class FlowMeter:
    def __init__(self, flow_sensor_gpio=18):
        self.flow = Pin(flow_sensor_gpio, Pin.IN, Pin.PULL_UP)
        self.count = 0
        self.start_counter = 0
        self.flow_rate = 0

        self.flow.irq(trigger=Pin.IRQ_FALLING, handler=self.count_pulse)

    def count_pulse(self, channel):
        if self.start_counter == 1:
            self.count += 1

    def start_measurement(self):
        self.start_counter = 1
        time.sleep(1)
        self.start_counter = 0
        self.flow_rate = self.count / 7.5
        self.count = 0
        return self.flow_rate
