import sqlite3
from datetime import datetime, date, timedelta
from werkzeug.security import generate_password_hash
from models import get_db, init_db, update_user_streak
from achievements_engine import check_and_unlock_achievements

def seed_demo_data():
    init_db()
    conn = get_db()
    cursor = conn.cursor()
    
    # Check if demo_student already exists
    cursor.execute("SELECT id FROM users WHERE username = 'demo_student'")
    existing = cursor.fetchone()
    if existing:
        user_id = existing['id']
        print(f"Demo student already exists with ID: {user_id}")
        conn.close()
        # Still evaluate achievements
        check_and_unlock_achievements(user_id)
        return user_id
        
    # Create demo student
    password_hash = generate_password_hash('demo123')
    cursor.execute('''
    INSERT INTO users (name, username, email, password_hash, college, course, year_of_study)
    VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (
        'Arun Kumar',
        'demo_student',
        'arun.kumar@studymate.edu',
        password_hash,
        'National Institute of Technology',
        'B.Sc Information Technology',
        '3rd Year'
    ))
    user_id = cursor.lastrowid
    
    today = date.today()
    today_str = today.isoformat()
    tomorrow_str = (today + timedelta(days=1)).isoformat()
    
    # 1. Add 4 subjects
    subjects_data = [
        ('Python Programming', 'CS301', 'Mr. Kumar', 20, 15, (today + timedelta(days=25)).isoformat(), '#4F46E5'),
        ('Database Management Systems', 'CS302', 'Dr. Ananya Sharma', 16, 10, (today + timedelta(days=30)).isoformat(), '#0284C7'),
        ('Operating Systems', 'CS303', 'Prof. Rajesh Verma', 18, 8, (today + timedelta(days=35)).isoformat(), '#7C3AED'),
        ('Web Development & UI', 'CS304', 'Mrs. Priya Sundar', 14, 11, (today + timedelta(days=20)).isoformat(), '#059669')
    ]
    
    subject_ids = {}
    for name, code, faculty, total, comp, target, color in subjects_data:
        cursor.execute('''
        INSERT INTO subjects (user_id, name, code, faculty, total_topics, completed_topics, target_date, color)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (user_id, name, code, faculty, total, comp, target, color))
        subject_ids[code] = cursor.lastrowid
        
    # 2. Add Study Tasks
    tasks_data = [
        (subject_ids['CS301'], 'Complete Python OOP inheritance & polymorphism exercises', today_str, 'High', 1, today_str + ' 10:30:00'),
        (subject_ids['CS302'], 'Study DBMS B+ Trees, Indexing & Hashing concepts', today_str, 'High', 1, today_str + ' 12:45:00'),
        (subject_ids['CS301'], 'Practice SQL complex joins & nested subqueries', today_str, 'Medium', 0, None),
        (subject_ids['CS303'], 'Revise OS CPU Scheduling Algorithms (SJF, Round Robin)', tomorrow_str, 'Medium', 0, None),
        (subject_ids['CS304'], 'Design responsive dashboard UI using CSS Flex & Grid', tomorrow_str, 'Low', 0, None)
    ]
    
    for sub_id, title, due, prio, comp, comp_time in tasks_data:
        cursor.execute('''
        INSERT INTO tasks (user_id, subject_id, title, due_date, priority, is_completed, completed_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (user_id, sub_id, title, due, prio, comp, comp_time))
        
    # 3. Add Study Plans
    plans_data = [
        (subject_ids['CS301'], 'Object-Oriented Design & Dunder Methods', today_str, '16:00', '17:30', 'High', 'Focus on __str__, __repr__, and operator overloading.'),
        (subject_ids['CS302'], 'Normalization (1NF to BCNF Decomposition)', today_str, '18:00', '19:30', 'High', 'Solve 5 functional dependency numerical problems.'),
        (subject_ids['CS303'], 'Deadlock Detection & Banker\'s Algorithm', tomorrow_str, '10:00', '11:30', 'Medium', 'Review safe state matrices and resource allocation graphs.'),
        (subject_ids['CS304'], 'CSS Grid Masterclass & Responsive Cards', tomorrow_str, '14:00', '15:30', 'Low', 'Implement CSS auto-fit minmax grid layout.')
    ]
    
    for sub_id, topic, pdate, start, end, prio, notes in plans_data:
        cursor.execute('''
        INSERT INTO study_plans (user_id, subject_id, topic, plan_date, start_time, end_time, priority, notes)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (user_id, sub_id, topic, pdate, start, end, prio, notes))
        
    # 4. Add Exams
    exams_data = [
        ('Python Programming Mid-Semester Exam', subject_ids['CS301'], (today + timedelta(days=8)).isoformat(), '10:00 AM', 'OOP, Decorators, Generators, File I/O, SQLite Integration', 'Bring calculator and college ID card. Room 302.'),
        ('DBMS University Semester Final', subject_ids['CS302'], (today + timedelta(days=16)).isoformat(), '02:00 PM', 'ER Diagrams, Relational Algebra, SQL, Normalization, ACID Transactions', 'Exam duration: 3 Hours. Total 100 marks.')
    ]
    
    for name, sub_id, edate, etime, topics, notes in exams_data:
        cursor.execute('''
        INSERT INTO exams (user_id, name, subject_id, exam_date, exam_time, important_topics, notes)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (user_id, name, sub_id, edate, etime, topics, notes))
        
    # 5. Add Goals
    goals_data = [
        ('Complete Python Programming Syllabus', 100, 75, (today + timedelta(days=20)).isoformat(), 'Academic', 0),
        ('Solve 50 SQL Coding Challenges', 100, 76, (today + timedelta(days=14)).isoformat(), 'Skills', 0),
        ('Maintain 3.5+ Hours Daily Study Habit', 100, 100, (today + timedelta(days=30)).isoformat(), 'Habit', 1)
    ]
    
    for title, target, curr, dline, cat, comp in goals_data:
        cursor.execute('''
        INSERT INTO goals (user_id, title, target_percent, current_percent, deadline, category, is_completed)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (user_id, title, target, curr, dline, cat, comp))
        
    # 6. Add Past 7 Days Study Sessions
    past_sessions = [
        (subject_ids['CS301'], (today - timedelta(days=6)).isoformat(), 120, 'Pomodoro', 'Completed chapter 1 & 2 basics'),
        (subject_ids['CS302'], (today - timedelta(days=5)).isoformat(), 150, 'Standard', 'ER modeling diagrams practice'),
        (subject_ids['CS303'], (today - timedelta(days=4)).isoformat(), 90, 'Pomodoro', 'Process synchronization concepts'),
        (subject_ids['CS304'], (today - timedelta(days=3)).isoformat(), 180, 'Standard', 'Built portfolio responsive layout'),
        (subject_ids['CS301'], (today - timedelta(days=2)).isoformat(), 210, 'Pomodoro', 'Deep dive into Python decorators & generators'),
        (subject_ids['CS302'], (today - timedelta(days=1)).isoformat(), 160, 'Pomodoro', 'Relational calculus and algebra query practice'),
        (subject_ids['CS301'], today_str, 135, 'Pomodoro', 'Finished OOP inheritance module')
    ]
    
    for sub_id, sdate, dur, stype, notes in past_sessions:
        cursor.execute('''
        INSERT INTO study_sessions (user_id, subject_id, session_date, duration_minutes, session_type, notes)
        VALUES (?, ?, ?, ?, ?, ?)
        ''', (user_id, sub_id, sdate, dur, stype, notes))
        
    # 7. Set Streak
    cursor.execute('''
    INSERT INTO streaks (user_id, current_streak, best_streak, last_activity_date)
    VALUES (?, 7, 14, ?)
    ''', (user_id, today_str))
    
    conn.commit()
    conn.close()
    
    # Evaluate and unlock achievements
    check_and_unlock_achievements(user_id)
    print("Demo data seeded successfully for demo_student!")
    return user_id

if __name__ == '__main__':
    seed_demo_data()
