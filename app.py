from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, date, time
import json
import os

app = Flask(__name__)

# Database Configuration
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{os.path.join(basedir, "campus_events.db")}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'your-secret-key-here'

db = SQLAlchemy(app)

# Models
class College(db.Model):
    __tablename__ = 'colleges'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False, unique=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    students = db.relationship('Student', backref='college', lazy=True, cascade='all, delete-orphan')
    events = db.relationship('Event', backref='college', lazy=True, cascade='all, delete-orphan')

class Student(db.Model):
    __tablename__ = 'students'
    id = db.Column(db.Integer, primary_key=True)
    college_id = db.Column(db.Integer, db.ForeignKey('colleges.id'), nullable=False)
    name = db.Column(db.String(255), nullable=False)
    srn = db.Column(db.String(50), nullable=False, unique=True)
    email = db.Column(db.String(255), nullable=False, unique=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    registrations = db.relationship('Registration', backref='student', lazy=True, cascade='all, delete-orphan')
    attendance = db.relationship('Attendance', backref='student', lazy=True, cascade='all, delete-orphan')
    feedback = db.relationship('Feedback', backref='student', lazy=True, cascade='all, delete-orphan')

class Event(db.Model):
    __tablename__ = 'events'
    id = db.Column(db.Integer, primary_key=True)
    college_id = db.Column(db.Integer, db.ForeignKey('colleges.id'), nullable=False)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    type = db.Column(db.String(100), nullable=False)
    date = db.Column(db.Date, nullable=False)
    time = db.Column(db.Time, nullable=False)
    venue = db.Column(db.String(255), nullable=False)
    status = db.Column(db.String(20), default='Active')
    resources = db.Column(db.Text)  # JSON string
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    registrations = db.relationship('Registration', backref='event', lazy=True, cascade='all, delete-orphan')
    attendance = db.relationship('Attendance', backref='event', lazy=True, cascade='all, delete-orphan')
    feedback = db.relationship('Feedback', backref='event', lazy=True, cascade='all, delete-orphan')

class Registration(db.Model):
    __tablename__ = 'registrations'
    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey('events.id'), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    registered_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    __table_args__ = (db.UniqueConstraint('event_id', 'student_id', name='unique_event_student_registration'),)

class Attendance(db.Model):
    __tablename__ = 'attendance'
    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey('events.id'), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    attended_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    __table_args__ = (db.UniqueConstraint('event_id', 'student_id', name='unique_event_student_attendance'),)

class Feedback(db.Model):
    __tablename__ = 'feedback'
    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey('events.id'), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    rating = db.Column(db.Integer, nullable=False)
    comment = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        db.UniqueConstraint('event_id', 'student_id', name='unique_event_student_feedback'),
        db.CheckConstraint('rating >= 1 AND rating <= 5', name='check_rating_range')
    )

# Helper function to serialize datetime objects
def serialize_datetime(obj):
    if isinstance(obj, (datetime, date, time)):
        return obj.isoformat()
    return str(obj)

# Routes

# Auth Routes (Mock)
@app.route('/auth/login', methods=['POST'])
def login():
    """Mock login endpoint - returns static token for testing"""
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')
    
    # Mock authentication - in real app, verify credentials
    if email and password:
        return jsonify({
            'success': True,
            'token': 'mock_jwt_token_12345',
            'user': {
                'email': email,
                'role': 'student'
            }
        }), 200
    
    return jsonify({'success': False, 'message': 'Invalid credentials'}), 401

# Event Routes
@app.route('/events', methods=['POST'])
def create_event():
    """Create a new event"""
    try:
        data = request.get_json()
        
        # Parse date and time
        event_date = datetime.strptime(data['date'], '%Y-%m-%d').date()
        event_time = datetime.strptime(data['time'], '%H:%M').time()
        
        event = Event(
            college_id=data['college_id'],
            title=data['title'],
            description=data.get('description', ''),
            type=data['type'],
            date=event_date,
            time=event_time,
            venue=data['venue'],
            status=data.get('status', 'Active'),
            resources=json.dumps(data.get('resources', {}))
        )
        
        db.session.add(event)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'event_id': event.id,
            'message': 'Event created successfully'
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 400

