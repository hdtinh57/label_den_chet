import csv
import os
import random
from pathlib import Path

def generate_prompts(elements_folder, prompts_output_folder):
    # Tạo folder đầu ra nếu nó không tồn tại
    if not os.path.exists(prompts_output_folder):
        os.makedirs(prompts_output_folder)

    # Danh sách để lưu các đường dẫn tệp _prompts.txt được tạo ra
    generated_files = []

    # Định nghĩa các mẫu đa dạng cho các prompt
    templates = [
        "A person wearing a {color} who is {action}.",
        "{action} person in a {color}.",
        "Someone with a {color}, {action}.",
        "A person in a {color} engaged in {action}.",
        "The person wearing a {color} and {action}.",
        "An individual in {color} doing {action}."
    ]

    # Lấy danh sách tất cả các file .csv trong folder elements
    csv_files = [f for f in os.listdir(elements_folder) if f.endswith('.csv')]

    # Xử lý từng file CSV
    for elements_file in csv_files:
        prompts = []
        csv_path = os.path.join(elements_folder, elements_file)
        with open(csv_path, mode='r') as file:
            reader = csv.DictReader(file)
            for row in reader:
                frame_id = row.get('frame_id')
                class_id = row.get('class_id')
                color = row.get('color')
                action = row.get('action')

                # Chọn ngẫu nhiên một template
                template = random.choice(templates)

                # Thay thế các placeholder bằng giá trị thực tế và viết hoa chữ cái đầu nếu cần
                if color and action:
                    prompt = template.format(color=color, action=action)
                    # Viết hoa ký tự đầu tiên nếu không được viết hoa
                    prompt = prompt[0].upper() + prompt[1:]
                elif color:
                    prompt = f"A person wearing a {color}."
                elif action:
                    prompt = f"A person who is {action}."
                else:
                    prompt = f"A person."

                prompts.append(prompt)

        # Lưu các prompt vào một file mới trong folder đầu ra
        prompts_file_name = f"{os.path.splitext(elements_file)[0]}_prompts.txt"
        prompts_file_path = os.path.join(prompts_output_folder, prompts_file_name)
        with open(prompts_file_path, mode='w') as file:
            for prompt in prompts:
                file.write(prompt + '\n')

        # Chuẩn hóa đường dẫn và in ra
        normalized_path = os.path.normpath(prompts_file_path)
        print(f"Generated prompts file at: {normalized_path}")

        # Thêm đường dẫn tệp đã tạo vào danh sách
        generated_files.append(normalized_path)

    # Trả về danh sách các đường dẫn tệp _prompts.txt đã được tạo
    return generated_files

# elements_folder = "elements"  # Đường dẫn đến thư mục elements
# prompts_output_folder = "prompt_gen"
# generate_prompts(elements_folder, prompts_output_folder)


