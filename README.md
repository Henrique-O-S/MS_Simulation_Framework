# MS

* Diogo Silva - up202004288@up.pt
* Henrique Silva - up202007242@up.pt
* Tiago Branquinho - up202005567@up.pt

## How to Build and Run

In order to run the code, you will need to have the following dependencies installed:
- [Python 3.10](https://www.python.org/downloads/) or above and `pip` package manager.
- [Make](https://www.gnu.org/software/make/).

The setup is equally done for both Windows and Linux based OS.

### 1. Clone the repository

Start by cloning the repository to your local machine using the following command:

```bash
$ git clone https://github.com/DiogoSilva11/MS.git

$ cd MS
```

### 2. Install the dependencies & Python virtual environment

Install all the necessary dependencies and the Python virtual environment by running the following command:

```bash
$ make install
```

### 3. Available commands

Calling the command `make help` will display the available ways to run the code.
There are different simulation scenarios that can be executed:
* `make run SCENARIO=baseline` - The baseline scenario represents the current Porto infrastructure and dynamics.
* `make run SCENARIO=future` - The future scenario represents an increased EV demand around 5 years into the future but maintaining the current infrastructure to detect bottlenecks.
* `make run SCENARIO=inner` - The inner scenario represents an increase of the number of chargers mostly in inner regions of the city, testing it within the future context.
* `make run SCENARIO=outer` - The outer scenario represents an increase of the number of chargers mostly in outer regions of the city, testing it within the future context.
* `make run SCENARIO=balanced` - The outer scenario represents a balanced increase of the number of chargers throughout the city's regions, testing it within the future context.

### 4. Visualization

The simulation execution is displayed in a visual interface in runtime. 

### 5. Cleanup

To clean up the project and remove the generated files, you can run the following command:

```bash
$ make clean
```

## Project Overview:
This project aims to analyze how **recharging stations** for electric vehicles (EVs) should be optimally distributed across a city network to meet the growing demand. The primary focus is on determining the **number** and **capacity** of recharging stations in different regions, as well as **minimizing waiting times** for EV users.

### Environment:
- **City Network Representation**:  
  The environment will be modeled as a graph where each **node** represents a region of the city (e.g., Campanhã in Porto), and each **edge** corresponds to the **distance** between the centroids of two regions. The distance will reflect the actual road network where possible (in case of a real city).
  
- **Region Characteristics**:  
  Each region will have:
  - A **defined number of recharging stations**, based on existing infrastructure or assumptions if fictional.
  - Each recharging station will have a **capacity** (i.e., the number of vehicles that can charge simultaneously).

- **Clock and Time Simulation**:  
  The system will have an accelerated **clock** to simulate the passage of time (e.g., day and night cycles) to track the **traffic flow** and recharging activity. Rush hours will be identified, with higher vehicle activity during these times.

### Vehicle Behavior:
- **Travel Patterns**:  
  - EVs will travel between regions, with **battery depletion** proportional to the distance traveled.  
  - Within a region, vehicles will also lose battery, but at a smaller, semi-randomized rate, accounting for local movements (e.g., short trips).  
  - EVs will travel at a predefined **average speed**, which simplifies simulation without focusing on traffic jams or other dynamic conditions.
  
- **Rush Hour & Travel Frequency**:  
  - A **probability matrix** will define travel frequency during rush hours. These peak periods should be well-defined based on real-world data (morning and evening rush hours, for instance).
  - Vehicles will often return to their **home region** after a trip, simulating daily commuting patterns.

- **Recharging Behavior**:  
  - EVs can **recharge** at:
    - **Home** (if the owner has the necessary infrastructure),
    - A **public recharging station** in the region they are located at.
  - Owners will have different **tolerance levels** for low battery. Once their battery drops below a threshold (e.g., 30%), the likelihood of them seeking a charging station increases significantly.

### Objectives:
1. **Station Distribution**:  
   Identify which regions require more recharging stations based on vehicle behavior and demand.
   
2. **Capacity Optimization**:  
   Determine the **optimal capacity** of each station to minimize **waiting times** and ensure that the infrastructure can meet demand.

3. **Waiting Time as KPI**:  
   The primary performance metric will be the **waiting time** for vehicles at charging stations. This metric will be crucial in determining whether the current infrastructure meets demand in different regions and if additional capacity is required.

### Recommendations & Clarifications:
- **Graph Representation**:  
  Clarify whether regions will be uniformly sized or if some regions will be larger or more complex than others. The distance calculation based on real roads is a great idea but ensure that the algorithm accounts for congestion or differing travel speeds across regions, if necessary.

- **Rush Hour Probability Matrix**:  
  - Ensure that the **rush hour periods** (morning/evening) and their impact on traffic flow are clearly defined.  
  - The probability matrix for travel during different periods (normal vs rush) could be calibrated using data from real-world sources, like traffic reports, if available for Porto.

- **Recharging Preferences**:  
  - For **home vs station recharging**, it may be useful to add another variable for **home recharging capacity** (i.e., some EV owners may only recharge at home, or prefer it heavily if convenient).
  - The vehicle's owner **tolerance to low battery** can be modeled as a probability distribution to add more realism (e.g., some are risk-averse and recharge sooner, while others let the battery drop to lower levels).

- **Simulation Details**:  
  - Will the **battery depletion rate** for each vehicle be uniform, or will there be variability (e.g., based on vehicle type)? This could help in modeling a more diverse set of EVs on the road.
  - **Charging speed** could vary between stations or even vehicle models, depending on the charger type (e.g., fast charging vs regular charging). This would add another layer of realism.

- **Capacity vs Waiting Time Relationship**:  
  Clarify how you will measure waiting time (e.g., queue length, average wait per vehicle) and what constitutes an unacceptable waiting time. This will help set the thresholds for capacity optimization in each region. 


### Technologies:
The language used will be Python. Leaflet will be used for the map visualization. The simulation will be run on a local machine using Openfire as a RTC server, where intelligent agents will run.

