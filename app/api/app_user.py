""" save the values to app_user. 
device token: this will be used to send push notifications"""


from flask import jsonify, request, make_response
import datetime as dt
from app.models import AppUser, Task
from app import db


def put(user):

    data = request.get_json()
    
    if "device_token" in data:
        user.device_token = data["device_token"]
    if "username" in data:
        user.username = data["username"]
    if "firebase_token" in data:
        user.firebase_token = data["firebase_token"]

    db.session.commit()

    message = "success"
    return make_response(jsonify(message), 200)
