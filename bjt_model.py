def calculate_bjt_bias(mode, vcc, beta, vbe, r1=0, r1_unit='kohm', r2=0, r2_unit='kohm', 
                       rb=0, rb_unit='kohm', rc=0, rc_unit='kohm', re=0, re_unit='kohm'):
    try:
        unit_multiplier = {'ohm': 1, 'kohm': 1e3, 'mohm': 1e6}
        
        RC = rc * unit_multiplier.get(rc_unit, 1e3)
        
        ib = 0
        ie = 0
        ic = 0
        ve = 0
        vb = 0
        vc = 0
        vce = 0
        
        if mode == 'fixed':
            RB = rb * unit_multiplier.get(rb_unit, 1e3)
            if RB <= 0:
                return {'error': 'ค่า R_B ต้องมากกว่า 0'}
            ib_amp = (vcc - vbe) / RB
            ic_amp = beta * ib_amp
            ie_amp = (beta + 1) * ib_amp
            ve = 0.0
            vb = vbe
            vc = vcc - (ic_amp * RC)
            vce = vc - ve
            ib = ib_amp * 1e6
            ic = ic_amp * 1e3
            ie = ie_amp * 1e3
            
        elif mode == 'emitter':
            RB = rb * unit_multiplier.get(rb_unit, 1e3)
            RE = re * unit_multiplier.get(re_unit, 1e3)
            denom = RB + (beta + 1) * RE
            if denom <= 0:
                return {'error': 'ค่าความต้านทานไม่ถูกต้อง'}
            ib_amp = (vcc - vbe) / denom
            ic_amp = beta * ib_amp
            ie_amp = (beta + 1) * ib_amp
            ve = ie_amp * RE
            vb = ve + vbe
            vc = vcc - (ic_amp * RC)
            vce = vc - ve
            ib = ib_amp * 1e6
            ic = ic_amp * 1e3
            ie = ie_amp * 1e3
            
        else:  # Voltage Divider (ใช้สูตรเดิมเป๊ะๆ จาก Lab 02 ของคุณ)
            R1 = r1 * unit_multiplier.get(r1_unit, 1e3)
            R2 = r2 * unit_multiplier.get(r2_unit, 1e3)
            RE = re * unit_multiplier.get(re_unit, 1e3)
            
            if (R1 + R2) <= 0:
                return {'error': 'ผลรวม R1 และ R2 ต้องมากกว่า 0'}
            
            vb = vcc * (R2 / (R1 + R2))
            ve = vb - vbe
            if ve < 0:
                ve = 0.0
                
            ie_amp = ve / RE if RE > 0 else 0
            ic_amp = ie_amp
            ib = (ic_amp / beta) * 1e6 if beta > 0 else 0 # µA
            vc = vcc - (ic_amp * RC)
            vce = vc - ve
            
            ic = ic_amp * 1e3 # mA
            ie = ie_amp * 1e3 # mA

        # ตรวจสอบย่านการทำงาน
        region = "Active" if vce > 0.2 else "Saturation"
        
        return {
            'vb': round(vb, 2),
            've': round(ve, 2),
            'vc': round(vc, 2),
            'vce': round(vce, 2),
            'ib': round(ib, 2),
            'ic': round(ic, 2),
            'ie': round(ie, 2),
            'region': region
        }
    except Exception as e:
        return {'error': 'เกิดข้อผิดพลาดในการคำนวณ กรุณาตรวจสอบค่าที่กรอก'}
