import hashlib, datetime as dt
import pandas as pd
import streamlit as st
import doc_anh, ghi_sheet as gs, kiem_tra

st.set_page_config(page_title="Sổ chi Gạch BL", page_icon="🧾", layout="centered")

ma = st.secrets.get("ACCESS_CODE", "")
if ma and not st.session_state.get("ok"):
    if st.text_input("Mã truy cập", type="password") == ma:
        st.session_state.ok = True
        st.rerun()
    st.stop()


@st.cache_resource(ttl=600)
def sheet():
    return gs.mo_sheet(st.secrets)


@st.cache_data(ttl=60)
def cai_dat():
    return gs.doc_cai_dat(sheet())


@st.cache_data(ttl=30)
def da_co():
    return gs.khoa_da_co(sheet()), gs.ma_anh_da_ghi(sheet())


def khoa_gemini():
    k = st.secrets.get("GEMINI_KEYS", [])
    return [x.strip() for x in k.split(",")] if isinstance(k, str) else list(k)


st.title("🧾 Sổ chi Gạch BL")
if st.session_state.get("tb"):
    st.success(st.session_state.pop("tb"))
try:
    cd, (khoa_co, anh_co) = cai_dat(), da_co()
except Exception as e:
    st.error(f"Không mở được Google Sheet: {e}")
    st.stop()

files = st.file_uploader("Chụp ảnh hoặc chọn ảnh (tối đa 5)", type=["jpg", "jpeg", "png", "webp"],
                         accept_multiple_files=True)
if len(files) > 5:
    st.error("Chỉ chọn tối đa 5 ảnh mỗi lần.")
elif files and st.button("Đọc ảnh", type="primary"):
    quy_tac = open("QUY_TAC_DOC.md", encoding="utf-8").read()
    prompt = doc_anh.lap_prompt(quy_tac, cd["nhom"])
    kq = {}
    for f in files:
        raw = f.getvalue()
        h = hashlib.sha1(raw).hexdigest()[:12]
        try:
            with st.spinner(f"Đang đọc {f.name}..."):
                r, m = doc_anh.doc(doc_anh.nen_anh(raw), prompt, cd["models"], khoa_gemini())
            kq[h] = {"ten": f.name, "raw": raw, "kq": r, "model": m}
        except Exception as e:
            st.error(f"{f.name}: {e}")
    st.session_state.kq = kq

COT = ["Ghi", "Ngày", "Nhóm", "Diễn giải", "Số tiền", "Trạng thái", "Ghi chú", "Cảnh báo"]
chon = []
for h, it in st.session_state.get("kq", {}).items():
    r = it["kq"]
    with st.expander(f"{it['ten']} · {len(r['dong'])} dòng chi · {len(r['khoan_an'])} dòng chấm ăn · {it['model']}",
                     expanded=True):
        st.image(it["raw"], use_container_width=True)
        if h in anh_co:
            st.warning("Ảnh này đã được ghi vào Sheet trước đó.")
        pt = kiem_tra.kiem_phep_tinh(r["phep_tinh"])
        loi = [x for x in pt if not x["khop"]]
        rows = []
        for d in r["dong"]:
            cb = kiem_tra.nhan_canh_bao(loi, d["so_tien"])
            if gs.khoa_dong(d["ngay"], d["dien_giai"], d["so_tien"]) in khoa_co: cb.append("trùng")
            if d["khong_chac"]: cb.append("không chắc")
            if d["so_tien"] <= 0: cb.append("số tiền 0")
            rows.append([("trùng" not in cb), d["ngay"], d["nhom"] if d["nhom"] in cd["nhom"] else cd["nhom"][-1],
                         d["dien_giai"], d["so_tien"], d["trang_thai"], d["ghi_chu"], ", ".join(cb)])
        ed = None
        if rows:
            ed = st.data_editor(pd.DataFrame(rows, columns=COT), key=f"c_{h}", hide_index=True,
                                num_rows="dynamic", use_container_width=True, disabled=["Cảnh báo"],
                                column_config={"Nhóm": st.column_config.SelectboxColumn(options=cd["nhom"]),
                                               "Số tiền": st.column_config.NumberColumn(format="%d", step=1000)})
            tong, vt = int(ed["Số tiền"].fillna(0).sum()), r["tong_viet_tay"]
            st.caption(f"Tổng các dòng: {tong:,} đ".replace(",", "."))
            if vt and vt != tong:
                st.warning(f"Tổng viết tay trên giấy {vt:,} đ khác tổng các dòng {tong:,} đ "
                           f"(lệch {abs(vt-tong):,} đ). Kiểm tra lại với ảnh.".replace(",", "."))
            elif vt:
                st.success("Tổng các dòng khớp tổng viết tay.")
        for x in loi:
            st.warning(kiem_tra.thong_bao(x))
        if pt and not loi:
            st.success(f"Đã kiểm tra {len(pt)} phép nhân / phép tổng viết tay: đều khớp.")
        elif pt:
            st.caption(f"Đã kiểm tra {len(pt)} phép tính viết tay, {len(pt)-len(loi)} khớp, {len(loi)} lệch.")
        ka = None
        if r["khoan_an"]:
            st.markdown("**Chấm ăn (số người)**")
            ka = st.data_editor(pd.DataFrame([[True, d["ngay"], d["trua"], d["toi"], d["ghi_chu"]]
                                              for d in r["khoan_an"]],
                                             columns=["Ghi", "Ngày", "Trưa", "Tối", "Ghi chú"]),
                                key=f"a_{h}", hide_index=True, num_rows="dynamic", use_container_width=True)
        chon.append((h, it, ed, ka))

if chon and st.button("Ghi vào Google Sheet", type="primary"):
    sh, bay_gio, n1, n2 = sheet(), dt.datetime.now().strftime("%d/%m/%Y %H:%M"), 0, 0
    for h, it, ed, ka in chon:
        if ed is not None:
            e = ed[ed["Ghi"] == True].fillna("")
            n1 += gs.ghi_chi(sh, [[x["Ngày"], x["Nhóm"], x["Diễn giải"], int(x["Số tiền"] or 0), x["Trạng thái"],
                                   x["Ghi chú"], it["ten"], h, it["model"], x["Cảnh báo"], bay_gio]
                                  for _, x in e.iterrows()])
        if ka is not None:
            k = ka[ka["Ghi"] == True].fillna("")
            n2 += gs.ghi_khoan(sh, [[x["Ngày"], int(x["Trưa"] or 0), int(x["Tối"] or 0), x["Ghi chú"], h]
                                    for _, x in k.iterrows()], cd["don_gia"])
    st.cache_data.clear()
    st.session_state.kq = {}
    st.session_state.tb = f"Đã ghi {n1} dòng chi và {n2} dòng chấm ăn vào Google Sheet."
    st.rerun()
