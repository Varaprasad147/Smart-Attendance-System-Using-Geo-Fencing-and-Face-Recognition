<<<<<<< HEAD
# Smart Attendance System Using Geo Fencing and Face Recognition

A Django-based attendance system with geofencing and facial recognition.

## Features

- Multi-role system (Super-Admin, Admin, Student)
- GPS-based geofencing
- AI facial recognition
- Real-time analytics
- JWT authentication

## Setup

1. Install dependencies: `pip install -r requirements.txt`
2. Configure MySQL database
3. Run migrations: `python manage.py migrate`
4. Create super admin: `python manage.py seed_superadmin`
5. Start services: Django, FastAPI face service, Redis, Celery

## Usage

- Super-Admin: `/super/dashboard`
- Admin: `/admin/dashboard`
- Student: `/student/dashboard`
=======
Smart Attendance System Using Geo-Fencing and Face Recognition
📌 Overview
The Smart Attendance System combines Face Recognition and Geo-Fencing to automate secure, location-based attendance marking for students and staff.
This system prevents proxy attendance, ensures authenticity, and provides a user-friendly admin dashboard for monitoring attendance in real time.

# ✨ Key Features
## 🔐 Face Recognition
Detects and recognizes faces using OpenCV and dlib/face_recognition.

Ensures only registered individuals can mark attendance.

High accuracy even in different lighting conditions.

📍 Geo-Fencing Based Validation
Attendance is allowed only when the user is within a predefined radius (e.g., 100m) of the institution.

Uses device GPS (browser/Android API) for location verification.

Prevents fake or proxy attendance from outside locations.

🖥️ Admin Dashboard
View daily/weekly/monthly attendance.

Add/manage students and staff.

Generate attendance reports in CSV/PDF.

Monitor geo-location logs and face recognition logs.

👨‍💻 User Portal
Students can view their attendance history.

Staff can verify class attendance.

Secure login for both students and admins.

🧰 Tech Stack
Backend
Python 3.x

Django Framework

SQLite/MySQL

Frontend
HTML5, CSS3

JavaScript

Bootstrap

AI Modules
OpenCV

face_recognition library

dlib

Location Services
Browser Geolocation API

⚙️ Installation Guide:
 1️⃣ Clone the Repository:
    git clone https://github.com/your-username/Smart-Attendance-System-Using-Geo-Fencing-and-Face-Recognition.git
    cd Smart-Attendance-System-Using-Geo-Fencing-and-Face-Recognition
 2️⃣ Create Virtual Environment:
    python -m venv venv
    venv/Scripts/activate  (Windows)
    source venv/bin/activate (Linux/Mac)
 3️⃣ Install Dependencies:
    pip install -r requirements.txt
 4️⃣ Apply Migrations:
    python manage.py makemigrations
    python manage.py migrate
  5️⃣ Run the Server:
    python manage.py runserver

🧪 How Face Recognition Works
Face encodings are generated during registration.

OpenCV captures a real-time frame from the camera.

The system compares live encodings with stored encodings.

If the match is above threshold → attendance is marked.

📍 How Geo-Fencing Works
User's location is captured using browser GPS.

Distance is calculated using Haversine formula.

📑 Future Enhancements
Mobile App (Flutter/React Native)

QR Code + Face recognition hybrid system

OTP verification for multi-factor attendance

AI-based spoof detection

🤝 Contributions
Pull requests are welcome.
For major changes, open an issue first to discuss the changes.

📄 License
This project is licensed under the MIT License.

👨‍🎓 Author
Nagalla Vara Prasad
B.Tech CSE (AI & ML) – GMRIT
Django | AI/ML | Computer Vision





  













>>>>>>> c4ac63b70c67d950d71d5dd3b1e3b02464ef52a3
