import json

class ODM():
    def __init__(self,file_path) -> None:
        if not file_path.endswith('.json'):
            file_path += ".json"
        
        file_path = "data/order/" + file_path

        try:
            with open(file_path,"r",encoding="utf-8") as f:
                self.data = json.load(f)
        except Exception as e :
            with open(file_path,"w",encoding="utf-8") as f:
                json.dump({"_all":{}}, f, ensure_ascii=False, indent=4)
                self.data = {"_all":{}}


        self.file_path = file_path

    def add_order(self,user_number,dish,other_number = None):
        if dish not in self.data["_all"]:
            self.data["_all"][dish] = []

        if other_number is not None:
            if f"_{other_number}_({user_number}代)" not in self.data:
                self.data[f"_{other_number}_({user_number}代)"]  = []

            self.data[f"_{other_number}_({user_number}代)"].append(dish)
            self.data["_all"][dish].append(other_number)

        else:
            if f"_{user_number}_" not in self.data:
                self.data[f"_{user_number}_"] = []    
                
            self.data[f"_{user_number}_"].append(dish)
            self.data["_all"][dish].append(user_number)

    def remove_order(self,user_number,dish,other_number = None):
        if dish not in self.data["_all"]:
            self.data["_all"][dish] = []

        if other_number is not None:
            self.data[f"_{other_number}_({user_number}代)"] = dish
            self.data["_all"][dish].append(other_number)

        else:
            self.data[f"_{user_number}_"] = dish
            self.data["_all"][dish].append(user_number)

    def get_order(self,user_number):
        return [
            {"name":value ,"type": "幫別人訂的" if f"({user_number}代)" in key else ("你定的" if f"_{user_number}_" not in key else "別人幫你訂的")}
            for key,value in self.data if not key == "_all" and ( f"_{user_number}_" in key or f"({user_number}代)" in key)
        ]

    def save_to_file(self):
        try:
            with open(self.file_path,"w",encoding="utf-8") as f:
                json.dump(self.data, f, ensure_ascii=False, indent=4)
        except Exception as e :
            print('資料存檔錯誤',self.file_path,e)
           
if __name__ == "__main__":
    manager = ODM("test.json")
   