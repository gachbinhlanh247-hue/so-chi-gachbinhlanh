"""Đọc ảnh chép tay bằng Gemini (REST). Tự đổi model / khóa khi lỗi hoặc hết lượt miễn phí."""
import base64, io, json, re, time, datetime as dt
import requests
from PIL import Image, ImageOps

URL = "https://generativelanguage.googleapis.com/v1beta/models/{m}:generateContent"
NGHI = {}  # (model, 4 ký tự cuối khóa) -> thời điểm hết nghỉ

SCHEMA = """Chỉ trả về JSON, không giải thích, đúng dạng:
{"loai_trang":"chi"|"khoan_an"|"khac","tong_viet_tay":số hoặc null,
 "dong":[{"ngay":"","nhom":"","dien_giai":"","so_tien":0,"trang_thai":"","ghi_chu":"","khong_chac":false}],
 "khoan_an":[{"ngay":"","trua":0,"toi":0,"ghi_chu":""}],
 "phep_tinh":[{"loai":"nhan"|"tong","mo_ta":"","so":[0,0],"ket_qua":0}]}"""


def nen_anh(raw, canh=1600):
    im = ImageOps.exif_transpose(Image.open(io.BytesIO(raw))).convert("RGB")
    im.thumbnail((canh, canh))
    b = io.BytesIO()
    im.save(b, "JPEG", quality=85)
    return b.getvalue()


def lap_prompt(quy_tac, nhom):
    return f"{quy_tac}\n\nNhóm hợp lệ: {', '.join(nhom)}.\nNếu ảnh không ghi năm thì dùng năm {dt.date.today().year}.\n{SCHEMA}"


def _so(x):
    """Số tiền: '70.000', '70,000', 70000, 70000.0 đều ra 70000 (dấu . , chỉ ngăn nghìn)."""
    if isinstance(x, (int, float)):
        return int(round(x))
    s = re.sub(r"[^\d.,\-]", "", str(x or ""))
    if re.fullmatch(r"-?\d{1,3}([.,]\d{3})+", s):
        s = re.sub(r"[.,]", "", s)
    try:
        return int(round(float(s.replace(",", ".") or 0)))
    except ValueError:
        return 0


def _chuan(r):
    text = "".join(p.get("text", "") for p in r["candidates"][0]["content"]["parts"] if not p.get("thought"))
    j = json.loads(re.sub(r"^```(?:json)?|```$", "", text.strip(), flags=re.M).strip())
    for d in j.get("dong") or []:
        d["so_tien"] = _so(d.get("so_tien"))
        for k in ("ngay", "nhom", "dien_giai", "trang_thai", "ghi_chu"):
            d[k] = str(d.get(k) or "").strip()
        d["khong_chac"] = bool(d.get("khong_chac"))
    for d in j.get("khoan_an") or []:
        d["trua"], d["toi"] = _so(d.get("trua")), _so(d.get("toi"))
        d["ngay"], d["ghi_chu"] = str(d.get("ngay") or "").strip(), str(d.get("ghi_chu") or "").strip()
    pt = []
    for p in j.get("phep_tinh") or []:
        so = [_so(x) for x in (p.get("so") or [])]
        kq = _so(p.get("ket_qua"))
        if len(so) >= 2 and kq:
            pt.append({"loai": "nhan" if str(p.get("loai", "")).lower().startswith("nh") else "tong",
                       "so": so, "ket_qua": kq, "mo_ta": str(p.get("mo_ta") or "").strip()})
    j["phep_tinh"] = pt
    j["dong"], j["khoan_an"] = j.get("dong") or [], j.get("khoan_an") or []
    j["tong_viet_tay"] = _so(j["tong_viet_tay"]) if j.get("tong_viet_tay") else None
    return j


def doc(anh_jpeg, prompt, models, keys, timeout=90):
    """Trả (kết_quả, tên_model). Thử lần lượt từng model x từng khóa."""
    body = {"contents": [{"parts": [{"text": prompt},
                                    {"inline_data": {"mime_type": "image/jpeg",
                                                     "data": base64.b64encode(anh_jpeg).decode()}}]}],
            "generationConfig": {"temperature": 0, "responseMimeType": "application/json"}}
    loi = []
    for m in models:
        for k in keys:
            ma = (m, k[-4:])
            if NGHI.get(ma, 0) > time.time():
                continue
            try:
                r = requests.post(URL.format(m=m), params={"key": k}, json=body, timeout=timeout)
            except requests.RequestException:
                NGHI[ma] = time.time() + 30
                loi.append(f"{m}: lỗi mạng")
                continue
            if r.status_code == 200:
                try:
                    return _chuan(r.json()), m
                except Exception:
                    loi.append(f"{m}: kết quả sai định dạng")
                    continue
            NGHI[ma] = time.time() + (600 if r.status_code == 429 else 60)
            loi.append(f"{m}: HTTP {r.status_code}")
    raise RuntimeError("Chưa model nào đọc được. " + ("; ".join(loi) or "Tất cả đang nghỉ, thử lại sau vài phút."))
