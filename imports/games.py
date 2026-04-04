import os
import tarfile
import tempfile

from flask import (
    abort,
    after_this_request,
    Blueprint,
    render_template,
    Response,
    send_file
)
from jinja2 import TemplateNotFound

from imports import config
from imports.game_objs import Game


## Globals ##
CONFIG = config.load_config(config.SERVER_CONFIG)
GAME_LIST = [Game(game).source_name for game in os.listdir('static/games') if os.path.isfile(f'static/games/{game}/{game}')]

bp = Blueprint("games", __name__, url_prefix="/games")


## Functions ##
@bp.route('/')
def games():
    try:
        script = render_template(
            "client/games",
            game_list=[Game(game) for game in os.listdir('static/games') if os.path.isfile(f'static/games/{game}/{game}')]
        )
    except TemplateNotFound:
        abort(404)

    return Response(script, mimetype="text/plain")


@bp.route('/<name>')
def game_name(name):
    if name not in GAME_LIST:
        abort(404)

    game_obj = Game(name)
    try:
        script = render_template(
            "engine/game-base",
            game = game_obj
        )
    except TemplateNotFound:
        abort(404)

    return Response(script, mimetype="text/plain")


@bp.route('/<name>-utils')
def game_utils(name):
    if name not in GAME_LIST:
        abort(404)

    game_obj = Game(name)
    try:
        script = render_template(
            "engine/game-utils",
            game = game_obj
        )
    except TemplateNotFound:
        abort(404)

    return Response(script, mimetype="text/plain")


@bp.route('/<name>-common')
def game_common(name):
    if name not in GAME_LIST:
        abort(404)

    game_obj = Game(name)
    try:
        script = render_template(
            "engine/game-common",
            game = game_obj
        )
    except TemplateNotFound:
        abort(404)

    return Response(script, mimetype="text/plain")


@bp.route("/<name>-sprites.tar.gz")
def get_sprites(name):
    # Check that sprite dir exists
    sprite_dir=f'static/games/{name}/sprites'
    if not os.path.isdir(sprite_dir):
        abort(404, "Directory not found")

    # Get tmp path for sprite .tar.gz
    fd, tmp_path = tempfile.mkstemp(suffix=".tar.gz")
    os.close(fd)

    # gzip sprites
    with tarfile.open(tmp_path, "w:gz") as tar:
        tar.add(sprite_dir, arcname=".")

    # Set up cleanup
    @after_this_request
    def cleanup(response):
        os.remove(tmp_path)
        return response

    # Send out gzipped sprites
    return send_file(
        tmp_path,
        as_attachment=True,
        download_name=f"{name}-sprites.tar.gz",
        mimetype="application/gzip",
    )

@bp.route('/<name>-demo')
def game_demo(name):
    if name not in GAME_LIST:
        abort(404)

    # Concatenate all demo templates to one file
    prefix = "engine/game-demo"
    demo_files = [
        "game-demo",
        "scenes/pause",
        "scenes/title"
    ]
    game_obj = Game(name)
    script=""
    for file in demo_files:
        try:
            script += render_template(
                f"{prefix}/{file}",
                game = game_obj
            )
        except TemplateNotFound:
            abort(404)

    return Response(script, mimetype="text/plain")

