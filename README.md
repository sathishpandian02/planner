# StudyMate – Student Study Planner & Academic Achievement System

A full-stack, feature-rich, and modern **Student Study Planner and Academic Achievement Tracking System** built with **Python (Flask)**, **SQLite**, **HTML5**, **CSS3**, and **JavaScript (Chart.js & Web Audio)**.

---

## 🌟 Key Features

1. **Student Authentication & User Isolation**
   - Secure Student Registration & Login with Werkzeug password hashing.
   - Per-user data isolation ensures each student accesses only their academic plans and progress.
   - Pre-seeded Demo Student account for instant presentations.

2. **Personalized Dynamic Dashboard**
   - Greeting banner with dynamically rotating motivational quotes.
   - Real-time stat cards: Today's Tasks, Completed, Pending, Study Hours, Active Streaks, and Overall Progress composite score.
   - Dynamic In-App Reminders (upcoming exams within 7 days, pending tasks, scheduled study sessions).
   - Quick-access to today's study schedule and to-dos.

3. **Subject & Syllabus Management**
   - Course tracking (Subject Name, Code, Faculty Instructor, Target Date, Color Themes).
   - Topic progress tracking with visual completion bars.

4. **Hourly Study Planner & Timetable**
   - Daily schedule manager with priority flags (High, Medium, Low).
   - Start and end time slots with actionable study objectives.

5. **Daily Tasks & To-Do Checklist**
   - Interactive checkbox toggle with AJAX completion and audio chime feedback.
   - Multi-criteria filtering (Subject, Priority, Status, Date) and real-time search.
   - Automatic streak update and achievement evaluation upon completion.

6. **Pomodoro & Focus Study Timer**
   - 25-minute Pomodoro focus timer & 5-minute break mode.
   - Subject tagging and focus notes logging.
   - Automatic recording of study sessions into SQLite database.

7. **Exams & Academic Deadlines Planner**
   - Upcoming exams timeline with days-remaining countdown badges.
   - Key topics and preparation room notes.

8. **Academic Goals Tracker**
   - Target vs Current percentage tracker with progress milestones.
   - Categorization by Academic, Coding Skills, Study Habits, and Projects.

9. **Progress Analytics & Chart.js Visualizations**
   - Daily, Weekly, and Monthly task completion ratios.
   - Interactive Bar Chart showing weekly study hours distribution (Monday – Sunday).
   - Horizontal Bar Chart showing subject syllabus completion percentages.

10. **Gamified Achievement System**
    - 12 unlockable achievement badges (e.g. *First Task Completed*, *7-Day Streak*, *10 Study Hours*, *Goal Crusher*, *Subject Mastery*).
    - Unlocked vs locked visual states, unlock timestamps, and cumulative XP points.

11. **Interactive Monthly Calendar**
    - Color-coded indicators for study sessions, exams, to-do deadlines, and academic goals.
    - Clickable day inspector modal to view all daily events.

12. **Student Profile & Security**
    - Student academic information editor (College, Degree, Year of Study).
    - Lifetime learning record stats and password management.

---

## 🛠️ Technology Stack

- **Backend**: Python 3.11+ / 3.12+, Flask, Werkzeug
- **Database**: SQLite3 (relational schema with foreign keys)
- **Frontend**: HTML5, Vanilla CSS3 (Custom bright modern design system), JavaScript (ES6)
- **Visuals & Charts**: Chart.js (CDN)
- **Audio Feedback**: Web Audio API (Synthesized completion sounds)

---

## 📁 Project Structure

```
StudyMate/
│
├── app.py                     # Main Flask routes, session auth & JSON API endpoints
├── models.py                  # SQLite database schema, connections & streak engine
├── achievements_engine.py     # Real-time achievement badge evaluation engine
├── seed_demo.py               # Demo account population script
├── requirements.txt           # Python dependencies
├── database.db                # SQLite database (auto-created on startup)
│
├── static/
│   ├── css/
│   │   └── style.css          # Bright modern student theme & responsive CSS
│   └── js/
│       └── main.js            # Timer, calendar, audio synthesizer & AJAX handlers
│
├── templates/
│   ├── base.html              # Core navigation layout, topbar, alerts & sidebar
│   ├── login.html             # Clean login page with 1-click demo fill
│   ├── register.html          # Student registration page
│   ├── dashboard.html         # Comprehensive student dashboard
│   ├── subjects.html          # Subjects & syllabus progress manager
│   ├── planner.html           # Hourly study timetable planner
│   ├── tasks.html             # Daily to-do list with filters & search
│   ├── timer.html             # Pomodoro focus timer with session logger
│   ├── exams.html             # Exams countdown & deadlines
│   ├── goals.html             # Academic target goals tracker
│   ├── progress.html          # Detailed charts & analytics
│   ├── achievements.html      # Gamified badges & XP rewards
│   ├── calendar.html          # Interactive monthly calendar view
│   └── profile.html           # Student profile & account settings
│
└── README.md
```

---

## 🚀 Installation & Running

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Run the Application
```bash
python app.py
```

### 3. Open in Browser
Navigate to:
```
http://127.0.0.1:5000
```

---

## 🔑 Demo Account Credentials

For quick presentation and evaluation, use the preloaded demo account:

- **Username**: `demo_student`
- **Password**: `demo123`

*(You can also click the "⚡ Fill Demo Student Credentials" button on the login screen for instant sign-in).*
