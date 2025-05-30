from sqlalchemy import create_engine, Column, Integer, String, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from pymongo import MongoClient
import os

# --- PostgreSQL Setup ---
# DATABASE_URL = "postgresql://postgres:root@localhost:5433/auto_iq_db"
DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()

class UploadData(Base):
    __tablename__ = "upload_data"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    sales = Column(Float)
    comments = Column(String)
    lead_category = Column(String)
    keywords = Column(String)
    sentiment = Column(String)



# --- MongoDB Setup ---
# MONGO_URI = "mongodb+srv://sneha123:sneha123@cluster0.ry1nlph.mongodb.net/auto_iq_db"
# mongo_client = MongoClient(MONGO_URI)
MONGO_URI = os.getenv("MONGO_URI")  # ✅ Loaded from Render
mongo_client = MongoClient(MONGO_URI)
mongo_db = mongo_client["auto_iq_db"]
mongo_collection = mongo_db["upload_data"]
# from sqlalchemy import create_engine
# from sqlalchemy.ext.declarative import declarative_base
# from sqlalchemy import Column, Integer, String, Float

# # 1. PostgreSQL connection URL
# DATABASE_URL = "postgresql://postgres:root@localhost:5433/auto_iq_db"

# # 2. Create engine
# engine = create_engine(DATABASE_URL)

# # 3. Create Base
# Base = declarative_base()

# # 4. Define the table
# class UploadData(Base):
#     __tablename__ = "upload_data"

#     id = Column(Integer, primary_key=True, index=True)
#     name = Column(String)
#     sales = Column(Float)
#     comments = Column(String)
#     lead_category = Column(String)
#     keywords = Column(String)
#     sentiment = Column(String)

# # 5. Create the table
# Base.metadata.create_all(bind=engine)

# print("✅ PostgreSQL table 'upload_data' created successfully.")

