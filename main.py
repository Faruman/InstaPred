#import os
#os.environ["GOOGLE_APPLICATION_CREDENTIALS"]="credentials.json"

from flask import Flask, render_template, request, url_for, session, redirect, flash
from google.cloud import datastore, storage
import bcrypt
import re
import base64
import uuid
from flask_sslify import SSLify
from io import BytesIO
from PIL import Image
from model import InstaPredLikeModel, InstaPredLabelModel
likeModel = InstaPredLikeModel("instapred_model", "v2")
hashtagModel = InstaPredLabelModel()

app = Flask(__name__)
sslify = SSLify(app)

app.secret_key = '4qjCwc_wHcTTUWlAjQtw_yJRB0vyDcLeCNq9UdWJCIs='

#get the database name
datastore_client = datastore.Client()
storage_client = storage.Client()


def create_user(user_dict):
    key = datastore_client.key("users")
    user = datastore.Entity(key, exclude_from_indexes=("password",))
    user.update(user_dict)
    datastore_client.put(user)

def fetch_user(email):
    query = datastore_client.query(kind="users")
    query.add_filter('email', '=', email)
    user = list(query.fetch(1))
    if len(user) > 0:
        return user[0]
    else:
        return None

def create_userFolder(userName):
    userName = userName.replace("@", "-")
    bucket = storage_client.bucket("instapredusercontent")
    bucket.blob(userName + "/")

def create_image(image, metadata, email):
    userName = email.replace("@", "-")
    bucket = storage_client.bucket("instapredusercontent")

    split = image.split('base64')
    format_image = re.findall(r"(?<=data:)(.*)(?=;)", split[0])[0]
    image_path = userName + "/" + str(uuid.uuid1()) + "." + re.findall("(?<=image\/).*", format_image)[0]
    blob = bucket.blob(image_path)
    base64_image = base64.b64decode(split[1])
    blob.upload_from_string(base64_image, content_type=format_image)

    key = datastore_client.key("image_metadata")
    image_meta = datastore.Entity(key)
    image_meta.update({"email": email, "image": image_path.split("/")[-1], **metadata})
    datastore_client.put(image_meta)

def fetch_images(email):
    userName = email.replace("@", "-")
    bucket = storage_client.bucket("instapredusercontent")
    blobs = list(bucket.list_blobs(prefix=userName))
    images = [{"name": blob.name.split("/")[-1],"image": "data:" + blob.content_type + ";base64," + base64.b64encode(blob.download_as_string()).decode("utf-8")} for blob in blobs]

    query = datastore_client.query(kind="image_metadata")
    query.add_filter('email', '=', email)
    image_meta = list(query.fetch())
    image_meta_keys = [meta["image"] for meta in image_meta]
    image_meta = [dict(meta) for meta in image_meta]
    image_meta_dict = dict(zip(image_meta_keys, image_meta))

    new_images = []
    for image in images:
        if image["name"] in image_meta_dict.keys():
            new_images.append({**image, "numLikes": image_meta_dict[image["name"]]["numLikes"], "proposedTags": image_meta_dict[image["name"]]["proposedTags"]})

    return new_images

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/features")
def features():
    return render_template("features.html")

@app.route("/pricing")
def pricing():
    return render_template("pricing.html")

@app.route("/login", methods=["POST", "GET"])
def login():
    if request.method == "POST":
        email = request.form.get("email").lower()
        password = request.form.get("password")
        remember_me = bool(request.form.get("rememberMe"))
        user = fetch_user(email)
        if user:
            if bcrypt.checkpw(password.encode('utf-8'), user['password']):
                # TODO: implement timeout for user
                if remember_me:
                    session["user"] = user
                else:
                    session["user"] = user
                flash('You have been successfully logged in.')
                return redirect(url_for("index"))
            return render_template("login.html", message= "Either the user does not exist or you entered a wrong password.")
        else:
            return render_template("login.html", message= "Either the user does not exist or you entered a wrong password.")
    else:
        return render_template("login.html")

@app.route("/gallery", methods= ["GET", "POST"])
def gallery():
    if request.method == "POST":
        if "user" in session.keys():
            image = request.form["photo"]

            num_preds = likeModel.predict(Image.open(BytesIO(base64.b64decode(image.split('base64')[1]))))
            hashtags = hashtagModel.predict(base64.b64decode(image.split('base64')[1]))

            model_output = {"success": True, "numLikes": num_preds, "proposedTags": hashtags}

            create_image(image, model_output, session["user"]["email"])
            return model_output
        else:
            return {"success": False}
    else:
        if "user" in session.keys():
            images = fetch_images(session["user"]["email"])
            return render_template("gallery.html", images=images)
        else:
            return redirect(url_for("index"))

@app.route("/logout")
def logout():
    if "user" in session.keys():
        session.pop("user")
        flash("You have been successfully logged out.")
    return redirect(url_for("index"))

@app.route("/signup", methods= ["GET", "POST"])
def signup():
    if request.method == "POST":
        validation_pass = False
        message = ""
        user = request.form.to_dict()
        user["email"] = user["email"].lower()
        if fetch_user(user["email"]):
            message = "The email you entered is already registered, please sign in."
            del user["email"]
        elif user["password"] != user["passwordRepeat"]:
            message = "Your passwords did not match."
        else:
            validation_pass = True
        del user["passwordRepeat"]
        if validation_pass:
            user["password"] = bcrypt.hashpw(user["password"].encode('utf-8'), bcrypt.gensalt())
            create_user(user)
            create_userFolder(user["email"])
            session["user"] = user
            return render_template("index.html")
        else:
            del user["password"]
            return render_template("signup.html", message= message, user= user)
    else:
        return render_template("signup.html")

if __name__ == "__main__":
    app.run(debug= False)