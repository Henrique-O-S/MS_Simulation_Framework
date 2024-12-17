import asyncio
import time
import os
import random
from flask import Flask
from flask_socketio import SocketIO


class SimulationVisualization:
    def __init__(self, app, socketio):
        self.app = app
        self.socketio = socketio

    def update_visualization(self, cars, regions):
        regions_data = [
            {'name': region.id, 'lat': region.latitude, 'lng': region.longitude, 'cars_charged': region.cars_charged, 'stress_metric': region.stress_metric}
            for region in regions
        ]
        cars_data = [
            {'name': car.id, 'lat': car.latitude, 'lng': car.longitude}
            for car in cars
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
        self.visualization = SimulationVisualization(app, socketio)
        self.running = True

    def run_step(self):
        for car in self.cars:
            car.run()

        # Update visualization
        self.visualization.update_visualization(self.cars, self.regions)

        # Check end conditions (e.g., all cars idle, no regions active, etc.)
        if self.check_simulation_end():
            self.visualization.signal_end()
            self.running = False

    def check_simulation_end(self):
        # Placeholder for simulation end conditions
        return False

    def run(self, steps):
        for step in range(steps):
            if not self.running:
                break
            print(f"Step {step}")
            self.run_step()
            if step % 5 == 0:
                for region in self.regions:
                    region.update()


            time.sleep(1 / 60)  # Simulate 60Hz updates