@app.route('/events', methods=['GET'])
def get_events():
    """Get all events with optional filters"""
    try:
        # Get query parameters
        event_type = request.args.get('type')
        event_date = request.args.get('date')
        status = request.args.get('status', 'Active')
        
        # Build query
        query = Event.query
        
        if event_type:
            query = query.filter(Event.type == event_type)
        if event_date:
            query = query.filter(Event.date == datetime.strptime(event_date, '%Y-%m-%d').date())
        if status:
            query = query.filter(Event.status == status)
        
        events = query.all()
        
        events_list = []
        for event in events:
            events_list.append({
                'id': event.id,
                'title': event.title,
                'description': event.description,
                'type': event.type,
                'date': serialize_datetime(event.date),
                'time': serialize_datetime(event.time),
                'venue': event.venue,
                'status': event.status,
                'resources': json.loads(event.resources) if event.resources else {},
                'college_name': event.college.name
            })
        
        return jsonify({'success': True, 'events': events_list}), 200
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 400

@app.route('/events/<int:event_id>', methods=['GET'])
def get_event(event_id):
    """Get specific event details"""
    try:
        event = Event.query.get_or_404(event_id)
        
        event_data = {
            'id': event.id,
            'title': event.title,
            'description': event.description,
            'type': event.type,
            'date': serialize_datetime(event.date),
            'time': serialize_datetime(event.time),
            'venue': event.venue,
            'status': event.status,
            'resources': json.loads(event.resources) if event.resources else {},
            'college_name': event.college.name,
            'registrations_count': len(event.registrations),
            'attendance_count': len(event.attendance)
        }
        
        return jsonify({'success': True, 'event': event_data}), 200
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 404

@app.route('/events/<int:event_id>', methods=['PUT'])
def update_event(event_id):
    """Update an event"""
    try:
        event = Event.query.get_or_404(event_id)
        data = request.get_json()
        
        if 'title' in data:
            event.title = data['title']
        if 'description' in data:
            event.description = data['description']
        if 'type' in data:
            event.type = data['type']
        if 'date' in data:
            event.date = datetime.strptime(data['date'], '%Y-%m-%d').date()
        if 'time' in data:
            event.time = datetime.strptime(data['time'], '%H:%M').time()
        if 'venue' in data:
            event.venue = data['venue']
        if 'status' in data:
            event.status = data['status']
        if 'resources' in data:
            event.resources = json.dumps(data['resources'])
        
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Event updated successfully'}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 400

@app.route('/events/<int:event_id>', methods=['DELETE'])
def delete_event(event_id):
    """Delete/cancel an event"""
    try:
        event = Event.query.get_or_404(event_id)
        event.status = 'Cancelled'
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Event cancelled successfully'}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 400

# Registration Routes
@app.route('/register', methods=['POST'])
def register_student():
    """Register a student for an event"""
    try:
        data = request.get_json()
        event_id = data['event_id']
        student_id = data['student_id']
        
        # Check if already registered
        existing = Registration.query.filter_by(event_id=event_id, student_id=student_id).first()
        if existing:
            return jsonify({'success': False, 'message': 'Student already registered for this event'}), 409
        
        registration = Registration(event_id=event_id, student_id=student_id)
        db.session.add(registration)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'registration_id': registration.id,
            'message': 'Successfully registered for event'
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 400

@app.route('/registrations/<int:event_id>', methods=['GET'])
def get_registrations(event_id):
    """Get all students registered for an event"""
    try:
        registrations = db.session.query(Registration, Student).join(Student).filter(Registration.event_id == event_id).all()
        
        students_list = []
        for reg, student in registrations:
            students_list.append({
                'student_id': student.id,
                'name': student.name,
                'srn': student.srn,
                'email': student.email,
                'registered_at': serialize_datetime(reg.registered_at)
            })
        
        return jsonify({
            'success': True,
            'event_id': event_id,
            'total_registrations': len(students_list),
            'students': students_list
        }), 200
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 400

