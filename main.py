from fastapi import FastAPI, Request, Form, status, UploadFile, File, Depends
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware
from pymongo.server_api import ServerApi
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime
import shutil, os, bcrypt, base64
from werkzeug.utils import secure_filename
from bson import ObjectId
from pydantic import BaseModel, EmailStr, Field

# 連結資料庫s
uri = "mongodb+srv://<username>:<password>@cluster0.mongodb.net/
client = AsyncIOMotorClient(uri, server_api=ServerApi('1'))
db = client["Rescue-straycats"]

app = FastAPI()

# 掛載 static 資料夾中的靜態資源（圖片、CSS）
app.mount("/static", StaticFiles(directory="static"), name="static")

# Jinja2 模板引擎：指定 HTML 存放資料夾
templates = Jinja2Templates(directory="templates")

# 跨域設定（前端開發時用）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Session Middleware 設定
app.add_middleware(
    SessionMiddleware, 
    secret_key="1s2e3c4r5e6t7k8e9y0",
    same_site="strict",
    https_only=True
)  

# 表單驗證模型
class RegisterForm(BaseModel):
    nickname: str = Field(..., min_length=2)
    email: EmailStr
    password: str = Field(..., min_length=6)
    confirm: str

class SignInForm(BaseModel):
    email: EmailStr
    password: str

# 首頁：顯示網站介紹 + 最新10筆通報
@app.get("/", response_class=HTMLResponse)
async def homepage(request: Request):
    reports_cursor = db.reports.find().sort("time", -1).limit(10)
    report_list = await reports_cursor.to_list(length=10)
    nickname = request.session.get("nickname")  # 若有登入，取得 nickname
    return templates.TemplateResponse("index.html", {
        "request": request,
        "reports": report_list,
        "nickname": nickname
    })


# 註冊功能
@app.post("/register")
async def register(
    nickname: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    confirm: str = Form(...)
):
    form = RegisterForm(nickname=nickname, email=email, password=password, confirm=confirm)

    if password != form.confirm:
        return RedirectResponse(
            url="/registered?msg=密碼與確認密碼不一致，請重新確認",
            status_code=303
        )

    user_col = db.user
    existing_user = await user_col.find_one({"email": form.email})
    if existing_user:
        return RedirectResponse(url="/registered?msg=信箱已註冊", status_code=303)
    
    # 密碼加密
    hashed_pw = bcrypt.hashpw(form.password.encode("utf-8"), bcrypt.gensalt())
    hashed_pw_b64 = base64.b64encode(hashed_pw).decode("utf-8")

    await user_col.insert_one({
        "nickname": form.nickname,
        "email": form.email,
        "password": hashed_pw_b64
    })
    return RedirectResponse(url="/registered?msg=註冊成功", status_code=303)

# 註冊後處理功能
@app.get("/registered", response_class=HTMLResponse)
async def registered(request: Request, msg: str = ""):
    return templates.TemplateResponse("registered.html", {
        "request": request,
        "msg": msg
    })

# 登入功能（儲存 session）
@app.post("/signin")
async def signin(
    request: Request,
    email: str = Form(...),
    password: str = Form(...)
):
    form = SignInForm(email=email, password=password)
    user = await db.user.find_one({"email": email})
    if not user:
        return RedirectResponse(url="/?msg=登入失敗，請檢查信箱或密碼！", status_code=303)
    stored_hash_b64 = user["password"]
    stored_hash = base64.b64decode(stored_hash_b64.encode("utf-8"))

    if not bcrypt.checkpw(form.password.encode("utf-8"), stored_hash):
        return RedirectResponse(url="/?msg=登入失敗，請檢查信箱或密碼！", status_code=303)

    # 登入成功，將暱稱儲存在 session 中
    request.session["nickname"] = user["nickname"]

    return RedirectResponse(url="/member", status_code=303)


# 登出功能（清除 session）
@app.get("/logout")
async def logout(request: Request):
    request.session.clear()
    return RedirectResponse(url="/", status_code=303)


# 會員頁（檢查 session）
@app.get("/member", response_class=HTMLResponse)
async def member(request: Request):
    nickname = request.session.get("nickname")
    if not nickname:
        return RedirectResponse(url="/", status_code=303)
    
    return templates.TemplateResponse("member.html", {
        "request": request,
        "nickname": nickname
    })

# 通報頁面 GET：顯示通報表單與紀錄
@app.get("/reporter", response_class=HTMLResponse)
async def reporter_page(request: Request):
    nickname = request.session.get("nickname")
    if not nickname:
        return RedirectResponse(url="/", status_code=303)

    reports_cursor = db.reports.find({"reporter": nickname}).sort("time", -1)
    reports = await reports_cursor.to_list(length=100)

    # 時間格式轉換（給模板用）
    for report in reports:
        try:
            report["formatted_time"] = datetime.strptime(report["time"], "%Y-%m-%dT%H:%M").strftime("%Y/%m/%d-%H:%M")
        except:
            report["formatted_time"] = report["time"]

    return templates.TemplateResponse("reporter.html", {
        "request": request,
        "reports": reports
    })

