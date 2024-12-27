import csv
import asyncio
import os
import threading
import time
from dotenv import load_dotenv, dotenv_values 
from flask import Flask, render_template
from flask_socketio import SocketIO
from flask_cors import CORS
from models.region import Region
from models.car import CarModel
from aux_funcs import extract_numeric_value
from car_seeder import CarSeeder
from agents.simulation import Simulation
from agents.car_class import Car_Class
from agents.region_class import Region_Class


load_dotenv()

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
                region_id, latitude, longitude, avg_pop, driving_perc, avg_m_inc, chargers, traffic = row
                latitude = float(latitude.replace(",", "."))
                longitude = float(longitude.replace(",", "."))
                avg_pop = int(avg_pop)
                driving_perc = float(driving_perc.replace(",", "."))
                avg_m_inc = float(avg_m_inc.replace(",", "."))
                chargers = int(chargers)
                traffic = int(traffic)
                regions.append(Region(region_id, latitude, longitude, int(avg_pop * driving_perc), avg_m_inc, chargers, traffic))

    def read_car_csv(self, filename, cars):
        with open(filename, "r") as csvfile:
            reader = csv.reader(csvfile, delimiter=";")
            next(reader)  # Skip the header
            for row in reader:
                car_id, autonomy, price = row
                autonomy = int(autonomy)
                price = int(price)
                cars.append(CarModel(car_id, autonomy, price))

    def main(self):
        region_file = "data/regions.csv"
        car_file = "data/cars.csv"
        regions = []
        car_models = []

        # Read input data
        if os.path.exists(region_file):
            self.read_region_csv(region_file, regions)
        if os.path.exists(car_file):
            self.read_car_csv(car_file, car_models)


        region_objects = []
        for region in regions:
            region_objects.append(Region_Class(
                region.id, region.latitude, region.longitude, region.chargers, region.traffic))
            
        # Generate cars based on models and regions
        cars_data = CarSeeder(car_models, regions).run()
        car_objects = []
        for region in region_objects:
            for car_model in cars_data[region.id]:
                for _ in range(cars_data[region.id][car_model]):
                    car = Car_Class(car_model.id, car_model.autonomy, int(os.getenv("CAR_VELOCITY")), region, region_objects)
                    car_objects.append(car)

        #THIS IS FOR TESTING
        '''car_objects.append(Car_Class(
            "low_end_ramalde_1", 100, 50, region_objects[0], region_objects))'''

        # Initialize simulation
        simulation = Simulation(car_objects, region_objects, self.app, self.socketio)
        
        print("Starting simulation...")
        simulation.run(steps=int(os.getenv("STEPS_PER_DAY"))*int(os.getenv("NUMBER_OF_DAYS")))  # Set the number of steps as needed

        print("Simulation ended.")



if __name__ == "__main__":
    app = Application()

    # Start the Flask-SocketIO server in a separate thread
    server_thread = threading.Thread(
        target=app.socketio.run, args=(app.app,), kwargs={'port': 8000})
    server_thread.start()

    # Start the simulation
    app.main()

    # Wait for the server thread to finish
    server_thread.join()