# Attendance Routes
@app.route('/attendance', methods=['POST'])
def mark_attendance():
    """Mark student attendance for an event"""
    try:
        data = request.get_json()
        event_id = data['event_id']
        student_id = data['student_id']
        
        # Check if student is registered
        registration = Registration.query.filter_by(event_id=event_id, student_id=student_id).first()
        if not registration:
            return jsonify({'success': False, 'message': 'Student not registered for this event'}), 404
        
        # Check if already marked attendance
        existing = Attendance.query.filter_by(event_id=event_id, student_id=student_id).first()
        if existing:
            return jsonify({'success': False, 'message': 'Attendance already marked'}), 409
        
        attendance = Attendance(event_id=event_id, student_id=student_id)
        db.session.add(attendance)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'attendance_id': attendance.id,
            'message': 'Attendance marked successfully'
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 400

@app.route('/attendance/<int:event_id>', methods=['GET'])
def get_attendance(event_id):
    """Get attendance list for an event"""
    try:
        attendance_records = db.session.query(Attendance, Student).join(Student).filter(Attendance.event_id == event_id).all()
        
        students_list = []
        for att, student in attendance_records:
            students_list.append({
                'student_id': student.id,
                'name': student.name,
                'srn': student.srn,
                'email': student.email,
                'attended_at': serialize_datetime(att.attended_at)
            })
        
        return jsonify({
            'success': True,
            'event_id': event_id,
            'total_attendance': len(students_list),
            'students': students_list
        }), 200
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 400

# Feedback Routes
@app.route('/feedback', methods=['POST'])
def submit_feedback():
    """Submit feedback for an event"""
    try:
        data = request.get_json()
        event_id = data['event_id']
        student_id = data['student_id']
        rating = data['rating']
        comment = data.get('comment', '')
        
        # Check if student attended the event
        attendance = Attendance.query.filter_by(event_id=event_id, student_id=student_id).first()
        if not attendance:
            return jsonify({'success': False, 'message': 'Can only provide feedback for attended events'}), 403
        
        # Check if feedback already submitted
        existing = Feedback.query.filter_by(event_id=event_id, student_id=student_id).first()
        if existing:
            return jsonify({'success': False, 'message': 'Feedback already submitted'}), 409
        
        feedback = Feedback(
            event_id=event_id,
            student_id=student_id,
            rating=rating,
            comment=comment
        )
        
        db.session.add(feedback)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'feedback_id': feedback.id,
            'message': 'Feedback submitted successfully'
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 400

@app.route('/feedback/<int:event_id>', methods=['GET'])
def get_feedback(event_id):
    """Get feedback for an event"""
    try:
        feedback_records = db.session.query(Feedback, Student).join(Student).filter(Feedback.event_id == event_id).all()
        
        feedback_list = []
        total_rating = 0
        
        for feedback, student in feedback_records:
            feedback_list.append({
                'student_name': student.name,
                'rating': feedback.rating,
                'comment': feedback.comment,
                'created_at': serialize_datetime(feedback.created_at)
            })
            total_rating += feedback.rating
        
        average_rating = round(total_rating / len(feedback_list), 2) if feedback_list else 0
        
        return jsonify({
            'success': True,
            'event_id': event_id,
            'total_feedback': len(feedback_list),
            'average_rating': average_rating,
            'feedback': feedback_list
        }), 200
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 400

# Report Routes
@app.route('/reports/registrations/<int:event_id>', methods=['GET'])
def report_registrations(event_id):
    """Get total registrations for an event"""
    try:
        total = Registration.query.filter_by(event_id=event_id).count()
        event = Event.query.get_or_404(event_id)
        
        return jsonify({
            'success': True,
            'event_id': event_id,
            'event_title': event.title,
            'total_registrations': total
        }), 200
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 400

@app.route('/reports/attendance/<int:event_id>', methods=['GET'])
def report_attendance(event_id):
    """Get attendance percentage for an event"""
    try:
        total_registered = Registration.query.filter_by(event_id=event_id).count()
        total_attended = Attendance.query.filter_by(event_id=event_id).count()
        
        percentage = round((total_attended / total_registered) * 100, 2) if total_registered > 0 else 0
        
        event = Event.query.get_or_404(event_id)
        
        return jsonify({
            'success': True,
            'event_id': event_id,
            'event_title': event.title,
            'total_registered': total_registered,
            'total_attended': total_attended,
            'attendance_percentage': percentage
        }), 200
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 400

