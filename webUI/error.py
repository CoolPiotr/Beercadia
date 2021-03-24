'''
Created on Mar. 24, 2021

@author: Pete Harris
'''
from flask import Blueprint, jsonify, render_template, current_app
import traceback

blueprint = Blueprint("error", __name__)

@blueprint.app_errorhandler(500)
def handle_server_error_webpage(error):
    return render_template("error.html", error=error, estring=str(error), traceback=htmlFormatTraceback(traceback.format_exc()))


def htmlFormatTraceback(trace):
    err = ""
    code = ""
    file = ""
    for i, ln in enumerate(reversed(trace.split("\n"))):
        if i == 1:
            err = ln
        elif i % 2 == 0:
            code = ln
        elif i % 2 == 1:
            file = ln
            if current_app.config["APP_PROJECT_FOLDER"] in file:
                codefile, codeline, codefunc = file.split(",")
                codefunc = codefunc[4:]
                codeline = codeline[6:]
                codefile = codefile.split(current_app.config["APP_PROJECT_FOLDER"])[1][1:-1]
                return ( err, code, codefile, codeline, codefunc )
    return ( err, "", "" )




class CustomErrorTemplate(Exception):
    status_code = 999
    
    def __init__(self, message, status_code=None, payload=None):
        Exception.__init__(self)
        self.message = message
        if status_code is not None:
            self.status_code = status_code
        self.payload = payload
    
    def to_dict(self):
        rv = dict(self.payload or ())
        rv["message"] = self.message
        return rv

@blueprint.errorhandler(CustomErrorTemplate)
def handle_custom_error_template_restapi(error):
    response = jsonify(error.to_dict())
    response.status_code = error.status_code
    return response

