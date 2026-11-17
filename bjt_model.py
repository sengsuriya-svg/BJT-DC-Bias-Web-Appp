def calculate_bjt_bias(vcc, r1, r1_unit, r2, r2_unit, rc, rc_unit, re, re_unit, beta, vbe):
    try:
        # ฟังก์ชันแปลงหน่วยตัวต้านทานเป็น Ohms (Ω)
        unit_multiplier = {'ohm': 1, 'kohm': 1e3, 'mohm': 1e6}
        
        R1 = r1 * unit_multiplier.get(r1_unit, 1e3)
        R2 = r2 * unit_multiplier.get(r2_unit, 1e3)
        RC = rc * unit_multiplier.get(rc_unit, 1e3)
        RE = re * unit_multiplier.get(re_unit, 1e3)
        
        # คำนวณ Voltage Divider Bias
        # VB = VCC * (R2 / (R1 + R2))
        vb = vcc * (R2 / (R1 + R2))
        
        # VE = VB - VBE
        ve = vb - vbe
        if ve < 0:
            ve = 0.0
            
        # IE = VE / RE
        ie = ve / RE if RE > 0 else 0
        
        # IC ≈ IE
        ic = ie
        
        # IB = IC / Beta
        ib = (ic / beta) * 1e6 if beta > 0 else 0 # แปลงเป็น µA
        
        # VC = VCC - (IC * RC)
        vc = vcc - (ic * RC)
        
        # VCE = VC - VE
        vce = vc - ve
        
        # ตรวจสอบย่านการทำงาน (Region)
        region = "Active" if vce > 0.2 else "Saturation"
        
        return {
            'vb': round(vb, 2),
            've': round(ve, 2),
            'vc': round(vc, 2),
            'vce': round(vce, 2),
            'ib': round(ib, 2),
            'ic': round(ic * 1e3, 2), # แปลงกลับเป็น mA แสดงผล
            'ie': round(ie * 1e3, 2), # แปลงกลับเป็น mA แสดงผล
            'region': region
        }
    except Exception as e:
        return {'error': 'เกิดข้อผิดพลาดในการคำนวณ กรุณาตรวจสอบค่าที่กรอก'}
