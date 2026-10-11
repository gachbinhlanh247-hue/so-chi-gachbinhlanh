# Sổ chi công ty – quy tắc cho Claude khi sửa phần mềm
Phần mềm Streamlit: chụp ảnh sổ chép tay → Gemini đọc → người dùng duyệt → ghi Google Sheet. Tất cả dùng gói miễn phí.
- File: `app.py` (giao diện), `kiem_tra.py` (tính lại phép nhân, tổng), `doc_anh.py` (Gemini, đổi model khi lỗi), `ghi_sheet.py` (Sheet), `QUY_TAC_DOC.md` (lời nhắc đọc ảnh).
- Không bao giờ ghi khóa Gemini, khóa Google, ID Sheet vào code hay tài liệu; chỉ dùng `st.secrets`.
- Luôn giữ bước duyệt trước khi ghi; luôn kiểm tra trùng (mã ảnh + khóa ngày|diễn giải|số tiền).
- Danh sách model, nhóm, đơn giá nằm ở tab `Cai_dat` của Sheet, không viết cứng vào code (trừ giá trị mặc định).
- Chỉ thêm tab / cột ở cuối, không đổi thứ tự cột đã có (công thức Tong_hop phụ thuộc cột B và D của Chi_tiet).
- Đổi yêu cầu chưa rõ thì hỏi người dùng trước; trả lời tiếng Việt, ngắn, từng bước.
- Chưa thử được từ môi trường không có mạng: gọi Gemini và ghi Sheet thật; luôn báo rõ điều này.
- Phép nhân / tổng viết tay: Gemini chỉ chép số, `kiem_tra.py` tự tính lại; không để AI tự sửa số cho khớp.
