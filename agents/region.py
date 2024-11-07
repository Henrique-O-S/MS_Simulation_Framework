import spade
from spade.behaviour import CyclicBehaviour
from spade.message import Message
from models.region import Region
import aioxmpp
import queue

class RegionAgent(spade.agent.Agent):
    def __init__(self, jid, password, latitude, longitude, chargers):
        super().__init__(jid, password)
        self.latitude = latitude
        self.longitude = longitude
        self.chargers = chargers
        self.available_chargers = self.chargers
        self.cars_charged = 0
        self.queue = queue.Queue()
        self.region_name = aioxmpp.JID.fromstr(jid).localpart

    async def setup(self):
        print(f"Region agent {self.jid} started.")

        # Add behavior to handle incoming requests
        b = self.ManageCars()
        template = spade.template.Template()
        self.add_behaviour(b, template)
    
    def stop_charging(self):
        self.available_chargers += 1
        self.cars_charged += 1
    
    def start_charging(self):
        self.available_chargers -= 1

    class ManageCars(CyclicBehaviour):
        async def run(self):
            #print("a")
            msg = await self.receive(timeout=2)
            #print("b")
            if msg:
                if msg.body == "[JoinQueue]":
                    print(f"Received join queue request from {msg.sender}")
                    if self.agent.available_chargers > 0:
                        self.agent.start_charging()
                        response = Message(to=str(msg.sender))
                        response.body = "[ChargingStarted]"
                        await self.send(response)
                        print(f"Assigned charging slot to {msg.sender}")
                    else:
                        # Add car to the queue
                        self.agent.queue.put(msg.sender)
                        print(f"Added {msg.sender} to the charging queue")
                elif msg.body == "[StopCharging]":
                    self.agent.stop_charging()
                    #print(f"Car finished charging at region {self.agent.jid}. Chargers available: {self.agent.available_chargers}")
                    
                    # Check if any cars are in the queue
                    if not self.agent.queue.empty():
                        next_car = self.agent.queue.get()
                        print(f"Notifying {next_car} to start charging.")
                        self.agent.start_charging()
                        response = Message(to=str(next_car))
                        response.body = "[ChargingStarted]"
                        await self.send(response)
                elif msg.body == "[AskAvailableChargers]":
                    response = Message(to=str(msg.sender))
                    response.body = f"{self.agent.available_chargers}-{self.agent.queue.qsize()}"
                    await self.send(response)
            else:
                # print("Did not receive any message after 10 seconds")
                pass


