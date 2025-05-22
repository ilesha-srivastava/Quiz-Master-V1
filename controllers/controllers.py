i# Defining all app routes

from flask import Flask, render_template, request, redirect, url_for, session
from models.models import *
# Imports the instance of current app from the app.py file
from app import app
from datetime import date, datetime
from werkzeug.security import generate_password_hash, check_password_hash
import re

# Home page 
@app.route("/")
def home():
    return render_template('index.html')

# Login page 
@app.route('/login', methods = ['GET', 'POST'])
def login():
    if request.method == 'POST':
        uname = request.form.get("username")
        password = request.form.get("password")

        # check whether the uname and password are already available in User table or not
        user_data = User.query.filter_by(username = uname).first()

        if user_data and check_password_hash(user_data.password, password):
            session['username'] = uname  # Store in session
            session['role'] = user_data.role
            if user_data.role == "ADMIN":
                return redirect(url_for("admin_dashboard"))
            
            elif user_data.role == "USER":
                return redirect(url_for('user_dashboard'))
            
        else:
            # If the user credentials are invalid, render the same page with an error message
            return render_template('login.html', message = "Invalid username or password")
    return render_template("login.html", message = "")

# signup page 
@app.route('/signup', methods = ['GET', 'POST'])
def signup():
    if request.method == 'POST':
        fullname = request.form.get("fullname")        
        uname = request.form.get("username")
        password = request.form.get("password")
        dob = request.form.get("dob")
        qualification = request.form.get("qualification")

        hashed_password = generate_password_hash(password)
        
        if not is_valid_password(password):
            return render_template("signup.html", 
            message="Password must be at least 8 characters and include uppercase, lowercase, digit, and special character.")
        # check whether the uname and password are already available in User table or not
        exists = User.query.filter_by(username = uname).first()
        if exists:          
            return render_template("signup.html", message = "Oops...Username already exists!!")
        
        new_user = User(fullname = fullname, username = uname, password = hashed_password, dob = dob, qualification = qualification)
        db.session.add(new_user)
        db.session.commit()

        # If registration is successful display message
        return render_template("login.html", message = "Registration Successful!!!")
    return render_template("signup.html")

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# Common route for admin dashboard
@app.route("/admin")
def admin_dashboard():
    # Everytime we render admin dashboard we are getting the subject information from the backend
    name = session.get('username')
    if not name or session.get('role') != 'ADMIN':
        return redirect(url_for('login'))
    
    subjects = get_subjects()
    return render_template("admin_dashboard.html", subjects = subjects)

# Common route for user dashboard
@app.route("/user")
def user_dashboard():    
    # Everytime we render admin dashboard we are getting the Quiz information from the backend
    name = session.get('username')

    if not name or session.get('role') != 'USER':
        return redirect(url_for('login'))
    
    quizzes = get_quiz()
    date_now = date.today()         #to get current date
    date_today_str = date_now.strftime("%Y-%m-%d")      # Specifyin the date format
    # Fetch all subjects with their chapters and quizzes
    subjects = Subject.query.options(
        db.joinedload(Subject.chapters)
        .joinedload(Chapter.quizzes)
    ).all()
    
    return render_template("user_dashboard.html", quizzes = quizzes, date_now = date_today_str, subjects=subjects)




####################################### CRUD OPERATIONS ON SUBJECTS #################################################
# route to add a subject 
@app.route("/addSubject", methods = ["POST", "GET"])
def add_subject():
    '''
    This function adds a subject to the database by taking the data from the inpit fields, 
    After the form submission the admin is redirected to the admin_dashboard.html
    '''
    name = session.get("username")
    if request.method == "POST":
        sid = request.form.get("subject_id")
        sname = request.form.get("subject_name")
        scredit = request.form.get("credits")
        sdesc = request.form.get("subject_description")

        # Creating a new Subject object
        new_sub = Subject(subject_code = sid, subject_name = sname, credit = scredit, description = sdesc)
        db.session.add(new_sub)
        db.session.commit()
        return redirect(url_for('admin_dashboard'))
    
    return render_template("add_edit_subject.html", add_subject = True)


