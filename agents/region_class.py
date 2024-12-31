import queue
import json

from log import Logger

TRAVELING = "[Traveling]"
IDLE = "[Idle]"
CHARGING = "[Charging]"
BEFORE_CHARGING = "[BeforeCharging]"
DECIDE_CHARGING = "[DecideCharging]"

class Region_Class:
    def __init__(self, id, latitude, longitude, chargers, traffic):
        self.id = id
        self.latitude = latitude
        self.longitude = longitude
        self.chargers = chargers
        self.traffic = traffic
        self.available_chargers = chargers
        self.queue = queue.Queue()
        self.cars_charged = 0
        self.stress_metric = 0
        self.logger = Logger(filename=str(id))
        
        # results
        self.charger_history = []
        self.queue_history = []

    def stop_charging(self):
        self.available_chargers += 1
        self.cars_charged += 1
        self.logger.log("Car has stopped charging")
        self.logger.log("Available chargers: " + str(self.available_chargers))
        self.logger.log("Cars charged: " + str(self.cars_charged))
        self.logger.log("")
        if not self.queue.empty():
            next_car = self.queue.get()
            self.start_charging(next_car)
            next_car.state = CHARGING # Notifies the next car that it has started charging. Avoids waiting for the next step to start charging.

    def start_charging(self, car):
        if self.available_chargers > 0:
            self.available_chargers -= 1
            self.logger.log("Car has started charging")
            self.logger.log("Available chargers: " + str(self.available_chargers))
            self.logger.log("")
            return True
        else:
            self.queue.put(car)
            self.logger.log("Car has been queued")
            self.logger.log("Queue size: " + str(self.queue.qsize()))
            self.logger.log("")
            return False

    def get_status(self):
        return self.available_chargers, self.queue.qsize()
    
    def update(self):
        # Calculate the stress metric based on available chargers and queue size
        ALFA = 1
        self.stress_metric = 1 - (self.available_chargers / self.chargers ) + ALFA * (self.queue.qsize() / self.chargers)
        
    def run(self, step):
        if step % 5 == 0:
            self.update()
        self.charger_history.append(self.available_chargers)
        self.queue_history.append(self.queue.qsize())
        
    def save_history(self):
        history = {
            "chargers": self.charger_history,
            "queue": self.queue_history
        }
        with open('logs/' + self.id + '.json', 'w') as f:
            json.dump(history, f)
