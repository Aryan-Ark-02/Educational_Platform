from flask import Flask, render_template, jsonify, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, UTC
import random
import io
import sys
from contextlib import redirect_stdout

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'  # Change this to a secure secret key
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# User model
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(UTC))

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Mock data for the dashboard
mock_data = {
    "total_courses": 12,
    "courses_in_progress": 4,
    "courses_completed": 8,
    "hours_studied": 87.5,
    "growth_rate": 12.5,
    "certificates": 3,
    "pending_certificates": 2,
    "community_points": 1250,
    "ranking": "Top 15% of all students",
    "learning_progress": {
        "Jan": 38,
        "Feb": 28,
        "Mar": 42,
        "Apr": 48,
        "May": 58,
        "Jun": 72,
        "Jul": 85
    },
    "weekly_engagement": {
        "Mon": 2.5,
        "Tue": 3.2,
        "Wed": 1.8,
        "Thu": 2.7,
        "Fri": 3.5,
        "Sat": 4.2,
        "Sun": 2.1
    }
}

# Mock data for courses
course_data = {
    "in_progress": [
        {
            "id": 1,
            "title": "Introduction to Web Development",
            "instructor": "Sarah Johnson",
            "progress": 75,
            "last_accessed": "2 hours ago",
            "status": "in-progress",
            "overview": "This course provides a comprehensive introduction to web development, covering HTML, CSS, and JavaScript fundamentals.",
            "modules": [
                {
                    "id": 1,
                    "title": "Introduction to HTML",
                    "description": "Learn the basics of HTML structure and elements",
                    "lessons": 4,
                    "duration": 45,
                    "status": "completed"
                },
                {
                    "id": 2,
                    "title": "CSS Fundamentals",
                    "description": "Style your HTML with Cascading Style Sheets",
                    "lessons": 5,
                    "duration": 60,
                    "status": "completed"
                },
                {
                    "id": 3,
                    "title": "Responsive Design",
                    "description": "Make your websites work on all devices",
                    "lessons": 4,
                    "duration": 55,
                    "status": "in_progress"
                },
                {
                    "id": 4,
                    "title": "JavaScript Basics",
                    "description": "Add interactivity to your websites",
                    "lessons": 6,
                    "duration": 75,
                    "status": "not_started"
                },
                {
                    "id": 5,
                    "title": "Web Accessibility",
                    "description": "Make your websites accessible to everyone",
                    "lessons": 3,
                    "duration": 40,
                    "status": "not_started"
                },
                {
                    "id": 6,
                    "title": "Final Project",
                    "description": "Build a complete responsive website",
                    "lessons": 1,
                    "duration": 120,
                    "status": "not_started"
                }
            ]
        },
        {
            "id": 2,
            "title": "Advanced JavaScript Concepts",
            "instructor": "Michael Chen",
            "progress": 45,
            "last_accessed": "Yesterday",
            "status": "in-progress"
        },
        {
            "id": 3,
            "title": "UX/UI Design Fundamentals",
            "instructor": "Emily Rodriguez",
            "progress": 90,
            "last_accessed": "3 days ago",
            "status": "almost-complete"
        }
    ],
    "upcoming_events": [
        {
            "id": 1,
            "title": "Web Development Workshop",
            "instructor": "Sarah Johnson",
            "date": "May 15, 2025",
            "time": "2:00 PM - 4:00 PM"
        },
        {
            "id": 2,
            "title": "JavaScript Study Group",
            "instructor": "Michael Chen",
            "date": "May 18, 2025",
            "time": "6:00 PM - 7:30 PM"
        },
        {
            "id": 3,
            "title": "Design Critique Session",
            "instructor": "Emily Rodriguez",
            "date": "May 20, 2025",
            "time": "3:00 PM - 5:00 PM"
        }
    ],
    "recommended": [
        {
            "id": 1,
            "title": "React for Beginners",
            "description": "Learn the fundamentals of React",
            "tags": ["Frontend", "JavaScript"]
        },
        {
            "id": 2,
            "title": "Python Data Analysis",
            "description": "Master data analysis with Python",
            "tags": ["Data", "Python"]
        },
        {
            "id": 3,
            "title": "Advanced UX Research",
            "description": "Take your UX skills to the next level",
            "tags": ["Design", "Research"]
        }
    ]
}

# Authentication routes
@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
        
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            login_user(user)
            next_page = request.args.get('next')
            return redirect(next_page or url_for('index'))
        else:
            flash('Invalid username or password', 'error')
            
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
        
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        
        if User.query.filter_by(username=username).first():
            flash('Username already exists', 'error')
            return redirect(url_for('register'))
            
        if User.query.filter_by(email=email).first():
            flash('Email already registered', 'error')
            return redirect(url_for('register'))
            
        user = User(username=username, email=email)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        
        flash('Registration successful! Please login.', 'success')
        return redirect(url_for('login'))
        
    return render_template('register.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

# Protect existing routes with login_required
@app.route('/')
@login_required
def index():
    return render_template('index.html', data=mock_data)

@app.route('/courses')
@login_required
def courses():
    return render_template('courses.html', data=mock_data, courses=course_data)

@app.route('/course/<int:course_id>')
@login_required
def course_details(course_id):
    course = next((course for course in course_data['in_progress'] if course['id'] == course_id), None)
    if course:
        return render_template('course_details.html', course=course)
    return "Course not found", 404

@app.route('/course/<int:course_id>/lesson/<int:lesson_id>')
@login_required
def lesson(course_id, lesson_id):
    course = next((course for course in course_data['in_progress'] if course['id'] == course_id), None)
    if not course:
        return "Course not found", 404
        
    lesson = next((module for module in course['modules'] if module['id'] == lesson_id), None)
    if not lesson:
        return "Lesson not found", 404
        
    return render_template('lesson.html', course=course, lesson=lesson)

@app.route('/api/dashboard-data')
def get_dashboard_data():
    return jsonify(mock_data)

@app.route('/api/course-data')
def get_course_data():
    return jsonify(course_data)

@app.route('/execute_code', methods=['POST'])
def execute_code():
    code = request.form.get('code', '')
    output = ''
    error = None

    try:
        # Capture stdout in a string buffer
        buffer = io.StringIO()
        with redirect_stdout(buffer):
            # Execute the code in a safe environment
            exec(code, {'__builtins__': __builtins__}, {})
        output = buffer.getvalue()
    except Exception as e:
        error = str(e)

    return jsonify({
        'output': output,
        'error': error
    })

if __name__ == '__main__':
    app.run(debug=True)

