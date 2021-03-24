'''
Created on Mar. 24, 2021

@author: Pete Harris
'''
from flask import (
    Blueprint, render_template
)
#from werkzeug.exceptions import abort

bp = Blueprint("pages", __name__)

@bp.route("/", methods=["GET"])
def mainpage():
    return render_template("main.html")
