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
        self.total_cars = 0
        self.queue = queue.Queue()
        self.logger = Logger(filename=str(id))
        
        # metrics
        self.cars_present = 0
        self.cars_home_charging = 0
        self.home_charged = 0
        self.available_chargers = chargers
        self.queued_cars = 0
        self.cars_charged = 0
        self.total_autonomy = 0
        self.average_autonomy = 0
        
        # KPIs
        self.average_home_time = 0
        self.charger_utilization = 0
        self.average_queue_size = 0
        self.stress_metric = 0
        self.average_wait_time = 0
        self.average_charging_time = 0
        
        # history
        self.history = {
            'cars_present': [],
            'cars_home_charging': [],
            'available_chargers': [],
            'queued_cars': [],
            'cars_charged': [],
            'average_autonomy': [],
            'average_home_time': [],
            'charger_utilization': [],
            'average_queue_size': [],
            'stress_metric': [],
            'average_wait_time': [],
            'average_charging_time': []
        }
        
    # ---------------------------------------------------------------------------------------------------------

    def stop_charging(self, charging_time, at_home):
        if at_home:
            self.cars_home_charging -= 1
            self.home_charged += 1
            self.average_home_time = (self.average_home_time * (self.home_charged - 1) + charging_time) / self.home_charged
        else:
            self.available_chargers += 1
            self.cars_charged += 1
            self.average_charging_time = (self.average_charging_time * (self.cars_charged - 1) + charging_time) / self.cars_charged
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
        
    def update_wait_time(self, wait_time):
        self.queued_cars += 1
        self.average_wait_time = (self.average_wait_time * (self.queued_cars - 1) + wait_time) / self.queued_cars
        
    # ---------------------------------------------------------------------------------------------------------
        
    def update_autonomy(self, autonomy):
        self.total_autonomy += autonomy
        
    # ---------------------------------------------------------------------------------------------------------
        
    def run(self):
        self.average_autonomy = self.total_autonomy / self.total_cars
        self.total_autonomy = 0
        self.charger_utilization = round((1 - (self.available_chargers / self.chargers)) * 100, 2)
        self.average_queue_size = round(self.queue.qsize() / self.chargers, 2)
        ALFA = 1
        self.stress_metric = round(1 - (self.available_chargers / self.chargers) + ALFA * (self.queue.qsize() / self.chargers), 2)
        self.history['cars_present'].append(self.cars_present)
        self.history['cars_home_charging'].append(self.cars_home_charging)
        self.history['available_chargers'].append(self.available_chargers)
        self.history['queued_cars'].append(self.queued_cars)
        self.history['cars_charged'].append(self.cars_charged)
        self.history['average_autonomy'].append(round(self.average_autonomy, 2))
        self.history['average_home_time'].append(round(self.average_home_time, 2))
        self.history['charger_utilization'].append(round(self.charger_utilization, 2))
        self.history['average_queue_size'].append(round(self.average_queue_size, 2))
        self.history['stress_metric'].append(round(self.stress_metric, 2))
        self.history['average_wait_time'].append(round(self.average_wait_time, 2))
        self.history['average_charging_time'].append(round(self.average_charging_time, 2))
        
    # ---------------------------------------------------------------------------------------------------------
        
    def save_history(self):
        with open('logs/outputs/' + self.id + '.json', 'w') as f:
            json.dump(self.history, f)

# -------------------------------------------------------------------------------------------------------------