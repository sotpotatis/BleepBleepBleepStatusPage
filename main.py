'''Main.py
Does all the main stuff...
Yeah, this is where everything flows together beautifully, like a peaceful river flowing in the Japanese countryside.
Haven't been there, but I have seen it on television.

This is yet another project started by sotpotatis - enjoy <3
'''
from flask import Flask
import logging, internal_libraries.data as data

#Logging!
logger = logging.getLogger(__name__)
#Main configuration for logging
logging.basicConfig(level=logging.DEBUG)

#Main configuration
server_configuration = data.get_configuration("server")
def create_app():
    '''Function for creating the main app.'''
    app = Flask(__name__) #This is a great start!
    #...but we need to add some blueprints
    #UI/Frontend
    logger.info("Registering UI-Frontend blueprint...")
    from routes.ui_frontend import uifr_app as ui_frontend_blueprint
    app.register_blueprint(ui_frontend_blueprint)
    logger.info("Registering API blueprint...")
    from routes.api import api_app as api_blueprint
    app.register_blueprint(api_blueprint)
    logger.info("Blueprints registered.")
    #Add required Jinja extension (see index.html, for instance)
    logger.info("Adding Jinja2 extensions...")
    app.jinja_env.add_extension("jinja2.ext.do")
    logger.info("Jinja2 extensions added.")
    return app #Return the final app

if __name__ == '__main__':
    logger.info("Creating app (inside ___name__ == 'main' loop)...")
    app = create_app()
    logger.info("App created (inside __name__ == 'main' loop).")
    app_parameters = server_configuration["app_parameters"]
    host = app_parameters["host"]
    port = app_parameters["port"]
    debug = app_parameters["debug"]
    #Check debug option and warn if it is enabled.
    if debug:
        logger.warning("[WARNING] You are running the app using debug=true. This is ONLY recommended when doing local debugging. NEVER do this in a production environment!")
    logger.info(f"Starting app on {host}:{port}, debug: {debug}...")
    #Start serving the app
    app.run(
        host=host,
        port=port,
        debug=debug
    )

# See PyCharm help at https://www.jetbrains.com/help/pycharm/
