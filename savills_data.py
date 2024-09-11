from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional


class Building(BaseModel):
    id: int
    name: str
    address: str



class Unit(BaseModel):
    id: int
    fullUnitId: str
    buildingId: int
    memberId: int
    


class Member(BaseModel):
    id: int
    name: str
    email: str
    phone: str
    profilePictureId: str
    isBOC: bool

    
class Booking(BaseModel):
    id: int
    fullUnitId: str
    buildingId: int
    userName: str
    userId: int
    startDate: str
    endDate: str
    statusCode: str
    createdAt: str
    phone: str
    email: str
    createdAt: str
    amenityName: str
    
