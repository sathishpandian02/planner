from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
import functools
from datetime import datetime, date, timedelta
from werkzeug.security import generate_password_hash, check_password_hash
from models import get_db, init_db, update_user_streak, get_user_streak, get_motivational_quote
from achievements_engine import check_and_unlock_achievements
import seed_demo

app = Flask(__name__)
app.secret_key = 'studymate_academic_secret_key_2026_super_secure'

def login_required(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if 'user_id' not in session:
            flash('Please log in to access your StudyMate workspace.', 'warning')
            return redirect(url_for('login'))
        return view(**kwargs)
    return wrapped_view

@app.before_request
def ensure_setup():
    # Store current user in g or session verification
    pass

@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
        
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        
        if not username or not password:
            flash('Please fill in both username and password.', 'danger')
            return render_template('login.html', username=username)
            
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
        user = cursor.fetchone()
        conn.close()
        
        if user and check_password_hash(user['password_hash'], password):
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['name'] = user['name']
            flash(f'Welcome back, {user["name"]}! Let\'s have a productive study session.', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password. Please try again.', 'danger')
            return render_template('login.html', username=username)
            
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
        
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '').strip()
        college = request.form.get('college', '').strip()
        course = request.form.get('course', '').strip()
        year_of_study = request.form.get('year_of_study', '').strip()
        
        if not name or not username or not email or not password:
            flash('Name, Username, Email, and Password are required fields.', 'danger')
            return render_template('register.html')
            
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
        if cursor.fetchone():
            conn.close()
            flash('Username is already taken. Please choose another username.', 'danger')
            return render_template('register.html')
            
        password_hash = generate_password_hash(password)
        try:
            cursor.execute('''
            INSERT INTO users (name, username, email, password_hash, college, course, year_of_study)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (name, username, email, password_hash, college, course, year_of_study))
            user_id = cursor.lastrowid
            
            # Initialize streak entry
            cursor.execute('''
            INSERT INTO streaks (user_id, current_streak, best_streak)
            VALUES (?, 0, 0)
            ''', (user_id,))
            conn.commit()
            
            # Auto-login newly registered user
            session['user_id'] = user_id
            session['username'] = username
            session['name'] = name
            
            # Auto-award potential starter achievements
            check_and_unlock_achievements(user_id)
            
            flash('Account created successfully! Welcome to StudyMate.', 'success')
            return redirect(url_for('dashboard'))
        except Exception as e:
            conn.rollback()
            flash(f'An error occurred during registration: {str(e)}', 'danger')
            return render_template('register.html')
        finally:
            conn.close()
            
    return render_template('register.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out safely. See you soon!', 'info')
    return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def dashboard():
    user_id = session['user_id']
    conn = get_db()
    cursor = conn.cursor()
    today_str = date.today().isoformat()
    
    # User info
    cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    user = cursor.fetchone()
    
    # 1. Today's Tasks calculations
    cursor.execute("SELECT COUNT(*) as total FROM tasks WHERE user_id = ? AND due_date = ?", (user_id, today_str))
    today_total = cursor.fetchone()['total'] or 0
    
    cursor.execute("SELECT COUNT(*) as comp FROM tasks WHERE user_id = ? AND due_date = ? AND is_completed = 1", (user_id, today_str))
    today_completed = cursor.fetchone()['comp'] or 0
    
    today_pending = today_total - today_completed
    daily_progress_pct = round((today_completed / today_total * 100)) if today_total > 0 else 0
    
    # 2. Total Study Hours today and overall
    cursor.execute("SELECT SUM(duration_minutes) as mins FROM study_sessions WHERE user_id = ? AND session_date = ?", (user_id, today_str))
    today_mins = cursor.fetchone()['mins'] or 0
    today_study_hours = round(today_mins / 60.0, 1)
    
    cursor.execute("SELECT SUM(duration_minutes) as mins FROM study_sessions WHERE user_id = ?", (user_id,))
    total_mins = cursor.fetchone()['mins'] or 0
    total_study_hours = round(total_mins / 60.0, 1)
    
    # 3. Streak
    streak_info = get_user_streak(user_id)
    
    # 4. Overall Progress Calculation
    # Balanced composite: (Tasks Completion Rate * 0.4) + (Subjects Completion Rate * 0.4) + (Goals Completion Rate * 0.2)
    cursor.execute("SELECT COUNT(*) as all_tasks, SUM(CASE WHEN is_completed = 1 THEN 1 ELSE 0 END) as comp_tasks FROM tasks WHERE user_id = ?", (user_id,))
    t_row = cursor.fetchone()
    all_tasks = t_row['all_tasks'] or 0
    comp_tasks = t_row['comp_tasks'] or 0
    task_rate = (comp_tasks / all_tasks * 100) if all_tasks > 0 else 0
    
    cursor.execute("SELECT SUM(total_topics) as tot_top, SUM(completed_topics) as comp_top FROM subjects WHERE user_id = ?", (user_id,))
    s_row = cursor.fetchone()
    tot_top = s_row['tot_top'] or 0
    comp_top = s_row['comp_top'] or 0
    subject_rate = (comp_top / tot_top * 100) if tot_top > 0 else 0
    
    cursor.execute("SELECT AVG(current_percent) as avg_goal FROM goals WHERE user_id = ?", (user_id,))
    g_row = cursor.fetchone()
    goal_rate = g_row['avg_goal'] if g_row and g_row['avg_goal'] is not None else 0
    
    if all_tasks == 0 and tot_top == 0 and goal_rate == 0:
        overall_progress = 0
    else:
        components = []
        if all_tasks > 0: components.append(task_rate)
        if tot_top > 0: components.append(subject_rate)
        if goal_rate > 0: components.append(goal_rate)
        overall_progress = round(sum(components) / len(components)) if components else 0
        
    # 5. Motivational Quote
    quote_text, quote_author = get_motivational_quote()
    
    # 6. Today's Study Plans
    cursor.execute('''
    SELECT sp.*, s.name as subject_name, s.color as subject_color 
    FROM study_plans sp
    LEFT JOIN subjects s ON sp.subject_id = s.id
    WHERE sp.user_id = ? AND sp.plan_date = ?
    ORDER BY sp.start_time ASC
    ''', (user_id, today_str))
    today_plans = cursor.fetchall()
    
    # 7. Today's Tasks List
    cursor.execute('''
    SELECT t.*, s.name as subject_name, s.color as subject_color
    FROM tasks t
    LEFT JOIN subjects s ON t.subject_id = s.id
    WHERE t.user_id = ? AND t.due_date = ?
    ORDER BY t.is_completed ASC, CASE t.priority WHEN 'High' THEN 1 WHEN 'Medium' THEN 2 ELSE 3 END
    ''', (user_id, today_str))
    today_tasks = cursor.fetchall()
    
    # 8. Upcoming Exams (Sorted nearest)
    cursor.execute('''
    SELECT e.*, s.name as subject_name, s.color as subject_color
    FROM exams e
    LEFT JOIN subjects s ON e.subject_id = s.id
    WHERE e.user_id = ? AND e.exam_date >= ?
    ORDER BY e.exam_date ASC
    LIMIT 4
    ''', (user_id, today_str))
    upcoming_exams = []
    for row in cursor.fetchall():
        exam_d = datetime.strptime(row['exam_date'], '%Y-%m-%d').date()
        days_left = (exam_d - date.today()).days
        upcoming_exams.append({
            'id': row['id'],
            'name': row['name'],
            'subject_name': row['subject_name'] or 'General',
            'subject_color': row['subject_color'] or '#4F46E5',
            'exam_date': row['exam_date'],
            'exam_time': row['exam_time'],
            'days_left': days_left,
            'important_topics': row['important_topics']
        })
        
    # 9. Dynamic Notifications / Reminders
    notifications = []
    if upcoming_exams:
        nearest = upcoming_exams[0]
        if nearest['days_left'] == 0:
            notifications.append({'type': 'urgent', 'icon': '🚨', 'text': f"Exam Today: {nearest['name']} at {nearest['exam_time'] or 'Scheduled Time'}!"})
        elif nearest['days_left'] <= 7:
            notifications.append({'type': 'warning', 'icon': '🔔', 'text': f"{nearest['name']} is in {nearest['days_left']} days ({nearest['exam_date']})."})
            
    if today_pending > 0:
        notifications.append({'type': 'info', 'icon': '📌', 'text': f"You have {today_pending} pending task{'s' if today_pending > 1 else ''} scheduled for today."})
    elif today_total > 0 and today_completed == today_total:
        notifications.append({'type': 'success', 'icon': '🎉', 'text': "Awesome! All tasks for today are completed!"})
        
    if today_plans:
        notifications.append({'type': 'plan', 'icon': '📅', 'text': f"{len(today_plans)} study session{'s' if len(today_plans) > 1 else ''} planned on your schedule today."})
        
    # 10. Subjects summary for dashboard
    cursor.execute('''
    SELECT *, 
        CASE WHEN total_topics > 0 THEN ROUND((completed_topics * 100.0 / total_topics)) ELSE 0 END as progress_pct
    FROM subjects WHERE user_id = ?
    ORDER BY name ASC
    LIMIT 4
    ''', (user_id,))
    dashboard_subjects = cursor.fetchall()
    
    conn.close()
    
    return render_template(
        'dashboard.html',
        user=user,
        today_total=today_total,
        today_completed=today_completed,
        today_pending=today_pending,
        daily_progress_pct=daily_progress_pct,
        today_study_hours=today_study_hours,
        total_study_hours=total_study_hours,
        streak_info=streak_info,
        overall_progress=overall_progress,
        quote_text=quote_text,
        quote_author=quote_author,
        today_plans=today_plans,
        today_tasks=today_tasks,
        upcoming_exams=upcoming_exams,
        notifications=notifications,
        dashboard_subjects=dashboard_subjects
    )

# --- SUBJECTS MODULE ---
@app.route('/subjects', methods=['GET', 'POST'])
@login_required
def subjects():
    user_id = session['user_id']
    conn = get_db()
    cursor = conn.cursor()
    
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        code = request.form.get('code', '').strip()
        faculty = request.form.get('faculty', '').strip()
        total_topics = int(request.form.get('total_topics', 10) or 10)
        completed_topics = int(request.form.get('completed_topics', 0) or 0)
        target_date = request.form.get('target_date', '').strip() or None
        color = request.form.get('color', '#4F46E5')
        
        if not name:
            flash('Subject Name is required.', 'danger')
        else:
            completed_topics = min(completed_topics, total_topics)
            cursor.execute('''
            INSERT INTO subjects (user_id, name, code, faculty, total_topics, completed_topics, target_date, color)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (user_id, name, code, faculty, total_topics, completed_topics, target_date, color))
            conn.commit()
            check_and_unlock_achievements(user_id)
            flash(f'Subject "{name}" added successfully!', 'success')
            return redirect(url_for('subjects'))
            
    cursor.execute('''
    SELECT *,
        CASE WHEN total_topics > 0 THEN ROUND((completed_topics * 100.0 / total_topics)) ELSE 0 END as progress_pct
    FROM subjects
    WHERE user_id = ?
    ORDER BY name ASC
    ''', (user_id,))
    subjects_list = cursor.fetchall()
    conn.close()
    
    return render_template('subjects.html', subjects=subjects_list)

@app.route('/subjects/<int:id>/edit', methods=['POST'])
@login_required
def edit_subject(id):
    user_id = session['user_id']
    name = request.form.get('name', '').strip()
    code = request.form.get('code', '').strip()
    faculty = request.form.get('faculty', '').strip()
    total_topics = int(request.form.get('total_topics', 10) or 10)
    completed_topics = int(request.form.get('completed_topics', 0) or 0)
    target_date = request.form.get('target_date', '').strip() or None
    color = request.form.get('color', '#4F46E5')
    
    completed_topics = min(completed_topics, total_topics)
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
    UPDATE subjects 
    SET name = ?, code = ?, faculty = ?, total_topics = ?, completed_topics = ?, target_date = ?, color = ?
    WHERE id = ? AND user_id = ?
    ''', (name, code, faculty, total_topics, completed_topics, target_date, color, id, user_id))
    conn.commit()
    conn.close()
    
    check_and_unlock_achievements(user_id)
    flash('Subject updated successfully!', 'success')
    return redirect(url_for('subjects'))

@app.route('/subjects/<int:id>/delete', methods=['POST'])
@login_required
def delete_subject(id):
    user_id = session['user_id']
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM subjects WHERE id = ? AND user_id = ?", (id, user_id))
    conn.commit()
    conn.close()
    flash('Subject deleted successfully.', 'info')
    return redirect(url_for('subjects'))

# --- STUDY PLANNER MODULE ---
@app.route('/planner', methods=['GET', 'POST'])
@login_required
def planner():
    user_id = session['user_id']
    conn = get_db()
    cursor = conn.cursor()
    
    selected_date = request.args.get('date', date.today().isoformat())
    
    if request.method == 'POST':
        subject_id = request.form.get('subject_id') or None
        topic = request.form.get('topic', '').strip()
        plan_date = request.form.get('plan_date', '').strip() or date.today().isoformat()
        start_time = request.form.get('start_time', '').strip()
        end_time = request.form.get('end_time', '').strip()
        priority = request.form.get('priority', 'Medium')
        notes = request.form.get('notes', '').strip()
        
        if not topic:
            flash('Topic is required for creating a study plan.', 'danger')
        else:
            cursor.execute('''
            INSERT INTO study_plans (user_id, subject_id, topic, plan_date, start_time, end_time, priority, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (user_id, subject_id, topic, plan_date, start_time, end_time, priority, notes))
            conn.commit()
            check_and_unlock_achievements(user_id)
            flash('Study plan scheduled successfully!', 'success')
            return redirect(url_for('planner', date=plan_date))
            
    cursor.execute('''
    SELECT sp.*, s.name as subject_name, s.color as subject_color
    FROM study_plans sp
    LEFT JOIN subjects s ON sp.subject_id = s.id
    WHERE sp.user_id = ? AND sp.plan_date = ?
    ORDER BY sp.start_time ASC
    ''', (user_id, selected_date))
    plans = cursor.fetchall()
    
    # Also fetch subjects for dropdown
    cursor.execute("SELECT id, name, code FROM subjects WHERE user_id = ? ORDER BY name ASC", (user_id,))
    subjects_list = cursor.fetchall()
    conn.close()
    
    return render_template('planner.html', plans=plans, subjects=subjects_list, selected_date=selected_date)

@app.route('/planner/<int:id>/toggle', methods=['POST'])
@login_required
def toggle_plan(id):
    user_id = session['user_id']
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT is_completed, plan_date FROM study_plans WHERE id = ? AND user_id = ?", (id, user_id))
    plan = cursor.fetchone()
    if plan:
        new_status = 0 if plan['is_completed'] else 1
        cursor.execute("UPDATE study_plans SET is_completed = ? WHERE id = ? AND user_id = ?", (new_status, id, user_id))
        conn.commit()
        if new_status == 1:
            update_user_streak(user_id, conn)
            check_and_unlock_achievements(user_id)
    conn.close()
    return redirect(request.referrer or url_for('planner'))

@app.route('/planner/<int:id>/delete', methods=['POST'])
@login_required
def delete_plan(id):
    user_id = session['user_id']
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM study_plans WHERE id = ? AND user_id = ?", (id, user_id))
    conn.commit()
    conn.close()
    flash('Study plan removed.', 'info')
    return redirect(request.referrer or url_for('planner'))

# --- DAILY TASKS MODULE ---
@app.route('/tasks', methods=['GET', 'POST'])
@login_required
def tasks():
    user_id = session['user_id']
    conn = get_db()
    cursor = conn.cursor()
    
    if request.method == 'POST':
        subject_id = request.form.get('subject_id') or None
        title = request.form.get('title', '').strip()
        due_date = request.form.get('due_date', '').strip() or date.today().isoformat()
        priority = request.form.get('priority', 'Medium')
        
        if not title:
            flash('Task description/title cannot be empty.', 'danger')
        else:
            cursor.execute('''
            INSERT INTO tasks (user_id, subject_id, title, due_date, priority)
            VALUES (?, ?, ?, ?, ?)
            ''', (user_id, subject_id, title, due_date, priority))
            conn.commit()
            flash('Daily task added successfully!', 'success')
            return redirect(url_for('tasks'))
            
    # Filters
    filter_subject = request.args.get('subject', '')
    filter_priority = request.args.get('priority', '')
    filter_status = request.args.get('status', '')
    filter_date = request.args.get('date', '')
    search_q = request.args.get('q', '').strip()
    
    query = '''
    SELECT t.*, s.name as subject_name, s.color as subject_color
    FROM tasks t
    LEFT JOIN subjects s ON t.subject_id = s.id
    WHERE t.user_id = ?
    '''
    params = [user_id]
    
    if filter_subject:
        query += ' AND t.subject_id = ?'
        params.append(filter_subject)
    if filter_priority:
        query += ' AND t.priority = ?'
        params.append(filter_priority)
    if filter_status == 'completed':
        query += ' AND t.is_completed = 1'
    elif filter_status == 'pending':
        query += ' AND t.is_completed = 0'
    if filter_date:
        query += ' AND t.due_date = ?'
        params.append(filter_date)
    if search_q:
        query += ' AND (t.title LIKE ? OR s.name LIKE ?)'
        params.extend([f'%{search_q}%', f'%{search_q}%'])
        
    query += ' ORDER BY t.is_completed ASC, t.due_date ASC, CASE t.priority WHEN "High" THEN 1 WHEN "Medium" THEN 2 ELSE 3 END'
    
    cursor.execute(query, params)
    tasks_list = cursor.fetchall()
    
    cursor.execute("SELECT id, name, code FROM subjects WHERE user_id = ? ORDER BY name ASC", (user_id,))
    subjects_list = cursor.fetchall()
    
    # Task statistics
    cursor.execute("SELECT COUNT(*) as total, SUM(CASE WHEN is_completed = 1 THEN 1 ELSE 0 END) as completed FROM tasks WHERE user_id = ?", (user_id,))
    stats_row = cursor.fetchone()
    total_tasks = stats_row['total'] or 0
    completed_tasks = stats_row['completed'] or 0
    pending_tasks = total_tasks - completed_tasks
    completion_rate = round((completed_tasks / total_tasks * 100)) if total_tasks > 0 else 0
    
    conn.close()
    
    return render_template(
        'tasks.html',
        tasks=tasks_list,
        subjects=subjects_list,
        total_tasks=total_tasks,
        completed_tasks=completed_tasks,
        pending_tasks=pending_tasks,
        completion_rate=completion_rate,
        current_filters={
            'subject': filter_subject,
            'priority': filter_priority,
            'status': filter_status,
            'date': filter_date,
            'q': search_q
        }
    )

@app.route('/tasks/<int:id>/toggle', methods=['POST'])
@login_required
def toggle_task(id):
    user_id = session['user_id']
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT is_completed, subject_id FROM tasks WHERE id = ? AND user_id = ?", (id, user_id))
    task = cursor.fetchone()
    
    if not task:
        conn.close()
        return jsonify({'success': False, 'error': 'Task not found'}), 404
        
    new_status = 0 if task['is_completed'] else 1
    comp_time = datetime.now().isoformat() if new_status == 1 else None
    
    cursor.execute('''
    UPDATE tasks 
    SET is_completed = ?, completed_at = ?
    WHERE id = ? AND user_id = ?
    ''', (new_status, comp_time, id, user_id))
    
    # If completed, also bump subject completed topics if linked and not exceeding total
    if new_status == 1 and task['subject_id']:
        cursor.execute('''
        UPDATE subjects 
        SET completed_topics = MIN(total_topics, completed_topics + 1)
        WHERE id = ? AND user_id = ?
        ''', (task['subject_id'], user_id))
        
    conn.commit()
    
    if new_status == 1:
        update_user_streak(user_id, conn)
        
    unlocked = check_and_unlock_achievements(user_id)
    conn.close()
    
    if request.is_json or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({
            'success': True,
            'new_status': new_status,
            'unlocked_achievements': unlocked
        })
        
    flash('Task status updated successfully!', 'success')
    return redirect(request.referrer or url_for('tasks'))

@app.route('/tasks/<int:id>/edit', methods=['POST'])
@login_required
def edit_task(id):
    user_id = session['user_id']
    subject_id = request.form.get('subject_id') or None
    title = request.form.get('title', '').strip()
    due_date = request.form.get('due_date', '').strip()
    priority = request.form.get('priority', 'Medium')
    
    if not title or not due_date:
        flash('Title and Due Date are required.', 'danger')
        return redirect(url_for('tasks'))
        
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
    UPDATE tasks 
    SET subject_id = ?, title = ?, due_date = ?, priority = ?
    WHERE id = ? AND user_id = ?
    ''', (subject_id, title, due_date, priority, id, user_id))
    conn.commit()
    conn.close()
    flash('Task updated successfully!', 'success')
    return redirect(url_for('tasks'))

@app.route('/tasks/<int:id>/delete', methods=['POST'])
@login_required
def delete_task(id):
    user_id = session['user_id']
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM tasks WHERE id = ? AND user_id = ?", (id, user_id))
    conn.commit()
    conn.close()
    flash('Task deleted.', 'info')
    return redirect(request.referrer or url_for('tasks'))

# --- STUDY TIMER / POMODORO MODULE ---
@app.route('/timer')
@login_required
def timer():
    user_id = session['user_id']
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("SELECT id, name, code FROM subjects WHERE user_id = ? ORDER BY name ASC", (user_id,))
    subjects_list = cursor.fetchall()
    
    today_str = date.today().isoformat()
    cursor.execute('''
    SELECT ss.*, s.name as subject_name, s.color as subject_color
    FROM study_sessions ss
    LEFT JOIN subjects s ON ss.subject_id = s.id
    WHERE ss.user_id = ? AND ss.session_date = ?
    ORDER BY ss.created_at DESC
    ''', (user_id, today_str))
    today_sessions = cursor.fetchall()
    
    cursor.execute("SELECT SUM(duration_minutes) as total_min FROM study_sessions WHERE user_id = ? AND session_date = ?", (user_id, today_str))
    today_minutes = cursor.fetchone()['total_min'] or 0
    
    cursor.execute("SELECT COUNT(*) as session_count FROM study_sessions WHERE user_id = ? AND session_date = ?", (user_id, today_str))
    today_count = cursor.fetchone()['session_count'] or 0
    
    conn.close()
    return render_template(
        'timer.html',
        subjects=subjects_list,
        today_sessions=today_sessions,
        today_minutes=today_minutes,
        today_count=today_count
    )

@app.route('/api/timer/save', methods=['POST'])
@login_required
def save_study_session():
    user_id = session['user_id']
    data = request.get_json() or {}
    
    subject_id = data.get('subject_id') or None
    duration_minutes = int(data.get('duration_minutes', 25))
    session_type = data.get('session_type', 'Pomodoro')
    notes = data.get('notes', '').strip()
    session_date = date.today().isoformat()
    
    if duration_minutes <= 0:
        return jsonify({'success': False, 'error': 'Invalid duration'}), 400
        
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
    INSERT INTO study_sessions (user_id, subject_id, session_date, duration_minutes, session_type, notes)
    VALUES (?, ?, ?, ?, ?, ?)
    ''', (user_id, subject_id, session_date, duration_minutes, session_type, notes))
    conn.commit()
    
    # Update streak
    update_user_streak(user_id, conn)
    
    # Check achievements
    unlocked = check_and_unlock_achievements(user_id)
    conn.close()
    
    return jsonify({
        'success': True,
        'message': f'Awesome job! Logged {duration_minutes} minutes of study time.',
        'unlocked_achievements': unlocked
    })

