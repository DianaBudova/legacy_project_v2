import importlib.util, random, json
from copy import deepcopy
from pathlib import Path
from src import process
from src.db import DataManager
spec=importlib.util.spec_from_file_location('before','artifacts/lab8/process_before.py')
old=importlib.util.module_from_spec(spec); spec.loader.exec_module(old)
rng=random.Random(8)
def run(module,data):
 writes=[]
 module.get_data=lambda name:deepcopy(data[name])
 module.save=lambda name, value:writes.append((name,deepcopy(value)))
 return module.proc(), writes
for i in range(200):
 data={'users':[{'id':rng.randrange(4),'name':str(j),'role':rng.choice([1,2,3,4,None])} for j in range(8)],
       'products':[{'id':rng.randrange(4)} for j in range(8)],
       'orders':[{'id':j,'user_id':rng.randrange(5),'product_id':rng.randrange(5),
                  'status':rng.choice(['paid','pending','cancelled','refunded','invalid']),
                  'amount':rng.choice([-1,0,0.01,499.99,500,500.01,1000,1000.01,1200]),
                  'date':rng.choice(['2024-01-15','invalid'])} for j in range(rng.randrange(20))]}
 assert run(old,data)==run(process,data), i
manager=DataManager()
data={name:manager._get_test_data(name) for name in ['users','orders','products']}
assert run(old,data)==run(process,data)
result,_=run(process,data)
Path('artifacts/lab8/compatibility.txt').write_text('Seed 8: 200 differential batches passed (result and both save calls).\nBuilt-in demo data: identical result and save calls.\n'+json.dumps(result,ensure_ascii=False,indent=2)+'\n')
print('200 differential batches and built-in demo: passed')
