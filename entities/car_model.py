# -------------------------------------------------------------------------------------------------------------

class CarModel:
    """
    A class used to represent a Car Model.
    
    Attributes:
        id (str): A unique identifier for the car model.
        autonomy (float): The autonomy of the car model, representing the range or distance it can travel.
        price (int): The price of the car model.
    """
    def __init__(self, id, autonomy, price):
        self.id = id
        self.autonomy = autonomy
        self.price = int(price)
        
    # ---------------------------------------------------------------------------------------------------------

    def get_id(self):
        """
        Retrieve the ID of the car model.

        Returns:
            int: The ID of the car model.
        """
        return self.id
    
    # ---------------------------------------------------------------------------------------------------------

    def get_autonomy(self):
        """
        Returns the autonomy of the car model.

        Returns:
            float: The autonomy of the car model.
        """
        return self.autonomy
    
    # ---------------------------------------------------------------------------------------------------------

    def get_price(self):
        """
        Retrieve the price of the car model.

        Returns:
            float: The price of the car model.
        """
        return self.price
    
    # ---------------------------------------------------------------------------------------------------------

    def __str__(self):
        """
        Returns a string representation of the car model instance.
        
        Returns:
            str: A string in the format "{id}, Autonomy: {autonomy}, Price: {price}".
        """
        return f"{self.id}, Autonomy: {self.autonomy}, Price: {self.price}"
    
# -------------------------------------------------------------------------------------------------------------