import asyncio
import spade
import re
import random
from spade import agent
from spade.behaviour import OneShotBehaviour, CyclicBehaviour, PeriodicBehaviour, FSMBehaviour, State
from spade.message import Message
from spade.template import Template
from aux_funcs import evaluate_proposals, haversine_distance, calculate_angle, sort_orders_by_shortest_path
import json
from math import sin, cos, radians

ASK_ORDERS = "[AskOrders]"
AWAIT_ORDERS = "[AwaitOrders]"
ANSWER_PROPOSALS = "[AnswerProposals]"
DELIVERING_ORDERS = "[DeliveringOrders]"
MOVING_TO_CENTER = "[MovingToCenter]"

TRAVELING = "[Traveling]"
IDLE = "[Idle]"
CHARGING = "[Charging]"

class CarAgent(agent.Agent):
    def __init__(self, jid, password, autonomy, velocity, currentRegion, regions):
        super().__init__(jid, password)
        self.autonomy = autonomy
        self.full_autonomy = autonomy
        self.velocity = velocity * 0.00001666666 * 200# in km/tick
        self.currentRegion = currentRegion
        self.latitude = currentRegion.latitude
        self.longitude = currentRegion.longitude
        self.number = int(self.extract_numeric_value(jid))
        self.distanceTravelled = 0
        self.regions = regions
        self.nextRegion = None
        self.chargeAtDestination = False

    async def setup(self):
        #print(f"Car agent {self.jid} started")

        fsm = self.CarFSMBehaviour()
        fsm.add_state(name=IDLE, state=self.Idle(), initial=True)
        fsm.add_state(name=TRAVELING, state=self.Traveling())
        fsm.add_state(name=CHARGING, state=self.Charging())


        fsm.add_transition(IDLE, TRAVELING)
        fsm.add_transition(TRAVELING, CHARGING)

        self.add_behaviour(fsm)

        # b1 = self.ReceiveMessageBehaviour()
        # self.add_behaviour(b1)

        stop_behaviour = self.StopBehaviour()
        template = spade.template.Template()
        template.body = "stop"
        self.add_behaviour(stop_behaviour, template)

    def extract_numeric_value(self, value_str):
        """
        Extracts the numeric value from a string containing numeric value followed by units.
        Example: "20km/h" -> 20
        """
        numeric_part = ""
        for char in value_str:
            if char.isdigit() or char == ".":
                numeric_part += char
        return float(numeric_part) if numeric_part else None

    def next_pos(self, angle):
        # Convert latitude from degrees to radians
        lat1 = radians(self.latitude)

        # Calculate the new latitude
        new_latitude = self.latitude + self.velocity * sin(angle) / 111.2

        # Calculate the new longitude
        new_longitude = self.longitude + self.velocity * \
            cos(angle) / (111.2 * cos(lat1))

        return new_latitude, new_longitude
    
    def pick_next_region(self):
        valid_regions = [region for region in self.regions if haversine_distance(self.latitude, self.longitude, region.latitude, region.longitude) < self.autonomy and region != self.currentRegion]
        if not valid_regions:
            raise Exception("No reachable region within autonomy")
        self.nextRegion = random.choice(valid_regions)        

    class CarFSMBehaviour(FSMBehaviour):
        async def on_start(self):
            #print(f"Drone FSM starting at initial state {self.current_state}")
            pass

        async def on_end(self):
            #print(f"Drone FSM finished at state {self.current_state}")
            await self.agent.stop()


    class Idle(State):
        async def run(self):
            print(f"Car agent travelling:")

            if random.random() < 1:
                self.agent.pick_next_region()
                self.set_next_state(TRAVELING)
    
    class Traveling(State):
        async def run(self):

            # Calculate the distance and angle to the destination

            while self.agent.autonomy > 0:
                # Move the car towards the destination
                angle = calculate_angle(
                    (self.agent.latitude, self.agent.longitude), (self.agent.nextRegion.latitude, self.agent.nextRegion.longitude))
                next_lat, next_long = self.agent.next_pos(angle)
                future_movement = haversine_distance(
                    self.agent.latitude, self.agent.longitude, next_lat, next_long)
                distance = haversine_distance(
                    self.agent.latitude, self.agent.longitude, self.agent.nextRegion.latitude, self.agent.nextRegion.longitude)
                distance_travelled = 0
                if future_movement > distance:
                    self.agent.latitude = self.agent.nextRegion.latitude
                    self.agent.longitude = self.agent.nextRegion.longitude
                    distance_travelled = distance
                    self.agent.autonomy -= distance_travelled
                    self.agent.distanceTravelled += distance_travelled
                    break
                else:
                    self.agent.latitude = next_lat
                    self.agent.longitude = next_long
                    distance_travelled = future_movement

                # Decrease the car's autonomy based on the distance travelled
                self.agent.autonomy -= distance_travelled
                self.agent.distanceTravelled += distance_travelled
                # Wait for a tick
                await asyncio.sleep(1 / 60)
            self.set_next_state(CHARGING)
            print("Arrived at destination")
            #self.agent.autonomy = self.agent.full_autonomy
            #self.agent.orders.extend(self.agent.future_orders)
            #if self.agent.orders:
            #    self.agent.weights.append(sum([order[3] for order in self.agent.orders]) / self.agent.capacity)
            #self.agent.future_orders = []
            #self.set_next_state(DELIVERING_ORDERS)
    
    class Charging(State):
        async def run(self):
            self.agent.currentRegion = self.agent.nextRegion
            self.agent.nextRegion = None
            print(f"Car agent charging:")
            

    class StopBehaviour(spade.behaviour.CyclicBehaviour):
        async def run(self):
            msg = await self.receive(timeout=10)
            if msg:
                if msg.body == "stop":
                    #print(f"Received stop message. Stopping drone {self.agent.jid} ...")
                    await self.agent.stop()