# route to edit a subject 
@app.route("/editSubject/<subject_code>", methods = ["GET", "POST"])
def edit_subject(subject_code):
    '''
    This function edits a subject details which already exists. 
    After editing the details the admin is redirected to dashboard.
    '''
    name = session.get("username")
    ob = get_subjectDetails(subject_code)
    if request.method == "POST":
        sid = request.form.get("subject-id")
        sname = request.form.get("subject-name")
        scredit = request.form.get("credits")
        sdesc = request.form.get("subject-description")
        ob.subject_code = sid
        ob.subject_name = sname
        ob.credit = scredit
        ob.description = sdesc
        db.session.commit()
        return redirect(url_for('admin_dashboard'))
    return render_template("add_edit_subject.html", subject = ob, add_subject = False)

# route to delete a subject 
@app.route("/deleteSubject/<subject_code>")
def delete_subject(subject_code):
    '''
    The function deletes the details of a subject from the database; if the quiz for that subject's chapter
    is not attempted
    '''
    name = session.get("username")

    if is_subject_attempted(subject_code):
        return render_template('admin_error.html', error="Can't delete - users have attempted quizzes in this subject")
    
    # Proceed with deletion if no attempts
    subject = Subject.query.get(subject_code)
    db.session.delete(subject)
    db.session.commit()
    return redirect(url_for('admin_dashboard'))


####################################### CRUD OPERATIONS ON CHAPTERS #################################################
# route to add a chapter
@app.route("/addChapter/<subject_id>", methods = ["POST", "GET"])
def add_chapter(subject_id):
    '''
    The function adds a chapter to the database for a particular subject.
    Subject ID is taken from the route itself.
    After the form submission the admin is redirected to dashboard
    '''
    name = session.get("username")

    if request.method == "POST":
        cid = request.form.get("chapter_id")
        cname = request.form.get("chapter_name")
        cdesc = request.form.get("chapter_description")
        questions = request.form.get("no_of_questions")

        # Creating a new Chapter object
        new_ch = Chapter(chapter_id = cid, chapter_name = cname, description = cdesc, no_of_questions = questions, subject_code = subject_id)
        db.session.add(new_ch)
        db.session.commit()
        return redirect(url_for('admin_dashboard'))
    
    return render_template("add_edit_chapter.html", subject_id = subject_id, add_chapter = True)

# route to edit a chapter 
@app.route("/editChapter/<chapter_id>", methods = ["GET", "POST"])
def edit_chapter(chapter_id):
    '''
    This function edits a chapter which already exists. 
    After editing the details the admin is redirected to dashboard.
    '''
    name = session.get("username")

    ob = get_chapterDetails(chapter_id)
    if request.method == "POST":
        cname = request.form.get("chapter-name")
        cdesc = request.form.get("chapter-description")
        questions = request.form.get("no_of_questions")

        # Updating the details.
        ob.chapter_id = chapter_id
        ob.chapter_name = cname
        ob.description = cdesc
        ob.no_of_questions = questions
        db.session.commit()        
        return redirect(url_for('admin_dashboard'))
    return render_template("add_edit_chapter.html", chapter = ob, add_chapter = False)

# route to delete a chapter 
@app.route("/deleteChapter/<chapter_id>")
def delete_chapter(chapter_id):
    '''
    The function deletes the details of a chapter from the database; if the quiz for that chapter
    is not attempted
    '''
    name = session.get("username")

    if is_chapter_attempted(chapter_id):
        return render_template('admin_error.html', error="Can't delete - users have attempted quizzes in this chapter")
    
    chapter = Chapter.query.get(chapter_id)
    db.session.delete(chapter)
    db.session.commit()
    return redirect(url_for('admin_dashboard'))


# route to Quiz page 
@app.route('/quiz')
def quiz():
    '''
    The function redirects to quiz page.
    '''
    name = session.get("username")
    ob = get_quiz()
   
    return render_template("quiz.html", quizzes = ob)
    


