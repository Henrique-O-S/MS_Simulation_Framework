import spade
from spade.agent import Agent
from spade.behaviour import OneShotBehaviour, PeriodicBehaviour, CyclicBehaviour, FSMBehaviour, State
from spade.message import Message
from spade.template import Template
from aux_funcs import assign_orders_to_drone
import datetime
import json


class CenterAgent(Agent):
    def __init__(self, jid, password, center_id, latitude, longitude, weight, orders, drones=[]):
        super().__init__(jid, password)
        self.center_id = center_id
        self.latitude = latitude
        self.longitude = longitude
        self.weight = weight
        self.orders = orders
        self.drones = drones
        self.dronesAvailable = []

    async def setup(self):
        #print(f"Center agent {self.center_id} started at ({self.latitude}, {self.longitude}) with weight {self.weight}")

        b2 = self.AwaitDrones()
        self.add_behaviour(b2)

        stop_behaviour = self.StopBehaviour()
        template = spade.template.Template()
        template.body = "stop"
        self.add_behaviour(stop_behaviour, template)

    def get_center_id(self):
        return self.center_id

    def get_latitude(self):
        return self.latitude

    def get_longitude(self):
        return self.longitude

    def get_weight(self):
        return self.weight

    def get_orders(self):
        return self.orders

    def get_drones(self):
        return self.drones

    class AwaitDrones(CyclicBehaviour):
        async def run(self):
            #print("Center agent awaiting drones availability")
            assigned_orders = []
            # wait for a message for 10 seconds
            msg = await self.receive(timeout=2)
            if msg:
                # Split message body into parts
                body_parts = msg.body.split("-")
                if len(body_parts) == 3:
                    tag, capacity_info, autonomy_info = body_parts
                    if tag == "[AskOrders]":
                        current_capacity = int(float(capacity_info))
                        current_autonomy = float(autonomy_info)
                        #print(f"Received drone's capacity. Current capacity: {current_capacity}")

                        # Assign orders to drones
                        assigned_orders = assign_orders_to_drone(
                            self.agent.orders, current_capacity, current_autonomy, (self.agent.latitude, self.agent.longitude))

                        # Assuming assigned_orders is a list of Order objects
                        assigned_orders_json = [
                            order.__dict__ for order in assigned_orders]

                        # Convert assigned_orders_json to a JSON string
                        assigned_orders_str = json.dumps({
                            "orders": assigned_orders_json,
                            "center": {
                                "latitude": self.agent.latitude,
                                "longitude": self.agent.longitude
                            }
                        })

                        # Reply with the assigned orders
                        reply = Message(to=str(msg.sender))
                        reply.body = f"[OrdersAssigned]-{assigned_orders_str}"
                        await self.send(reply)

                        #print("Center agent awaiting drones response")
                        # wait for a message for 10 seconds
                        response = await self.receive(timeout=2)
                        if response:
                            if response.body == "[Accepted]":
                                #print("Proposal accepted by drone. Processing orders.")
                                # Process orders and remove them from stock
                                for assigned_order in assigned_orders:
                                    #print a message if the order was not found in stock
                                    if assigned_order.id not in [order.id for order in self.agent.orders]:
                                        pass
                                        #print(f"Order {assigned_order.id} not found in stock.")
                                    else:
                                        # Remove the order with the specified ID from self.agent.orders
                                        self.agent.orders = [
                                            order for order in self.agent.orders if order.id != assigned_order.id]
                            elif response.body == "[Rejected]":
                                #print("Proposal rejected by drone.")
                                pass
                        else:
                            #print("Did not receive a response to proposal after 10 seconds")
                            pass

                    else:
                        #print("Received unrecognized tag")
                        pass
                else:
                    #print("Invalid message format")
                    pass
            else:
                #print("Did not receive any message after 10 seconds")
                pass

    class StopBehaviour(spade.behaviour.CyclicBehaviour):
        async def run(self):
            msg = await self.receive(timeout=10)
            if msg:
                if msg.body == "stop":
                    #print(f"Received stop message. Stopping center {self.agent.jid} ...")
                    await self.agent.stop()


if __name__ == "__main__":
    print("This module defines the CenterAgent class. It should be imported in other scripts.")