# 通報頁面 POST：儲存資料至資料庫
@app.post("/reporter")
async def submit_report(
    request: Request,
    time: str = Form(...),
    city: str = Form(...),
    district: str = Form(...),
    location: str = Form(...),
    status: str = Form(...),
    description: str = Form(...),
    cat_photo: UploadFile = File(...),
    env_photo: UploadFile = File(...)
):
    nickname = request.session.get("nickname")
    if not nickname:
        return JSONResponse(content={"error": "未登入"}, status_code=401)

    # 儲存圖片
    os.makedirs("static/upload", exist_ok=True)
    cat_filename = f"{datetime.now().timestamp()}_{secure_filename(cat_photo.filename)}"
    env_filename = f"{datetime.now().timestamp()}_{secure_filename(env_photo.filename)}"

    with open(os.path.join("static/upload", cat_filename), "wb") as f:
        f.write(await cat_photo.read())
    with open(os.path.join("static/upload", env_filename), "wb") as f:
        f.write(await env_photo.read())

    # 儲存資料進資料庫
    await db.reports.insert_one({
        "reporter": nickname,
        "time": time,
        "city": city,
        "district": district,
        "location": location,
        "status": status,
        "description": description,
        "cat_photo": f"/static/upload/{cat_filename}",
        "env_photo": f"/static/upload/{env_filename}",
        "rescue_status": None
    })

    # 時間格式化給前端用
    formatted_time = datetime.strptime(time, "%Y-%m-%dT%H:%M").strftime("%Y/%m/%d-%H:%M")

    return JSONResponse({
        "formatted_time": formatted_time,
        "location": location,
        "status": status,
        "description": description,
        "cat_photo": f"/static/upload/{cat_filename}",
        "env_photo": f"/static/upload/{env_filename}"
    })

# 救援者頁面：可查看與篩選通報資料
@app.get("/rescuer", response_class=HTMLResponse)
async def rescuer_page(request: Request, city: str = "", district: str = ""):
    nickname = request.session.get("nickname")
    if not nickname:
        return RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)

    query = {"rescue_status": {"$ne": "已救援"}}
    if city and district:
        query["location"] = {"$regex": f"{city} {district}"}
    elif city:
        query["location"] = {"$regex": city}
    elif district:
        query["location"] = {"$regex": district}

    reports = await db.reports.find(query).sort("time", -1).to_list(length=100)
    rescued_reports = await db.rescued_history \
        .find({"rescued_by": nickname}) \
        .sort("rescued_time", -1) \
        .to_list(length=100)

    for report in reports:
        try:
            report["formatted_time"] = datetime.strptime(report["time"], "%Y-%m-%dT%H:%M") \
                .strftime("%Y/%m/%d-%H:%M")
        except:
            report["formatted_time"] = report["time"]

    for record in rescued_reports:
        try:
            t = record.get("rescued_time") or record.get("time")
            if isinstance(t, datetime):
                record["formatted_time"] = t.strftime("%Y/%m/%d-%H:%M")
            else:
                record["formatted_time"] = datetime.strptime(t, "%Y-%m-%dT%H:%M") \
                    .strftime("%Y/%m/%d-%H:%M")
        except:
            record["formatted_time"] = str(record.get("rescued_time", ""))

    return templates.TemplateResponse("rescuer.html", {
        "request": request,
        "reports": reports,
        "rescued_reports": rescued_reports,
        "city": city,
        "district": district
    })

@app.post("/update_status/{report_id}")
async def update_status(report_id: str, request: Request):
    nickname = request.session.get("nickname")
    report = await db.reports.find_one({"_id": ObjectId(report_id)})

    if report and nickname:
        # 將原始報告標記為已救援（保留於 reports)
        await db.reports.update_one(
            {"_id": ObjectId(report_id)},
            {"$set": {"rescue_status": "已救援"}}
        )
        # 記錄這筆成為此會員的歷史救援
        rescue_record = {
            "rescued_by": nickname,
            "rescued_time": datetime.now(),
            "location": report.get("location"),
            "status": report.get("status"),
            "description": report.get("description"),
            "cat_photo": report.get("cat_photo"),
            "env_photo": report.get("env_photo"),
            "time": report.get("time"),
        }
        await db.rescued_history.insert_one(rescue_record)
        return JSONResponse({"success": True})
    return JSONResponse({"success": False}, status_code=404)
