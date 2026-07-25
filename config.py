import os
from dotenv import load_dotenv

# Load environment variables from .env file (for local development)
load_dotenv()

# Base URL for Vignan ECAP (Webpros)
BASE_URL = os.getenv("BASE_URL", "https://webprosindia.com/vignanit/")
LOGIN_URL = BASE_URL + "Login.aspx"
ATTENDANCE_URL = BASE_URL + "Academics/StudentAttendanceByDay.aspx"

# Bot Token - Load strictly from environment variable for security
BOT_TOKEN = os.getenv("BOT_TOKEN")

