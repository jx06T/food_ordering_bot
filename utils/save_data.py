import json

def store_data(file_path,data):
    try:
        with open("data/"+file_path,"w",encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
    except Exception as e :
        print('資料存檔錯誤',file_path,e)
        
def get_data(file_path):
    try:
        with open("data/"+file_path,"r",encoding="utf-8") as f:
             data = json.load(f)
             return data
        
    except Exception as e :
        try:
            with open("data/"+file_path,"w",encoding="utf-8") as f:
                json.dump({}, f, ensure_ascii=False, indent=4)
                return {}
                
        except Exception as e:
            print('資料讀取錯誤',file_path,e)

def combined_data(file_path,new_data):
    try:
        try:
            with open("data/"+file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

        except FileNotFoundError:
            data = {}
        except json.JSONDecodeError:
            data = {}
        
        if isinstance(data, dict) and isinstance(new_data, dict):
            data.update(new_data)
        elif isinstance(data, list) and isinstance(new_data, list):
            data.extend(new_data)
        else:
            raise ValueError("資料的類型不匹配")
        
        with open("data/"+file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
    
    except Exception as e:
        print("添加錯誤",e)

def add_data(file_path,key_path,value):
    try:
        try:
            with open("data/"+file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

        except FileNotFoundError:
            data = {}
        except json.JSONDecodeError:
            data = {}
        
        keys = key_path.split(".")
        target_data = data
        
        for i, key in enumerate(keys):
            if i == len(keys) - 1:

                if isinstance(value, dict):
                    target_data[key] = {**target_data.get(key, {}), **value} 
                    # target_data.update(value) 
                  
                elif isinstance(value, list) :
                    target_data[key] = target_data.get(key, []) + value 
                    # target_data.extend(value)
                else :
                    target_data[key] = value
                    # target_data = value

            else:
                if key not in data:
                    target_data[key] = {}
            
                target_data = target_data[key]

        with open("data/"+file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
    
    except Exception as e:
        print("添加錯誤",e)

if __name__ == "__main__":
    store_data("test.json",{"test":'12345',"ttt":[1,2,3,4,"5"],"aaa":{"bbb":[4,5],"ccc":"ss"}})
    print(get_data("test.json"))

    combined_data("test.json",{"test0":'123456',"ttt":[5,"88"]})
    print(get_data("test.json"))
    
    add_data("test.json","aaa.bbb",[44])
    print(get_data("test.json"))

    add_data("test.json","aaa.ccc",44)
    print(get_data("test.json"))

    add_data("test.json","zzz.qqq.ss",[44,88])
    print(get_data("test.json"))

    add_data("test.json","aaa",{"wss":88})
    print(get_data("test.json"))

    add_data("test.json","aaa",0)
    print(get_data("test.json"))