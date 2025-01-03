# -------------------------------------------------------------------------------------------------------------

import numpy as np
import random
import os

from dotenv import load_dotenv

# -------------------------------------------------------------------------------------------------------------

load_dotenv()

# -------------------------------------------------------------------------------------------------------------

class CarSeeder:
    def __init__(self, cars, regions, salary_fluctuation = float(os.getenv("SALARY_FLUCTUATION")), percentage_willing_to_spend = float(os.getenv("PERCENTAGE_WILLING_TO_SPEND")), probability_of_buying=float(os.getenv("PROBABILITY_OF_BUYING"))):
        self.cars = cars
        self.regions = regions
        self.salaryFluctuation = salary_fluctuation
        self.percWillingToSpend = percentage_willing_to_spend
        self.probabilityOfBuying = probability_of_buying
        
    # ---------------------------------------------------------------------------------------------------------

    def generate_income(self, avg_income):
        sigma = np.sqrt(np.log(1 + (self.salaryFluctuation ** 2)))
        mu = np.log(avg_income) - (sigma**2 / 2)
        return np.random.lognormal(mu, sigma)
    
    # ---------------------------------------------------------------------------------------------------------

    def affordable_cars(self, income):
        affordable = []
        for car in self.cars:
            if car.price <= income * self.percWillingToSpend:
                affordable.append(car)
        return affordable
    
    # ---------------------------------------------------------------------------------------------------------

    def simulate_region(self, region):
        avg_income = region.avg_income
        results = {car: 0 for car in self.cars}
        for _ in range(region.avg_drivers):
            income = self.generate_income(avg_income)
            affordable = self.affordable_cars(income)
            if affordable and random.random() < self.probabilityOfBuying:
                chosen_car = random.choice(affordable)
                results[chosen_car] += 1
        return results
    
    # ---------------------------------------------------------------------------------------------------------

    def run(self):
        all_results = {}
        for region in self.regions:
            region_result = self.simulate_region(region)
            all_results[region.id] = region_result
            print('\n' + region.id)
            for car in region_result:
                print(f"{car.id}: {region_result[car]}")
        return all_results

# -------------------------------------------------------------------------------------------------------------