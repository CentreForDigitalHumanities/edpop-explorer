
class Car():
    # What happens when I create an instance of this class
    def __init__(self, color_param, brand_param):
        self.color = color_param
        self.brand = brand_param

    def get_paintjob(self, new_color):
        self.color = new_color
        print("My new color is", self.color)

    @classmethod
    def define_car(cls):
        return "A car is a four wheeled method of transportation."


class SportsCar(Car):
    def __init__(self, color_param, brand_param, horsepower):
        self.color = color_param
        self.brand = brand_param
        self.horsepower = horsepower



# These are the instances
cristinas_car = SportsCar(color_param='red', brand_param='ferrari', horsepower=20)
joaquins_car = Car(color_param='green',brand_param='fiat')


print(Car.define_car())