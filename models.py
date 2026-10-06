import sqlite3
import os
from datetime import datetime, date, timedelta
from werkzeug.security import generate_password_hash, check_password_hash

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'database.db')

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def init_db():
    conn = get_db()
    cursor = conn.cursor()
    
    # 1. Users table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        username TEXT UNIQUE NOT NULL,
        email TEXT NOT NULL,
        password_hash TEXT NOT NULL,
        college TEXT,
        course TEXT,
        year_of_study TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # 2. Subjects table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS subjects (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        name TEXT NOT NULL,
        code TEXT,
        faculty TEXT,
        total_topics INTEGER DEFAULT 10,
        completed_topics INTEGER DEFAULT 0,
        target_date DATE,
        color TEXT DEFAULT '#4F46E5',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
    )
    ''')
    
    # 3. Study Plans table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS study_plans (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        subject_id INTEGER,
        topic TEXT NOT NULL,
        plan_date DATE NOT NULL,
        start_time TEXT,
        end_time TEXT,
        priority TEXT DEFAULT 'Medium',
        notes TEXT,
        is_completed INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
        FOREIGN KEY (subject_id) REFERENCES subjects(id) ON DELETE SET NULL
    )
    ''')
    
    # 4. Tasks table (Daily To-Do)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS tasks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        subject_id INTEGER,
        title TEXT NOT NULL,
        due_date DATE NOT NULL,
        priority TEXT DEFAULT 'Medium',
        is_completed INTEGER DEFAULT 0,
        completed_at TIMESTAMP,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
        FOREIGN KEY (subject_id) REFERENCES subjects(id) ON DELETE SET NULL
    )
    ''')
    
    # 5. Study Sessions table (Pomodoro / Study Timer logs)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS study_sessions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        subject_id INTEGER,
        session_date DATE NOT NULL,
        duration_minutes INTEGER NOT NULL,
        session_type TEXT DEFAULT 'Pomodoro',
        notes TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
        FOREIGN KEY (subject_id) REFERENCES subjects(id) ON DELETE SET NULL
    )
    ''')
    
    # 6. Exams table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS exams (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        name TEXT NOT NULL,
        subject_id INTEGER,
        exam_date DATE NOT NULL,
        exam_time TEXT,
        important_topics TEXT,
        notes TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
        FOREIGN KEY (subject_id) REFERENCES subjects(id) ON DELETE SET NULL
    )
    ''')
    
    # 7. Goals table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS goals (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        title TEXT NOT NULL,
        target_percent INTEGER DEFAULT 100,
        current_percent INTEGER DEFAULT 0,
        deadline DATE,
        category TEXT DEFAULT 'Academic',
        is_completed INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
    )
    ''')
    
    # 8. Master Achievements table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS achievements (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        key TEXT UNIQUE NOT NULL,
        title TEXT NOT NULL,
        description TEXT NOT NULL,
        icon TEXT NOT NULL,
        category TEXT NOT NULL,
        points INTEGER DEFAULT 50
    )
    ''')
    
    # 9. User Unlocked Achievements table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS user_achievements (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        achievement_id INTEGER NOT NULL,
        unlocked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(user_id, achievement_id),
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
        FOREIGN KEY (achievement_id) REFERENCES achievements(id) ON DELETE CASCADE
    )
    ''')
    
    # 10. Streaks table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS streaks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER UNIQUE NOT NULL,
        current_streak INTEGER DEFAULT 0,
        best_streak INTEGER DEFAULT 0,
        last_activity_date DATE,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
    )
    ''')
    
    # Seed default achievements
    default_achievements = [
        ('first_task', 'First Task Completed', 'Completed your very first study task in StudyMate.', '🏆', 'Tasks', 20),
        ('streak_3', '3-Day Study Streak', 'Maintained an active study habit for 3 consecutive days.', '🔥', 'Streaks', 30),
        ('streak_7', '7-Day Study Champion', 'Studied for 7 continuous days without breaking streak.', '⚡', 'Streaks', 60),
        ('streak_30', '30-Day Master of Focus', 'Unstoppable consistency! 30-day continuous study streak.', '🚀', 'Streaks', 200),
        ('study_10_hours', '10 Study Hours', 'Dedicated 10 total hours of deep focused study sessions.', '📚', 'Timer', 50),
        ('study_50_hours', '50 Study Hours Prodigy', 'Logged over 50 hours of productive study time.', '👑', 'Timer', 150),
        ('first_goal', 'Goal Crusher', 'Completed your first academic target goal at 100%.', '🎯', 'Goals', 40),
        ('tasks_10', 'Task Master (10 Tasks)', 'Successfully accomplished 10 study to-do tasks.', '⭐', 'Tasks', 40),
        ('tasks_50', 'Centurion of Progress', 'Completed 50 study tasks with precision.', '💎', 'Tasks', 100),
        ('subject_master', 'Subject Mastery', 'Completed 100% of all topics in any subject.', '🎓', 'Subjects', 75),
        ('planner_pro', 'Master Planner', 'Created 5 or more organized study plan schedules.', '📅', 'Planner', 30),
        ('weekly_perfection', 'High Achiever', 'Achieved over 90% task completion in a single week.', '🏅', 'Overall', 80)
    ]
    
    for key, title, desc, icon, cat, pts in default_achievements:
        cursor.execute('''
        INSERT OR IGNORE INTO achievements (key, title, description, icon, category, points)
        VALUES (?, ?, ?, ?, ?, ?)
        ''', (key, title, desc, icon, cat, pts))
        
    conn.commit()
    conn.close()

def update_user_streak(user_id, conn=None):
    """Updates the user's study streak when they complete a task or study session."""
    should_close = False
    if conn is None:
        conn = get_db()
        should_close = True
        
    cursor = conn.cursor()
    today = date.today()
    today_str = today.isoformat()
    yesterday_str = (today - timedelta(days=1)).isoformat()
    
    cursor.execute("SELECT current_streak, best_streak, last_activity_date FROM streaks WHERE user_id = ?", (user_id,))
    streak_row = cursor.fetchone()
    
    if not streak_row:
        cursor.execute('''
        INSERT INTO streaks (user_id, current_streak, best_streak, last_activity_date)
        VALUES (?, 1, 1, ?)
        ''', (user_id, today_str))
    else:
        curr = streak_row['current_streak']
        best = streak_row['best_streak']
        last_date = streak_row['last_activity_date']
        
        if last_date == today_str:
            # Already active today, streak remains current
            pass
        elif last_date == yesterday_str:
            # Continuing consecutive streak
            new_curr = curr + 1
            new_best = max(best, new_curr)
            cursor.execute('''
            UPDATE streaks SET current_streak = ?, best_streak = ?, last_activity_date = ?
            WHERE user_id = ?
            ''', (new_curr, new_best, today_str, user_id))
        else:
            # Streak was broken, restart at 1
            cursor.execute('''
            UPDATE streaks SET current_streak = 1, best_streak = ?, last_activity_date = ?
            WHERE user_id = ?
            ''', (max(best, 1), today_str, user_id))
            
    conn.commit()
    if should_close:
        conn.close()

def get_user_streak(user_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT current_streak, best_streak, last_activity_date FROM streaks WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()
    
    if not row:
        return {'current_streak': 0, 'best_streak': 0, 'is_active_today': False}
        
    today_str = date.today().isoformat()
    yesterday_str = (date.today() - timedelta(days=1)).isoformat()
    last_date = row['last_activity_date']
    
    # If last activity was before yesterday, streak is currently 0 until they do something today
    if last_date and last_date != today_str and last_date != yesterday_str:
        current = 0
    else:
        current = row['current_streak']
        
    return {
        'current_streak': current,
        'best_streak': row['best_streak'],
        'is_active_today': (last_date == today_str)
    }

def get_motivational_quote():
    quotes = [
        ("Small progress every day leads to big results.", "Anonymous"),
        ("Your future is created by what you do today, not tomorrow.", "Robert Kiyosaki"),
        ("One chapter at a time. Keep going!", "StudyMate"),
        ("Success doesn't come to you, you go to it.", "Marva Collins"),
        ("The secret of getting ahead is getting started.", "Mark Twain"),
        ("Focus on progress, not perfection.", "Bill Phillips"),
        ("Believe you can and you're halfway there.", "Theodore Roosevelt"),
        ("Discipline is choosing between what you want now and what you want most.", "Abraham Lincoln")
    ]
    day_index = (datetime.now().day + datetime.now().month) % len(quotes)
    return quotes[day_index]
