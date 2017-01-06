from flask import Flask
from flask_cors import CORS
from src.common.Respond import Respond

from src.controllers.usersController import users_controller
from src.controllers.coursesController import courses_controller
from src.controllers.subjectsController import subjects_controller
from src.controllers.chaptersController import chapters_controller
from src.controllers.conceptsController import concepts_controller
from src.controllers.appController import app_controller
from src.controllers.paymentsController import payments_controller

app = Flask(__name__)
CORS(app)


@app.route('/')
def index():
    return Respond.success("Welcome to Noted Api")


@app.errorhandler(404)
def page_not_found(e):
    return Respond.not_found()


@app.errorhandler(500)
def page_not_found(e):
    return Respond.error("Some error occurred")


app.register_blueprint(users_controller, url_prefix="/users")
app.register_blueprint(subjects_controller, url_prefix="/subjects")
app.register_blueprint(courses_controller, url_prefix="/courses")
app.register_blueprint(chapters_controller, url_prefix="/chapters")
app.register_blueprint(concepts_controller, url_prefix="/concepts")
app.register_blueprint(app_controller, url_prefix="/study")
app.register_blueprint(payments_controller, url_prefix="/study/payments")