import requests

from typing import List

from fastapi import FastAPI
from pydantic import BaseModel

from tronpy.keys import to_hex_address

from sqlalchemy import  Column, Integer, String, Float, select
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine


app = FastAPI()

base = declarative_base()
engine = create_async_engine("sqlite+aiosqlite:///data-base.db", echo=True)
SessionLocal = sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)

class TronAccount(base):
    __tablename__ = 'tron_account'

    id = Column(Integer, primary_key=True, index=True)
    address = Column(String, default = "")
    balance = Column(Float, default = 0.0)
    bandwidth = Column(Float, default = 0.0)
    energy = Column(Float, default = 0.0)

class InputData(BaseModel):
    address:str

class OutData(BaseModel):
    id:int
    address:str
    balance:float
    bandwidth:float
    energy:float

    class Config:
        from_attributes = True

def getBalance(address_hex):
    url = f"https://api.trongrid.io/v1/accounts/{address_hex}"
    response = requests.get(url).json()
    try:
        balance = response['data'][0]['balance'] / 1000000
        return balance
    except (KeyError, IndexError):
        return None

def getResources(address_hex):
    url = "https://api.trongrid.io/wallet/getaccountresource"
    response = requests.post(url, json={"address": address_hex}).json()
    bandwidth = response.get('freeNetLimit', 0) + response.get('NetLimit', 0)
    energy = response.get('EnergyLimit', 0)
    
    return bandwidth, energy


@app.on_event("startup")
async def startup():
    async with engine.begin() as conn:
        await conn.run_sync(base.metadata.create_all)

@app.get("/get-data/", response_model=List[OutData])
async def getData():
    async with SessionLocal() as session:
        result = await session.execute(
            select(TronAccount)
        )
        accounts = result.scalars().all()
        return accounts

@app.post("/post-address/")
async def postData(data: InputData):
    address = to_hex_address(data.address)
    balance = getBalance(address)
    bandwidth, energy = getResources(address)

    async with SessionLocal() as session:
        account = TronAccount(
            address = address,
            balance = balance, 
            bandwidth = bandwidth,
            energy = energy
        )
        session.add(account)
        await session.commit()

    return{
        "message": "Success",
        "address": data.address,
        "balance": balance,
        "bandwidth": bandwidth,
        "energy": energy
    }