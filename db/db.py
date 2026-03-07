from pymongo import MongoClient
import os
from dotenv import load_dotenv
from bson import ObjectId

load_dotenv()

MONGO_URI = os.getenv("MONGODB_URI")

client = MongoClient(MONGO_URI)
db = client["hospital_ai_db"]


def get_visit():
    """ดึง visit ทั้งหมด"""
    visits = list(db["visits"].find())

    for v in visits:
        v["_id"] = str(v["_id"])

    return visits


def get_visit_by_id(visit_id):
    """ดึง visit เดียว"""
    visit = db["visits"].find_one({"_id": ObjectId(visit_id)})

    if visit:
        visit["_id"] = str(visit["_id"])

    return visit