class Nutrition:
    def __init__(self,name,type,calories,fats,carbohydrate,protein):
        self.name = name
        self.type = type
        self.calories = calories
        self.fats = fats
        self.carbohydrates = carbohydrate
        self.protein = protein

    def get_name(self):
        return self.name

    def get_type(self):
        return self.type

    def get_calories(self):
        return  self.calories

    def get_fats(self):
        return self.fats

    def get_carbohydrates(self):
        return self.carbohydrates

    def get_protein(self):
        return self.protein

    def set_name(self,name):
        self.name = name

    def set_type(self,type):
        self.type = type

    def set_calories(self,calories):
        self.calories = calories

    def set_fats(self, fats):
            self.fats = fats

    def set_carbohydrates(self,cabohydrates):
        self.cabohydrates = cabohydrates

    def set_protein(self,protein):
        self.protein = protein