####################################### CRUD OPERATIONS ON QUIZ #################################################
# route to add a quiz
@app.route('/addQuiz', methods = ["POST", "GET"])
def add_quiz():
    '''
    The function adds a quiz for a particular chapter.
    The admin can choose the chapter for the quiz by the dropdown (in hmtl frontend)
    After submitting the quiz details in the form the user is redirected to quiz page.
    '''
    name = session.get("username")

    if request.method == "POST":
        quiz_id = request.form.get('quiz_id')
        quiz_name = request.form.get("quiz_name")
        date = request.form.get("date_of_quiz")
        duration = request.form.get("duration")
        chapter_id = request.form.get("chapter_id")  # Get the selected chapter_id

        new_quiz = Quiz(quiz_id = quiz_id, quiz_name = quiz_name, date_of_quiz = date, duration = duration, chapter_id=chapter_id)
        db.session.add(new_quiz)
        db.session.commit()
        return redirect(url_for('quiz'))
    
    # Fetch all chapters to populate the dropdown
    chapters = Chapter.query.all()
    return render_template("add_edit_quiz.html", chapters = chapters, add_quiz = True)

# route to edit a quiz
@app.route('/editQuiz/<quiz_id>', methods = ["POST", "GET"])
def edit_quiz(quiz_id):
    '''
    This function edits a quiz which already exists in a chapter. 
    After editing the details the admin is redirected to dashboard.
    '''
    name = session.get("username")

    ob = get_quizDetails(quiz_id)
    if request.method == "POST":
        quiz_name = request.form.get("quiz_name")
        date = request.form.get("date_of_quiz")
        duration = request.form.get("duration")
        chapter_id = request.form.get("chapter_id")  # Get the selected chapter_id

        # Updating the details for quiz.
        ob.quiz_name = quiz_name
        ob.date_of_quiz = date
        ob.duration = duration
        ob.chapter_id = chapter_id
        db.session.commit()
        return redirect(url_for('quiz'))
    
    # Fetch all chapters to populate the dropdown
    chapters = Chapter.query.all()
    return render_template("add_edit_quiz.html", quiz = ob, chapters = chapters, add_quiz = False)


# route to delete a quiz
@app.route('/deleteQuiz/<quiz_id>', methods = ["POST", "GET"])
def delete_quiz(quiz_id):
    '''
    The function deletes the details of a quiz from the database; if the quiz is not attempted
    '''
    name = session.get("username")

    if is_quiz_attempted(quiz_id):
        return render_template('admin_error.html', error="Can't delete - users have attempted this quiz")
    
    quiz = Quiz.query.get(quiz_id)
    db.session.delete(quiz)
    db.session.commit()
    return redirect(url_for('quiz'))


####################################### CRUD OPERATIONS ON QUESTIONS #################################################
# route to add a question
@app.route('/addQuestion/<quiz_id>', methods=["POST", "GET"])
def add_question(quiz_id):
    '''
    The function gets the question details from the form and adds the details to 
    the database.
    Afetr submitting the details the user is directed to the quiz page.
    '''
    name = session.get("username")

    if request.method == "POST":
        question_title = request.form.get("question_title")
        statement = request.form.get("question_statement")
        option_1 = request.form.get("option_1")
        option_2 = request.form.get("option_2")
        option_3 = request.form.get("option_3")
        option_4 = request.form.get("option_4")
        answer = request.form.get("answer")

        # Create a new question object
        new_question = Question(
            question_title=question_title,
            question_statement = statement,
            quiz_id=quiz_id,
            option_1_id=option_1,
            option_2_id=option_2,
            option_3_id=option_3,
            option_4_id=option_4,
            answer_id=answer
        )
        db.session.add(new_question)
        db.session.commit()

        return redirect(url_for('quiz'))
    
    return render_template("add_edit_question.html", quiz_id=quiz_id, add_question = True)


