import random
import os
from dotenv import load_dotenv, dotenv_values
from aux_funcs import haversine_distance, calculate_angle, region_distances
from math import sin, cos, radians

load_dotenv()


TRAVELING = "[Traveling]"
IDLE = "[Idle]"
CHARGING = "[Charging]"
BEFORE_CHARGING = "[BeforeCharging]"
DECIDE_CHARGING = "[DecideCharging]"
CHARGING_AT_HOME = "[ChargingAtHome]"
IN_QUEUE = "[InQueue]"

class Car_Class:
    def __init__(self, id, autonomy, velocity, current_region, regions):
        self.id = id
        self.full_autonomy = autonomy
        self.autonomy = autonomy * random.uniform(0.5, 1.0)
        self.velocity = velocity / (int(os.getenv("STEPS_PER_DAY")) / 24) # km/step
        self.current_region = current_region
        self.home_region = current_region
        self.latitude = current_region.latitude
        self.longitude = current_region.longitude
        self.distance_travelled = 0
        self.regions = regions
        self.next_region = None
        self.charge_at_destination = False
        self.stuck_at_region = False
        self.state = IDLE

    def get_battery_percentage(self):
        return self.autonomy / self.full_autonomy
    
    def arrived_at_destination(self):
        self.current_region = self.next_region
        self.next_region = None

    def reachable_regions(self):
        return [region for region in self.regions if region_distances[self.current_region.id][region.id] < self.autonomy]

    def pick_next_region(self):
        valid_regions = [region for region in self.reachable_regions() if region != self.current_region]
        if not valid_regions:
            return None
        traffic = [region.traffic if region != self.home_region else 30 for region in valid_regions]
        return random.choices(valid_regions, weights=traffic, k=1)[0]

    def next_pos(self, angle):
        new_latitude = self.latitude + self.velocity * sin(angle) / 111.2
        new_longitude = self.longitude + self.velocity * cos(angle) / (111.2 * cos(radians(self.latitude)))
        return new_latitude, new_longitude

    def charge(self):
        self.autonomy = self.full_autonomy

    def run(self, rush_hour):
        #print(f"Current battery: {self.get_battery_percentage()}")
        if self.state == IDLE:
            if self.get_battery_percentage() < float(os.getenv("AUTONOMY_TOLERANCE")) and random.random() < float(os.getenv("PROBABILITY_OF_CHARGING")):
                if self.current_region == self.home_region and random.random() < float(os.getenv("PROBABILITY_OF_CHARGING_AT_HOME")):
                    #print(f"{self.id} has started charging at home")
                    self.state = CHARGING
                else:
                    #print(f"Decided to charge.")
                    self.state = DECIDE_CHARGING
            elif rush_hour:
                if random.random() < float(os.getenv("CHANCE_OF_STAYING_IDLE_RUSH_HOUR")):
                    #print(f"Decided to stay idle for now.")
                    self.state = IDLE
                else:  # Travel if not idling or charging
                    #print(f"Deciding to travel.")
                    next_region = self.pick_next_region()
                    if next_region:
                        self.next_region = next_region
                        self.state = TRAVELING
                    else:
                        #print("No valid region to travel to. Im stuck in region. Going to recharge")
                        self.stuckAtRegion = True
                        self.state = BEFORE_CHARGING
            else:
                if random.random() < float(os.getenv("CHANCE_OF_STAYING_IDLE")):
                #print(f"Decided to stay idle for now."
                    self.state = IDLE
                else:  # Travel if not idling or charging
                    #print(f"Deciding to travel.")
                    next_region = self.pick_next_region()
                    if next_region:
                        self.next_region = next_region
                        self.state = TRAVELING
                    else:
                        #print("No valid region to travel to. Im stuck in region. Going to recharge")
                        self.stuckAtRegion = True
                        self.state = BEFORE_CHARGING

        elif self.state == TRAVELING:
            # Move the car towards the destination
            angle = calculate_angle(
                (self.latitude, self.longitude), (self.next_region.latitude, self.next_region.longitude))
            next_lat, next_long = self.next_pos(angle)
            future_movement = haversine_distance(
                self.latitude, self.longitude, next_lat, next_long)
            distance = haversine_distance(
                self.latitude, self.longitude, self.next_region.latitude, self.next_region.longitude)
            distance_travelled = 0
            if future_movement > distance:
                self.latitude = self.next_region.latitude
                self.longitude = self.next_region.longitude
                distance_travelled = distance
                self.autonomy -= distance_travelled
                self.distance_travelled += distance_travelled
                self.arrived_at_destination()
                #print("Arrived at destination")
                if self.charge_at_destination:
                    self.charge_at_destination = False
                    self.state = BEFORE_CHARGING
                else:
                    self.state = IDLE
            else:
                self.latitude = next_lat
                self.longitude = next_long
                distance_travelled = future_movement

                # Decrease the car's autonomy based on the distance travelled
                self.autonomy -= distance_travelled
                self.distance_travelled += distance_travelled
            

        elif self.state == DECIDE_CHARGING:
            reachable_regions = self.reachable_regions()
            responses = [(region, region.get_status()) for region in reachable_regions]

            def score(response):
                region, (chargers, queue_size) = response
                distance = region_distances[self.current_region.id][region.id]
                distance += 0.1
                return float(os.getenv("DISTANCE_WEIGHT")) * (1 / distance) + float(os.getenv("AVAILABILITY_WEIGHT")) * chargers - float(os.getenv("QUEUE_WEIGHT")) * queue_size

            responses.sort(key=score, reverse=True)

            charging_region = responses[0][0] if responses else None

            #print(f"Charging region picked: {charging_region}")

            if self.current_region.id == charging_region.id:
                #print("Already at charging region")
                self.state = BEFORE_CHARGING
            else:
                for region in self.regions:
                    if region.id == charging_region.id:
                        #print(f"Charging region found: {region}")
                        self.charge_at_destination = True
                        self.next_region = region
                        self.state = TRAVELING

        elif self.state == BEFORE_CHARGING:
            if self.stuck_at_region:
                #print("Stuck at region. Charging now.")
                if self.current_region.start_charging(self):
                        self.stuck_at_region = False
                        self.state = CHARGING
                else:
                    #print("Waiting for charger.")
                    self.state = IN_QUEUE
                    pass
            else:
                #print("Charging at destination.")
                if self.current_region.start_charging(self):
                        self.stuck_at_region = False
                        self.state = CHARGING
                else:
                    #print("Waiting for charger.")
                    self.state = IN_QUEUE
                    pass

        elif self.state == IN_QUEUE:
            pass

        elif self.state == CHARGING:
            #print(f"{self.id} has started charging at {self.current_region}")
            if self.autonomy >= self.full_autonomy:
                #print(f"{self.id} has finished charging. Battery full.")
                self.autonomy = self.full_autonomy
                self.current_region.stop_charging()
                self.state = IDLE
            else:
                self.autonomy += float(os.getenv("CHARGING_PER_STEP"))
                #print(f"{self.id} is still charging. Battery: {self.get_battery_percentage()}")

        elif self.state == CHARGING_AT_HOME:
            if self.autonomy >= self.full_autonomy:
                #print(f"{self.id} has finished charging. Battery full.")
                self.autonomy = self.full_autonomy
                self.state = IDLE
            else:
                self.autonomy += float(os.getenv("CHARGING_PER_STEP"))
                #print(f"{self.id} is still charging at home. Battery: {self.get_battery_percentage()}

        else:
            print("Deu raia")
            self.state = IDLE