@app.route('/reports/feedback/<int:event_id>', methods=['GET'])
def report_feedback(event_id):
    """Get average feedback for an event"""
    try:
        feedback_records = Feedback.query.filter_by(event_id=event_id).all()
        
        if not feedback_records:
            average_rating = 0
            total_feedback = 0
        else:
            total_rating = sum(f.rating for f in feedback_records)
            average_rating = round(total_rating / len(feedback_records), 2)
            total_feedback = len(feedback_records)
        
        event = Event.query.get_or_404(event_id)
        
        return jsonify({
            'success': True,
            'event_id': event_id,
            'event_title': event.title,
            'total_feedback': total_feedback,
            'average_rating': average_rating
        }), 200
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 400

@app.route('/reports/popularity', methods=['GET'])
def report_popularity():
    """Get events sorted by registration count"""
    try:
        event_type = request.args.get('type')
        
        # Build query with registration count
        query = db.session.query(
            Event,
            db.func.count(Registration.id).label('registration_count')
        ).outerjoin(Registration).group_by(Event.id)
        
        if event_type:
            query = query.filter(Event.type == event_type)
        
        results = query.order_by(db.desc('registration_count')).all()
        
        events_list = []
        for event, reg_count in results:
            events_list.append({
                'event_id': event.id,
                'title': event.title,
                'type': event.type,
                'date': serialize_datetime(event.date),
                'registration_count': reg_count,
                'college_name': event.college.name
            })
        
        return jsonify({
            'success': True,
            'events': events_list
        }), 200
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 400

@app.route('/reports/participation/<int:student_id>', methods=['GET'])
def report_participation(student_id):
    """Get number of events attended by a student"""
    try:
        events_attended = Attendance.query.filter_by(student_id=student_id).count()
        events_registered = Registration.query.filter_by(student_id=student_id).count()
        
        student = Student.query.get_or_404(student_id)
        
        return jsonify({
            'success': True,
            'student_id': student_id,
            'student_name': student.name,
            'events_registered': events_registered,
            'events_attended': events_attended,
            'attendance_rate': round((events_attended / events_registered) * 100, 2) if events_registered > 0 else 0
        }), 200
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 400

@app.route('/reports/top-students', methods=['GET'])
def report_top_students():
    """Get top 3 most active students"""
    try:
        # Get students with most event attendance
        results = db.session.query(
            Student,
            db.func.count(Attendance.id).label('events_attended')
        ).join(Attendance).group_by(Student.id).order_by(db.desc('events_attended')).limit(3).all()
        
        students_list = []
        for student, events_count in results:
            students_list.append({
                'student_id': student.id,
                'name': student.name,
                'srn': student.srn,
                'college_name': student.college.name,
                'events_attended': events_count
            })
        
        return jsonify({
            'success': True,
            'top_students': students_list
        }), 200
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 400

# Initialize database
# Initialize database and seed data
with app.app_context():
    db.create_all()

    # Add sample data if tables are empty
    if College.query.count() == 0:
        # Add sample colleges
        college1 = College(name='Engineering College A')
        college2 = College(name='Arts & Science College B')
        db.session.add(college1)
        db.session.add(college2)
        db.session.commit()

        # Add sample students
        student1 = Student(college_id=college1.id, name='John Doe', srn='ENG001', email='john@example.com')
        student2 = Student(college_id=college1.id, name='Jane Smith', srn='ENG002', email='jane@example.com')
        db.session.add(student1)
        db.session.add(student2)
        db.session.commit()

        # Add sample event
        event1 = Event(
            college_id=college1.id,
            title='Python Workshop',
            description='Learn Python programming basics',
            type='Workshop',
            date=date(2024, 12, 15),
            time=time(10, 0),
            venue='Lab 1',
            resources='{"materials": ["slides.pdf", "code.zip"]}'
        )
        db.session.add(event1)
        db.session.commit()
if __name__ == '__main__':
    app.run(debug=True)

