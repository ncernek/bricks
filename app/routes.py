'''this blueprint gets added as an extension to the main Flask app in __init__'''
import os
from datetime import timedelta
from flask import Blueprint, current_app, session
from app import chat as old_chat
from app import notify
from app.api import (
    auth_token,
    task,
    app_user,
    team,
    invite,
    join,
    feedback,
    stats,
    privacy_policy,
    landing_page,
    nudge,
    assist,
    chat
)
from app.security import validate_twilio_request, validate_google_cron_request

main = Blueprint('main', __name__)


@main.route("/api/auth_token", methods=['GET'])
def auth_token_wrapper():
    return auth_token.get()

@main.route("/api/task", methods=["GET", "PUT"])
@auth_token.verify
def task_wrapper(user):
    return task.main(user)

@main.route("/api/app_user", methods=["PUT"])
@auth_token.verify
def app_user_wrapper(user):
    return app_user.put(user)

@main.route("/api/team", methods=["GET", "PUT"])
@auth_token.verify
def team_wrapper(user):
    return team.main(user)

@main.route("/api/invite", methods=["POST"])
@auth_token.verify
def invite_wrapper(user):
    return invite.post(user)

@main.route("/api/join", methods=["POST"])
@auth_token.verify
def join_wrapper(user):
    return join.post(user)

@main.route("/api/feedback", methods=["POST"])
@auth_token.verify
def feedback_wrapper(user):
    return feedback.post(user)

@main.route("/api/stats", methods=["GET"])
@auth_token.verify
def stats_wrapper(user):
    return stats.get(user)

@main.route("/api/nudge", methods=["POST"])
@auth_token.verify
def nudge_wrapper(user):
    return nudge.post(user)

@main.route("/api/assist", methods=["POST"])
@auth_token.verify
def assist_wrapper(user):
    return assist.post(user)

@main.route("/api/chat", methods=["POST"])
@auth_token.verify
def chat_wrapper(user):
    return chat.post(user)

@main.route("/privacy-policy", methods=["GET"])
def policy_wrapper():
    return privacy_policy.get()

@main.route("/")
def landing_page_wrapper():
    return landing_page.get()


@main.route( "/chat", methods=['GET', 'POST'])
@validate_twilio_request
def conduct_conversations_wrapper():
    return old_chat.main()


@main.route("/notify", methods=['GET'])
@validate_google_cron_request
def send_notifications_wrapper():
    return notify.main()


# TODO(Nico) is this the right place to put this?
@current_app.before_request
def session_timeout():
    session.permanent = True
    current_app.permanent_session_lifetime = timedelta(seconds=10)