# --- EXAMS & DEADLINES MODULE ---
@app.route('/exams', methods=['GET', 'POST'])
@login_required
def exams():
    user_id = session['user_id']
    conn = get_db()
    cursor = conn.cursor()
    
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        subject_id = request.form.get('subject_id') or None
        exam_date = request.form.get('exam_date', '').strip()
        exam_time = request.form.get('exam_time', '').strip()
        important_topics = request.form.get('important_topics', '').strip()
        notes = request.form.get('notes', '').strip()
        
        if not name or not exam_date:
            flash('Exam Name and Exam Date are required.', 'danger')
        else:
            cursor.execute('''
            INSERT INTO exams (user_id, name, subject_id, exam_date, exam_time, important_topics, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (user_id, name, subject_id, exam_date, exam_time, important_topics, notes))
            conn.commit()
            flash('Exam / Deadline added to schedule!', 'success')
            return redirect(url_for('exams'))
            
    cursor.execute('''
    SELECT e.*, s.name as subject_name, s.color as subject_color
    FROM exams e
    LEFT JOIN subjects s ON e.subject_id = s.id
    WHERE e.user_id = ?
    ORDER BY e.exam_date ASC
    ''', (user_id,))
    raw_exams = cursor.fetchall()
    
    exams_list = []
    today = date.today()
    for row in raw_exams:
        e_date = datetime.strptime(row['exam_date'], '%Y-%m-%d').date()
        days_left = (e_date - today).days
        exams_list.append({
            'id': row['id'],
            'name': row['name'],
            'subject_id': row['subject_id'],
            'subject_name': row['subject_name'] or 'General',
            'subject_color': row['subject_color'] or '#4F46E5',
            'exam_date': row['exam_date'],
            'exam_time': row['exam_time'],
            'important_topics': row['important_topics'],
            'notes': row['notes'],
            'days_left': days_left,
            'is_past': days_left < 0
        })
        
    cursor.execute("SELECT id, name, code FROM subjects WHERE user_id = ? ORDER BY name ASC", (user_id,))
    subjects_list = cursor.fetchall()
    conn.close()
    
    return render_template('exams.html', exams=exams_list, subjects=subjects_list)

@app.route('/exams/<int:id>/edit', methods=['POST'])
@login_required
def edit_exam(id):
    user_id = session['user_id']
    name = request.form.get('name', '').strip()
    subject_id = request.form.get('subject_id') or None
    exam_date = request.form.get('exam_date', '').strip()
    exam_time = request.form.get('exam_time', '').strip()
    important_topics = request.form.get('important_topics', '').strip()
    notes = request.form.get('notes', '').strip()
    
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
    UPDATE exams
    SET name = ?, subject_id = ?, exam_date = ?, exam_time = ?, important_topics = ?, notes = ?
    WHERE id = ? AND user_id = ?
    ''', (name, subject_id, exam_date, exam_time, important_topics, notes, id, user_id))
    conn.commit()
    conn.close()
    flash('Exam details updated!', 'success')
    return redirect(url_for('exams'))

