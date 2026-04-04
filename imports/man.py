import os
import html
import subprocess

from flask import (
    abort,
    Blueprint,
    render_template,
    Response
)
from jinja2 import TemplateNotFound

from imports import config
from imports.games import GAME_LIST

#TODO: Default man page for games
#TODO: big one... add fxn for this: man pages in game dirs (submodules)
CONFIG = config.load_config(config.SERVER_CONFIG)
MAN_DIR = "man"

bp = Blueprint("man", __name__, url_prefix="/man", template_folder="../man")

@bp.route("/<name>.1")
def man(name):
    try:
        rendered = render_template(
            f"{name}.1",
            host=CONFIG.host,
            port=CONFIG.port,
            game_list=f"\n{', '.join(GAME_LIST)}"
        )
    except TemplateNotFound:
        abort(404)

    return Response(rendered, mimetype="text/plain; charset=utf-8")

@bp.route("/<name>")
def man_html(name):
    try:
        roff = render_template(
            f"{name}.1",
            host=CONFIG.host,
            port=CONFIG.port,
            html=True
        )
    except TemplateNotFound:
        abort(404)

    try:
        rendered = subprocess.run(
            ["groff", "-Thtml", "-man"],
            input=roff,
            text=True,
            capture_output=True,
            check=True,
        ).stdout
    except subprocess.CalledProcessError as e:
        return Response(
            f"<pre>{html.escape(e.stderr or 'groff failed')}</pre>",
            status=500,
            mimetype="text/html; charset=utf-8",
        )

    return render_template(
        "man_page.html",
        name=name,
        rendered=rendered
    )

@bp.route("/")
def man_index():
    pages = []

    for filename in sorted(os.listdir(MAN_DIR)):
        if not filename.endswith(".1"):
            continue

        name = filename[:-2]  # strip ".1"
        pages.append({
            "name": name,
            "html_url": f"/man/{name}",
        })
    try:
        resp = render_template(
            "man_index.html",
            pages=pages,
            html=True
        )
    except TemplateNotFound:
        abort(404)

    return resp

