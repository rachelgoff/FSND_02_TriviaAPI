import os
import sys
from flask import Flask, request, abort, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.sql import func
from flask_cors import CORS
import random

from models import setup_db, Question, Category

QUESTIONS_PER_PAGE = 10

def create_app(test_config=None):
  # create and configure the app
  app = Flask(__name__)
  setup_db(app)

  '''
  Set up CORS. Allow '*' for origins. 
  '''

  CORS(app, resource={r"*/api/*": {"origins": "*"}})


  '''
  Use the after_request decorator to set Access-Control-Allow.
  '''
  @app.after_request
  def after_request(response):
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type, Authorization, true')
    response.headers.add('Access-Control-Allow-Methods', 'GET, POST, PATCH, DELETE, OPTIONS')
    response.headers.add('Access-Control-Allow-Credentials', 'true')
    
    return response

  def paginated_questions(request, questions):
    page = request.args.get('page', 1, type=int)
    start = (page - 1) * QUESTIONS_PER_PAGE
    end = start + QUESTIONS_PER_PAGE
    
    formatted_questions = [question.format() for question in questions]
    current_questions = formatted_questions[start:end]
    
    return current_questions

  def get_questions_by_category(category_id):
    questions_by_categories = Question.query.filter_by(category=category_id).all()
    formatted_questions_by_categories = [question.format() for question in questions_by_categories]
    
    return formatted_questions_by_categories

  '''
  Create an endpoint to handle GET requests for all available categories.
  '''
  @app.route('/categories/')
  @app.route('/categories')
  def get_categories():
    categories = Category.query.all()
    formatted_categories = [category.format() for category in categories]
    
    return jsonify({
      'success': True,
      'categories': formatted_categories
      })

  '''
   An endpoint to handle GET requests for questions, including pagination (every 10 questions). This endpoint returns a list of questions, 
  number of total questions, current category, categories. 
  '''
  #Chrome will redirect with trailing slash automatically. Added two decorators to resolve different browsers behavior issue.
  @app.route('/questions/')
  @app.route('/questions') 
  def get_questions():
    category_list = []
    category_type = ''

    try:
      questions = Question.query.order_by('id').all()
      formatted_total_questions = [question.format() for question in questions]
      current_questions = paginated_questions(request, questions)
    except:
      abort(400)

    if len(current_questions) == 0:
      abort(404)
    else:
      categories = Category.query.all()
      for category in categories:
        category_list.append(category.type)

      return jsonify({
        'success': True,
        'questions': current_questions,
        'categories': category_list,
        'total_questions': len(questions)
        })

  '''
  An endpoint to DELETE question using a question ID. 
  '''
  @app.route('/questions/<int:question_id>', methods=['DELETE'])
  def delete_question(question_id):
    try:
      question = Question.query.get(question_id)
      if question is None:
        abort(404)
      
      question.delete()
      questions = Question.query.order_by('id').all()
      current_questions = paginated_questions(request, questions)

      return jsonify({
          "success": True
          })
    except:
      abort(404)
  
  '''
  An endpoint to POST a new question, which will require the question and answer text, category, and difficulty score.
  '''

  @app.route('/questions', methods=['POST'])
  def create_question():
    body = request.get_json()
    new_question = body.get('question')
    new_answer = body.get('answer')
    new_category = body.get('category')
    new_difficulty = body.get('difficulty')

    try:
      new_question = Question(question=new_question, answer=new_answer, category=new_category, difficulty=new_difficulty)
      new_question.insert()
      questions = Question.query.order_by('id').all()
      current_questions = paginated_questions(request, questions)
      categories = Category.query.all()
      formatted_categories = [category.format() for category in categories]

      return jsonify({
          "success": True,
          "question": new_question.question,
          "answer": new_question.answer,
          "current_category": new_question.category,
          "difficulty": new_question.difficulty,
          "questions": current_questions,
          # "total_questions": len(questions),
          # "categories" : formatted_categories
        })
    except:
      abort(422)

  '''
  @TODO: 
  A POST endpoint to get questions based on a search term. It returns any questions for whom the search term is a substring of the question. 
  '''
  @app.route('/questions/search', methods=['POST'])
  def search_questions():
    try:
      body = request.get_json()
      search = body.get('searchTerm')
      search_results = Question.query.filter(Question.question.ilike("%" + search + "%"))
      formatted_matched_questions = [search_result.format() for search_result in search_results]

      questions = Question.query.order_by('id').all()
      formatted_total_questions = [question.format() for question in questions]

      return jsonify({
          "success": True,
          "questions": formatted_matched_questions,
          "total_questions": formatted_total_questions,
          "current_category": formatted_matched_questions[0]['category'],
          "current_question":formatted_matched_questions[0]
        })
    except:
      abort(400)


  '''
  A GET endpoint to get questions based on category. 
  '''
  @app.route('/categories/<int:category_id>/questions', methods=['GET'])
  def get_by_category(category_id):
      try:
          questions_by_categories = Question.query.filter_by(category=category_id).all()
          formatted_questions_by_categories = [question.format() for question in questions_by_categories]

          total_questions = Question.query.order_by('id').all()
          formatted_total_questions = [question.format() for question in total_questions]

          return jsonify({
            "success": True,
            "questions": formatted_questions_by_categories,
            "total_questions": formatted_total_questions,
            "current_category": formatted_questions_by_categories[0]['category']
            })

      except:
        abort(400)


  '''
  A POST endpoint to get questions to play the quiz. This endpoint takes category and previous question parameters and returns a random questions within the given category, 
  if provided, and that is not one of the previous questions. 

  '''
  @app.route('/quizzes', methods=['POST'])
  def get_next_question():
    try:
      body = request.get_json()
      previous_questions = body.get('previous_questions')
      quiz_category = body.get('quiz_category')
      if quiz_category == 0: # When ALL is select, start next question from a random category
        next_questions = Question.query.filter(Question.id.notin_(previous_questions)).order_by(func.random()).limit(1)
      else:
        next_questions = Question.query.filter(Question.category == quiz_category, Question.id.notin_(previous_questions)).order_by(func.random()).limit(1)
      formatted_next_questions = [question.format() for question in next_questions]

      if len(formatted_next_questions) > 0:
        return jsonify({
          "success": True,
          "question": formatted_next_questions[0], # the first element from the question list
          "previousQuestions": previous_questions,
          "guess": '',
          "showAnswer": False
          })
      else:
        return jsonify({
          "success": False
          })

    except:
      abort(400)

  '''
  Error handlers for all expected errors. 
  '''

  @app.errorhandler(404)
  def not_found(error):
    return jsonify({
      "success": False,
      "error": 404,
      "message": "Resource not found"
      }), 404

  @app.errorhandler(400)
  def bad_request(error):
    return jsonify({
      "success": False,
      "error": 400,
      "message": "Bad request"
      }), 400

  @app.errorhandler(422)
  def unprocessable_entity(error):
    return jsonify({
      "success": False,
      "error": 422,
      "message": "Unprocessable entity"
      }), 422

  @app.errorhandler(500)
  def internal_server_error(error):
    return jsonify({
      "success": False,
      "error": 500,
      "message": "Internal server error"
      }), 500

  @app.errorhandler(405)
  def method_not_allowed(error):
    return jsonify({
      "success": False,
      "error": 405,
      "message": "Method not allowed"
      }), 405

  
  return app

    