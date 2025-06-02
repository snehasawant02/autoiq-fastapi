from fastapi import FastAPI, UploadFile, File, Request,Depends, HTTPException, Form,status
from fastapi.responses import HTMLResponse, JSONResponse,FileResponse,RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import pandas as pd
import os
from app.database import SessionLocal, UploadData,Base, engine
from pymongo import MongoClient
import pandas as pd
from app.auth import authenticate_user, create_access_token, get_password_hash, get_current_user
from fastapi.security import OAuth2PasswordRequestForm
from datetime import timedelta
from dotenv import load_dotenv
import openai
from pymongo import MongoClient

openai.api_key = os.getenv("OPENAI_API_KEY")

print("FastAPI app starting...")

from openai import OpenAI
client1 = OpenAI()


UPLOAD_FOLDER = "data"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app = FastAPI()


load_dotenv()
@app.on_event("startup")
def startup_event():
    Base.metadata.create_all(bind=engine)

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})
# @app.get("/", response_class=HTMLResponse)
# def home():
#     return HTMLResponse("<h2> AutoIQ backend is running.</h2>")



@app.post("/upload")
def upload_file(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user)  #  Protect this route
):
    print(f"User {current_user['email']} is uploading a file.")
    file_location = os.path.join(UPLOAD_FOLDER, file.filename)
    with open(file_location, "wb+") as f:
        f.write(file.file.read())

    try:
        df = pd.read_csv(file_location) if file.filename.endswith(".csv") else pd.read_excel(file_location)

        info = {
            "columns": df.columns.tolist(),
            "shape": df.shape,
            "summary": df.describe(include='all').to_dict()
        }

        if 'sales' in df.columns:
            from app.ml.lead_classifier import predict_lead_category
            df['Lead Category'] = predict_lead_category(df['sales'])

        if 'comments' in df.columns:
            from app.nlp.text_analysis import extract_keywords
            df['Top Keywords'] = df['comments'].apply(lambda text: extract_keywords(text))
            from app.ml.sentiment_model import predict_sentiment
            df['Sentiment'] = df['comments'].apply(lambda text: predict_sentiment(text))

        df.to_csv(os.path.join(UPLOAD_FOLDER, "processed_" + file.filename), index=False)
        # Save to PostgreSQL
        sql_db = SessionLocal()
        for _, row in df.iterrows():
            record = UploadData(
                name=row.get("name"),
                sales=row.get("sales"),
                comments=row.get("comments"),
                lead_category=row.get("Lead Category"),
                keywords=row.get("Top Keywords"),
                sentiment=row.get("Sentiment")
            )
            sql_db.add(record)
        sql_db.commit()  # outside the loop
        
        mongo_client = MongoClient(os.getenv("MONGO_URI"))
        mongo_db = mongo_client["auto_iq_db"]
        mongo_collection = mongo_db["upload_data"]
                # Save to MongoDB
        mongo_collection.insert_many(df.to_dict("records"))
        print("/upload called")

        return JSONResponse(content={"preview": df.head(10).to_dict(orient="records")})
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=400)


@app.get("/view-data", response_class=HTMLResponse)
def view_data(request: Request, current_user: dict = Depends(get_current_user)):
    sql_db = SessionLocal()
    records = sql_db.query(UploadData).order_by(UploadData.id.desc()).limit(20).all()
    print(" /view data called")

    return templates.TemplateResponse("view_data.html", {
        "request": request,
        "records": records
    })
@app.get("/dashboard", response_class=HTMLResponse)
def dashboard(request: Request, current_user: dict = Depends(get_current_user)):
    db = SessionLocal()
    data = db.query(UploadData).all()

    lead_counts = {"High": 0, "Medium": 0, "Low": 0}
    sentiment_counts = {"POSITIVE": 0, "NEGATIVE": 0, "NEUTRAL": 0}

    for row in data:
        lc = (row.lead_category or "").capitalize()
        if lc in lead_counts:
            lead_counts[lc] += 1

        snt = (row.sentiment or "").split()[0].upper()
        if snt in sentiment_counts:
            sentiment_counts[snt] += 1
            print(" /dashboard called")

    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "lead_data": lead_counts,
        "sentiment_data": sentiment_counts
    })

@app.get("/download-excel")
def download_excel():
    db = SessionLocal()
    records = db.query(UploadData).all()
    print(" /download called")

    # Convert to DataFrame
    df = pd.DataFrame([{
        "name": r.name,
        "sales": r.sales,
        "comments": r.comments,
        "Lead Category": r.lead_category,
        "Top Keywords": r.keywords,
        "Sentiment": r.sentiment
    } for r in records])

    file_path = "data/exported_data.xlsx"
    df.to_excel(file_path, index=False)

    return FileResponse(file_path, media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                        filename="AutoIQ_Export.xlsx")

client = MongoClient(os.getenv("MONGO_URI"))
users_col = client["auto_iq_db"]["users"]

@app.post("/register")
def register_user(
    email: str = Form(...),
    password: str = Form(...),
    role: str = Form("user")
):
    if users_col.find_one({"email": email}):
        raise HTTPException(status_code=400, detail="Email already registered")
    hashed_password = get_password_hash(password)
    users_col.insert_one({
        "email": email,
        "password": hashed_password,
        "role": role
    })
    print(" /register called")

    return {"message": "User registered successfully"}

@app.post("/login")
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=400, detail="Invalid credentials")
    token = create_access_token(data={"sub": str(user["_id"])}, expires_delta=timedelta(minutes=30))
    return {"access_token": token, "token_type": "bearer"}
@app.post("/logout")
def logout():
    # Inform frontend to delete token (no real backend logout here unless blacklisting is used)
    return {"message": "Logout successful. Please delete your token on the client side."}
# or paste key directly for testing

@app.get("/summary")
def generate_feedback_summary():
    db = SessionLocal()
    comments = db.query(UploadData.comments).filter(UploadData.comments != None).limit(50).all()
    comment_texts = [c[0] for c in comments if c[0]]

    if not comment_texts:
        return {"summary": "No comments available to summarize."}

    prompt = (
        "Summarize the following customer feedback into key points:\n\n"
        + "\n".join(comment_texts)
    )

    try:
        response = client1.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=300,
            temperature=0.7
        )
        summary = response.choices[0].message.content
        return {"summary": summary}

    except Exception as e:
        return {"error": str(e)}
@app.get("/login-form", response_class=HTMLResponse)
def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})


@app.post("/login-form")
def login_form_submit(username: str = Form(...), password: str = Form(...)):
    print(" Login form submitted")
    user = authenticate_user(username, password)
    if not user:
        print(" Invalid credentials")
        return HTMLResponse("<h3>Invalid credentials</h3>", status_code=401)

    token = create_access_token(data={"sub": str(user['_id'])})
    print(" Token created")
    role = user['role']
    if role == "admin":
        response = RedirectResponse(url="/dashboard", status_code=302)
    else:
        response = RedirectResponse(url="/upload-page", status_code=302)
    response.set_cookie(key="access_token", value=token, httponly=True)
    return response

@app.get("/upload-page", response_class=HTMLResponse)
def upload_page(request: Request, current_user: dict = Depends(get_current_user)):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/upload-page", response_class=HTMLResponse)
def show_upload_page(request: Request, current_user: dict = Depends(get_current_user)):
    return templates.TemplateResponse("upload_page.html", {"request": request})
