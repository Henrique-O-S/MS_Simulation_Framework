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
BEFORE_CHARGING = "[BeforeCharging]"
DECIDE_CHARGING = "[DecideCharging]"


class CarAgent(agent.Agent):
    def __init__(self, jid, password, autonomy, velocity, currentRegion, regions, region_jids):
        super().__init__(jid, password)
        self.autonomy = autonomy
        self.full_autonomy = autonomy
        self.velocity = velocity * 0.00001666666 * 200  # in km/tick
        self.currentRegion = currentRegion
        self.latitude = currentRegion.latitude
        self.longitude = currentRegion.longitude
        self.number = int(self.extract_numeric_value(jid))
        self.distanceTravelled = 0
        self.regions = regions
        self.nextRegion = None
        self.chargeAtDestination = False
        self.stuckAtRegion = False
        self.region_jids = region_jids

    async def setup(self):
        # print(f"Car agent {self.jid} started")

        fsm = self.CarFSMBehaviour()
        fsm.add_state(name=IDLE, state=self.Idle(), initial=True)
        fsm.add_state(name=DECIDE_CHARGING, state=self.DecideCharging())
        fsm.add_state(name=BEFORE_CHARGING, state=self.BeforeCharging())
        fsm.add_state(name=TRAVELING, state=self.Traveling())
        fsm.add_state(name=CHARGING, state=self.Charging())

        fsm.add_transition(IDLE, DECIDE_CHARGING)
        fsm.add_transition(IDLE, TRAVELING)
        fsm.add_transition(IDLE, IDLE)

        fsm.add_transition(DECIDE_CHARGING, BEFORE_CHARGING)
        fsm.add_transition(DECIDE_CHARGING, TRAVELING)

        fsm.add_transition(TRAVELING, IDLE)
        fsm.add_transition(TRAVELING, BEFORE_CHARGING)

        fsm.add_transition(BEFORE_CHARGING, CHARGING)

        fsm.add_transition(CHARGING, IDLE)

        self.add_behaviour(fsm)

        # b1 = self.ReceiveMessageBehaviour()
        # self.add_behaviour(b1)

        stop_behaviour = self.StopBehaviour()
        template = spade.template.Template()
        template.body = "stop"
        self.add_behaviour(stop_behaviour, template)

    def get_battery_percentage(self):
        return self.autonomy / self.full_autonomy

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

    def reachable_regions(self):
        return [region for region in self.regions if haversine_distance(
            self.latitude, self.longitude, region.latitude, region.longitude) < self.autonomy]

    def pick_next_region(self):
        valid_regions = [region for region in self.reachable_regions() if region != self.currentRegion]
        if len(valid_regions) == 0:
            return None
        return random.choice(valid_regions)

    def arrived_at_destination(self):
        self.currentRegion = self.nextRegion
        self.nextRegion = None

    class CarFSMBehaviour(FSMBehaviour):
        async def on_start(self):
            # print(f"Drone FSM starting at initial state {self.current_state}")
            pass

        async def on_end(self):
            # print(f"Drone FSM finished at state {self.current_state}")
            await self.agent.stop()

    class Idle(State):
        async def run(self):
            # print(f"Car agent {self.agent.jid} is idle.")
            print(f"Current battery: {self.agent.get_battery_percentage()}")
            # If battery is bellow 30, 70 percent chance of charging
            if self.agent.get_battery_percentage() < 0.3 and random.random() < 0.7:
                print(f"Decided to charge.")
                self.set_next_state(DECIDE_CHARGING)

            elif random.random() < 0.3:  # 30% chance of staying idle
                print(f"Decided to stay idle for now.")
                # await asyncio.sleep(6)  # Stay idle for 6 seconds
                print("Waking up from idle.")
                self.set_next_state(IDLE)

            else:  # Travel if not idling or charging
                print(f"Deciding to travel.")
                next_region = self.agent.pick_next_region()
                if next_region:
                    self.agent.nextRegion = next_region
                    self.set_next_state(TRAVELING)
                else:
                    print("No valid region to travel to. Staying idle.")
                    self.agent.stuckAtRegion = True
                    self.set_next_state(BEFORE_CHARGING)

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
            self.agent.arrived_at_destination()
            print("Arrived at destination")
            if self.agent.chargeAtDestination:
                self.agent.chargeAtDestination = False
                self.set_next_state(BEFORE_CHARGING)
            else:
                self.set_next_state(IDLE)

    class DecideCharging(State):
        async def run(self):
            expectedResponses = 0
            reachable_regions = self.agent.reachable_regions()
            for region_jid in self.agent.region_jids.values():
                if region_jid not in map(lambda x: x.id + "@localhost", reachable_regions):
                    print("Region not reachable ", region_jid)
                    continue
                expectedResponses += 1
                message = Message(to=region_jid)
                print("asking for available chargers in ", region_jid)
                message.body = "[AskAvailableChargers]"
                await self.send(message)

            # Wait for the responses
            responses = []
            for _ in range(expectedResponses):
                msg = await self.receive(timeout=3)
                if msg:
                    responses.append((msg.sender, int(msg.body)))

            responses.sort(key=lambda x: x[1], reverse=True)

            chargingRegionID = responses[0][0].localpart

            print(f"Charging region picked: {chargingRegionID}")

            if self.agent.currentRegion.id == chargingRegionID:
                print("Already at charging region")
                self.set_next_state(BEFORE_CHARGING)

            else:
                for region in self.agent.regions:
                    if region.id == chargingRegionID:
                        print(f"Charging region found: {region}")
                        self.agent.chargeAtDestination = True
                        self.agent.nextRegion = region
                        self.set_next_state(TRAVELING)

    class BeforeCharging(State):
        async def run(self):
            message = Message(to=self.agent.currentRegion.id + "@localhost")
            message.body = "[JoinQueue]"
            await self.send(message)
            msg = None
            while not msg:
                msg = await self.receive(timeout=10)
                if msg:
                    if msg.body == "[ChargingStarted]":
                        self.set_next_state(CHARGING)
                else:
                    print(f"{self.agent.jid} is waiting for a charger...")

    class Charging(State):
        async def run(self):
            print(f"{self.agent.jid} has started charging at {self.agent.currentRegion}")
            await asyncio.sleep(10)  # Charging time
            self.agent.autonomy = self.agent.full_autonomy  # Reset battery after charging
            message = Message(
                to=self.agent.region_jids[self.agent.currentRegion.id])
            message.body = "[StopCharging]"
            await self.send(message)
            print(f"{self.agent.jid} has finished charging. Battery full.")
            self.set_next_state(IDLE)

    class StopBehaviour(spade.behaviour.CyclicBehaviour):
        async def run(self):
            msg = await self.receive(timeout=10)
            if msg:
                if msg.body == "stop":
                    # print(f"Received stop message. Stopping drone {self.agent.jid} ...")
                    await self.agent.stop()
