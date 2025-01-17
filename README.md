# MS

https://github.com/user-attachments/assets/92173f3a-d7f2-49f2-b4d7-f18adcf78589

* Diogo Silva - up202004288@up.pt
* Henrique Silva - up202007242@up.pt
* Tiago Branquinho - up202005567@up.pt

## Article

[MS___Recharging_Stations_Distribution_For_E_Mobility.pdf](docs/report/MS___Recharging_Stations_Distribution_For_E_Mobility.pdf)

## How to Build and Run

In order to run the code, you will need to have the following dependencies installed:
- [Python 3.10](https://www.python.org/downloads/) or above and `pip` package manager.
- [Make](https://www.gnu.org/software/make/).

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
There are different simulation models that can be tested:
* `make run SCENARIO=baseline` - The baseline scenario represents the current Porto infrastructure and dynamics.
* `make run SCENARIO=future` - The future scenario represents an increased EV demand around 5 years into the future but maintaining the current infrastructure to detect bottlenecks.
* `make run SCENARIO=inner` - The inner scenario represents an increase of the number of chargers mostly in inner regions of the city, testing it within the future context.
* `make run SCENARIO=outer` - The outer scenario represents an increase of the number of chargers mostly in outer regions of the city, testing it within the future context.
* `make run SCENARIO=balanced` - The outer scenario represents a balanced increase of the number of chargers throughout the city's regions, testing it within the future context.

### 4. Visualization

The simulation execution is displayed in a visual interface in runtime. 

### 5. Results

The final results, including the simulation history, can be displayed and analyzed by running the respective scenario's notebook inside the logs/ folder.

### 5. Cleanup

To clean up the project and remove the generated files, you can run the following command:

```bash
$ make clean
```
