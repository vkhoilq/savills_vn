import requests
from res_client import BaseRESTClient
import base64
from typing import Tuple
import datetime
import json
from savills_data import Building, Unit, Member, Booking

from time import time
from rich import print

class Savills(BaseRESTClient):
    ## Hardcode the tenantId its for Vista Verde
    ## if wanna get the tenantId, use api
    ## https://vn.propertycube.asia/core/api/UserLink/GetLinkedAccount?MaxResultCount=100&SkipCount=0&culture=vi
    ## TBD
    

    
    building = None
    unit = None
    member = None
    
    def __init__(self, user, password):
        
        super().__init__(user,password,"https://vn.propertycube.asia")
        self.login()
    
    def login(self):
        
        
        ## override login method to use the login endpoint
        headers = {
        'Host': 'accounts-vn.propertycube.asia',
        'Accept': 'application/json',
        'Devicetypeid': '2',
        'Cache-Control': 'no-cache',
        'Api-Version': '2',
        'Content-Type': 'application/json',
        'Accept-Encoding': 'gzip, deflate',
        'User-Agent': 'okhttp/4.9.2',
        'Cookie': 'ApplicationGatewayAffinity=4d41f1ce71536351747e651ab04cb5f4; ApplicationGatewayAffinityCORS=4d41f1ce71536351747e651ab04cb5f4'
        }
        
        login_struct = {
            "userNameOrEmailAddress": self.user,
            "password": self.password
        }
        str = json.dumps(login_struct)
        encodedata = base64.b64encode(str.encode()).decode()
        try:
            response = requests.post(
                f"https://accounts-vn.propertycube.asia/api/TokenAuth/Authenticate?culture=vi",
                headers=headers,
                json={"data": encodedata}
            )
            response.raise_for_status()

            data = response.json()
            self.token = data["result"]["accessToken"]

        except requests.exceptions.RequestException as e:
            print(f"Login failed: {e}")
            return False

        ## Special Treatment for Savills
        result = self.get(f"/core/api/UserLink/GetLinkedAccount?MaxResultCount=100&SkipCount=0&culture=vi")
        tenantId = result["result"][0]["tenantId"]
        userId = result["result"][0]["id"]
        result = self.get(f"/core/api/UserLink/SwitchToUserAccount?targetTenantId={tenantId}&targetUserId={userId}&culture=vi")
        switchAccountToken = result["result"]["switchAccountToken"]
        ## hardcode the switch "e30=" is {} in base64
        result = self.post(f"/core/api/TokenAuth/LinkedAccountAuthenticate?switchAccountToken={switchAccountToken}&culture=vi",data={"data": "e30="})
        self.token = result["result"]["accessToken"]
        
        if self.member == None: 
            self.unit = self.get_unit_info()
            self.member,self.building = self.get_personal_info()
        
        return True
    
    def get_unit_info(self) -> Unit:
        result = self.get(f"/core/api/units/UnitsByMember?culture=vi")
        results = result["result"]
        result = results["items"][0]
        # right now get only item 0 assume only 1 unit
        unit = Unit(
            id=result["unitId"],
            fullUnitId=result["fullUnitCode"],
            memberId=result["memberId"],
            buildingId=result["buildingId"]
        )
        return unit
    
    def get_personal_info(self) -> Tuple[Member,Building]:

        result = self.get(f"/core/api/services/app/Session/GetCurrentLoginInformations?culture=vi")
        user = result["result"]["user"]
        member = Member(
            id=user["id"],
            name=user["displayName"],
            email=user["emailAddress"],
            phone=user["phoneCode"]+ " " + user["phoneNumber"],
            profilePictureId=user["profilePictureId"],
            isBOC=user["isBOC"]
        )
        
        tenant = result["result"]["tenant"]
        
        building = Building(
            id=tenant["tenantAddress"]["tenantId"],
            name=tenant["name"],
            address=tenant["tenantAddress"]["address"]
        )
        return member,building
    
    def get_bookings(self,venueId=3) -> list[Booking]:
        ## Hardcode first to get all Tennis which ID is 3
        # in case wanna support get all Venues use this api
        # https://vn.propertycube.asia/booking/api/amenities?isActive=true&buildingId=0&culture=vi
        
        #hardcoded for now
        pagesize = 15
        page = 1
        
        result = self.get(f"/booking/api/bookings/mybookings?pageSize={pagesize}&page={page}&unitId=&groupStatus=ONGOING&keyword=&isActive=true&culture=vi")
        items = result["result"]["items"]
        bookings = [Booking(
                            id=item["reservationId"],
                            fullUnitId=item["fullUnitId"],
                            buildingId=item["buildingId"],
                            userName=item["userName"],
                            statusCode=item["status"]["statusCode"],
                            createdAt=item["createdAt"],
                            startDate=item["startDate"],
                            endDate=item["endDate"],
                            phone=item["phone"],
                            email=item["email"],
                            amenityName=item["userId"]
                            ) 
                    for item in items]
        return bookings
    
    
    def get_booking_detail(self,booking_number):
        result = self.get(f"/booking/api/bookings/{booking_number}?culture=vi")
        result = result["result"]
        booking = Booking(
            id=result["reservationId"],
            fullUnitId=result["fullUnitId"],
            buildingId=result["buildingId"],
            userName=result["userName"],
            statusCode=result["status"]["statusCode"],
            createdAt=result["createdAt"],
            startDate=result["startDate"],
            endDate=result["endDate"],
            phone=result["phone"],
            email=result["email"],
            amenityName=result["amenity"]["amenityName"],
            userId=result["userId"]
        )
        return booking
    
    def delete_booking(self,booking_number):
        delete_booking_dict = {
            "reservationId":booking_number,
            "status":"CANCELED"
        }
        str = json.dumps(delete_booking_dict)
        encodedata = base64.b64encode(str.encode()).decode()
        try:
            result = self.put(f"/booking/api/bookings/resident?culture=vi",data={"data":encodedata})
            return True
        except Exception as e:
            print(e)
            return False
    
    def create_booking(self, startDate:datetime.datetime, endDate=None, amenityId=3, retries = 5):
        #https://vn.propertycube.asia/booking/api/bookings/create?culture=vi
        #https://vn.propertycube.asia/booking/api/bookings/create?culture=vi
        
        if endDate == None:
            endDate = startDate + datetime.timedelta(hours=1)
            
        booking_dict = {
            "startDate":startDate.isoformat(),
            "endDate":endDate.isoformat(),
            "amenityId":amenityId,
            "status":"REQUESTED",
            "amenity":{"amenityId":amenityId},
            "buildingId":self.unit.buildingId,
            "unitId":self.unit.id,
            "fullUnitId":self.unit.fullUnitId,
            "userId":self.member.id,
            "name":self.member.name,
            "userName":self.member.name,
            "phone":self.member.phone,
            "email":self.member.email,
            "profilePictureId":self.member.profilePictureId,
            "paymentStatus": None,
            "remark": "",
            "isAcceptPolicy": True,
            "tenantId": self.building.id,
            "numberOfPerson": "",
            "files": []
        }
        str = json.dumps(booking_dict,ensure_ascii=False)
        encodedata = base64.b64encode(str.encode('utf8')).decode()
        output = f'{"data"}'
        while retries>0:
            try:
                result = self.post(f"/booking/api/bookings/create?culture=vi",data={"data": encodedata})
                return result["result"]["id"]
            except Exception as e:
                print(e)
                retries -= 1
                
        return None
    
    def get_neighbor_info(self,house_code="T1-34-02"):
        # use the get Fee API to get the neighbor's information
        try:
            result = self.get(f"/core/api/Fees/fees/receiptfilters?fullUnitCode={house_code}&isMain=true&page=1&pageSize=1&IsIncludeFeePayer=true&culture=vi")
            result = result["result"]["items"][0]["feePayer"]
            member = Member(
                id=result["residentId"],
                name=result["fullName"],
                phone=result["phoneNumber"],
                email=result["email"],
                profilePictureId="",
                isBOC=False

            )
            return member
        except Exception as e:
            print(e)
            return None