# route to edit a question
@app.route('/editQuestion/<question_id>', methods = ["POST", "GET"])
def edit_question(question_id):
    '''
    This function edits a question which already exists in a quiz. 
    After editing the details the admin is redirected to dashboard.
    '''
    name = session.get("username")

    ob = get_questionDetails(question_id)
    if request.method == "POST":
        title = request.form.get("question_title")
        statement = request.form.get("question_statement")
        op1 = request.form.get("option_1")
        op2 = request.form.get("option_2")
        op3 = request.form.get("option_3")
        op4 = request.form.get("option_4")
        answer = request.form.get("answer") 

        # Update the details for question
        ob.question_title = title
        ob.question_statement = statement
        ob.option_1_id = op1
        ob.option_2_id = op2
        ob.option_3_id = op3
        ob.option_4_id = op4
        ob.answer_id = answer        
        db.session.commit()
        return redirect(url_for('quiz'))    

    return render_template("add_edit_question.html", question = ob, add_question = False)

# route to delete a question
@app.route("/deleteQuestion/<question_id>")
def delete_question(question_id):
    '''
    The function deletes the details of a questions from the database. If the quiz question 
    is not attempted.
    '''
    name = session.get("username")

    if is_question_attempted(question_id):
        return render_template('admin_error.html', error=f"Cannot delete question - it has been attempted by users")
    
    question = Question.query.get(question_id)
    db.session.delete(question)
    db.session.commit()
    return redirect(url_for('admin_dashboard'))

############################# User Dashboard Related Functionalities #################################

# Route to view quiz on user dashboard
@app.route('/view_quiz/<quiz_id>')
def view_quiz(quiz_id):
    '''
    Fetch the quiz details along with its questions
    ''' 
    name = session.get("username")
    if not name or session.get('role') != 'USER':
        return redirect(url_for('login'))

    quiz = get_quizDetails(quiz_id)    
    chapter = get_chapterDetails(quiz.chapter_id)
    subject = get_subjectDetails(chapter.subject_code)
    return render_template("view_quiz.html", quiz=quiz, subject = subject, chapter = chapter)

# start quiz when user clicks on attempt
@app.route('/start_quiz/<quiz_id>')
def start_quiz(quiz_id):
    '''
    The function fetches the quiz, chapter, subject details from database and 
    renders the attempt_quiz.html page.
    '''
    name = session.get("username")
    if not name or session.get('role') != 'USER':
        return redirect(url_for('login'))
    # quiz -> chapter, questions(rel)
    quiz = get_quizDetails(quiz_id)

    # chapter -> subject
    chapter = get_chapterDetails(quiz.chapter_id)

    subject = get_chapterDetails(chapter.subject_code)

    return render_template("attempt_quiz.html", quiz = quiz, chapter = chapter, subject = subject)


# Route to display the quiz results after quiz submission by the user
@app.route('/submitQuiz/<quiz_id>', methods=["POST"])
def submit_quiz(quiz_id):
    '''
    The functions gets the answers to the question for the quiz and adds the response details to the user.
    After the user clicks the submit button we redirect to the route for the quiz_results.
    '''
    name = session.get("username")
    if not name or session.get('role') != 'USER':
        return redirect(url_for('login'))
    user = User.query.filter_by(username=name).first()      # User details


    # Get user answer response from the form and storing them in a dictionary
    user_answers = {}
    print(request.form.items())
    for key, value in request.form.items():
        # key - question
        # value - option chosed for that particular question
        print(key, value)   
        if key.startswith("question_"):
            question_id = key.replace("question_", "")
            user_answers[question_id] = value

    # Calculating the marks scored using the supporter function i have defined in below.
    score = calculate_attempt_score(user_answers)

    # Creating a new Scores object
    new_attempt = Scores(user_id = user.id, quiz_id = quiz_id,
        time_stamp_of_attempt = datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        marks_scored = score
    )

    db.session.add(new_attempt)
    db.session.commit()

    # Saving individual responses with the committed attempt ID
    for question_id, selected_answer in user_answers.items():
        new_response = QuizAttempt(
            user_id=user.id,
            quiz_id=quiz_id,
            question_id=question_id,
            selected_answer=selected_answer,
            attempt_id=new_attempt.id  
        )
        db.session.add(new_response)

    db.session.commit()

    # Redirect to the results page
    return redirect(url_for('quiz_results', quiz_id=quiz_id, attempt_id=new_attempt.id))


