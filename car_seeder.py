import numpy as np
import random
import matplotlib.pyplot as plt


class CarSeeder:
    def __init__(self, cars, regions, salary_fluctuation = 0.2, percentage_willing_to_spend = 0.2, probability_of_buying=0.4):
        self.cars = cars
        self.regions = regions
        self.salaryFluctuation = salary_fluctuation
        self.percWillingToSpend = percentage_willing_to_spend
        self.probabilityOfBuying = probability_of_buying

    def generate_income(self, avg_income):
        return np.random.normal(avg_income, avg_income * self.salaryFluctuation) # normal distribution with some margins

    def affordable_cars(self, income):
        affordable = []
        for car in self.cars:
            if car.price <= income * self.percWillingToSpend:
                affordable.append(car)
        return affordable

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

    def run(self):
        all_results = {}
        for region in self.regions:
            region_result = self.simulate_region(region)
            all_results[region.id] = region_result
            print(region.id)
            for car in region_result:
                print(f"{car.id}: {region_result[car]}")
        #self.plot_car_distribution(all_results)
        return all_results

    def plot_car_distribution(self, all_results):
        for region_id, region_result in all_results.items():
            car_ids = list(region_result.keys())
            totals = list(region_result.values())

            plt.figure(figsize=(10, 6))
            plt.bar(car_ids, totals, color=['blue', 'green', 'red', 'cyan', 'magenta', 'yellow'])
            plt.xlabel('Car Model')
            plt.ylabel('Number of Cars Sold')
            plt.title(f'Total Electric Cars Sold in {region_id}')
            plt.xticks(rotation=45)
            plt.tight_layout()
            plt.show()
