import asyncio
import spade
import re
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


class DroneAgent(agent.Agent):
    def __init__(self, jid, password, capacity, autonomy, velocity, initialPos, centers=[]):
        super().__init__(jid, password)
        self.capacity = capacity
        self.current_capacity = capacity
        self.autonomy = autonomy
        self.full_autonomy = autonomy
        self.velocity = velocity * 0.00001666666 * 200# in km/tick
        self.initialPos = initialPos
        self.latitude = 0
        self.longitude = 0
        self.number = int(self.extract_numeric_value(jid))
        self.centers = centers
        self.orders = []
        self.future_orders = []
        self.proposals = []
        self.distanceTravelled = 0
        self.weights = []

    async def setup(self):
        #print(f"Drone agent {self.number} started at ({self.latitude}, {self.longitude}) with capacity {self.capacity}, autonomy {self.autonomy} and velocity {self.velocity}")

        fsm = self.DroneFSMBehaviour()
        fsm.add_state(name=DELIVERING_ORDERS, state=self.DeliveringOrders())
        fsm.add_state(name=ASK_ORDERS, state=self.AskOrders(), initial=True)
        fsm.add_state(name=AWAIT_ORDERS, state=self.AwaitOrders())
        fsm.add_state(name=ANSWER_PROPOSALS, state=self.AnswerProposals())
        fsm.add_state(name=MOVING_TO_CENTER, state=self.MovingToCenter())
        fsm.add_transition(source=ASK_ORDERS, dest=AWAIT_ORDERS)
        fsm.add_transition(source=AWAIT_ORDERS, dest=ANSWER_PROPOSALS)
        fsm.add_transition(source=AWAIT_ORDERS, dest=ASK_ORDERS)
        fsm.add_transition(source=ANSWER_PROPOSALS, dest=ASK_ORDERS)
        fsm.add_transition(source=ANSWER_PROPOSALS, dest=DELIVERING_ORDERS)
        fsm.add_transition(source=DELIVERING_ORDERS, dest=ASK_ORDERS)
        fsm.add_transition(source=ANSWER_PROPOSALS, dest=MOVING_TO_CENTER)
        fsm.add_transition(source=MOVING_TO_CENTER, dest=DELIVERING_ORDERS)
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

    def get_number(self):
        return self.number

    def get_capacity(self):
        return self.capacity

    def get_autonomy(self):
        return self.autonomy

    def get_velocity(self):
        return self.velocity

    def get_orders(self):
        return self.orders

    def get_latitude(self):
        return self.latitude

    def get_longitude(self):
        return self.longitude

    class DroneFSMBehaviour(FSMBehaviour):
        async def on_start(self):
            #print(f"Drone FSM starting at initial state {self.current_state}")
            pass

        async def on_end(self):
            #print(f"Drone FSM finished at state {self.current_state}")
            await self.agent.stop()

    class AskOrders(State):
        async def run(self):
            #print(f"Drone agent asking orders:")

            # Send message to drones asking for their availability
            for center in self.agent.centers:
                #print(f"Asking orders from center {center}")
                msg = spade.message.Message(to=str(center))
                msg.body = "[AskOrders]-" + \
                    str(self.agent.current_capacity) + \
                    "-" + str(self.agent.full_autonomy)
                await self.send(msg)

            self.set_next_state(AWAIT_ORDERS)

    class AwaitOrders(State):
        async def run(self):
            #print("Waiting for orders from the center")
            proposals = []
            for center in self.agent.centers:
                # Wait for a message for 10 seconds
                msg = await self.receive(timeout=2)
                if msg:
                    # Split message body into parts
                    body_parts = msg.body.split("-")
                    if len(body_parts) == 2 and body_parts[0] == "[OrdersAssigned]":
                        assigned_orders_str = body_parts[1]
                        # Convert string representation of JSON to actual dictionary
                        assigned_orders_dict = json.loads(assigned_orders_str)
                        #print(f"[DRONE{self.agent.jid}]Received orders from center {msg.sender}: {assigned_orders_dict['orders']}")
                        proposals.append(
                            (re.match(r"center(\d+)@localhost", (str(msg.sender))).group(1), assigned_orders_dict))
                    else:
                        #print("Received unrecognized message")
                        pass
                else:
                    #print("Did not receive any instructions after 10 seconds")
                    break

            if proposals:
                self.agent.proposals = proposals
                self.set_next_state(ANSWER_PROPOSALS)
            else:
                self.set_next_state(ASK_ORDERS)

    class AnswerProposals(State):
        async def run(self):
            #print("Answering proposals")
            # Evaluate and select the best proposal
            best_proposal = evaluate_proposals(self.agent.proposals)
            if best_proposal:
                center_id, orders, center_location = best_proposal
                #print(f"Selected proposal from center {center_id}: {orders}")
                # Add orders from the best proposal to self.orders
                self.agent.future_orders.extend(orders)
                self.agent.nextCenter = center_location
                # Send acceptance message to the selected center
                reply = Message(to=("center"+center_id+"@localhost"))
                reply.body = "[Accepted]"
                await self.send(reply)

                # Send rejection messages to other centers
                for other_proposal in self.agent.proposals:
                    if other_proposal[0] != center_id:
                        #print(f"Rejecting proposal from center {other_proposal[0]}")
                        rejection_msg = Message(
                            to=("center"+other_proposal[0]+"@localhost"))
                        rejection_msg.body = "[Rejected]"
                        await self.send(rejection_msg)
            else:
                #print("No proposals received")
                self.agent.proposals = []
                self.set_next_state(ASK_ORDERS)
                return

            self.agent.proposals = []
            # Should be substituted after the next step is implemented
            self.set_next_state(MOVING_TO_CENTER)

    class DeliveringOrders(State):
        async def run(self):
            #print("Delivering ", len(self.agent.orders), " orders")

            # iterate trough a copy of the list. NECESSARY!!
            for order in list(self.agent.orders):
                #print(f"Delivering order {order}")

                # Calculate the distance and angle to the delivery location

                while self.agent.autonomy > 0:
                    # Move the drone towards the center
                    angle = calculate_angle(
                        (self.agent.latitude, self.agent.longitude), (order[1], order[2]))
                    next_lat, next_long = self.agent.next_pos(angle)
                    future_movement = haversine_distance(
                        self.agent.latitude, self.agent.longitude, next_lat, next_long)
                    distance = haversine_distance(
                        self.agent.latitude, self.agent.longitude, order[1], order[2])
                    distance_travelled = 0
                    if future_movement > distance:
                        self.agent.latitude = order[1]
                        self.agent.longitude = order[2]
                        distance_travelled = distance
                        self.agent.autonomy -= distance_travelled
                        self.agent.distanceTravelled += distance_travelled
                        break

                    else:
                        self.agent.latitude = next_lat
                        self.agent.longitude = next_long
                        distance_travelled = future_movement


                    # Decrease the drone's autonomy based on the distance travelled
                    self.agent.autonomy -= distance_travelled
                    self.agent.distanceTravelled += distance_travelled
                    # Wait for a tick
                    await asyncio.sleep(1 / 60)

                if self.agent.autonomy <= 0:
                    with open("output.txt", "a") as f:
                        f.write(f"Drone {self.agent.number} ran out of gas\n")
                    #print("Drone ran out of gas")
                    # await self.agent.stop()

                #print(f"[{self.agent.jid}]Finished delivering order {order}")
                self.agent.orders.remove(order)
            # self.agent.orders = []
            self.set_next_state(ASK_ORDERS)

    class MovingToCenter(State):

        async def run(self):
            #print("Moving to center")

            # Calculate the distance and angle to the center

            while self.agent.autonomy > 0:
                # Move the drone towards the center
                angle = calculate_angle(
                    (self.agent.latitude, self.agent.longitude), (self.agent.nextCenter["latitude"], self.agent.nextCenter["longitude"]))
                next_lat, next_long = self.agent.next_pos(angle)
                future_movement = haversine_distance(
                    self.agent.latitude, self.agent.longitude, next_lat, next_long)
                distance = haversine_distance(
                    self.agent.latitude, self.agent.longitude, self.agent.nextCenter["latitude"], self.agent.nextCenter["longitude"])
                distance_travelled = 0
                if future_movement > distance:
                    self.agent.latitude = self.agent.nextCenter["latitude"]
                    self.agent.longitude = self.agent.nextCenter["longitude"]
                    distance_travelled = distance
                    self.agent.autonomy -= distance_travelled
                    self.agent.distanceTravelled += distance_travelled
                    break
                else:
                    self.agent.latitude = next_lat
                    self.agent.longitude = next_long
                    distance_travelled = future_movement

                # Decrease the drone's autonomy based on the distance travelled
                self.agent.autonomy -= distance_travelled
                self.agent.distanceTravelled += distance_travelled
                # Wait for a tick
                await asyncio.sleep(1 / 60)

            if self.agent.autonomy <= 0:
                with open("output.txt", "a") as f:
                    f.write(f"Drone {self.agent.number} ran out of gas\n")
                #print("Drone ran out of gas ", self.agent.autonomy)
                # await self.agent.stop()

            #print("Arrived at center")
            self.agent.autonomy = self.agent.full_autonomy
            self.agent.orders.extend(self.agent.future_orders)
            if self.agent.orders:
                self.agent.weights.append(sum([order[3] for order in self.agent.orders]) / self.agent.capacity)
            self.agent.future_orders = []
            self.set_next_state(DELIVERING_ORDERS)

    class StopBehaviour(spade.behaviour.CyclicBehaviour):
        async def run(self):
            msg = await self.receive(timeout=10)
            if msg:
                if msg.body == "stop":
                    #print(f"Received stop message. Stopping drone {self.agent.jid} ...")
                    await self.agent.stop()
