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
    """
    A class used to represent a Region.
    
    Attributes:
        id (str): The unique identifier for the region.
        latitude (float): The latitude coordinate of the region.
        longitude (float): The longitude coordinate of the region.
        avg_drivers (int): The average number of drivers in the region.
        avg_income (int): The average income of the drivers in the region.
        chargers (int): The total number of chargers in the region.
        traffic (int): The traffic level in the region.
        total_cars (int): The total number of cars from the region.
        queue (queue.Queue): The queue of cars waiting to charge.
        logger (Logger): The logger instance for logging events.
        cars_present (int): The number of cars currently present in the region.
        cars_home_charging (int): The number of cars charging at home.
        home_charged (int): The number of cars that have charged at home.
        available_chargers (int): The number of available chargers.
        queued_cars (int): The number of cars that queued for charging.
        cars_charged (int): The number of cars that have been charged.
        total_autonomy (int): The total autonomy of all cars.
        average_autonomy (float): The average autonomy of the cars.
        average_home_time (float): The average time cars spend charging at home.
        charger_utilization (float): The utilization rate of the chargers.
        average_queue_size (float): The average size of the charging queue.
        stress_metric (float): The stress metric of the region.
        average_wait_time (float): The average wait time for charging.
        average_charging_time (float): The average time spent charging.
        history (dict): The history of various metrics over time.
    """
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
        """
        Stops the charging process for a car and updates relevant statistics.

        Args:
            charging_time (float): The time the car spent charging.
            at_home (bool): A flag indicating whether the car was charging at home.
        """
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
        """
        Attempts to start charging a car. If there are available chargers, the car starts charging
        and the number of available chargers is decremented. If no chargers are available, the car
        is added to the queue.

        Args:
            car: The car object that is attempting to start charging.

        Returns:
            bool: True if the car has started charging, False if the car has been queued.
        """
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
        """
        Get the current status of the region.

        Returns:
            tuple: A tuple containing the number of available chargers (int) 
                   and the size of the queue (int).
        """
        return self.available_chargers, self.queue.qsize()
        
    # ---------------------------------------------------------------------------------------------------------
        
    def update_wait_time(self, wait_time):
        """
        Update the average wait time for the region.

        Args:
            wait_time (float): The wait time to be added to the average wait time.

        Returns:
            None
        """
        self.queued_cars += 1
        self.average_wait_time = (self.average_wait_time * (self.queued_cars - 1) + wait_time) / self.queued_cars
        
    # ---------------------------------------------------------------------------------------------------------
        
    def update_autonomy(self, autonomy):
        """
        Updates the total autonomy of the region.

        Args:
            autonomy (float): The amount of autonomy to add to the total autonomy.
        """
        self.total_autonomy += autonomy
        
    # ---------------------------------------------------------------------------------------------------------
        
    def run(self):
        """
        Executes the main logic for updating the region's metrics and history.
        """
        self.average_autonomy = self.total_autonomy / self.total_cars
        self.total_autonomy = 0
        self.charger_utilization = round((1 - (self.available_chargers / self.chargers)) * 100, 2)
        self.average_queue_size = round(self.queue.qsize() / self.chargers, 2)
        ALFA = 1
        self.stress_metric = round(1 - (self.available_chargers / self.chargers) + ALFA * (self.queue.qsize() / self.chargers), 2)
        self.history['cars_present'].append(self.cars_present)
        self.history['cars_home_charging'].append(self.cars_home_charging)
        self.history['available_chargers'].append(self.available_chargers)
        self.history['queued_cars'].append(self.queue.qsize())
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
        """
        Saves the simulation history of the region to a JSON file.
        """
        with open('logs/outputs/' + self.id + '.json', 'w') as f:
            json.dump(self.history, f)

# -------------------------------------------------------------------------------------------------------------