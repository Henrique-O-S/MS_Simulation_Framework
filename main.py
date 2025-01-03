# -------------------------------------------------------------------------------------------------------------

import csv
import os
import threading

from dotenv import load_dotenv
from flask import Flask, render_template
from flask_socketio import SocketIO
from flask_cors import CORS

from simulation import Simulation
from entities.region import Region
from entities.car_model import CarModel
from entities.car_seeder import CarSeeder
from entities.car import Car

# -------------------------------------------------------------------------------------------------------------

load_dotenv()

# -------------------------------------------------------------------------------------------------------------

class Application:
    def __init__(self):
        self.delete_logs()
        self.app = Flask(__name__)
        CORS(self.app, resources={r"/*": {"origins": "*"}})
        self.socketio = SocketIO(self.app)
        @self.app.route('/')
        def index():
            return render_template('map.html')
        
    # ---------------------------------------------------------------------------------------------------------
        
    def delete_logs(self): 
        folder = "logs/outputs/"
        for filename in os.listdir(folder):
            if filename != ".gitignore":
                file_path = os.path.join(folder, filename)
                try:
                    os.remove(file_path)
                except Exception as e:
                    print(f"Error deleting file {file_path}: {e}")
                    
    # ---------------------------------------------------------------------------------------------------------

    def read_region_data(self, filename, regions):
        with open(filename, "r") as csvfile:
            reader = csv.reader(csvfile, delimiter=";")
            next(reader) 
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
                
    # ---------------------------------------------------------------------------------------------------------

    def read_car_model_data(self, filename, cars):
        with open(filename, "r") as csvfile:
            reader = csv.reader(csvfile, delimiter=";")
            next(reader)
            for row in reader:
                car_id, autonomy, price = row
                autonomy = int(autonomy)
                price = int(price)
                cars.append(CarModel(car_id, autonomy, price))
                
    # ---------------------------------------------------------------------------------------------------------
    
    def generate_cars(self, car_models, regions):
        cars_data = CarSeeder(car_models, regions).run()
        cars = []
        for region in regions:
            for car_model in cars_data[region.id]:
                for i in range(cars_data[region.id][car_model]):
                    id = region.id + '_' + car_model.id + '_' + str(i)
                    car = Car(id, car_model.autonomy, int(os.getenv("CAR_VELOCITY")), region, regions)
                    cars.append(car)
            region.total_cars = sum(cars_data[region.id].values())
        return cars
    
    # ---------------------------------------------------------------------------------------------------------

    def main(self):  
        region_file = "data/regions.csv"
        regions = []
        if os.path.exists(region_file):
            self.read_region_data(region_file, regions)
        
        car_file = "data/cars.csv"
        car_models = []
        if os.path.exists(car_file):
            self.read_car_model_data(car_file, car_models)
            
        cars = self.generate_cars(car_models, regions)

        simulation = Simulation(cars, regions, self.app, self.socketio)
        print("\nStarting simulation...")
        simulation.run(steps=int(os.getenv("STEPS_PER_DAY"))*int(os.getenv("NUMBER_OF_DAYS"))) 
        print("Simulation ended.")
        
# -------------------------------------------------------------------------------------------------------------

if __name__ == "__main__":
    app = Application()
    server_thread = threading.Thread(
        target=app.socketio.run, args=(app.app,), kwargs={'port': 8000})
    server_thread.start()
    app.main()
    server_thread.join()
    
# -------------------------------------------------------------------------------------------------------------