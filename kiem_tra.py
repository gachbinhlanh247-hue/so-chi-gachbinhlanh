"""Tự tính lại các phép nhân / phép tổng viết tay. Python tính, không tin kết quả AI tự tính."""


def d(n):
    return f"{int(n):,}".replace(",", ".")


def _mot_chu_so(a, b):
    sa, sb = str(abs(a)), str(abs(b))
    return len(sa) == len(sb) and sum(x != y for x, y in zip(sa, sb)) == 1


def kiem_phep_tinh(ds):
    """ds: [{loai: nhan|tong, so: [...], ket_qua, mo_ta}] -> thêm tinh_lai, khop, lech, mot_chu_so."""
    out = []
    for p in ds or []:
        if p["loai"] == "nhan":
            tl = 1
            for x in p["so"]:
                tl *= x
        else:
            tl = sum(p["so"])
        out.append({**p, "tinh_lai": tl, "khop": tl == p["ket_qua"], "lech": tl - p["ket_qua"],
                    "mot_chu_so": tl != p["ket_qua"] and _mot_chu_so(tl, p["ket_qua"])})
    return out


def thong_bao(p):
    bt = (" × " if p["loai"] == "nhan" else " + ").join(d(x) for x in p["so"])
    ten = "Phép nhân" if p["loai"] == "nhan" else "Tổng"
    mo = f" ({p['mo_ta']})" if p.get("mo_ta") else ""
    if p["khop"]:
        return f"{ten}{mo}: {bt} = {d(p['ket_qua'])} — khớp."
    s = (f"{ten}{mo}: {bt}. Giấy viết {d(p['ket_qua'])}, tính lại ra {d(p['tinh_lai'])} "
         f"(lệch {d(abs(p['lech']))} đ). Có thể người viết cộng/nhân sai, hoặc máy đọc sai số — so với ảnh gốc.")
    if p["mot_chu_so"]:
        s += " Hai số chỉ khác nhau một chữ số, nhiều khả năng sai một chữ số."
    return s


def nhan_canh_bao(loi, tien):
    """Nhãn cảnh báo cho một dòng chi có số tiền nằm trong phép tính bị lệch."""
    tags = []
    for p in loi:
        if tien in p["so"] or (p["loai"] == "nhan" and tien == p["ket_qua"]):
            t = "phép nhân lệch" if p["loai"] == "nhan" else "tổng nhóm lệch"
            if t not in tags:
                tags.append(t)
    return tags
