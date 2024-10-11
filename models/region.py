class Region:
    def __init__(self, id, latitude, longitude, avg_drivers, avg_income, chargers):
        self.id = id
        self.latitude = float(latitude)
        self.longitude = float(longitude)
        self.avg_drivers = int(avg_drivers)
        self.avg_income = int(avg_income)
        self.chargers = int(chargers)

    def get_id(self):
        return self.id

    def get_latitude(self):
        return self.latitude

    def get_longitude(self):
        return self.longitude
    
    def __str__(self):
        return f"{self.id}, Latitude: {self.latitude}, Longitude: {self.longitude}"