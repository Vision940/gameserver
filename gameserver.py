#!/usr/bin/env python3

import signal

from flask import (
    Flask,
    render_template,
    request,
    Response
)

from server import config # server config loader
from server import db # db connection handling
from server.games import games # game module handling
from server import man # man index and html/terminal pages

from server import __version__ as SERVER_VER # server version
from server.api.api import Api # api object

# Initialize app
app = Flask(__name__)

# Register import blueprints
app.register_blueprint(games.bp)
app.register_blueprint(man.bp)
api_routes = [
    "admin",
    "user"
]
api = Api(*api_routes, name="api")
api.register_api(app)

# Initialize game blueprints
games.import_game_bps(app)

# Initialize database
db.init_pool()

# Save SERVER_CONFIG as CONFIG for readability
CONFIG = config.SERVER_CONFIG

# Set up exit handler
def handle_exit(*args):
    db.close_pool()
    raise KeyboardInterrupt()
signal.signal(signal.SIGINT, handle_exit)
signal.signal(signal.SIGTERM, handle_exit)


@app.route('/')
def index():
    script = render_template(
        "client/init",
        url=request.host_url.rstrip("/"),
        admins=CONFIG.admins,
        server_ver=SERVER_VER
    )

    return Response(script, mimetype="text/plain")


##############
# Completion #
##############

@app.route('/templates/<name>-completion')
def completion(name):
    script = render_template(
        "client/completion",
        game=name,
        game_list=games.GAME_CMDS
    )

    return Response(script, mimetype="text/plain")


@app.route('/templates/<name>-alias-completion')
def alias_completion(name):
    script = render_template(
        "client/alias-completion",
        alias=name
    )

    return Response(script, mimetype="text/plain")


########
# Main #
########

if __name__ == '__main__':
    app.run(host=CONFIG.host, port=CONFIG.port, debug=True, threaded=True)