@app.route('/exams/<int:id>/delete', methods=['POST'])
@login_required
def delete_exam(id):
    user_id = session['user_id']
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM exams WHERE id = ? AND user_id = ?", (id, user_id))
    conn.commit()
    conn.close()
    flash('Exam removed from planner.', 'info')
    return redirect(url_for('exams'))

# --- STUDY GOALS MODULE ---
@app.route('/goals', methods=['GET', 'POST'])
@login_required
def goals():
    user_id = session['user_id']
    conn = get_db()
    cursor = conn.cursor()
    
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        target_percent = int(request.form.get('target_percent', 100) or 100)
        current_percent = int(request.form.get('current_percent', 0) or 0)
        deadline = request.form.get('deadline', '').strip() or None
        category = request.form.get('category', 'Academic')
        
        if not title:
            flash('Goal title is required.', 'danger')
        else:
            is_comp = 1 if current_percent >= target_percent else 0
            cursor.execute('''
            INSERT INTO goals (user_id, title, target_percent, current_percent, deadline, category, is_completed)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (user_id, title, target_percent, current_percent, deadline, category, is_comp))
            conn.commit()
            check_and_unlock_achievements(user_id)
            flash('Academic goal established!', 'success')
            return redirect(url_for('goals'))
            
    cursor.execute("SELECT * FROM goals WHERE user_id = ? ORDER BY is_completed ASC, deadline ASC", (user_id,))
    goals_list = cursor.fetchall()
    
    # Goals stats
    cursor.execute("SELECT COUNT(*) as total, SUM(CASE WHEN current_percent >= target_percent OR is_completed = 1 THEN 1 ELSE 0 END) as comp FROM goals WHERE user_id = ?", (user_id,))
    g_stats = cursor.fetchone()
    total_goals = g_stats['total'] or 0
    comp_goals = g_stats['comp'] or 0
    
    conn.close()
    return render_template('goals.html', goals=goals_list, total_goals=total_goals, comp_goals=comp_goals)

@app.route('/goals/<int:id>/update-progress', methods=['POST'])
@login_required
def update_goal_progress(id):
    user_id = session['user_id']
    new_percent = int(request.form.get('current_percent', 0))
    new_percent = max(0, min(100, new_percent))
    
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT target_percent FROM goals WHERE id = ? AND user_id = ?", (id, user_id))
    goal = cursor.fetchone()
    
    if goal:
        is_completed = 1 if new_percent >= goal['target_percent'] else 0
        cursor.execute('''
        UPDATE goals 
        SET current_percent = ?, is_completed = ?
        WHERE id = ? AND user_id = ?
        ''', (new_percent, is_completed, id, user_id))
        conn.commit()
        check_and_unlock_achievements(user_id)
        flash('Goal progress updated!', 'success')
        
    conn.close()
    return redirect(url_for('goals'))

@app.route('/goals/<int:id>/delete', methods=['POST'])
@login_required
def delete_goal(id):
    user_id = session['user_id']
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM goals WHERE id = ? AND user_id = ?", (id, user_id))
    conn.commit()
    conn.close()
    flash('Goal removed.', 'info')
    return redirect(url_for('goals'))

# --- PROGRESS TRACKING MODULE ---
@app.route('/progress')
@login_required
def progress():
    user_id = session['user_id']
    conn = get_db()
    cursor = conn.cursor()
    today = date.today()
    
    # 1. Total study hours
    cursor.execute("SELECT SUM(duration_minutes) as total_min FROM study_sessions WHERE user_id = ?", (user_id,))
    tot_min = cursor.fetchone()['total_min'] or 0
    total_study_hours = round(tot_min / 60.0, 1)
    
    # 2. This week study hours
    start_of_week = today - timedelta(days=today.weekday())
    cursor.execute("SELECT SUM(duration_minutes) as week_min FROM study_sessions WHERE user_id = ? AND session_date >= ?", (user_id, start_of_week.isoformat()))
    week_min = cursor.fetchone()['week_min'] or 0
    week_study_hours = round(week_min / 60.0, 1)
    
    # 3. Tasks statistics (Daily, Weekly, Monthly)
    # Daily
    cursor.execute("SELECT COUNT(*) as total, SUM(CASE WHEN is_completed = 1 THEN 1 ELSE 0 END) as comp FROM tasks WHERE user_id = ? AND due_date = ?", (user_id, today.isoformat()))
    d_row = cursor.fetchone()
    daily_total = d_row['total'] or 0
    daily_comp = d_row['comp'] or 0
    daily_pct = round((daily_comp / daily_total * 100)) if daily_total > 0 else 0
    
    # Weekly
    cursor.execute("SELECT COUNT(*) as total, SUM(CASE WHEN is_completed = 1 THEN 1 ELSE 0 END) as comp FROM tasks WHERE user_id = ? AND due_date >= ?", (user_id, start_of_week.isoformat()))
    w_row = cursor.fetchone()
    weekly_total = w_row['total'] or 0
    weekly_comp = w_row['comp'] or 0
    weekly_pct = round((weekly_comp / weekly_total * 100)) if weekly_total > 0 else 0
    
    # Monthly
    start_of_month = today.replace(day=1)
    cursor.execute("SELECT COUNT(*) as total, SUM(CASE WHEN is_completed = 1 THEN 1 ELSE 0 END) as comp FROM tasks WHERE user_id = ? AND due_date >= ?", (user_id, start_of_month.isoformat()))
    m_row = cursor.fetchone()
    monthly_total = m_row['total'] or 0
    monthly_comp = m_row['comp'] or 0
    monthly_pct = round((monthly_comp / monthly_total * 100)) if monthly_total > 0 else 0
    
    # 4. Subjects Progress Details
    cursor.execute('''
    SELECT *, 
        CASE WHEN total_topics > 0 THEN ROUND((completed_topics * 100.0 / total_topics)) ELSE 0 END as progress_pct
    FROM subjects WHERE user_id = ?
    ORDER BY progress_pct DESC
    ''', (user_id,))
    subjects_progress = cursor.fetchall()
    
    # 5. Streak
    streak_info = get_user_streak(user_id)
    
    conn.close()
    
    return render_template(
        'progress.html',
        total_study_hours=total_study_hours,
        week_study_hours=week_study_hours,
        daily_pct=daily_pct,
        weekly_pct=weekly_pct,
        monthly_pct=monthly_pct,
        daily_comp=daily_comp,
        daily_total=daily_total,
        weekly_comp=weekly_comp,
        weekly_total=weekly_total,
        monthly_comp=monthly_comp,
        monthly_total=monthly_total,
        subjects_progress=subjects_progress,
        streak_info=streak_info
    )

@app.route('/api/progress-data')
@login_required
def api_progress_data():
    user_id = session['user_id']
    conn = get_db()
    cursor = conn.cursor()
    today = date.today()
    
    # 1. Weekly study hours breakdown (Monday to Sunday of current week)
    monday = today - timedelta(days=today.weekday())
    week_days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
    study_hours_by_day = [0.0] * 7
    
    for i in range(7):
        day_date = monday + timedelta(days=i)
        cursor.execute("SELECT SUM(duration_minutes) as mins FROM study_sessions WHERE user_id = ? AND session_date = ?", (user_id, day_date.isoformat()))
        res = cursor.fetchone()['mins']
        study_hours_by_day[i] = round((res or 0) / 60.0, 1)
        
    # 2. Subject progress breakdown
    cursor.execute('''
    SELECT name, color,
        CASE WHEN total_topics > 0 THEN ROUND((completed_topics * 100.0 / total_topics)) ELSE 0 END as progress_pct
    FROM subjects WHERE user_id = ?
    ORDER BY name ASC
    ''', (user_id,))
    sub_rows = cursor.fetchall()
    subject_names = [r['name'] for r in sub_rows]
    subject_pcts = [r['progress_pct'] for r in sub_rows]
    subject_colors = [r['color'] or '#4F46E5' for r in sub_rows]
    
    # 3. Task Status Breakdown
    cursor.execute("SELECT COUNT(*) as total, SUM(CASE WHEN is_completed = 1 THEN 1 ELSE 0 END) as completed FROM tasks WHERE user_id = ?", (user_id,))
    t_row = cursor.fetchone()
    total_t = t_row['total'] or 0
    comp_t = t_row['completed'] or 0
    pend_t = total_t - comp_t
    
    conn.close()
    
    return jsonify({
        'week_days': week_days,
        'study_hours_by_day': study_hours_by_day,
        'subject_names': subject_names,
        'subject_pcts': subject_pcts,
        'subject_colors': subject_colors,
        'task_distribution': {
            'completed': comp_t,
            'pending': pend_t
        }
    })

# --- ACHIEVEMENTS MODULE ---
@app.route('/achievements')
@login_required
def achievements():
    user_id = session['user_id']
    # Trigger check first to ensure up-to-date unlocks
    check_and_unlock_achievements(user_id)
    
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('''
    SELECT a.*, 
        ua.unlocked_at,
        CASE WHEN ua.id IS NOT NULL THEN 1 ELSE 0 END as is_unlocked
    FROM achievements a
    LEFT JOIN user_achievements ua ON a.id = ua.achievement_id AND ua.user_id = ?
    ORDER BY is_unlocked DESC, a.points ASC
    ''', (user_id,))
    badges = cursor.fetchall()
    
    unlocked_count = sum(1 for b in badges if b['is_unlocked'])
    total_count = len(badges)
    total_points = sum(b['points'] for b in badges if b['is_unlocked'])
    
    conn.close()
    return render_template(
        'achievements.html',
        badges=badges,
        unlocked_count=unlocked_count,
        total_count=total_count,
        total_points=total_points
    )

# --- CALENDAR VIEW MODULE ---
@app.route('/calendar')
@login_required
def calendar_view():
    return render_template('calendar.html')

@app.route('/api/calendar-events')
@login_required
def api_calendar_events():
    user_id = session['user_id']
    conn = get_db()
    cursor = conn.cursor()
    events = []
    
    # 1. Study Plans
    cursor.execute('''
    SELECT sp.id, sp.topic, sp.plan_date, sp.start_time, sp.end_time, sp.is_completed, s.name as subject_name, s.color as subject_color
    FROM study_plans sp
    LEFT JOIN subjects s ON sp.subject_id = s.id
    WHERE sp.user_id = ?
    ''', (user_id,))
    for p in cursor.fetchall():
        events.append({
            'id': f"plan_{p['id']}",
            'type': 'plan',
            'title': f"📖 {p['subject_name'] or 'Study'}: {p['topic']}",
            'date': p['plan_date'],
            'time': f"{p['start_time']} - {p['end_time']}" if p['start_time'] else "All Day",
            'is_completed': bool(p['is_completed']),
            'color': p['subject_color'] or '#4F46E5',
            'category': 'Study Plan'
        })
        
    # 2. Exams
    cursor.execute('''
    SELECT e.id, e.name, e.exam_date, e.exam_time, s.name as subject_name, s.color as subject_color
    FROM exams e
    LEFT JOIN subjects s ON e.subject_id = s.id
    WHERE e.user_id = ?
    ''', (user_id,))
    for e in cursor.fetchall():
        events.append({
            'id': f"exam_{e['id']}",
            'type': 'exam',
            'title': f"📝 Exam: {e['name']}",
            'date': e['exam_date'],
            'time': e['exam_time'] or 'TBD',
            'color': '#EF4444',
            'category': 'Exam'
        })
        
    # 3. Tasks
    cursor.execute('''
    SELECT t.id, t.title, t.due_date, t.priority, t.is_completed, s.name as subject_name
    FROM tasks t
    LEFT JOIN subjects s ON t.subject_id = s.id
    WHERE t.user_id = ?
    ''', (user_id,))
    for t in cursor.fetchall():
        events.append({
            'id': f"task_{t['id']}",
            'type': 'task',
            'title': f"{'✅' if t['is_completed'] else '☐'} Task: {t['title']}",
            'date': t['due_date'],
            'time': f"Priority: {t['priority']}",
            'is_completed': bool(t['is_completed']),
            'color': '#10B981' if t['is_completed'] else '#F59E0B',
            'category': 'Task'
        })
        
    # 4. Goals Deadline
    cursor.execute("SELECT id, title, deadline, current_percent, target_percent FROM goals WHERE user_id = ? AND deadline IS NOT NULL", (user_id,))
    for g in cursor.fetchall():
        events.append({
            'id': f"goal_{g['id']}",
            'type': 'goal',
            'title': f"🎯 Goal Deadline: {g['title']} ({g['current_percent']}/{g['target_percent']}%)",
            'date': g['deadline'],
            'time': 'Deadline',
            'color': '#8B5CF6',
            'category': 'Goal'
        })
        
    conn.close()
    return jsonify({'events': events})

# --- PROFILE MODULE ---
@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    user_id = session['user_id']
    conn = get_db()
    cursor = conn.cursor()
    
    if request.method == 'POST':
        action = request.form.get('action')
        
        if action == 'update_profile':
            name = request.form.get('name', '').strip()
            email = request.form.get('email', '').strip()
            college = request.form.get('college', '').strip()
            course = request.form.get('course', '').strip()
            year_of_study = request.form.get('year_of_study', '').strip()
            
            if not name or not email:
                flash('Name and Email are required.', 'danger')
            else:
                cursor.execute('''
                UPDATE users 
                SET name = ?, email = ?, college = ?, course = ?, year_of_study = ?
                WHERE id = ?
                ''', (name, email, college, course, year_of_study, user_id))
                conn.commit()
                session['name'] = name
                flash('Profile information updated successfully!', 'success')
                
        elif action == 'change_password':
            old_password = request.form.get('old_password', '').strip()
            new_password = request.form.get('new_password', '').strip()
            confirm_password = request.form.get('confirm_password', '').strip()
            
            cursor.execute("SELECT password_hash FROM users WHERE id = ?", (user_id,))
            u = cursor.fetchone()
            
            if not check_password_hash(u['password_hash'], old_password):
                flash('Incorrect current password.', 'danger')
            elif len(new_password) < 4:
                flash('New password must be at least 4 characters long.', 'danger')
            elif new_password != confirm_password:
                flash('New password and confirmation do not match.', 'danger')
            else:
                new_hash = generate_password_hash(new_password)
                cursor.execute("UPDATE users SET password_hash = ? WHERE id = ?", (new_hash, user_id))
                conn.commit()
                flash('Password changed successfully!', 'success')
                
        return redirect(url_for('profile'))
        
    cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    user = cursor.fetchone()
    
    # Stats for profile card
    cursor.execute("SELECT COUNT(*) as total_tasks, SUM(CASE WHEN is_completed = 1 THEN 1 ELSE 0 END) as comp_tasks FROM tasks WHERE user_id = ?", (user_id,))
    t_row = cursor.fetchone()
    
    cursor.execute("SELECT SUM(duration_minutes) as mins FROM study_sessions WHERE user_id = ?", (user_id,))
    total_mins = cursor.fetchone()['mins'] or 0
    
    cursor.execute("SELECT COUNT(*) as unlocked FROM user_achievements WHERE user_id = ?", (user_id,))
    unlocked_ach = cursor.fetchone()['unlocked'] or 0
    
    streak_info = get_user_streak(user_id)
    
    conn.close()
    return render_template(
        'profile.html',
        user=user,
        total_tasks=t_row['total_tasks'] or 0,
        completed_tasks=t_row['comp_tasks'] or 0,
        total_study_hours=round(total_mins / 60.0, 1),
        unlocked_achievements=unlocked_ach,
        streak_info=streak_info
    )

if __name__ == '__main__':
    init_db()
    # Seed demo student if not present
    seed_demo.seed_demo_data()
    print("StudyMate is running at http://127.0.0.1:5000")
    app.run(host='0.0.0.0', port=5000, debug=True)
