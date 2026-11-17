from flask import Flask, render_template, request
from bjt_model import calculate_bjt_bias

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def index():
    results = None
    selected_mode = 'divider'
    
    if request.method == 'POST':
        try:
            selected_mode = request.form.get('mode', 'divider')
            vcc = float(request.form.get('vcc', 12.0))
            beta = float(request.form.get('beta', 100))
            vbe = float(request.form.get('vbe', 0.70))
            
            r1 = float(request.form.get('r1', 0) or 0)
            r1_unit = request.form.get('r1_unit', 'kohm')
            r2 = float(request.form.get('r2', 0) or 0)
            r2_unit = request.form.get('r2_unit', 'kohm')
            rb = float(request.form.get('rb', 0) or 0)
            rb_unit = request.form.get('rb_unit', 'kohm')
            rc = float(request.form.get('rc', 0) or 0)
            rc_unit = request.form.get('rc_unit', 'kohm')
            re = float(request.form.get('re', 0) or 0)
            re_unit = request.form.get('re_unit', 'kohm')
            
            results = calculate_bjt_bias(
                mode=selected_mode, vcc=vcc, beta=beta, vbe=vbe,
                r1=r1, r1_unit=r1_unit, r2=r2, r2_unit=r2_unit,
                rb=rb, rb_unit=rb_unit, rc=rc, rc_unit=rc_unit,
                re=re, re_unit=re_unit
            )
        except ValueError:
            results = {'error': 'กรุณากรอกข้อมูลเป็นตัวเลขให้ถูกต้อง'}

    return render_template('index.html', results=results, selected_mode=selected_mode)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