# Route to display the quiz report 
@app.route('/quizResults/<quiz_id>/<int:attempt_id>')
def quiz_results(quiz_id, attempt_id):   
    '''
    This function gets all the data from the database and renders quiz_results.html page
    '''
    name = session.get("username")
    if not name or session.get('role') != 'USER':
        return redirect(url_for('login'))
    user = User.query.filter_by(username=name).first()

    # Fetchomg the quiz attempt details from database
    attempt = Scores.query.filter_by(id=attempt_id).first()
    quiz = Quiz.query.filter_by(quiz_id=quiz_id).first()
    chapter = Chapter.query.filter_by(chapter_id=quiz.chapter_id).first()
    subject = Subject.query.filter_by(subject_code=chapter.subject_code).first()

    # Fetching user responses for the current attempt
    user_responses = QuizAttempt.query.filter_by(attempt_id=attempt_id).all()

    # Converting the fetched response to a dictionary
    user_responses_dict = {}
    for response in user_responses:
        user_responses_dict[response.question_id] = response.selected_answer    

    # total number of questions in the quiz
    total_questions = len(quiz.questions)

    return render_template(
        "quiz_results.html", quiz=quiz, chapter=chapter, subject=subject,
         score=attempt.marks_scored, total_questions=total_questions, 
        user_responses=user_responses_dict, attempt=attempt
    )


######################################### Admin Summary ###################################################

# Route to admin_summary page
@app.route('/admin_summary')
def admin_summary():
    '''
    The function gets all the user data from the User table.
    '''
    name = session.get("username")
    if not name or session.get('role') != 'ADMIN':
        return redirect(url_for('login'))
    users = User.query.filter_by(role = "USER").all()  # Get all users
    return render_template('admin_summary.html', users=users)

# Route to view a specific user's quiz details from the admin summary page
@app.route('/admin_summary/user_details/<int:user_id>')
def admin_user_details(user_id):
    '''
    This function get all the quiz attempts done by a specific user and stores
    the attempts in a dictionary
    '''
    name = session.get("username")
    if not name or session.get('role') != 'ADMIN':
        return redirect(url_for('login'))
    user = User.query.get(user_id)
    quiz_attempts = Scores.query.filter_by(user_id=user.id).all()    
    
    # Dictionary to store the quizzes' attempted by the user
    user_attempts = {}
        # Key -> quiz_id, value -> dicttionary = {quiz_id: {quiz_name, subject, ...}}
    for attempt in quiz_attempts:
        quiz = Quiz.query.get(attempt.quiz_id)
        chapter = Chapter.query.get(quiz.chapter_id)
        subject = Subject.query.get(chapter.subject_code)
        
        # Storing the quiz details and scores in user_responses
        user_attempts[attempt.id] = {
            'quiz_name': quiz.quiz_name,
            'subject': subject.subject_name,
            'chapter': chapter.chapter_name,
            'marks_scored': attempt.marks_scored,
            'date': attempt.time_stamp_of_attempt
        }
    
    return render_template('a_user_details.html', user=user, attempts=user_attempts)

######################################### User Summary ###################################################

