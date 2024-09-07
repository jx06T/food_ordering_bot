import json
from datetime import datetime
import copy

class ODM():
    def __init__(self,file_path,restaurant) -> None:
        if not file_path.endswith('.json'):
            file_path += ".json"
        
        file_path = "data/order/" + file_path

        # try:
        #     with open(file_path,"r",encoding="utf-8") as f:
        #         self.data = json.load(f)
        # except Exception as e :
        #     with open(file_path,"w",encoding="utf-8") as f:
        #         json.dump({"_all":{}}, f, ensure_ascii=False, indent=4)
        #         self.data = {"_all":{}}

        self.data = {"_all":{}}
        self.isOpen = True
        self.bill = {"_all":{}}
        self.file_path = file_path
        self.identity_group = datetime.now().strftime("%m/%d") + restaurant + "發起者"

    def add_order(self,user_number,dish,other_number = None):
        if dish not in self.data["_all"]:
            self.data["_all"][dish] = []

        if other_number is not None:
            self.data.setdefault(f"[{other_number}]({user_number}代)",[]).append(dish)
            self.bill.setdefault(f"[{other_number}]({user_number}代)",[]).append(dish)
            self.data["_all"][dish].append(f"[{other_number}]({user_number}代)")

        else:
            self.data.setdefault(f"[{user_number}]",[]).append(dish)
            self.bill.setdefault(f"[{user_number}]",[]).append(dish)
            self.data["_all"][dish].append(f"[{user_number}]")

    def remove_order(self,path,dish):
        if dish not in self.data["_all"]:
            self.data["_all"][dish] = []
            return
        
        self.data["_all"][dish].remove(path)

        self.data.get(path,[]).remove(dish)
        if len(self.data.get(path,[1,1])) == 0:
            del self.data[path]

        self.bill.get(path,[]).remove(dish)
        if len(self.bill.get(path,[1,1])) == 0:
            del self.bill[path]

    def transform_data(self, user_number):
        result = []
        for key, value in self.data.items():
            if  key != "_all" and ( f"[{user_number}]" in key or f"({user_number}代)" in key):
                result.extend([{"source" :key ,"name": item, "type": ("幫別人訂的" if f"({user_number}代)" in key else ("你訂的" if f"[{user_number}](" not in key else "別人幫你訂的")) } for item in value])
        return result

    def get_order(self,user_number):
        return self.transform_data(user_number)

    def all_order_list(self):
        return [
            (key,value)
            for key, value in self.data.items() if  key != "_all"
        ]

    def get_bill(self):
        return [
            (key,value)
            for key, value in self.bill.items() if  key != "_all"
        ]

    def checkout(self,path):
        del self.bill[path]

    def get_list(self):
        return [
            # ("name":key,"count":len(value))
            (key,len(value))
            for key, value in self.data["_all"].items() 
        ]

    # def save_to_file(self):
    #     try:
    #         with open(self.file_path,"w",encoding="utf-8") as f:
    #             json.dump(self.data, f, ensure_ascii=False, indent=4)
    #     except Exception as e :
    #         print('資料存檔錯誤',self.file_path,e)
           
if __name__ == "__main__":
    manager = ODM("test.json")
   