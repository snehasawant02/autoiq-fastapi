# from database import SessionLocal, mongo_collection
# from sqlalchemy import text


# # PostgreSQL Test
# try:
    
#     session = SessionLocal()
#     result = session.execute(text("SELECT 1"))
#     print(result.scalar())
#     session.close()
#     print(" PostgreSQL connected:", result.fetchone())
# except Exception as e:
#     print(" PostgreSQL error:", e)

# # MongoDB Test
# try:
#     collections = mongo_collection.database.list_collection_names()
#     print(" MongoDB connected. Collections:", collections)
# except Exception as e:
#     print(" MongoDB error:", e)
from database import SessionLocal, mongo_collection
from sqlalchemy import text

# PostgreSQL Test
try:
    session = SessionLocal()
    result = session.execute(text("SELECT 1"))
    value = result.scalar()  # fetch before closing
    print(" PostgreSQL connected. Result:", value)
    session.close()
except Exception as e:
    print(" PostgreSQL error:", e)

# MongoDB Test
try:
    collections = mongo_collection.database.list_collection_names()
    print(" MongoDB connected. Collections:", collections)
except Exception as e:
    print(" MongoDB error:", e)
