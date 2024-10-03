class Order:
    def __init__(self, id, latitude, longitude, weight):
        self.id = id
        self.latitude = float(latitude.replace(',', '.'))  # Convert to float, replacing comma with dot if necessary
        self.longitude = float(longitude.replace(',', '.'))  # Convert to float, replacing comma with dot if necessary
        self.weight = int(weight)  # Convert to integer

    def get_id(self):
        return self.id

    def get_latitude(self):
        return self.latitude

    def get_longitude(self):
        return self.longitude

    def get_weight(self):
        return self.weight
    
    def __str__(self):
        return f"Order ID: {self.id}, Latitude: {self.latitude}, Longitude: {self.longitude}, Weight: {self.weight}"