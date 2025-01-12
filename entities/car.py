# -------------------------------------------------------------------------------------------------------------

import random
import os

from math import sin, cos, radians, ceil

from utils import haversine_distance, calculate_angle, region_distances
from logs.log import Logger
from dotenv import load_dotenv

# -------------------------------------------------------------------------------------------------------------

os.environ.clear()
load_dotenv()

TRAVELING = "[Traveling]"
IDLE = "[Idle]"
CHARGING = "[Charging]"
BEFORE_CHARGING = "[BeforeCharging]"
DECIDE_CHARGING = "[DecideCharging]"
CHARGING_AT_HOME = "[ChargingAtHome]"
IN_QUEUE = "[InQueue]"

# -------------------------------------------------------------------------------------------------------------

class Car:
    """
    Represents a car in the simulation.

    Attributes:
        id (int): Unique identifier for the car.
        full_autonomy (float): The maximum autonomy of the car in kilometers.
        autonomy (float): The current autonomy of the car in kilometers.
        velocity (float): The velocity of the car in kilometers per step.
        current_region (Region): The current region where the car is located.
        home_region (Region): The home region of the car.
        latitude (float): The current latitude of the car.
        longitude (float): The current longitude of the car.
        distance_travelled (float): The total distance travelled by the car.
        wait_time (int): The time the car has spent waiting.
        charging_time (int): The time the car has spent charging.
        regions (list): List of all regions in the simulation.
        next_region (Region): The next region the car will travel to.
        charge_at_destination (bool): Whether the car will charge at the destination.
        stuck_at_region (bool): Whether the car is stuck at a region.
        state (str): The current state of the car.
        idle_probabilities (dict): Probabilities of the car staying idle at different times of the day.
        displayed (bool): Whether the car is displayed in the simulation.
        stepsToTravel (int): The number of steps required to travel to the next region.
        currentTripSteps (int): The number of steps taken in the current trip.
        distanceToTravel (float): The distance to travel to the next region.
        logger (Logger): Logger instance for logging car activities.
        availabilityWeigh (float): Weight for availability in the decision-making process.
        distanceWeight (float): Weight for distance in the decision-making process.
        queueWeigh (float): Weight for queue size in the decision-making process.
        stop_charging_at_home (bool): Whether the car should stop charging at home.
    """
    def __init__(self, id, autonomy, velocity, current_region, regions):
        self.id = id
        self.full_autonomy = autonomy
        self.autonomy = autonomy * random.uniform(0.5, 1.0)
        self.velocity = velocity / (int(os.getenv("STEPS_PER_DAY")) / 24) # km/step
        self.current_region = current_region
        self.current_region.cars_present += 1
        self.home_region = current_region
        self.latitude = current_region.latitude
        self.longitude = current_region.longitude
        self.distance_travelled = 0
        self.wait_time = 0
        self.charging_time = 0
        self.regions = regions
        self.next_region = None
        self.charge_at_destination = False
        self.stuck_at_region = False
        self.state = IDLE
        self.idle_probabilities = {
            "rush_hour": float(os.getenv("CHANCE_OF_STAYING_IDLE_RUSH_HOUR")),
            "lunch_time": float(os.getenv("CHANCE_OF_STAYING_IDLE_LUNCH_TIME")),
            "night_time": float(os.getenv("CHANCE_OF_STAYING_IDLE_NIGHT_TIME")),
            "dawn_time": float(os.getenv("CHANCE_OF_STAYING_IDLE_DAWN_TIME")),
            "default": float(os.getenv("CHANCE_OF_STAYING_IDLE"))
        }
        self.displayed = False
        self.stepsToTravel = 0
        self.currentTripSteps = 0
        self.distanceToTravel = 0
        self.logger = Logger(filename="cars")
        self.availabilityWeigh = float(os.getenv("AVAILABILITY_WEIGHT"))
        self.distanceWeight = float(os.getenv("DISTANCE_WEIGHT"))
        self.queueWeigh = float(os.getenv("QUEUE_WEIGHT"))
        self.stop_charging_at_home = False
        
    # ---------------------------------------------------------------------------------------------------------

    def get_battery_percentage(self):
        """
        Calculate the battery percentage of the car.

        Returns:
            float: The current battery percentage based on the car's autonomy and full autonomy.
        """
        return (self.autonomy / self.full_autonomy) * 100
    
    # ---------------------------------------------------------------------------------------------------------
    
    def arrived_at_destination(self):
        """
        Updates the car's current region to the next region and adjusts the count of cars present in each region.
        """
        self.current_region.cars_present -= 1
        self.current_region = self.next_region
        self.current_region.cars_present += 1
        self.next_region = None
        
    # ---------------------------------------------------------------------------------------------------------

    def reachable_regions(self):
        """
        Determines the regions that are reachable from the current region based on the car's autonomy.

        Returns:
            list: A list of regions that are within the car's autonomy range from the current region.
        """
        return [region for region in self.regions if region_distances[self.current_region.id][region.id] < self.autonomy]
    
    # ---------------------------------------------------------------------------------------------------------

    def pick_next_region(self):
        """
        Selects the next region for the car to move to from the list of reachable regions, 
        excluding the current region. If no valid regions are available, returns None. 
        The selection is weighted by the traffic in each region, with the home region 
        having a fixed traffic weight of 30.

        Returns:
            Region: The next region to move to, or None if no valid regions are available.
        """
        valid_regions = [region for region in self.reachable_regions() if region != self.current_region]
        if not valid_regions:
            return None
        traffic = [region.traffic if region != self.home_region else 30 for region in valid_regions]
        return random.choices(valid_regions, weights=traffic, k=1)[0]
    
    # ---------------------------------------------------------------------------------------------------------

    def next_pos(self, angle):
        """
        Calculate the next position of the car based on the given angle.

        Args:
            angle (float): The angle in radians at which the car is moving.

        Returns:
            tuple: A tuple containing the new latitude and longitude of the car.
        """
        new_latitude = self.latitude + self.velocity * sin(angle) / 111.2
        new_longitude = self.longitude + self.velocity * cos(angle) / (111.2 * cos(radians(self.latitude)))
        return new_latitude, new_longitude
    
    # ---------------------------------------------------------------------------------------------------------

    def idle(self, time_of_day):
        """
        Determines the car's behavior based on the time of day and battery level.

        Args:
            time_of_day (str): The current time of day, used to determine idle probabilities.
        """
        battery_threshold = float(os.getenv("AUTONOMY_TOLERANCE"))
        idle_chance = self.idle_probabilities.get(time_of_day, self.idle_probabilities["default"])
        if self.get_battery_percentage() < battery_threshold:
            self.consider_charging()
        elif random.random() >= idle_chance:
            self.consider_traveling()

    # ---------------------------------------------------------------------------------------------------------

    def consider_charging(self):
        """
        Determine whether the car should start charging based on random probabilities and its current region.
        """
        if random.random() < float(os.getenv("PROBABILITY_OF_CHARGING")):
            if self.current_region == self.home_region and random.random() < float(os.getenv("PROBABILITY_OF_CHARGING_AT_HOME")):
                self.state = CHARGING_AT_HOME
                self.home_region.cars_home_charging += 1
            else:
                self.state = DECIDE_CHARGING
                
    # ---------------------------------------------------------------------------------------------------------

    def consider_traveling(self):
        """
        Determines the next region for the car to travel to and updates the car's state accordingly.
        """
        next_region = self.pick_next_region()
        if next_region:
            self.next_region = next_region
            self.state = TRAVELING
        else:
            self.stuckAtRegion = True
            self.state = BEFORE_CHARGING
                    
    # ---------------------------------------------------------------------------------------------------------
                        
    def traveling(self):
        """
        Handles the movement of the car towards its next destination.

        If the car is displayed, it calculates the angle and the next position,
        then updates the car's latitude and longitude based on the calculated
        future movement. It also updates the car's autonomy and distance travelled.
        If the car reaches its destination, it updates the state accordingly.

        If the car is not displayed and stepsToTravel is 0, it calculates the
        distance to travel and the number of steps required to reach the destination.

        If the car is not displayed and stepsToTravel is greater than 0, it updates
        the current trip steps and checks if the car has reached its destination.
        If the destination is reached, it updates the car's latitude, longitude,
        autonomy, distance travelled, and state accordingly.
        """
        if(self.displayed):
            angle = calculate_angle(
                (self.latitude, self.longitude), (self.next_region.latitude, self.next_region.longitude))
            next_lat, next_long = self.next_pos(angle)
            future_movement = haversine_distance(
                self.latitude, self.longitude, next_lat, next_long)
            distance = haversine_distance(
                self.latitude, self.longitude, self.next_region.latitude, self.next_region.longitude)
            if future_movement >= distance:
                self.latitude = self.next_region.latitude
                self.longitude = self.next_region.longitude
                self.autonomy -= distance
                self.distance_travelled += distance
                self.arrived_at_destination()
                if self.charge_at_destination:
                    self.charge_at_destination = False
                    self.state = BEFORE_CHARGING
                else:
                    self.state = IDLE
            else:
                self.latitude = next_lat
                self.longitude = next_long
                self.autonomy -= future_movement
                self.distance_travelled += future_movement
        elif (self.stepsToTravel == 0):
            angle = calculate_angle(
                (self.latitude, self.longitude), (self.next_region.latitude, self.next_region.longitude))
            next_lat, next_long = self.next_pos(angle)
            future_movement = haversine_distance(
                self.latitude, self.longitude, next_lat, next_long)
            self.distanceToTravel = haversine_distance(
                self.latitude, self.longitude, self.next_region.latitude, self.next_region.longitude)
            self.stepsToTravel = ceil(self.distanceToTravel / future_movement)
        else:
            self.currentTripSteps += 1
            if self.currentTripSteps >= self.stepsToTravel:
                self.latitude = self.next_region.latitude
                self.longitude = self.next_region.longitude
                self.autonomy -= self.distanceToTravel
                self.distance_travelled += self.distanceToTravel
                self.arrived_at_destination()
                if self.charge_at_destination:
                    self.charge_at_destination = False
                    self.state = BEFORE_CHARGING
                else:
                    self.state = IDLE
                self.stepsToTravel = 0
                self.currentTripSteps = 0
            
    # ---------------------------------------------------------------------------------------------------------
            
    def decide_charging(self):
        """
        Determines the best region for the car to charge based on the availability of chargers,
        the size of the queue, and the distance to the region. The decision is made by scoring
        each reachable region and selecting the one with the highest score.
        """
        reachable_regions = self.reachable_regions()
        responses = [(region, region.get_status()) for region in reachable_regions]
        def score(response):
            region, (chargers, queue_size) = response
            distance = region_distances[self.current_region.id][region.id]
            distance += 0.1
            return self.distanceWeight * (1 / distance) + self.availabilityWeigh * chargers - self.queueWeigh * queue_size
        responses.sort(key=score, reverse=True)
        charging_region = responses[0][0] if responses else None
        if self.current_region.id == charging_region.id:
            self.state = BEFORE_CHARGING
        else:
            for region in self.regions:
                if region.id == charging_region.id:
                    self.charge_at_destination = True
                    self.next_region = region
                    self.state = TRAVELING
                    
    # ---------------------------------------------------------------------------------------------------------
                    
    def before_charging(self):
        """
        Attempt to start charging the car in the current region.
        """
        if self.current_region.start_charging(self):
            self.stuck_at_region = False
            self.exit_queue() # queue was empty
        else:
            self.state = IN_QUEUE
            
    # ---------------------------------------------------------------------------------------------------------

    def in_queue(self):
        """
        This method should be called to simulate the car waiting in a queue.
        Each call to this method increases the car's wait time by one unit.
        """
        self.wait_time += 1
        
    # ---------------------------------------------------------------------------------------------------------
        
    def exit_queue(self):
        """
        Handles the logic for a car exiting the queue.
        """
        self.current_region.update_wait_time(self.wait_time)
        self.wait_time = 0
        self.state = CHARGING
    
    # ---------------------------------------------------------------------------------------------------------
    
    def charging(self, time_of_day, at_home=False):
        """
        Manages the charging process of the car.

        Args:
            time_of_day (str): The current time of day, used to determine idle probabilities.
            at_home (bool): Indicates whether the car is charging at home. Defaults to False.
        """
        if self.autonomy >= self.full_autonomy:
            self.autonomy = self.full_autonomy
            self.current_region.stop_charging(self.charging_time, at_home)
            self.charging_time = 0
            self.state = IDLE
        else:
            charging_rate = float(os.getenv("CHARGING_PER_STEP_HOME")) if at_home else float(os.getenv("CHARGING_PER_STEP"))
            self.autonomy += charging_rate
            self.charging_time += 1
            if not at_home and random.random() < self.stop_charging_probability():
                self.current_region.stop_charging(self.charging_time, at_home)
                self.charging_time = 0
                self.state = IDLE 
            elif not self.stop_charging_at_home and at_home and random.random() < self.stop_charging_at_home_probability():
                self.stop_charging_at_home = True
            elif self.stop_charging_at_home and random.random() < self.idle_probabilities.get(time_of_day, self.idle_probabilities["default"]):
                self.current_region.stop_charging(self.charging_time, at_home)
                self.charging_time = 0
                self.stop_charging_at_home = False
                self.consider_traveling()
                
    # ---------------------------------------------------------------------------------------------------------

    def stop_charging_probability(self):
        """
        Calculate the probability of stopping the charging process based on the current battery percentage.

        Returns:
            float: The probability of stopping the charging process. 
                   If the battery percentage is less than 50%, the probability is 0.
                   If the battery percentage is 50% or more, the probability increases linearly from 0 to 5%.
        """
        battery_perc = self.get_battery_percentage()
        if battery_perc < 50:
            return 0
        else:
            return (battery_perc - 50) / 1000  # linearly increase from 0 to 5% probability 
        
    # ---------------------------------------------------------------------------------------------------------
        
    def stop_charging_at_home_probability(self):
        """
        Calculate the probability of stopping charging at home based on the current battery percentage.

        Returns:
            float: The probability of stopping charging at home. 
                   Returns 0 if the battery percentage is less than 30%.
                   Otherwise, returns a value linearly increasing from 0 to 0.7 as the battery percentage 
                   increases from 30% to 100%.
        """
        battery_perc = self.get_battery_percentage()
        if battery_perc < 30:
            return 0
        else:
            return (battery_perc - 30) / 100  # linearly increase from 0 to 70% probability 
            
    # ---------------------------------------------------------------------------------------------------------

    def run(self, time_of_day):
        """
        Executes the behavior of the car based on its current state and the time of day.

        Args:
            time_of_day (int): The current time of day.
        """
        if self.state == IDLE:
            self.idle(time_of_day)
        elif self.state == TRAVELING:
            self.traveling()
        elif self.state == DECIDE_CHARGING:
            self.decide_charging()
        elif self.state == BEFORE_CHARGING:
            self.before_charging()
        elif self.state == IN_QUEUE:
            self.in_queue()
        elif self.state == CHARGING:
            self.charging(time_of_day, at_home=False)
        elif self.state == CHARGING_AT_HOME:
            self.charging(time_of_day, at_home=True)
        self.home_region.update_autonomy(self.get_battery_percentage())
        if self.displayed:
            self.logger.log(f"{self.id} {self.state}")
            
# -------------------------------------------------------------------------------------------------------------