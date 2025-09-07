from flask import Flask
from datetime import datetime

app = Flask(__name__)

@app.route("/fecha")
def obtener_fecha():
    now = datetime.now()
    return now.strftime("%d/%m/%Y %H:%M:%S")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
