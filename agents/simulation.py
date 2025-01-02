import asyncio
import time
import os
import random
from flask import Flask
from flask_socketio import SocketIO


class SimulationVisualization:
    def __init__(self, app, socketio, regions, cars):
        self.app = app
        self.socketio = socketio
        self.regions = regions
        self.select_cars_for_display(cars)
        
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

    def update_visualization(self):
        regions_data = [
            {'name': region.id, 'lat': region.latitude, 'lng': region.longitude, 'cars_charged': region.cars_charged, 'stress_metric': region.stress_metric}
            for region in self.regions
        ]
        cars_data = [
            {'name': car.id, 'lat': car.latitude, 'lng': car.longitude}
            for car in self.displayed_cars
        ]
        self.socketio.emit('map_updated', {'region_data': regions_data, 'car_data': cars_data})

    def signal_end(self):
        self.socketio.emit('simulation_end', {})
        print("Simulation ended.")
        os._exit(0)


class Simulation:
    def __init__(self, cars, regions, app, socketio):
        self.cars = cars
        self.regions = regions
        self.visualization = SimulationVisualization(app, socketio, regions, cars)
        self.running = True
        self.rush_hour = False

    def run_step(self, step):
        for car in self.cars:
            car.run(self.rush_hour)
            
        for region in self.regions:
            region.run(step)

        # Update visualization
        self.visualization.update_visualization()

        # Check end conditions (e.g., all cars idle, no regions active, etc.)
        if self.check_simulation_end():
            self.visualization.signal_end()
            self.running = False

    def check_simulation_end(self):
        # Placeholder for simulation end conditions
        return False

    def run(self, steps):
        for step in range(steps):
            print(f"Step {step}")
            if not self.running:
                break
            if (step % int(os.getenv("STEPS_PER_DAY")) >= int(os.getenv("STEPS_PER_DAY")) * 7.5 / 24 and step % int(os.getenv("STEPS_PER_DAY")) <= int(os.getenv("STEPS_PER_DAY")) * 9 / 24) or (step % int(os.getenv("STEPS_PER_DAY")) >= int(os.getenv("STEPS_PER_DAY")) * 17 / 24 and step % int(os.getenv("STEPS_PER_DAY")) <= int(os.getenv("STEPS_PER_DAY")) * 19 / 24):
                self.rush_hour = True
            else:
                self.rush_hour = False
            self.run_step(step)

            time.sleep(1 / 60)  # Simulate 60Hz updates
            
        for region in self.regions:
            region.save_history()