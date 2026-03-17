import os

from flask import (
    abort,
    current_app,
    Blueprint,
    render_template,
    Response
)
from jinja2 import (
    TemplateNotFound
)

from imports import config
from imports import json

CONFIG = config.load_config(config.SERVER_CONFIG)
GAME_LIST = [file for file in os.listdir('static/games') if os.path.isfile(f'static/games/{file}')]

bp = Blueprint("games", __name__, url_prefix="/games")

class Imports:
    def __init__(self, imports: list):
        self.templates = []
        self.statics = []
        for imp in imports:
            if imp.startswith("templates/"):
                self.templates.append(imp.lstrip("templates/"))
            elif imp.startswith("static/"):
                self.statics.append(imp.lstrip("static/"))
            else:
                current_app.logger.error("Import config path doesn't start with valid route")

#TODO: support grid option to json
class Game:
    def __init__(self, json_config):
        cfg = json.load_json(json_config)
        self.version = cfg.get("version", "")
        self.cmd_name = cfg.get("cmd_name", "")
        self.full_name = cfg.get("full_name", "")
        self.imports = Imports(cfg.get("imports", []))

@bp.route('/')
def games():
    try:
        script = render_template(
            "client/games",
            game_list=GAME_LIST
        )
    except TemplateNotFound:
        abort(404)

    return Response(script, mimetype="text/plain")

@bp.route('/<name>')
def game_name(name):
    if name not in GAME_LIST:
        abort(404)

    game_obj = Game(f'static/games/configs/{name}.json')
    try:
        script = render_template(
            "engine/base-game",
            game = game_obj
        )
    except TemplateNotFound:
        abort(404)

    return Response(script, mimetype="text/plain")

