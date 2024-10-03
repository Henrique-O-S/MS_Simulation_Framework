import asyncio
from spade.agent import Agent
from spade.behaviour import CyclicBehaviour
from spade.message import Message
import time
import requests
import os

class UpdatePointsBehaviour(CyclicBehaviour):
    def __init__(self, agent):
        super().__init__()
        self.agent = agent
        self.interval = 1 / 60

    async def run(self):
        self.agent.update_visualization()
        await asyncio.sleep(self.interval)


class WorldAgent(Agent):
    def __init__(self, jid, password, centers, drones, restrictions, app, socketio):
        super().__init__(jid, password)
        self.centers = centers
        self.drones = drones
        self.restrictions = restrictions
        self.app = app
        self.socketio = socketio

    async def setup(self):
        await super().setup()
        self.add_behaviour(UpdatePointsBehaviour(self))

    def update_visualization(self):
        centers_data = [{'name': center.name, 'lat': center.latitude,
                        'lng': center.longitude, 'num_orders': len(center.orders)} for center in self.centers]
        orders_data = [{'name': order.id, 'lat': order.latitude, 'lng': order.longitude}
                       for center in self.centers for order in center.orders]
        drones_data = [{'name': "drone_" + str(drone.number), 'lat': drone.latitude, 'lng': drone.longitude,
                        'orders': [order[0] for order in drone.orders]} for drone in self.drones]
        self.socketio.emit(
            'map_updated', {'center_data': centers_data, 'order_data': orders_data, 'drone_data': drones_data})
        # Check if all orders are delivered
        if all(len(center.orders) == 0 for center in self.centers) and all(len(drone.orders) == 0 for drone in self.drones):
            distance = 0
            times = {}
            occupation = {}
            for drone in self.drones:
                distance += drone.distanceTravelled
                times["DRONE_" + str(drone.number)] = drone.distanceTravelled / ((drone.velocity * 3600 * 60) / 200)
                # print average drone weight occupation
                occupation["DRONE_" + str(drone.number)] = (sum(drone.weights) / len(drone.weights)) * 100

            print(f"Total distance: {distance} km.")
            #print maximum, minimum and average time taken in total
            max_time = max(times.values())
            min_time = min(times.values())
            avg_time = sum(times.values()) / len(times)
            print(f"Maximum time taken: {max_time} hours.")
            print(f"Minimum time taken: {min_time} hours.")
            print(f"Average time taken: {avg_time} hours.")
            print("Drone times in hours: ", times)
            print("Drone occupation ratios in %: ", occupation)
            self.signal_end()
            self.stop()
    def signal_end(self):
        self.socketio.emit('simulation_end', {})
        print("Simulation ended.")
        os._exit(0)