def test_neighbor_info():
    # test right info
    house_code = "T1-34-02"
    print(f"House Code {house_code}")
    member = savills.get_neighbor_info(house_code=house_code)
    print(member)
    
    # test wrong info
    house_code = "T1-35-02"
    print(f"House Code {house_code}")
    member = savills.get_neighbor_info(house_code=house_code)
    print(member)
    
    ## looping
    for i in range(1,15):
        house_code = f"T1-33-{i:02}"
        print(f"House Code {house_code}")
        member = savills.get_neighbor_info(house_code=house_code)
        print(member)
        print("------------------------------------")
        
def test_get_booking_detail(start=24222,stop=24300):
    for i in range(24222,24300):
        try:
            booking = savills.get_booking_detail(i)
            print(booking)
        except Exception as e:
            print(e)
        print("------------------------------------")
    
def test_create_get_delete_booking():
    from gettime import get_timezone
    # Get the next 3 hours round up to the current hour
    startDate = datetime.datetime.now(tz=get_timezone()).replace(microsecond=0,minute=0,second=0) + datetime.timedelta(days=30)
    booking_number = savills.create_booking(startDate=startDate)
    print(f' Success Booking Number {booking_number}')
    print(f"Booking time {time() - start}")
    print(f'Get Detail Booking Number {booking_number}')
    print(savills.get_booking_detail(booking_number))
    print(f"Detail Booking time {time() - start}")
    print(f'Delete Booking Number {booking_number}')
    print(savills.delete_booking(booking_number))
    print(f"Delete Booking time {time() - start}")
    


if  __name__ == "__main__":
    ## replace with your username and password
    from config import USERNAME,PASSWORD
    start = time()
    savills = Savills(USERNAME,PASSWORD)
    print(f"Login time {time() - start}")
    start = time()
    test_neighbor_info()

