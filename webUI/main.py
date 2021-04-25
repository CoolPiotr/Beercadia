'''
Created on Mar. 24, 2021

@author: Pete Harris
'''
import os
from flask import Flask

def create_app(test_config=None):
    # create and configure the app
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
            SECRET_KEY="dev: not so seecret key",
            APP_PROJECT_FOLDER="Beercadia"
    )
    
    if test_config is None:
        # load the instance config, if it exists, when not testing
        app.config.from_pyfile("config.py", silent=True)
    else:
        app.config.from_mapping(test_config)
    
    # ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass
    
    
    from webUI import error
    app.register_blueprint(error.blueprint)
    
    
    from webUI import pages
    app.register_blueprint(pages.bp)
    app.add_url_rule("/", endpoint="index")
    
    
    #from website import error
    #app.register_blueprint(error.bp)
    
    return app

if __name__ == '__main__':
    from socket import gethostname
    #from website import db
    #db.init_db()    # might want this for database in the future, for running on PythonAnywhere from their bash script.
    if 'liveconsole' not in gethostname():
        # this won't run even from console if run from PythonAnywhere console (named 'liveconsole'),
        # so this script can be used to just activate DB in previous line.
        app = create_app()
        app.run()
        