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

os.environ.clear()
load_dotenv()

# -------------------------------------------------------------------------------------------------------------
 
class Application:
    '''
    The Application class initializes and runs a Flask web application with SocketIO support.
    
    Attributes:
        app (Flask): The Flask web application instance.
        socketio (SocketIO): The SocketIO instance for real-time communication.
    '''
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
        """
        Deletes all logs in the 'logs/outputs/' directory.
        """
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
        """
        Reads region data from a CSV file and appends it to the provided regions list.

        Args:
            filename (str): The path to the CSV file containing the region data.
            regions (list): A list to which the parsed Region objects will be appended.
        """
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
        """
        Reads car model data from a CSV file and appends it to the provided list of car models.

        Args:
            filename (str): The path to the CSV file containing car model data.
            cars (list): A list to which the car models will be appended. Each car model is an instance of the CarModel class.
        """
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
        """
        Generates a list of Car objects based on the provided car models and regions.

        Args:
            car_models (list): A list of car model objects to be used for generating cars.
            regions (list): A list of region objects where the cars will be generated.

        Returns:
            list: A list of Car objects generated for the specified regions and car models.
        """
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
        """
        Main function to initialize and run the simulation.
        """
        region_file = "data/regions.csv"
        improvement_level = int(os.getenv("REGION_IMPROVEMENT"))
        if (improvement_level != 0):
            region_file = "data/regions_improved_" + str(improvement_level) + ".csv"
        regions = []
        if os.path.exists(region_file):
            self.read_region_data(region_file, regions)
        
        car_file = "data/cars.csv"
        car_models = []
        if os.path.exists(car_file):
            self.read_car_model_data(car_file, car_models)
            
        cars = self.generate_cars(car_models, regions)
        print(f"\n{len(cars)} cars generated.")

        simulation = Simulation(cars, regions, self.app, self.socketio)
        print("\nStarting simulation...")
        simulation.run(steps=int(os.getenv("STEPS_PER_DAY"))*int(os.getenv("NUMBER_OF_DAYS"))) 
        
# -------------------------------------------------------------------------------------------------------------

if __name__ == "__main__":
    app = Application()
    server_thread = threading.Thread(
        target=app.socketio.run, args=(app.app,), kwargs={'port': 8000})
    server_thread.start()
    app.main()
    server_thread.join()
    
# -------------------------------------------------------------------------------------------------------------