def calculate_bjt_bias(mode, vcc, beta, vbe, r1=0, r1_unit='kohm', r2=0, r2_unit='kohm', 
                       rb=0, rb_unit='kohm', rc=0, rc_unit='kohm', re=0, re_unit='kohm'):
    try:
        unit_multiplier = {'ohm': 1, 'kohm': 1e3, 'mohm': 1e6}
        
        # แปลงค่าตัวต้านทานเป็น Ohms (Ω)
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
            # Fixed Bias: IB = (VCC - VBE) / RB
            ib = (vcc - vbe) / RB
            ic = beta * ib
            ie = (beta + 1) * ib
            ve = 0.0
            vb = vbe
            vc = vcc - (ic * RC)
            vce = vc - ve
            
        elif mode == 'emitter':
            RB = rb * unit_multiplier.get(rb_unit, 1e3)
            RE = re * unit_multiplier.get(re_unit, 1e3)
            denom = RB + (beta + 1) * RE
            if denom <= 0:
                return {'error': 'ค่าความต้านทานไม่ถูกต้อง'}
            # Emitter Bias: IB = (VCC - VBE) / [RB + (beta + 1)RE]
            ib = (vcc - vbe) / denom
            ic = beta * ib
            ie = (beta + 1) * ib
            ve = ie * RE
            vb = ve + vbe
            vc = vcc - (ic * RC)
            vce = vc - ve
            
        else:  # Voltage Divider Bias (ค่าเดิม)
            R1 = r1 * unit_multiplier.get(r1_unit, 1e3)
            R2 = r2 * unit_multiplier.get(r2_unit, 1e3)
            RE = re * unit_multiplier.get(re_unit, 1e3)
            
            if (R1 + R2) <= 0:
                return {'error': 'ผลรวม R1 และ R2 ต้องมากกว่า 0'}
            
            vth = vcc * (R2 / (R1 + R2))
            rth = (R1 * R2) / (R1 + R2)
            denom = rth + (beta + 1) * RE
            if denom <= 0:
                return {'error': 'ค่าความต้านทานไม่ถูกต้อง'}
                
            ib = (vth - vbe) / denom
            ic = beta * ib
            ie = (beta + 1) * ib
            ve = ie * RE
            vb = ve + vbe
            vc = vcc - (ic * RC)
            vce = vc - ve

        # ตรวจสอบย่านการทำงาน (Active Region)
        region = "Active" if vce > 0.2 and ib > 0 else "Saturation / Cutoff"
        
        return {
            'vb': round(vb, 2),
            've': round(ve, 2),
            'vc': round(vc, 2),
            'vce': round(vce, 2),
            'ib': round(ib * 1e6, 2),  # แปลงเป็น µA
            'ic': round(ic * 1e3, 2),  # แปลงเป็น mA
            'ie': round(ie * 1e3, 2),  # แปลงเป็น mA
            'region': region
        }
    except Exception as e:
        return {'error': 'เกิดข้อผิดพลาดในการคำนวณ กรุณาตรวจสอบค่าที่กรอก'}
