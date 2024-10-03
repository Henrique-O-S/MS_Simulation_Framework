import csv
import asyncio
import os
import threading
from flask import Flask, render_template
from flask_socketio import SocketIO
from flask_cors import CORS
from spade.agent import Agent
from agents.center import CenterAgent
from agents.drone import DroneAgent
from agents.world import WorldAgent
from models.order import Order
from aux_funcs import extract_numeric_value


class Application:
    def __init__(self):
        self.app = Flask(__name__)
        # Set CORS allowed origins to "*"
        CORS(self.app, resources={r"/*": {"origins": "*"}})
        self.socketio = SocketIO(self.app)

        @self.app.route('/')
        def index():
            return render_template('map.html')

    def read_center_csv(self, filename):
        centers = []
        with open(filename, "r") as csvfile:
            reader = csv.reader(csvfile, delimiter=";")
            next(reader)  # Skip the header
            params = next(reader)  # Read the parameters
            center_id, latitude, longitude, weight = params
            latitude = float(latitude.replace(",", "."))
            longitude = float(longitude.replace(",", "."))
            weight = float(weight)
            orders = []
            for row in reader:
                order_id, order_latitude, order_longitude, order_weight = row
                orders.append(Order(order_id, order_latitude,
                              order_longitude, order_weight))
            centers.append(CenterAgent(center_id + "@localhost",
                           "1234", center_id, latitude, longitude, weight, orders))
        return centers

    def read_drone_csv(self, filename):
        drones = []
        with open(filename, "r") as csvfile:
            reader = csv.reader(csvfile, delimiter=";")
            next(reader)  # Skip the header
            for row in reader:
                drone_id, capacity, autonomy, velocity, initialPos = row
                drones.append(DroneAgent(drone_id + "@localhost", "1234", extract_numeric_value(
                    capacity), extract_numeric_value(autonomy), extract_numeric_value(velocity), initialPos))
        return drones

    def main(self):
        center_files = ["data/delivery_center1.csv",
                        "data/delivery_center2.csv"]
        drone_file = "data/delivery_drones.csv"
        agents = []
        centers = []
        for filename in center_files:
            if os.path.exists(filename):
                res = self.read_center_csv(filename)
                centers.extend(res)
                agents.extend(res)
            #else:
                #print(f"File {filename} not found.")
        if os.path.exists(drone_file):
            drones = self.read_drone_csv(drone_file)
            for drone in drones:
                drone.centers = map(lambda x: x.jid, centers)
                for center in centers:
                    if(drone.initialPos == center.center_id):
                        drone.latitude = center.latitude
                        drone.longitude = center.longitude
            for agent in agents:
                agent.drones = map(lambda x: x.jid, drones)
            agents.extend(drones)
        #else:
            #print(f"File {filename} not found.")

        # Pass drones jid to centers and vice versa
        for agent in agents:
            if isinstance(agent, DroneAgent):
                agent.centers = [center.jid for center in centers]
        

        self.world_agent = WorldAgent(
            "world@localhost", "1234", centers, drones, [], self.app, self.socketio)
        agents.append(self.world_agent)

        async def run_agents():
            for agent in agents:
                await agent.start(auto_register=True)

        asyncio.run(run_agents())


if __name__ == "__main__":
    app = Application()

    # Start the Flask-SocketIO server in a separate thread
    server_thread = threading.Thread(
        target=app.socketio.run, args=(app.app,), kwargs={'port': 8000})
    server_thread.start()

# Start the agents
app.main()

# Wait for the server thread to finish
server_thread.join()
