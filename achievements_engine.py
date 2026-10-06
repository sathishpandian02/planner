from models import get_db, get_user_streak

def check_and_unlock_achievements(user_id):
    """
    Evaluates all achievement criteria for the user.
    Unlocks eligible achievements and returns a list of newly unlocked achievements.
    """
    conn = get_db()
    cursor = conn.cursor()
    
    # Get all already unlocked achievement keys for this user
    cursor.execute('''
    SELECT a.key 
    FROM achievements a
    JOIN user_achievements ua ON a.id = ua.achievement_id
    WHERE ua.user_id = ?
    ''', (user_id,))
    unlocked_keys = {row['key'] for row in cursor.fetchall()}
    
    # 1. Total completed tasks
    cursor.execute("SELECT COUNT(*) as cnt FROM tasks WHERE user_id = ? AND is_completed = 1", (user_id,))
    completed_tasks_count = cursor.fetchone()['cnt']
    
    # 2. Total study minutes
    cursor.execute("SELECT SUM(duration_minutes) as total_min FROM study_sessions WHERE user_id = ?", (user_id,))
    res_min = cursor.fetchone()['total_min']
    total_study_hours = (res_min or 0) / 60.0
    
    # 3. Completed goals
    cursor.execute("SELECT COUNT(*) as cnt FROM goals WHERE user_id = ? AND (current_percent >= target_percent OR is_completed = 1)", (user_id,))
    completed_goals_count = cursor.fetchone()['cnt']
    
    # 4. Streaks
    streak_data = get_user_streak(user_id)
    best_streak = streak_data['best_streak']
    
    # 5. Subjects with 100% completion
    cursor.execute("SELECT COUNT(*) as cnt FROM subjects WHERE user_id = ? AND total_topics > 0 AND completed_topics >= total_topics", (user_id,))
    completed_subjects_count = cursor.fetchone()['cnt']
    
    # 6. Total study plans
    cursor.execute("SELECT COUNT(*) as cnt FROM study_plans WHERE user_id = ?", (user_id,))
    total_plans_count = cursor.fetchone()['cnt']
    
    # 7. Weekly task completion %
    cursor.execute('''
    SELECT 
        COUNT(*) as total_w,
        SUM(CASE WHEN is_completed = 1 THEN 1 ELSE 0 END) as comp_w
    FROM tasks
    WHERE user_id = ? AND due_date >= date('now', '-7 days')
    ''', (user_id,))
    weekly_row = cursor.fetchone()
    total_w = weekly_row['total_w'] or 0
    comp_w = weekly_row['comp_w'] or 0
    weekly_rate = (comp_w / total_w * 100) if total_w >= 5 else 0
    
    # Evaluation map
    criteria = {
        'first_task': completed_tasks_count >= 1,
        'streak_3': best_streak >= 3,
        'streak_7': best_streak >= 7,
        'streak_30': best_streak >= 30,
        'study_10_hours': total_study_hours >= 10,
        'study_50_hours': total_study_hours >= 50,
        'first_goal': completed_goals_count >= 1,
        'tasks_10': completed_tasks_count >= 10,
        'tasks_50': completed_tasks_count >= 50,
        'subject_master': completed_subjects_count >= 1,
        'planner_pro': total_plans_count >= 5,
        'weekly_perfection': weekly_rate >= 90
    }
    
    newly_unlocked = []
    
    for key, condition in criteria.items():
        if condition and key not in unlocked_keys:
            cursor.execute("SELECT id, title, icon, points FROM achievements WHERE key = ?", (key,))
            ach = cursor.fetchone()
            if ach:
                cursor.execute('''
                INSERT OR IGNORE INTO user_achievements (user_id, achievement_id)
                VALUES (?, ?)
                ''', (user_id, ach['id']))
                newly_unlocked.append({
                    'title': ach['title'],
                    'icon': ach['icon'],
                    'points': ach['points']
                })
                
    conn.commit()
    conn.close()
    return newly_unlocked