# Route to user score page which displays the scores 
@app.route('/user_scores')
def user_quiz_attempts():
    '''
    This function is trigerred when the user hits the scores link in the navbar.
    It displays all the quiz attempts and its scores for a particular user.

    '''
    name = session.get("username")
    if not name or session.get('role') != 'USER':
        return redirect(url_for('login'))
    user = User.query.filter_by(username = name).first()        # User details
    quiz_scores = Scores.query.filter_by(user_id=user.id).all()         # All scores details of the quiz attempted by that user
    # print("Quiz Attempt: ", quiz_scores)

    
    # Storing the quizzes and quiz score details in a dictionary
    quizzes = {}
        # Key -> quiz_id, value -> quiz object
    user_responses = {}
        # Key -> quiz_id, value -> dicttionary
    num_questions = 0
    for score in quiz_scores:
        quiz = Quiz.query.get(score.quiz_id)
        quizzes[score.quiz_id] = quiz

        # count the number of questions in the quiz
        num_questions = Question.query.filter_by(quiz_id = score.quiz_id).count()

        # Storing the quiz details and scores in user_responses
        user_responses[score.quiz_id] = {
            "quiz_title": quiz.quiz_name,
            "num_questions": num_questions,
            "date_of_attempt": score.time_stamp_of_attempt,
            "duration": quiz.duration,
            "marks_scored": score.marks_scored,
        }

    # print("user responses: ", user_responses)
    # print("quizzess: ", quizzes)
    return render_template('user_scores.html', quiz_scores = quiz_scores, 
                          user_responses = user_responses, quizzes = quizzes, no_of_questions = num_questions)


# Route to user summary page
@app.route('/user_summary')
def user_summary():
    '''
    This function is trigerred when the user hits the summary link in the navbar.
    It counts the total number of subject, chapter, quizzes, attempted quizzes and passes it to the html template.
    It calculates the chapter wise average scores.
    Renders the user_summary page

    '''
    name = session.get("username")
    if not name or session.get('role') != 'USER':
        return redirect(url_for('login'))
    user = User.query.filter_by(username=name).first()

    # Calculate the total number of subjects, chapters, quizzes, and attempted_quizzes
    total_subjects = Subject.query.count()
    total_chapters = Chapter.query.count()
    total_quizzes = Quiz.query.count()
    attempted_quizzes = Scores.query.filter_by(user_id=user.id).count()

    # Calculate chapter averages using supporter function
    chapter_avg_scores = calculate_chapter_averages(user.id)

    return render_template('user_summary.html', user=user,
                         total_subjects=total_subjects, total_chapters=total_chapters,
                         total_quizzes=total_quizzes, attempted_quizzes=attempted_quizzes,
                         chapter_avg_scores=chapter_avg_scores)
        

######################################### Search Functionality ###################################################

@app.route("/search", methods = ["GET", "POST"])
def search():
    '''
    This function searches for subject, quiz, or user
    '''
    name = session.get("username")

    if request.method == "POST":
        search_query = request.form.get("search_query")
        subject = search_subject(search_query)
        quiz = search_quiz(search_query)
        user = search_user(search_query)
        if subject:
            return render_template("admin_dashboard.html", subjects = subject)
        elif user:
            return render_template("admin_summary.html", users = user)

    return redirect(url_for("admin_dashboard"))

@app.route("/search/user", methods = ["GET", "POST"])
def search_user_dashboard():
    '''
    This function searches for subject, quiz, or user
    '''
    name = session.get("username")
    if request.method == "POST":
        search_query = request.form.get("search_query")
        subject = search_subject(search_query)
        quiz = search_quiz(search_query)
        user = search_user(search_query)
        date_now = date.today()         #to get current date
        date_today_str = date_now.strftime("%Y-%m-%d")      # Specifyin the date format
        if subject:
            return render_template("user_dashboard.html", subjects = subject, date_now = date_today_str)
    return redirect(url_for("user_dashboard"))
########################################### Supporter Functions ############################################################
def is_valid_password(password):
    """
    Validates that the password has:
    - At least 8 characters
    - At least one uppercase letter
    - At least one lowercase letter
    - At least one digit
    - At least one special character
    """
    pattern = re.compile(
        r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[\W_]).{8,}$'
    )
    return bool(pattern.match(password))

def get_subjects():            
    # This function will return all the subjects from the database
    subjects = Subject.query.all()
    return subjects

def get_quiz():   
    # This function will return all the quizzes from the database
    quizzes = Quiz.query.all()
    return quizzes

def get_chapterDetails(chapter_id):         # USED IN MILESTONE 3
    # Gives details of a particular chapter using the chapter_id provided as the parameter
    chapter = Chapter.query.filter_by(chapter_id = chapter_id).first()
    return chapter

