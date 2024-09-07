import json

class RDM():
    def __init__(self,file_path) -> None:
        if not file_path.endswith('.json'):
            file_path += ".json"

        file_path = "data/" + file_path

        try:
            with open(file_path,"r",encoding="utf-8") as f:
                self.data = json.load(f)
        except Exception as e :
            with open(file_path,"w",encoding="utf-8") as f:
                json.dump({"_restaurants":[]}, f, ensure_ascii=False, indent=4)
                self.data = {"_restaurants":[]}

        self.file_path = file_path

    def add_restaurant(self,name):
        if "_restaurants" not in self.data:
            self.data["_restaurants"] = []

        self.data["_restaurants"].append(name)

    def get_restaurants(self):
        return self.data.get("_restaurants",[])
    
    def add_image(self,restaurant,img_path):
        if restaurant not in self.data:
            self.data[restaurant] = {}
        if "image" not in self.data[restaurant]:
            self.data[restaurant]["image"] = []

        self.data[restaurant]["image"].append(img_path)

    def get_image(self,restaurant):
        return self.data.get(restaurant,{}).get("image",[])

    def add_dish(self,restaurant,dish_name,note):
        if restaurant not in self.data:
            self.data[restaurant] = {}
        if "menu" not in self.data[restaurant]:
            self.data[restaurant]["menu"] = {}
            
        self.data[restaurant]["menu"][dish_name] =  {**self.data[restaurant]["menu"].get(dish_name,{}), **note}

    def get_dish(self,restaurant,dish_name = None):
        if dish_name is None:
            return self.data.get(restaurant,{}).get("menu",{})
        else:
            return self.data.get(restaurant,{}).get("menu",{}).get(dish_name,None)

    def save_to_file(self):
        try:
            with open(self.file_path,"w",encoding="utf-8") as f:
                json.dump(self.data, f, ensure_ascii=False, indent=4)
        except Exception as e :
            print('資料存檔錯誤',self.file_path,e)
           
if __name__ == "__main__":
    manager = RDM("test.json")
   