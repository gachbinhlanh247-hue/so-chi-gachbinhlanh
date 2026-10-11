# Hướng dẫn cài đặt (làm một lần, khoảng 20 phút, tất cả miễn phí)

## 1. Khóa Gemini
Vào https://aistudio.google.com/apikey → **Create API key**. Có thể tạo thêm khóa từ tài khoản Google khác
để tăng tổng hạn mức miễn phí.

## 2. Google Sheet
Tạo một Google Sheet trống. Chép **ID** trong địa chỉ: `docs.google.com/spreadsheets/d/<ID>/edit`.
Các tab Chi_tiet, Khoan_an, Tong_hop, Cai_dat sẽ tự được tạo ở lần chạy đầu.

## 3. Khóa Google (tài khoản dịch vụ)
1. Vào https://console.cloud.google.com → tạo Project mới.
2. Menu **APIs & Services → Library** → bật **Google Sheets API**.
3. **IAM & Admin → Service Accounts → Create** (đặt tên bất kỳ) → vào tài khoản vừa tạo → **Keys → Add key → JSON** (tải file về).
4. Mở Google Sheet → **Chia sẻ** → dán địa chỉ email `client_email` trong file JSON → quyền **Editor**.

## 4. Đưa lên Streamlit (miễn phí)
1. Tạo kho GitHub riêng tư, tải các file trong thư mục này lên (không tải file khóa JSON).
2. Vào https://share.streamlit.io → **Create app** → chọn kho, nhánh main, file `app.py`.
3. **Advanced settings → Secrets**, dán nội dung sau rồi thay bằng giá trị thật (phần `[GOOGLE_SERVICE_ACCOUNT]` chép từng dòng từ file JSON):

```toml
GEMINI_KEYS = ["khoa-gemini-1", "khoa-gemini-2"]
SHEET_ID = "id-cua-google-sheet"
ACCESS_CODE = "ma-chung-ban-tu-dat"

[GOOGLE_SERVICE_ACCOUNT]
type = "service_account"
project_id = "..."
private_key_id = "..."
private_key = "-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n"
client_email = "...@....iam.gserviceaccount.com"
client_id = "..."
token_uri = "https://oauth2.googleapis.com/token"
```
4. Bấm **Deploy**. Mở link trên điện thoại, chọn "Thêm vào màn hình chính".

## 5. Dùng hằng ngày
Mở link → nhập mã → chụp/chọn ảnh → **Đọc ảnh** → sửa trong bảng → **Ghi vào Google Sheet**.

## 6. Chỉnh sửa không cần code
- Đổi / thêm model Gemini, nhóm chi, đơn giá bữa ăn: sửa tab **Cai_dat** trong Sheet (mỗi model một dòng, cột A là `model`).
- Đổi cách đọc ảnh: sửa file `QUY_TAC_DOC.md` trên GitHub.
- Nếu một model báo lỗi 404, tên model đã đổi: xóa dòng đó trong Cai_dat, hoặc thay bằng tên mới trên trang tài liệu của Google AI Studio.
