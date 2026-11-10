from flask import Flask, render_template, request
from bjt_model import calculate_bjt_bias

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def index():
    results = None
    if request.method == 'POST':
        try:
            vcc = float(request.form.get('vcc', 12.0))
            r1 = float(request.form.get('r1', 100.0))
            r1_unit = request.form.get('r1_unit', 'kohm')
            r2 = float(request.form.get('r2', 22.0))
            r2_unit = request.form.get('r2_unit', 'kohm')
            rc = float(request.form.get('rc', 2.2))
            rc_unit = request.form.get('rc_unit', 'kohm')
            re = float(request.form.get('re', 1.0))
            re_unit = request.form.get('re_unit', 'kohm')
            beta = float(request.form.get('beta', 100))
            vbe = float(request.form.get('vbe', 0.70))
            
            results = calculate_bjt_bias(
                vcc, r1, r1_unit, r2, r2_unit, 
                rc, rc_unit, re, re_unit, beta, vbe
            )
        except ValueError:
            results = {'error': 'กรุณากรอกข้อมูลเป็นตัวเลขให้ถูกต้อง'}

    return render_template('index.html', results=results)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
