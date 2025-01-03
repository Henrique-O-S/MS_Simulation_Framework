class Region:
    def __init__(self, id, latitude, longitude, avg_drivers, avg_income, chargers, traffic):
        self.id = id
        self.latitude = float(latitude)
        self.longitude = float(longitude)
        self.avg_drivers = int(avg_drivers)
        self.avg_income = int(avg_income)
        self.chargers = int(chargers)
        self.available_chargers = chargers
        self.carsCharged = 0
        self.traffic = int(traffic)
    
    def _get_available_chargers(self):
        return self.available_chargers

    def get_charging_statistics(self):
        return {'%' + ' available chargers': self.available_chargers / self.chargers, 'cars charged': self.carsCharged}

    def start_charging(self):
        self.available_chargers -= 1

    def stop_charging(self):
        self.available_chargers += 1
        self.carsCharged += 1

    def get_id(self):
        return self.id

    def get_latitude(self):
        return self.latitude

    def get_longitude(self):
        return self.longitude
    
    def __str__(self):
        return f"{self.id}, Latitude: {self.latitude}, Longitude: {self.longitude}"

    def __eq__(self, other):
        return self.latitude == other.latitude and self.longitude == other.longitude