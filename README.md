UniBuzz - A Campus Event Management Platform

A lightweight prototype of a campus event management platform built with Flask and SQLAlchemy with APIs for event management, creation, feedback collection and student management.

Features
- Event Management: Create, update, delete, and manage campus events
- Student Registration: Register students for events with duplicate prevention
- Attendance Tracking: Mark and track student attendance for events
- Feedback System: Collect and analyze student feedback with ratings (1-5)
- Comprehensive Reports: Generate various reports on participation, popularity, and engagement

Tech Stack
- Backend: Python Flask
- Database: SQLite
- ORM: SQLAlchemy
- API: RESTful API

Installation & Setup

Prerequisites
- Python 3.7+
- pip (Python package installer)

Installation Steps
1. Clone the repository:
   git clone <repository-url>
   cd campus-event-platform

2. Create virtual environment:
bashpython -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

3. Install dependencies:
bashpip install flask flask-sqlalchemy

4. Run the application:
bashpython app.py

5. Access the application at http://localhost:5000

