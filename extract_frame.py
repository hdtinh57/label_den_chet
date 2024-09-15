import cv2
import os

def extract_frames(video_path, output_folder, frame_interval=0.5):
    # Tạo thư mục nếu chưa tồn tại
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    # Mở video
    cap = cv2.VideoCapture(video_path)
    fps = cap.get(cv2.CAP_PROP_FPS)  # Lấy số frame trên mỗi giây của video
    frame_count = 0
    save_count = 0
    frame_time = 1 / fps  # Thời gian của mỗi frame
    interval_frame_count = int(frame_interval / frame_time)  # Số frame giữa mỗi lần cắt

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        # Chỉ lưu frame sau mỗi khoảng thời gian 0.5 giây
        if frame_count % interval_frame_count == 0:
            frame_name = os.path.join(output_folder, f"{save_count:06}.png")
            cv2.imwrite(frame_name, frame)
            print(f"Saved {frame_name}")
            save_count += 1
        frame_count += 1

    cap.release()
    print(f"Extracted frames with interval of {frame_interval} seconds from {video_path}")

# Đường dẫn tới video và thư mục lưu trữ frame
video_path = "cctv.mp4"
output_folder = "images/0000"

# Gọi hàm với khoảng cách giữa các frame là 0.5 giây
extract_frames(video_path, output_folder, frame_interval=0.5)



