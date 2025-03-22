import os
from dotenv import load_dotenv

# تحميل المتغيرات من ملف .env
load_dotenv(.env)

# توكن بوت تليجرام
TOKEN = os.getenv("8007030873:AAGrEqAR9QDn_MqjSCQXmIUxIoFp-wEz1Dw")

# معرف المسؤول
ADMIN_ID = int(os.getenv("@Mtgcoin2030"))

# إعدادات قاعدة البيانات MySQL
DB_CONFIG = {
    "host": os.getenv("localhost"),
    "user": os.getenv("usdtppst_Boot"),
    "password": os.getenv("Medoarab1@"),
    "database": os.getenv("usdtppst_Boot")
}