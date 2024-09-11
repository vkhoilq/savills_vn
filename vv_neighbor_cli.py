import time
from savills import Savills
from savills_data import Neighbor

import sys
import datetime


neighbor_list = []

if __name__ == "__main__":
    ## replace with your username and password
    from config import USERNAME,PASSWORD
    start = time()
    savills = Savills(USERNAME,PASSWORD)
    print(f"Login time {time() - start}")
    start = time()
    for i in ['T1','T2','O','L']: # 4 blocks
        for j in range(2,35): # 34 floors start from 2
            for k in range(1,13): # 12 units per floors
                house_code = f"{i}-{j:02}-{k:02}"
                print(f"House Code {house_code}")
                member = savills.get_neighbor_info(house_code=house_code)
                # use profilePictureId to store the fullUnitName
                if member is not None:
                    member.profilePictureId = house_code
                    print(member)
                    neighbor_list.append(member)
                else:
                    print(f"House Code {house_code} not found")

    