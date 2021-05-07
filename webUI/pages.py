'''
Created on Mar. 24, 2021

@author: Pete Harris
'''
from flask import (
    Blueprint, render_template
)
import math
from webUI.db import hardware_data
#from werkzeug.exceptions import abort

bp = Blueprint("pages", __name__)

@bp.context_processor
def utility_processor():
    return dict(str=str, int=int, cos=math.cos, sin=math.sin, radians=math.radians, round=round, floor=math.floor)

@bp.route("/", methods=["GET"])
def mainpage():
    return render_template("main.html")

@bp.route("/hardware", methods=["GET"])
def hardwaredata():
    return render_template("hardware_list.html", hardware=hardware_data())

@bp.route("/playground", methods=["GET"])
def playground():
    return render_template("svgplayground.html")