def get_subjectDetails(subject_code):       # USED IN MILESTONE 3
    # Gives details of a particular subject using the subject_id provided as the parameter
    subject = Subject.query.filter_by(subject_code = subject_code).first()
    return subject

def get_questionDetails(question_id):       # milestone 3
    # Gives details of a particular subject using the question_id provided as the parameter
    question = Question.query.filter_by(question_id = question_id).first()
    return question

def get_quizDetails(quiz_id):
    # Gives details of a particular quiz using the quiz_id provided as the parameter
    quiz = Quiz.query.filter_by(quiz_id = quiz_id).first()
    return quiz

def calculate_attempt_score(user_answers):
    # Calculates the score for a quiz attempt by comparing user answers with correct answers
    # Returns a Tuple of (score, total_questions)    
    score = 0
    print(user_answers.items())
    for question_id, selected_answer in user_answers.items():
        question = Question.query.filter_by(question_id=question_id).first()
        if selected_answer == question.answer_id:
            score += 1
    return score


def calculate_chapter_averages(user_id):
    """
    Calculates average scores per chapter 
    It gets all the score details for a user and 
    returns List of dictionaries containing chapter performance data
    """
    chapter_averages = []
    
    # Get all scores for this user
    user_scores = Scores.query.filter_by(user_id=user_id).all()
    
    # Dictionary to 
    chapter_scores = {}
        # key -> chapter_key, value -> score for that particular chapter quiz
    for score in user_scores:
        # fetching quiz, chapter, subject details for each score
        quiz = Quiz.query.get(score.quiz_id)            
        chapter = Chapter.query.get(quiz.chapter_id)            
        subject = Subject.query.get(chapter.subject_code)

        # Getting chapterid , cname and subject name for the quiz score            
        chapter_key = (chapter.chapter_id, chapter.chapter_name, subject.subject_name)
        
        if chapter_key not in chapter_scores:
            chapter_scores[chapter_key] = []
            
        # What if the user attempts a quiz multiplt times, then we keep the chapter key same and just
        # append the score in the value list of already existing chapter_key in the dictionary
        chapter_scores[chapter_key].append(score.marks_scored)


    # Calculate averages
    for (chapter_id, chapter_name, subject_name), scores in chapter_scores.items():
        chapter_averages.append({
            'chapter_id': chapter_id,
            'chapter_name': chapter_name,
            'subject_name': subject_name,
            'avg_score': sum(scores) / len(scores),
            'attempt_count': len(scores)
        })
    
    return chapter_averages



def is_quiz_attempted(quiz_id):
    #heck if a quiz has any attempts
    attempted = Scores.query.filter_by(quiz_id=quiz_id).first()
    if attempted:
        return True
    else:
        return False

def is_chapter_attempted(chapter_id):
    #Check if any quiz in chapter has attempts
    quizzes = Quiz.query.filter_by(chapter_id=chapter_id).all()
    attempted = False
    for quiz in quizzes:
        quiz_attempt = is_quiz_attempted(quiz.quiz_id)
        if quiz_attempt:
            attempted = True
            break 
    return attempted

def is_subject_attempted(subject_code):
    #Check if any quiz in subject has attempts#
    chapters = Chapter.query.filter_by(subject_code=subject_code).all()
    attempted = False
    for chapter in chapters:
        chapter_attempt = is_chapter_attempted(chapter.chapter_id)
        if chapter_attempt:
            attempted = True
            break 
    return attempted


def is_question_attempted(question_id):
    #Check if a question has any attempts
    #Check if any quiz in subject has attempts#
    attempted = QuizAttempt.query.filter_by(question_id=question_id).first()
    if attempted:
        return True
    else:
        return False
    

# Search patterns
def search_subject(text):       #used in milestone 6
    return Subject.query.filter(Subject.subject_name.like(f"{text}%")).all()

def search_quiz(text):       #used in milestone 6
    return Quiz.query.filter(Quiz.quiz_name.like(f"{text}%")).all()

def search_user(text):       #used in milestone 6
    return User.query.filter(User.username.like(f"{text}%")).all()
