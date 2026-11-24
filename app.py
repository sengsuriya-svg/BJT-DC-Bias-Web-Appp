from flask import Flask, render_template, request

from bjt_model import calculate_bjt_bias
from plots import line_svg
from spice_engine import simulate

app = Flask(__name__)


@app.route('/', methods=['GET', 'POST'])
def index():
    results = None
    selected_mode = 'divider'
    selected_analysis = 'bias'
    spice_result = None

    if request.method == 'POST':
        selected_analysis = request.form.get('analysis', 'bias')

        if selected_analysis == 'bias':
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
        elif selected_analysis in ('spice_dc', 'spice_ac', 'spice_tran'):
            selected_mode = 'divider'
            analysis = selected_analysis.replace('spice_', '')
            spice_form = {
                'vcc': request.form.get('s_vcc', '12'),
                'r1': request.form.get('s_r1', '100'),
                'r1_unit': request.form.get('s_r1_unit', 'kohm'),
                'r2': request.form.get('s_r2', '22'),
                'r2_unit': request.form.get('s_r2_unit', 'kohm'),
                'rc': request.form.get('s_rc', '2.2'),
                'rc_unit': request.form.get('s_rc_unit', 'kohm'),
                're': request.form.get('s_re', '1'),
                're_unit': request.form.get('s_re_unit', 'kohm'),
                'rl': request.form.get('s_rl', '10'),
                'rl_unit': request.form.get('s_rl_unit', 'kohm'),
                'cin': request.form.get('s_cin', '10'),
                'cin_unit': request.form.get('s_cin_unit', 'uF'),
                'cout': request.form.get('s_cout', '10'),
                'cout_unit': request.form.get('s_cout_unit', 'uF'),
                'amplitude': request.form.get('amplitude', '0.01'),
                'frequency': request.form.get('frequency', '1000'),
            }
            spice_result = simulate(spice_form, analysis)
            spice_result['plot'] = None
            # Keep dc values under dc_values too; Jinja resolves .values to the
            # dict method, which hides a plain dict key named "values".
            spice_result['dc_values'] = spice_result.get('values')
            if spice_result['status'] == 'success' and analysis == 'ac':
                # AC points are [frequency, gain_dB, phase_deg]; plot gain only
                # because dB and degrees must not share one y-axis.
                spice_result['plot'] = line_svg(
                    [point[:2] for point in spice_result['points']],
                    'Frequency (Hz)', 'Gain (dB)',
                    'AC frequency response (ngspice)',
                    ['Gain (dB)'],
                    log_x=True,
                )
            elif spice_result['status'] == 'success' and analysis == 'tran':
                spice_result['plot'] = line_svg(
                    spice_result['points'],
                    'Time (s)', 'Voltage (V)',
                    'Transient response (ngspice)',
                    ['Vin', 'Vout'],
                )
        else:
            selected_analysis = 'bias'
            results = {'error': 'Unknown analysis mode'}

    return render_template(
        'index.html',
        results=results,
        spice_result=spice_result,
        selected_mode=selected_mode,
        selected_analysis=selected_analysis,
        form=request.form,
    )


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
