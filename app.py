from flask import Flask, render_template, request
from bjt_model import calculate_voltage_divider_bias

app = Flask(__name__)

@app.route("/", methods=["GET", "POST"])
def index():
    results = None
    if request.method == "POST":
        try:
            vcc = float(request.form.get("vcc", 12))
            r1 = float(request.form.get("r1", 56000))
            r2 = float(request.form.get("r2", 10000))
            rc = float(request.form.get("rc", 2200))
            re = float(request.form.get("re", 1000))
            beta = float(request.form.get("beta", 100))
            
            results = calculate_voltage_divider_bias(vcc, r1, r2, rc, re, beta)
        except ValueError:
            results = {"error": "กรุณากรอกข้อมูลตัวเลขให้ถูกต้องครบถ้วน"}

    return render_template("index.html", results=results)

if __name__ == "__main__":
    app.run(debug=True)
