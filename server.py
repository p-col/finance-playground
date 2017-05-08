#!/usr/bin/env python


from flask import Flask, render_template, jsonify
# from flask import send_from_directory
from flask import url_for

app = Flask(__name__)
app.config.update(
        PROPAGATE_EXCEPTIONS = True
    )

@app.route("/")
def getIndex():
    return render_template("index.html")

@app.route("/hour")
def getHourData():
    return render_template("data.html", resolution_name="hours")

def main():
    app.run()

if __name__ == "__main__":
    main()
