import queue

TRAVELING = "[Traveling]"
IDLE = "[Idle]"
CHARGING = "[Charging]"
BEFORE_CHARGING = "[BeforeCharging]"
DECIDE_CHARGING = "[DecideCharging]"

class Region_Class:
    def __init__(self, id, latitude, longitude, chargers):
        self.id = id
        self.latitude = latitude
        self.longitude = longitude
        self.chargers = chargers
        self.available_chargers = chargers
        self.queue = queue.Queue()
        self.cars_charged = 0

    def stop_charging(self):
        self.available_chargers += 1
        self.cars_charged += 1
        if not self.queue.empty():
            next_car = self.queue.get()
            self.start_charging(next_car)
            next_car.state = CHARGING # Notifies the next car that it has started charging. Avoids waiting for the next step to start charging.

    def start_charging(self, car):
        if self.available_chargers > 0:
            self.available_chargers -= 1
            return True
        else:
            self.queue.put(car)
            return False

    def get_status(self):
        return self.available_chargers, self.queue.qsize()
