import os
from flask import Flask, request, abort, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS, cross_origin
import random
from collections import Counter

from models import setup_db, Question, Category

QUESTIONS_PER_PAGE = 10


def get_common_category(categories, questions):
    if questions == []:
        return ""
    c = Counter([q["category"] for q in questions])
    return categories[c.most_common(1)[0][0]]


def create_app(test_config=None):
    # create and configure the app
    app = Flask(__name__)
    setup_db(app)
  
    '''
    Set up CORS. Allow '*' for origins. Delete the sample route after completing the TODOs
    '''
    CORS(app)

    '''
    Use the after_request decorator to set Access-Control-Allow
    '''
    @app.after_request
    def after_request(response):
        response.headers.add('Access-Control-Allow-Origin', 'http://localhost:3000')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        response.headers.add('Access-Control-Allow-Methods', 'GET, POST, DELETE')
        response.headers.add('Access-Control-Allow-Credentials', 'true')
        return response
    '''
    Create an endpoint to handle GET requests 
    for all available categories.
    '''
    @app.route('/categories')
    def get_available_categories():
        categories = {cat.id: cat.type.lower() for cat in Category.query.all()}
        if categories:
            return jsonify({
                "success": True,
                "categories": categories
            })
        else:
            abort(404)


    '''
    Create an endpoint to handle GET requests for questions, 
    including pagination (every 10 questions). 
    This endpoint should return a list of questions, 
    number of total questions, current category, categories. 

    TEST: At this point, when you start the application
    you should see questions and categories generated,
    ten questions per page and pagination at the bottom of the screen for three pages.
    Clicking on the page numbers should update the questions. 
    '''
    @app.route("/questions")
    def get_questions():
        page = request.args.get('page', 1, type=int)
        questions = [question.format() \
            for question in Question.query.order_by(Question.id).all()]
        categories = {cat.id: cat.type.lower() for cat in Category.query.all()}
        start = (page-1) * QUESTIONS_PER_PAGE
        end = start + QUESTIONS_PER_PAGE
        selected_questions = questions[start:end]
        if len(selected_questions) == 0:
            abort(404)
        return jsonify({
                "success": True,
                "questions": selected_questions,
                "total_questions": len(questions),
                "categories": categories,
                "current_category":
                    get_common_category(categories, selected_questions)
            })


    '''
    Create an endpoint to DELETE question using a question ID. 

    TEST: When you click the trash icon next to a question, the question will be removed.
    This removal will persist in the database and when you refresh the page. 
    '''
    @app.route("/questions/<int:question_id>", methods=["DELETE"])
    def delete_question(question_id):
        try:
            question = Question.query.get(question_id)
            if question is None:
                abort(404)
            question.delete()
            return jsonify({
                "success": True,
                "question_id": question_id
            })
        except Exception as ex:
            print(ex)
            abort(422)

    '''
    Create an endpoint to POST a new question, 
    which will require the question and answer text, 
    category, and difficulty score.

    TEST: When you submit a question on the "Add" tab, 
    the form will clear and the question will appear at the end of the last page
    of the questions list in the "List" tab.  
    '''
    @app.route("/questions", methods=['POST'])
    def add_question():
        try:
            assert request.json["question"], "A question can't be empty!!"
            assert request.json["answer"], "An answer can't be empty!!"
            question = Question(request.json["question"],
                                request.json["answer"],
                                request.json["category"],
                                request.json["difficulty"])
            question.insert()
            return jsonify({
                "success": True
            })
        except Exception as ex:
            print(ex)
            abort(422)

    '''
    Create a POST endpoint to get questions based on a search term. 
    It should return any questions for whom the search term 
    is a substring of the question. 

    TEST: Search by any phrase. The questions list will update to include 
    only question that include that string within their question. 
    Try using the word "title" to start. 
    '''
    @app.route("/search", methods=["POST"])
    def query_questions():
        try:
            search_query = request.json["search_term"]
            filtered_questions = [q.format() for q in Question.query.filter(
                Question.question.ilike(f'%{search_query}%')).all()]
            categories = {cat.id: cat.type.lower() for cat in Category.query.all()}
            return jsonify({
                "success": True,
                "questions": filtered_questions,
                "total_questions": len(filtered_questions),
                "current_category":
                    get_common_category(categories, filtered_questions)
            })
        except Exception as ex:
            abort(422)


    '''
    Create a GET endpoint to get questions based on category. 

    TEST: In the "List" tab / main screen, clicking on one of the 
    categories in the left column will cause only questions of that 
    category to be shown. 
    '''
    @app.route("/categories/<int:category_id>/questions")
    def get_questions_by_category(category_id):
        try:
            filtered_questions = [q.format() \
                for q in Question.query.filter(
                    Question.category == category_id).all()]
            categories = {cat.id: cat.type.lower() for cat in Category.query.all()}
            return jsonify({
                "success": True,
                "questions": filtered_questions,
                "total_questions": len(filtered_questions),
                "current_category": categories[category_id]
            })
        except Exception as ex:
            abort(404)

    '''
    Create a POST endpoint to get questions to play the quiz. 
    This endpoint should take category and previous question parameters 
    and return a random questions within the given category, 
    if provided, and that is not one of the previous questions. 

    TEST: In the "Play" tab, after a user selects "All" or a category,
    one question at a time is displayed, the user is allowed to answer
    and shown whether they were correct or not. 
    '''
    @app.route("/quizzes", methods=["POST"])
    def quiz():
        try:
            previous_questions = set(request.json["previous_questions"])
            category_id = request.json["quiz_category"]["id"]
            if category_id == 0:
                category_questions = Question.query.all()
            else:
                category_questions = \
                    Question.query.filter(Question.category == category_id).all()
            random.shuffle(category_questions)
            for q in category_questions:
                if q.id not in previous_questions:
                    return jsonify({
                        "success": True,
                        "question": q.format()
                    })
            return jsonify({
                "success": True,
                "question": ''
            })
        except Exception as ex:
            print(ex)
            abort(422)
        
        
    

    '''
    Create error handlers for all expected errors 
    including 404 and 422. 
    '''
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({
            "success": False,
            "message": "Not Found"
        }), 404
    
    @app.errorhandler(422)
    def unprocessable(error):
        return jsonify({
            "success": False,
            "message": "Unprocessable"
        }), 422
    
    return app
