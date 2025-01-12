# -------------------------------------------------------------------------------------------------------------

import numpy as np
import random
import os

from dotenv import load_dotenv

# -------------------------------------------------------------------------------------------------------------

os.environ.clear()
load_dotenv()

# -------------------------------------------------------------------------------------------------------------

class CarSeeder:
    """
    CarSeeder is responsible for estimating car purchases across different regions based on income and other factors.
    
    Attributes:
        cars (list): A list of car objects available for purchase.
        regions (list): A list of region objects where the calculations will be executed.
        salaryFluctuation (float): The fluctuation in salary, used to generate income variations.
        percWillingToSpend (float): The percentage of income that people are willing to spend on a car.
        probabilityOfBuying (float): The probability that a person will buy a car if they can afford it.
    """
    def __init__(self, cars, regions, salary_fluctuation = float(os.getenv("SALARY_FLUCTUATION")), percentage_willing_to_spend = float(os.getenv("PERCENTAGE_WILLING_TO_SPEND")), probability_of_buying=float(os.getenv("PROBABILITY_OF_BUYING"))):
        self.cars = cars
        self.regions = regions
        self.salaryFluctuation = salary_fluctuation
        self.percWillingToSpend = percentage_willing_to_spend
        self.probabilityOfBuying = probability_of_buying
        
    # ---------------------------------------------------------------------------------------------------------

    def generate_income(self, avg_income):
        """
        Generates a random income based on a log-normal distribution.

        Args:
            avg_income (float): The average income to base the distribution on.

        Returns:
            float: A randomly generated income value.
        """
        sigma = np.sqrt(np.log(1 + (self.salaryFluctuation ** 2)))
        mu = np.log(avg_income) - (sigma**2 / 2)
        return np.random.lognormal(mu, sigma)
    
    # ---------------------------------------------------------------------------------------------------------

    def affordable_cars(self, income):
        """
        Determine which cars are affordable based on the given income.

        Args:
            income (float): The income of the individual.

        Returns:
            list: A list of cars that are affordable based on the income and the percentage willing to spend.
        """
        affordable = []
        for car in self.cars:
            if car.price <= income * self.percWillingToSpend:
                affordable.append(car)
        return affordable
    
    # ---------------------------------------------------------------------------------------------------------

    def simulate_region(self, region):
        """
        Simulates car purchases in a given region based on average income and probability of buying.

        Args:
            region (Region): The region object containing average income and average number of drivers.

        Returns:
            dict: A dictionary with car models as keys and the number of purchases as values.
        """
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
        """
        Executes the calculations for all regions and prints the results.

        Returns:
            dict: A dictionary where the keys are region IDs and the values are the results of the calculations for each region.
        """
        all_results = {}
        for region in self.regions:
            region_result = self.simulate_region(region)
            all_results[region.id] = region_result
            print('\n' + region.id)
            for car in region_result:
                print(f"{car.id}: {region_result[car]}")
        return all_results

# -------------------------------------------------------------------------------------------------------------