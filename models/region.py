class Region:
    def __init__(self, id, latitude, longitude, avg_drivers, avg_m_income, S_chargers, A_chargers, B_chargers):
        self.id = id
        self.latitude = float(latitude.replace(',', '.'))
        self.longitude = float(longitude.replace(',', '.'))
        self.avg_drivers = int(avg_drivers)
        self.avg_m_income = int(avg_m_income)
        self.S_chargers = int(S_chargers)
        self.A_chargers = int(A_chargers)
        self.B_chargers = int(B_chargers)

    def get_id(self):
        return self.id

    def get_latitude(self):
        return self.latitude

    def get_longitude(self):
        return self.longitude
    
    def __str__(self):
        return f"{self.id}, Latitude: {self.latitude}, Longitude: {self.longitude}"