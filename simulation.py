# -------------------------------------------------------------------------------------------------------------

import time
import os
import random

from utils import stepsToTime, isBetweenHours

# -------------------------------------------------------------------------------------------------------------

class Simulation:
    def __init__(self, cars, regions, app, socketio):
        self.cars = cars
        self.regions = regions
        self.visualization = SimulationVisualization(app, socketio, regions, cars)
        self.running = True
        self.time_of_day = "default"
        self.steps_per_day = int(os.getenv("STEPS_PER_DAY"))
        
    # ---------------------------------------------------------------------------------------------------------

    def run_step(self, step):
        for car in self.cars:
            car.run(self.time_of_day)
        for region in self.regions:
            region.run()
        self.visualization.update_visualization(step, self.time_of_day)
        if self.check_simulation_end():
            self.visualization.signal_end()
            self.running = False
            
    # ---------------------------------------------------------------------------------------------------------

    def check_simulation_end(self):
        return False
    
    # ---------------------------------------------------------------------------------------------------------
    
    def checkTimeOfDay(self, step):
        time_ranges = [
            ((7.5, 9), "rush_hour"),
            ((17, 19), "rush_hour"),
            ((12, 14), "lunch_time"),
            ((21, 23.99), "night_time"),
            ((0, 6), "dawn_time"),
        ]

        for (start, end), label in time_ranges:
            if isBetweenHours(start, end, step, self.steps_per_day):
                self.time_of_day = label
                return
        
        # Default case
        self.time_of_day = "default"
            
    # ---------------------------------------------------------------------------------------------------------

    def run(self, steps):
        for step in range(steps):
            if not self.running:
                break
            self.checkTimeOfDay(step)
            self.run_step(step)
            time.sleep(1 / 60)
        for region in self.regions:
            region.save_history()
            
# -------------------------------------------------------------------------------------------------------------

class SimulationVisualization:
    def __init__(self, app, socketio, regions, cars):
        self.app = app
        self.socketio = socketio
        self.regions = regions
        self.select_cars_for_display(cars)
        self.steps_per_day = int(os.getenv("STEPS_PER_DAY"))
        
    # ---------------------------------------------------------------------------------------------------------
        
    def select_cars_for_display(self, cars):
        def get_random_cars(cars, prefix, count=2):
            filtered_cars = [car for car in cars if car.id.startswith(prefix)]
            return random.sample(filtered_cars, min(len(filtered_cars), count))
        region_names = [region.id for region in self.regions]
        self.displayed_cars = []
        for name in region_names:
            selected_cars = get_random_cars(cars, name)
            for car in selected_cars:
                car.displayed = True
            self.displayed_cars.extend(selected_cars)
            
    # ---------------------------------------------------------------------------------------------------------

    def update_visualization(self, step, time_of_day):
        regions_data = [
            {
                'name': region.id,
                'lat': region.latitude,
                'lng': region.longitude,
                'cars_present': region.cars_present,
                'home_charging': region.cars_home_charging,
                'available_chargers': region.available_chargers,
                'queued_cars': region.queue.qsize(),
                'cars_charged': region.cars_charged,
                'autonomy': round(region.average_autonomy),
                'home_time': round(region.average_home_time),
                'charger_utilization': round(region.charger_utilization),
                'queue_size': round(region.average_queue_size),
                'stress_metric': round(region.stress_metric, 1),
                'wait_time': round(region.average_wait_time),
                'charging_time': round(region.average_charging_time)
            }
            for region in self.regions
        ]
        cars_data = [
            {
                'name': car.id,
                'lat': car.latitude,
                'lng': car.longitude
            }
            for car in self.displayed_cars
        ]
        self.socketio.emit(
            'map_updated',
            {
                'step': step,
                'region_data': regions_data,
                'car_data': cars_data,
                'time': stepsToTime(step, self.steps_per_day),
                'rush_hour': time_of_day
            }
        )

    # ---------------------------------------------------------------------------------------------------------

    def signal_end(self):
        self.socketio.emit('simulation_end', {})
        print("Simulation ended.")
        os._exit(0)
            
# -------------------------------------------------------------------------------------------------------------