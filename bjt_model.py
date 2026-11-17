def calculate_bjt_bias(vcc, r1, r1_unit, r2, r2_unit, rc, rc_unit, re, re_unit, beta, vbe):
    try:
        # แปลงหน่วยตัวต้านทานเป็น Ohms (Ω)
        unit_multiplier = {'ohm': 1, 'kohm': 1e3, 'mohm': 1e6}
        
        R1 = r1 * unit_multiplier.get(r1_unit, 1e3)
        R2 = r2 * unit_multiplier.get(r2_unit, 1e3)
        RC = rc * unit_multiplier.get(rc_unit, 1e3)
        RE = re * unit_multiplier.get(re_unit, 1e3)
        
        # คำนวณ Voltage Divider Bias (Exact/Thevenin Analysis)
        # V_TH = VCC * (R2 / (R1 + R2))
        # R_TH = (R1 * R2) / (R1 + R2)
        v_th = vcc * (R2 / (R1 + R2))
        r_th = (R1 * R2) / (R1 + R2)
        
        # IB = (V_TH - VBE) / (R_TH + (Beta + 1) * RE)
        ib = (v_th - vbe) / (r_th + (beta + 1) * RE)
        if ib < 0:
            ib = 0.0
            
        ic = beta * ib
        ie = (beta + 1) * ib
        
        vb = v_th # หรือ VBE + VE
        ve = ie * RE
        vc = vcc - (ic * RC)
        vce = vc - ve
        
        region = "Active" if vce > 0.2 else "Saturation"
        
        return {
            'vb': round(vb, 2),
            've': round(ve, 2),
            'vc': round(vc, 2),
            'vce': round(vce, 2),
            'ib': round(ib * 1e6, 2),  # µA
            'ic': round(ic * 1e3, 2),  # mA
            'ie': round(ie * 1e3, 2),  # mA
            'region': region
        }
    except Exception as e:
        return {'error': 'กรุณากรอกข้อมูลเป็นตัวเลขให้ถูกต้อง'}
