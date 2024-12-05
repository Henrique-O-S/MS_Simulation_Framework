import csv
import asyncio
import os
import threading
from flask import Flask, render_template
from flask_socketio import SocketIO
from flask_cors import CORS
from spade.agent import Agent
from agents.center import CenterAgent
from agents.region import RegionAgent
from agents.drone import DroneAgent
from agents.world import WorldAgent
from agents.car import CarAgent
from models.region import Region
from models.car import CarModel
from aux_funcs import extract_numeric_value
from car_seeder import CarSeeder


class Application:
    def __init__(self):
        self.app = Flask(__name__)
        # Set CORS allowed origins to "*"
        CORS(self.app, resources={r"/*": {"origins": "*"}})
        self.socketio = SocketIO(self.app)

        @self.app.route('/')
        def index():
            return render_template('map.html')

    def read_region_csv(self, filename, regions):
        with open(filename, "r") as csvfile:
            reader = csv.reader(csvfile, delimiter=";")
            next(reader)  # Skip the header
            for row in reader:
                region_id, latitude, longitude, avg_pop, driving_perc, avg_m_inc, chargers = row
                latitude = float(latitude.replace(",", "."))
                longitude = float(longitude.replace(",", "."))
                avg_pop = int(avg_pop)
                driving_perc = float(driving_perc.replace(",", "."))
                avg_m_inc = float(avg_m_inc.replace(",", "."))
                chargers = int(chargers)
                regions.append(Region(region_id, latitude, longitude, int(avg_pop * driving_perc), avg_m_inc, chargers))

    def read_car_csv(self, filename, cars):
        with open(filename, "r") as csvfile:
            reader = csv.reader(csvfile, delimiter=";")
            next(reader)  # Skip the header
            for row in reader:
                car_id, autonomy, price = row
                autonomy = int(autonomy)
                price = int(price)
                cars.append(CarModel(car_id, autonomy, price))

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
        regions = []
        region_file = "data/regions.csv"
        carModels = []
        car_file = "data/cars.csv"
        agents = []
        if os.path.exists(region_file):
            self.read_region_csv(region_file, regions)
        if os.path.exists(car_file):
            self.read_car_csv(car_file, carModels)

        carsData = CarSeeder(carModels, regions).run()
        carAgents = []
        regionAgents = []
        region_jids = {}
        for region in regions:
            jid = f"{region.id}@localhost"
            region_jids[region.id] = jid
            agents.append(RegionAgent(
                jid, "1234", region.latitude, region.longitude, region.chargers))
            regionAgents.append(RegionAgent(
                jid, "1234", region.latitude, region.longitude, region.chargers))
        #CHOOSE ONE OF THE COMMENTS BELOW

            #THIS IS NORMAL SIMULATION
        for region in regions:
            count = 1
            for carModel in carsData[region.id]:
                for _ in range(carsData[region.id][carModel]):
                    jid = f"{carModel.id}_{region.id}_{count}@localhost"
                    agents.append(CarAgent(
                        jid, "1234", carModel.autonomy, 50, region, regions, region_jids))
                    carAgents.append(CarAgent(
                        jid, "1234", carModel.autonomy, 50, region, regions, region_jids))
                    count += 1

            #THIS IS FOR TESTING
        agents.append(CarAgent(
            "low_end_ramalde_1@localhost", "1234", 100, 50, regions[0], regions, region_jids))
        
        carAgents = [agent for agent in agents if isinstance(agent, CarAgent)]
        regionAgents = [agent for agent in agents if isinstance(agent, RegionAgent)]
        

        self.world_agent = WorldAgent(
            "world@localhost", "1234", regionAgents, carAgents, self.app, self.socketio)
        agents.append(self.world_agent)
        print("starting")
        async def run_agents():
            for agent in agents:
                await agent.start(auto_register=True)
        print("done")
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
