# Defining all the data models

# child to parent? foreign key 
# parent to all children? backref 

from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

# entitiy 1 - Stores User information
class User(db.Model):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key = True, autoincrement = True)
    fullname = db.Column(db.String, nullable = False)
    username = db.Column(db.String, unique = True, nullable = False)
    password = db.Column(db.String, nullable = False)
    role = db.Column(db.String, default = "USER")
    dob = db.Column(db.String, nullable = False)
    qualification = db.Column(db.String, nullable = False)

# entity 2 - Stores Subject information
class Subject(db.Model):
    __tablename__ = 'subject'
    subject_code = db.Column(db.Integer, primary_key = True)
    subject_name = db.Column(db.String, nullable = False)
    credit = db.Column(db.Integer, nullable = False)
    description = db.Column(db.String, nullable = False)
    chapters = db.relationship('Chapter', cascade = 'all,delete', backref = 'subject', lazy = True)

# entity 3 - Stores Chapter information that belongs to a subject
class Chapter(db.Model):
    __tablename__ = 'chapter'
    chapter_id = db.Column(db.Integer, primary_key = True, autoincrement = True)
    chapter_name = db.Column(db.String, nullable = False)
    description = db.Column(db.String, nullable = False)
    no_of_questions = db.Column(db.Integer, nullable = False)
    subject_code = db.Column(db.Integer, db.ForeignKey('subject.subject_code'), nullable = False )
    quizzes = db.relationship('Quiz', cascade = 'all,delete', backref = 'chapter', lazy = True)

# entity 4 - Stores Quiz information that belongs to a chapter
class Quiz(db.Model):
    __tablename__ = 'quiz'
    quiz_id = db.Column(db.Integer, primary_key = True)
    chapter_id = db.Column(db.Integer, db.ForeignKey('chapter.chapter_id'), nullable = False)
    quiz_name = db.Column(db.String, nullable = False)
    date_of_quiz = db.Column(db.String, nullable = False)
    duration = db.Column(db.String, nullable = False)
    questions = db.relationship('Question', cascade = 'all,delete', backref = 'quiz', lazy = True)

# entity 5- Stores Question information that belongs to a quiz
class Question(db.Model):
    __tablename__ = 'question'
    question_id = db.Column(db.Integer, primary_key = True)
    question_title = db.Column(db.String, nullable = False)
    question_statement = db.Column(db.String, nullable = False)
    quiz_id = db.Column(db.Integer, db.ForeignKey('quiz.quiz_id'), nullable = False)
    option_1_id = db.Column(db.String, nullable = False)
    option_2_id = db.Column(db.String, nullable = False)
    option_3_id = db.Column(db.String, nullable = False)
    option_4_id = db.Column(db.String, nullable = False)
    answer_id = db.Column(db.String, nullable = False)

# entity 6 - Stores selected answer of user for a quiz question
class QuizAttempt(db.Model):
    __tablename__ = 'quiz_attempt'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    quiz_id = db.Column(db.Integer, db.ForeignKey('quiz.quiz_id'), nullable=False)
    question_id = db.Column(db.Integer, db.ForeignKey('question.question_id'), nullable=False)
    selected_answer = db.Column(db.String, nullable=False)
    attempt_id = db.Column(db.Integer, db.ForeignKey('scores.id'), nullable=False)  # Link to QuizAttempt
    user = db.relationship('User',cascade = 'all,delete', backref='quiz_attempt')
    quiz = db.relationship('Quiz',cascade = 'all,delete', backref='quiz_attempt')
    question = db.relationship('Question',cascade = 'all,delete', backref='quiz_attempt')
    attempt = db.relationship('Scores',cascade = 'all,delete', backref='quiz_attempt')


# entity 7 - Stores the scores for each user in a quiz
class Scores(db.Model):
    __tablename__ = 'scores'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    quiz_id = db.Column(db.Integer, db.ForeignKey('quiz.quiz_id'), nullable=False)
    time_stamp_of_attempt = db.Column(db.String, nullable=False)
    marks_scored = db.Column(db.Integer, nullable=False)
    user = db.relationship('User',cascade = 'all,delete', backref='scores')
    quiz = db.relationship('Quiz',cascade = 'all,delete', backref='scores')







############################# MILESTONE 1 COMPLETED ABOVE ##################################
