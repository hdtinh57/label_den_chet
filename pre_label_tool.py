import cv2
import os
from ultralytics import YOLO
from pathlib import Path
from tqdm import tqdm

def extract_and_detect(video_path, frame_output_folder, label_output_folder, frame_interval=0.5):
    # Tạo thư mục nếu chưa tồn tại
    if not os.path.exists(frame_output_folder):
        os.makedirs(frame_output_folder)
    if not os.path.exists(label_output_folder):
        os.makedirs(label_output_folder)

    # Mở video
    cap = cv2.VideoCapture(str(video_path))  # Chuyển đổi video_path thành chuỗi
    fps = cap.get(cv2.CAP_PROP_FPS)  # Lấy số frame trên mỗi giây của video
    frame_count = 0
    save_count = 0
    frame_time = 1 / fps  # Thời gian của mỗi frame
    interval_frame_count = int(frame_interval / frame_time)  # Số frame giữa mỗi lần cắt
    # Load mô hình YOLOv8
    model = YOLO('yolov8l.pt')  # Bạn có thể thay thế bằng phiên bản mô hình khác (yolov8s.pt, yolov8m.pt,...)

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        # Chỉ lưu frame sau mỗi khoảng thời gian 0.5 giây
        if frame_count % interval_frame_count == 0:
            # Lưu frame dưới dạng hình ảnh
            frame_name = os.path.join(frame_output_folder, f"{save_count:06}.png")
            cv2.imwrite(frame_name, frame)
            print(f"Saved {frame_name}")
            
            # Chạy mô hình YOLOv8 trên frame
            results = model(frame)
            
            # Tạo tên file .txt tương ứng
            txt_path = os.path.join(label_output_folder, f"{save_count:06}.txt")

            # Lưu bounding box vào file .txt theo định dạng yêu cầu
            with open(txt_path, 'w') as f:
                for result in results:
                    boxes = result.boxes  # Lấy kết quả bounding box
                    for box in boxes:
                        cls = int(box.cls[0])  # Class ID
                        
                        # Chỉ lưu bounding box của class "person" (ID = 0)
                        if cls == 0:
                            # Chuẩn hóa tọa độ: Chia các giá trị cho kích thước của ảnh
                            img_h, img_w = frame.shape[:2]  # Lấy chiều cao và chiều rộng của ảnh
                            x_center = box.xywh[0][0] / img_w
                            y_center = box.xywh[0][1] / img_h
                            width = box.xywh[0][2] / img_w
                            height = box.xywh[0][3] / img_h
                            
                            # Lưu vào file .txt với định dạng "0 class_id x_center y_center width height"
                            f.write(f"0 {cls} {x_center:.6f} {y_center:.6f} {width:.6f} {height:.6f}\n")
            
            print(f"Saved {txt_path}")
            save_count += 1
        
        frame_count += 1

    cap.release()
    

def process_all_videos(input_folder, frame_output_base, label_output_base, frame_interval=0.5):
    print("---PREPAIRING---")
    video_files = list(Path(input_folder).glob('*.mp4'))  # Lấy tất cả các video .mp4 trong thư mục
    for i, video_path in enumerate(tqdm(video_files, desc="Processing videos", unit="video")):
        # Tạo tên thư mục con cho mỗi video
        frame_output_folder = os.path.join(frame_output_base, f"{i:04}")
        label_output_folder = os.path.join(label_output_base, f"{i:04}")
        print((video_path.name).upper())
        # Gọi hàm xử lý cho từng video
        extract_and_detect(video_path, frame_output_folder, label_output_folder, frame_interval)
        print("--------------------------------------------------")
        print(f"Video completed: {video_path.name}")
        print(f"Video path: {frame_output_folder} and {label_output_folder}")
        print("--------------------------------------------------")
# Đường dẫn tới thư mục chứa video, thư mục cơ sở lưu trữ frame và nhãn
input_folder = "video_data"
frame_output_base = "images"
label_output_base = "labels_with_ids"

# Gọi hàm để xử lý tất cả video trong thư mục đầu vào
process_all_videos(input_folder, frame_output_base, label_output_base, frame_interval=0.5)
