# 🎓 E-Learning Platform (Django LMS)

A modern, full-featured Learning Management System (LMS) built with **Django 6** and styled with **Tailwind CSS**. It features dark/light mode with circular view transitions, role-based dashboards (Students & Instructors), multi-format lessons (YouTube/uploaded video, text, images, attachments), progress tracking, and automated shareable certificate generation.

---

## 🌟 Key Features & Screenshots

- **Role-Based Experience:** Custom profiles and dashboards for **Students** and **Instructors**, with an admin-approved instructor upgrade workflow.
- **Curriculum Builder:** Modular course architecture with rich-text overviews and polymorphic lesson items (`Video`, `Text`, `Image`, `File`).
- **Interactive Video Player:** Supports embedded YouTube videos or custom uploaded video playback with speed controls.
- **Student Progress & Certificates:** Real-time circular progress tracking and personalized, high-resolution PNG certificate generation upon 100% course completion.
- **Modern UI/UX:** Responsive dark-first theme with smooth view transitions.
- **Secure Authentication:** Standard credentials, and Google OAuth2 social login via `django-allauth`.

---

## 💡 Engineering Challenges & Solutions


---

## 🏗️ Architectural Decisions

---

## 🛡️ Security & Performance Highlights

---

## 🔮 Roadmap & Planned Features

---

## 🚀 Getting Started

You can run this project using **Docker (Recommended - Fastest)** or manually with a **Python Virtual Environment**.

---

### Option A: Run with Docker (Recommended) 🐳

This method requires **no manual database installation** — Docker will set up both Django and PostgreSQL automatically.

#### 1. Prerequisites
- Install [Docker Desktop](https://www.docker.com/products/docker-desktop/) and ensure it is running.

#### 2. Clone the Repository
```bash
git clone https://github.com/kasabian22/Courses_Platform.git
cd Courses_Platform
```

#### 3. Setup Environment Variables
Copy `.env.example` to create your local `.env` file:
- **macOS / Linux**:
  ```bash
  cp .env.example .env
  ```
- **Windows (Command Prompt / PowerShell)**:
  ```powershell
  copy .env.example .env
  ```

#### 4. Build and Start the Application
```bash
docker compose up --build
```
Once the containers finish building, open your browser and navigate to:
👉 **[http://localhost:8000](http://localhost:8000)**

#### 5. Create an Admin Account (Superuser)
In a new terminal window, run:
```bash
docker compose exec web python manage.py createsuperuser
```
Follow the prompts to set your admin username, email, and password. You can then log into the admin dashboard at:
👉 **[http://localhost:8000/admin/](http://localhost:8000/admin/)**

---

### Option B: Run Locally with Python Virtual Environment 🐍

Use this method if you prefer running Python directly on your system without Docker.

#### 1. Prerequisites
- **Python 3.12+**
- **PostgreSQL** running locally on port `5432` with a database named `elearning_db`.

#### 2. Clone and Setup Environment
```bash
git clone https://github.com/kasabian22/Courses_Platform.git
cd Courses_Platform
```

#### 3. Create and Activate a Virtual Environment
- **macOS / Linux**:
  ```bash
  python3 -m venv venv
  source venv/bin/activate
  ```
- **Windows**:
  ```powershell
  python -m venv venv
  venv\Scripts\activate
  ```

#### 4. Install Dependencies
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

#### 5. Configure `.env`
Copy `.env.example` to `.env`:
```powershell
copy .env.example .env
```
Open `.env` and set `DB_HOST=localhost`, and enter your local PostgreSQL `DB_USER` and `DB_PASSWORD`.

#### 6. Apply Database Migrations
```bash
python manage.py migrate
```

#### 7. Create Superuser (Admin)
```bash
python manage.py createsuperuser
```

#### 8. Start the Development Server
```bash
python manage.py runserver
```
Visit **[http://127.0.0.1:8000](http://127.0.0.1:8000)** in your browser.

---

## 🛠️ Helpful Commands

| Action | Docker Command | Local Command |
|---|---|---|
| **Stop Server** | `docker compose down` | `Ctrl + C` |
| **Run Migrations** | `docker compose exec web python manage.py migrate` | `python manage.py migrate` |
| **Django Shell** | `docker compose exec web python manage.py shell` | `python manage.py shell` |
| **View Logs** | `docker compose logs -f web` | View terminal output |