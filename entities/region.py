# -------------------------------------------------------------------------------------------------------------

import queue
import json

from logs.log import Logger

# -------------------------------------------------------------------------------------------------------------

TRAVELING = "[Traveling]"
IDLE = "[Idle]"
CHARGING = "[Charging]"
BEFORE_CHARGING = "[BeforeCharging]"
DECIDE_CHARGING = "[DecideCharging]"

# -------------------------------------------------------------------------------------------------------------

class Region:
    def __init__(self, id, latitude, longitude, avg_drivers, avg_income, chargers, traffic):
        self.id = id
        self.latitude = latitude
        self.longitude = longitude
        self.avg_drivers = int(avg_drivers)
        self.avg_income = int(avg_income)
        self.chargers = chargers
        self.traffic = traffic
        self.available_chargers = chargers
        self.total_cars = 0
        self.total_autonomy = 0
        self.queue = queue.Queue()
        self.queued_cars = 0
        self.cars_charged = 0
        self.stress_metric = 0
        self.average_wait_time = 0
        self.average_autonomy = 0
        self.logger = Logger(filename=str(id))
        self.charger_history = []
        self.queue_history = []
        self.wait_history = []
        self.autonomy_history = []
        
    # ---------------------------------------------------------------------------------------------------------

    def stop_charging(self):
        self.available_chargers += 1
        self.cars_charged += 1
        self.logger.log("Car has stopped charging")
        self.logger.log("Available chargers: " + str(self.available_chargers))
        self.logger.log("Cars charged: " + str(self.cars_charged))
        self.logger.log("")
        if not self.queue.empty():
            next_car = self.queue.get()
            next_car.exit_queue()
            self.start_charging(next_car)
            
    # ---------------------------------------------------------------------------------------------------------

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
        
    # ---------------------------------------------------------------------------------------------------------

    def get_status(self):
        return self.available_chargers, self.queue.qsize()
    
    # ---------------------------------------------------------------------------------------------------------
    
    def update(self):
        ALFA = 1
        self.stress_metric = 1 - (self.available_chargers / self.chargers ) + ALFA * (self.queue.qsize() / self.chargers)
        
    # ---------------------------------------------------------------------------------------------------------
        
    def update_wait_time(self, wait_time):
        self.queued_cars += 1
        self.average_wait_time = (self.average_wait_time * (self.queued_cars - 1) + wait_time) / self.queued_cars
        
    # ---------------------------------------------------------------------------------------------------------
        
    def update_autonomy(self, autonomy):
        self.total_autonomy += autonomy
        
    # ---------------------------------------------------------------------------------------------------------
        
    def run(self, step):
        if step % 5 == 0:
            self.update()
        self.average_autonomy = self.total_autonomy / self.total_cars
        self.total_autonomy = 0
        self.charger_history.append(self.available_chargers)
        self.queue_history.append(round(self.queue.qsize() / self.chargers, 2))
        self.wait_history.append(round(self.average_wait_time, 2))
        self.autonomy_history.append(round(self.average_autonomy, 2))
        self.save_history()
        
    # ---------------------------------------------------------------------------------------------------------
        
    def save_history(self):
        history = {
            "chargers": self.charger_history,
            "queue": self.queue_history,
            "wait": self.wait_history,
            "autonomy": self.autonomy_history
        }
        with open('logs/outputs/' + self.id + '.json', 'w') as f:
            json.dump(history, f)

# -------------------------------------------------------------------------------------------------------------