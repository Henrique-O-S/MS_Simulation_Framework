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
        return (self.autonomy / self.full_autonomy) * 100
    
    # ---------------------------------------------------------------------------------------------------------
    
    def arrived_at_destination(self):
        self.current_region.cars_present -= 1
        self.current_region = self.next_region
        self.current_region.cars_present += 1
        self.next_region = None
        
    # ---------------------------------------------------------------------------------------------------------

    def reachable_regions(self):
        return [region for region in self.regions if region_distances[self.current_region.id][region.id] < self.autonomy]
    
    # ---------------------------------------------------------------------------------------------------------

    def pick_next_region(self):
        valid_regions = [region for region in self.reachable_regions() if region != self.current_region]
        if not valid_regions:
            return None
        traffic = [region.traffic if region != self.home_region else 30 for region in valid_regions]
        return random.choices(valid_regions, weights=traffic, k=1)[0]
    
    # ---------------------------------------------------------------------------------------------------------

    def next_pos(self, angle):
        new_latitude = self.latitude + self.velocity * sin(angle) / 111.2
        new_longitude = self.longitude + self.velocity * cos(angle) / (111.2 * cos(radians(self.latitude)))
        return new_latitude, new_longitude
    
    # ---------------------------------------------------------------------------------------------------------

    def idle(self, time_of_day):
        battery_threshold = float(os.getenv("AUTONOMY_TOLERANCE"))
        idle_chance = self.idle_probabilities.get(time_of_day, self.idle_probabilities["default"])
        if self.get_battery_percentage() < battery_threshold:
            self.consider_charging()
        elif random.random() >= idle_chance:
            self.consider_traveling()

    # ---------------------------------------------------------------------------------------------------------

    def consider_charging(self):
        if random.random() < float(os.getenv("PROBABILITY_OF_CHARGING")):
            if self.current_region == self.home_region and random.random() < float(os.getenv("PROBABILITY_OF_CHARGING_AT_HOME")):
                self.state = CHARGING_AT_HOME
                self.home_region.cars_home_charging += 1
            else:
                self.state = DECIDE_CHARGING
                
    # ---------------------------------------------------------------------------------------------------------

    def consider_traveling(self):
        next_region = self.pick_next_region()
        if next_region:
            self.next_region = next_region
            self.state = TRAVELING
        else:
            self.stuckAtRegion = True
            self.state = BEFORE_CHARGING
                    
    # ---------------------------------------------------------------------------------------------------------
                        
    def traveling(self):
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
        if self.current_region.start_charging(self):
            self.stuck_at_region = False
            self.exit_queue() # queue was empty
        else:
            self.state = IN_QUEUE
            
    # ---------------------------------------------------------------------------------------------------------

    def in_queue(self):
        self.wait_time += 1
        
    # ---------------------------------------------------------------------------------------------------------
        
    def exit_queue(self):
        self.current_region.update_wait_time(self.wait_time)
        self.wait_time = 0
        self.state = CHARGING
    
    # ---------------------------------------------------------------------------------------------------------
    
    def charging(self, time_of_day, at_home=False):
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

    def stop_charging_probability(self):
        battery_perc = self.get_battery_percentage()
        if battery_perc < 50:
            return 0
        else:
            return (battery_perc - 50) / 1000  # Linearly increase from 0 to 5% probability 
        
    def stop_charging_at_home_probability(self):
        battery_perc = self.get_battery_percentage()
        if battery_perc < 30:
            return 0
        else:
            return (battery_perc - 30) / 100  # Linearly increase from 0 to 70% probability 
            
    # ---------------------------------------------------------------------------------------------------------

    def run(self, time_of_day):
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