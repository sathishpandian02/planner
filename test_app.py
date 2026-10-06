import unittest
from app import app
from models import get_db

class StudyMateComprehensiveTests(unittest.TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        self.client = app.test_client()

    def test_01_demo_login_and_dashboard(self):
        # Test demo login
        res = self.client.post('/login', data={
            'username': 'demo_student',
            'password': 'demo123'
        }, follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'Good Day', res.data)
        self.assertIn(b'Python Programming', res.data)

    def test_02_new_student_registration_flow(self):
        import time
        uname = f"test_student_{int(time.time())}"
        # Register fresh student
        res = self.client.post('/register', data={
            'name': 'Test Student',
            'username': uname,
            'email': f'{uname}@student.edu',
            'password': 'password123',
            'college': 'Test Institute of Tech',
            'course': 'B.Tech CS',
            'year_of_study': '2nd Year'
        }, follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'Account created successfully', res.data)
        
        # Test adding a subject
        res = self.client.post('/subjects', data={
            'name': 'Algorithms & Data Structures',
            'code': 'CS201',
            'faculty': 'Dr. Sharma',
            'total_topics': 15,
            'completed_topics': 5,
            'target_date': '2026-11-30',
            'color': '#0EA5E9'
        }, follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'Algorithms &amp; Data Structures', res.data)

        # Test adding a task
        res = self.client.post('/tasks', data={
            'title': 'Implement Binary Search Tree in Python',
            'due_date': '2026-10-15',
            'priority': 'High'
        }, follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'Implement Binary Search Tree', res.data)

        # Test toggling task
        with self.client.session_transaction() as sess:
            curr_uid = sess['user_id']
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM tasks WHERE user_id = ? AND title LIKE '%Binary Search Tree%'", (curr_uid,))
        task = cursor.fetchone()
        conn.close()
        self.assertIsNotNone(task)
        
        res = self.client.post(f'/tasks/{task["id"]}/toggle', headers={'X-Requested-With': 'XMLHttpRequest'})
        self.assertEqual(res.status_code, 200)
        json_data = res.get_json()
        self.assertTrue(json_data['success'])
        self.assertEqual(json_data['new_status'], 1)

        # Test study timer save
        res = self.client.post('/api/timer/save', json={
            'duration_minutes': 25,
            'session_type': 'Pomodoro',
            'notes': 'Focused on tree traversals'
        })
        self.assertEqual(res.status_code, 200)
        self.assertTrue(res.get_json()['success'])

        # Test adding an exam
        res = self.client.post('/exams', data={
            'name': 'Algorithms Mid-Term Exam',
            'exam_date': '2026-10-25',
            'exam_time': '09:30 AM',
            'important_topics': 'Trees, Graphs, Sorting algorithms'
        }, follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'Algorithms Mid-Term Exam', res.data)

        # Test adding a goal
        res = self.client.post('/goals', data={
            'title': 'Solve 100 LeetCode Problems',
            'target_percent': 100,
            'current_percent': 40,
            'category': 'Skills'
        }, follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'Solve 100 LeetCode Problems', res.data)

        # Test progress API
        res = self.client.get('/api/progress-data')
        self.assertEqual(res.status_code, 200)
        self.assertIn('week_days', res.get_json())

        # Test calendar events API
        res = self.client.get('/api/calendar-events')
        self.assertEqual(res.status_code, 200)
        self.assertIn('events', res.get_json())

        # Test achievements page
        res = self.client.get('/achievements')
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'Academic Milestones & Badges', res.data)

        # Test logout
        res = self.client.get('/logout', follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'You have been logged out safely', res.data)

if __name__ == '__main__':
    unittest.main()
