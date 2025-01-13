# -------------------------------------------------------------------------------------------------------------

import time
import os
import random

from utils import stepsToTime, isBetweenHours

# -------------------------------------------------------------------------------------------------------------

class Simulation:
    '''
    Simulation class to manage and run a traffic simulation.
    
    Attributes:
        cars (list): List of car objects participating in the simulation.
        regions (list): List of region objects in the simulation.
        visualization (SimulationVisualization): Object to handle the visualization of the simulation.
        running (bool): Flag to indicate if the simulation is running.
        time_of_day (str): Current time of day in the simulation.
        steps_per_day (int): Number of steps representing a full day in the simulation.
    '''
    def __init__(self, cars, regions, app, socketio):
        self.cars = cars
        self.regions = regions
        self.visualization = SimulationVisualization(app, socketio, regions, cars)
        self.running = True
        self.time_of_day = "default"
        self.steps_per_day = int(os.getenv("STEPS_PER_DAY"))
        
    # ---------------------------------------------------------------------------------------------------------

    def run_step(self, step):
        """
        Executes a single simulation step.

        Args:
            step (int): The current step number of the simulation.
        """
        for car in self.cars:
            car.run(self.time_of_day)
        for region in self.regions:
            region.run()
        self.visualization.update_visualization(step, self.time_of_day)
    
    # ---------------------------------------------------------------------------------------------------------
    
    def checkTimeOfDay(self, step):
        """
        Determines the time of day based on the current simulation step and updates the `time_of_day` attribute accordingly.

        Args:
            step (int): The current simulation step.

        Time ranges and their corresponding labels:
            - (7.5, 9): "rush_hour"
            - (17, 19): "rush_hour"
            - (12, 14): "lunch_time"
            - (21, 23.99): "night_time"
            - (0, 6): "dawn_time"
        """
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
        self.time_of_day = "default"
            
    # ---------------------------------------------------------------------------------------------------------

    def run(self, steps):
        """
        Runs the simulation for a given number of steps.

        Args:
            steps (int): The number of steps to run the simulation.
        """
        try:
            for step in range(steps):
                if not self.running:
                    break
                self.checkTimeOfDay(step)
                self.run_step(step)
                time.sleep(1 / 60)
            print("\nSimulation completed.")
        except KeyboardInterrupt:
            print("\nSimulation interrupted.")
        finally:
            for region in self.regions:
                region.save_history()
            self.visualization.signal_end()
            
# -------------------------------------------------------------------------------------------------------------

class SimulationVisualization:
    """
    A class to handle the visualization of a simulation.

    Attributes:
        app (Flask): The Flask application instance.
        socketio (SocketIO): The SocketIO instance for real-time communication.
        regions (list): A list of region objects involved in the simulation.
        displayed_cars (list): A list of car objects selected for display.
        steps_per_day (int): Number of simulation steps per day.
    """
    def __init__(self, app, socketio, regions, cars):
        self.app = app
        self.socketio = socketio
        self.regions = regions
        self.select_cars_for_display(cars)
        self.steps_per_day = int(os.getenv("STEPS_PER_DAY"))
        print(f"Visualization running at http://localhost:8000")
        
    # ---------------------------------------------------------------------------------------------------------
        
    def select_cars_for_display(self, cars):
        """
        Selects cars for display based on their region prefix and marks them as displayed.

        Args:
            cars (list): A list of car objects to be filtered and selected for display.

        Returns:
            None
        """
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
        """
        Updates the visualization by emitting the current state of regions and cars to the client.

        Args:
            step (int): The current simulation step.
            time_of_day (str): The current time of day in the simulation.
        """
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
        """
        Emit a 'simulation_end' signal and terminate the program.
        """
        self.socketio.emit('simulation_end', {})
        os._exit(0)
            
# -------------------------------------------------------------------------------------------------------------