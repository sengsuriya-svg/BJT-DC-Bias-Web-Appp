def calculate_voltage_divider_bias(vcc, r1, r2, rc, re, beta, vbe=0.7):
    """
    คำนวณค่า DC Bias สำหรับวงจร Voltage Divider
    """
    v_th = vcc * (r2 / (r1 + r2))
    r_th = (r1 * r2) / (r1 + r2)
    
    ib = (v_th - vbe) / (r_th + (beta + 1) * re)
    
    if ib < 0:
        return {"error": "ทรานซิสเตอร์อยู่ในภาวะ Cut-off (กระแส Base ติดลบ)"}

    ic = beta * ib
    ie = (beta + 1) * ib

    ve = ie * re
    vc = vcc - (ic * rc)
    vce = vc - ve

    if vce < 0.2:
        region = "Saturation Region (อิ่มตัว)"
    elif ic <= 0:
        region = "Cut-off Region (คัทออฟ)"
    else:
        region = "Active Region (แอกทีฟ - เหมาะสำหรับการขยายสัญญาณ)"

    return {
        "ib": round(ib * 1e6, 3),  # ไมโครแอมป์ (µA)
        "ic": round(ic * 1e3, 3),  # มิลลิแอมป์ (mA)
        "ie": round(ie * 1e3, 3),  # มิลลิแอมป์ (mA)
        "ve": round(ve, 3),
        "vc": round(vc, 3),
        "vce": round(vce, 3),
        "region": region
    }
