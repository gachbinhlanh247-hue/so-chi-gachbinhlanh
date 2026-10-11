"""Ghi / đọc Google Sheet bằng tài khoản dịch vụ. Tự tạo các tab nếu chưa có."""
import re
import gspread

NHOM_MAC_DINH = ["Tiền ăn", "Dụng cụ", "Bổ sung", "Chi khác"]
MODEL_MAC_DINH = ["gemini-flash-latest", "gemini-flash-lite-latest", "gemini-2.5-flash", "gemini-2.5-flash-lite"]
CHI = ["Ngày", "Nhóm", "Diễn giải", "Số tiền", "Trạng thái", "Ghi chú", "Ảnh nguồn", "Mã ảnh", "Model", "Cảnh báo", "Ghi lúc"]
AN = ["Ngày", "Trưa", "Tối", "Đơn giá", "Thành tiền", "Ghi chú", "Mã ảnh"]


def mo_sheet(secrets):
    gc = gspread.service_account_from_dict(dict(secrets["GOOGLE_SERVICE_ACCOUNT"]))
    sh = gc.open_by_key(secrets["SHEET_ID"])
    _dam_bao_tab(sh)
    return sh


def _tao(sh, ten, dong, cot=12):
    ws = sh.add_worksheet(ten, rows=2000, cols=cot)
    ws.update(range_name="A1", values=dong, value_input_option="USER_ENTERED")
    ws.freeze(rows=1)


def _dam_bao_tab(sh):
    co = {w.title for w in sh.worksheets()}
    if "Chi_tiet" not in co: _tao(sh, "Chi_tiet", [CHI])
    if "Khoan_an" not in co: _tao(sh, "Khoan_an", [AN], 8)
    if "Cai_dat" not in co:
        _tao(sh, "Cai_dat", [["Loai", "Gia tri"]] + [["model", m] for m in MODEL_MAC_DINH]
             + [["nhom", n] for n in NHOM_MAC_DINH] + [["don_gia_bua", 33000]], 3)
    if "Tong_hop" not in co:
        n = len(NHOM_MAC_DINH)
        dong = [["Hạng mục", "Số tiền"]]
        dong += [[g, f"=SUMIF(Chi_tiet!$B:$B,A{i+2},Chi_tiet!$D:$D)"] for i, g in enumerate(NHOM_MAC_DINH)]
        dong += [["Khoán ăn (số bữa × đơn giá)", "=SUM(Khoan_an!E:E)"], ["TỔNG CỘNG", f"=SUM(B2:B{n+2})"]]
        _tao(sh, "Tong_hop", dong, 3)
    ws = sh.worksheet("Chi_tiet")  # bỏ tab trống mặc định nếu có
    for t in ("Sheet1", "Trang tính1"):
        if t in co and len(co) > 1:
            sh.del_worksheet(sh.worksheet(t))


def doc_cai_dat(sh):
    rows = sh.worksheet("Cai_dat").get_all_values()[1:]
    lay = lambda k: [r[1].strip() for r in rows if len(r) > 1 and r[0].strip() == k and r[1].strip()]
    dg = lay("don_gia_bua")
    return {"models": lay("model") or MODEL_MAC_DINH, "nhom": lay("nhom") or NHOM_MAC_DINH,
            "don_gia": int(re.sub(r"\D", "", dg[0]) or 33000) if dg else 33000}


def khoa_dong(ngay, dien_giai, tien):
    return f"{str(ngay).strip()}|{str(dien_giai).strip().lower()}|{int(tien or 0)}"


def khoa_da_co(sh):
    v = sh.worksheet("Chi_tiet").get_all_values()[1:]
    return {khoa_dong(r[0], r[2], re.sub(r"\D", "", r[3]) or 0) for r in v if len(r) > 3}


def ma_anh_da_ghi(sh):
    a = sh.worksheet("Chi_tiet").get_all_values()[1:]
    b = sh.worksheet("Khoan_an").get_all_values()[1:]
    return {r[7] for r in a if len(r) > 7} | {r[6] for r in b if len(r) > 6}


def ghi_chi(sh, rows):
    if rows:
        sh.worksheet("Chi_tiet").append_rows(rows, value_input_option="RAW")
    return len(rows)


def ghi_khoan(sh, rows, don_gia):
    """rows: [ngay, trua, toi, ghi_chu, ma_anh]"""
    if not rows:
        return 0
    ws = sh.worksheet("Khoan_an")
    r0 = len(ws.col_values(1)) + 1
    out = [["'" + str(ng), tr, to, don_gia, f"=(B{r0+i}+C{r0+i})*D{r0+i}", gc, ma]
           for i, (ng, tr, to, gc, ma) in enumerate(rows)]
    ws.append_rows(out, value_input_option="USER_ENTERED")
    return len(out)
