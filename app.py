from flask import Flask

app = Flask(__name__)  # Correction ici : name au lieu de name

@app.route("/")
def home():
    return "Hello, OpenTelemetry!"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
