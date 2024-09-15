import os
from ultralytics import YOLO
from pathlib import Path
import cv2

def detect_objects_yolov8(frame_folder, output_folder):
    # Tạo thư mục nếu chưa tồn tại
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    # Load mô hình YOLOv8
    model = YOLO('yolov8l.pt')  # Bạn có thể thay thế bằng phiên bản mô hình khác (yolov8s.pt, yolov8m.pt,...)
    
    # Duyệt qua tất cả các frame trong folder
    for img_path in Path(frame_folder).glob('*.png'):
        # Đọc kích thước ảnh
        img = cv2.imread(str(img_path))
        img_h, img_w = img.shape[:2]  # Lấy chiều cao và chiều rộng của ảnh

        # Chạy mô hình YOLOv8 trên từng frame
        results = model(img_path)
        
        # Lấy tên file (frame) và tạo tên file .txt tương ứng
        img_name = img_path.stem  # Lấy phần tên file mà không có phần đuôi .png
        txt_path = os.path.join(output_folder, f"{img_name}.txt")
        
        # Lưu bounding box vào file .txt theo định dạng yêu cầu
        with open(txt_path, 'w') as f:
            for result in results:
                boxes = result.boxes  # Lấy kết quả bounding box
                for box in boxes:
                    cls = int(box.cls[0])  # Class ID
                    
                    # Chỉ lưu bounding box của class "person" (ID = 0)
                    if cls == 0:
                        # Chuẩn hóa tọa độ: Chia các giá trị cho kích thước của ảnh
                        x_center = box.xywh[0][0] / img_w
                        y_center = box.xywh[0][1] / img_h
                        width = box.xywh[0][2] / img_w
                        height = box.xywh[0][3] / img_h
                        
                        # Lưu vào file .txt với định dạng "0 class_id x_center y_center width height"
                        f.write(f"0 {cls} {x_center:.6f} {y_center:.6f} {width:.6f} {height:.6f}\n")
        
        print(f"Saved {txt_path}")

# Đường dẫn tới thư mục chứa frame và nơi lưu file bounding box
frame_folder = "images/0000"
output_folder = "labels_with_ids/0000"

# Gọi hàm để phát hiện object và lưu bounding box vào file .txt
detect_objects_yolov8(frame_folder, output_folder)
