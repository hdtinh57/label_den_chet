import os
import json
import csv
import openai
import re
from prompt_gen import generate_prompts
# Configuration
# openai.api_key = "api ne "  # Replace with your OpenAI API key
prompts_output_folder = "prompt_gen"  # Replace with the actual path
labels_folder = "labels_with_ids"  # Replace with the actual path
elements_folder = "elements"  # Replace with the actual path
output_folder = "expression"  # Replace with the actual path

def main():
    # Generate prompts using generate_prompts function
    prompt_file_paths = generate_prompts(elements_folder, prompts_output_folder)

    # Process each generated prompt file
    for i, prompt_file_path in enumerate(prompt_file_paths):
        # Determine the subfolder name for each elements file
        subfolder_name = f"{i:04d}"
        subfolder_path = os.path.join(output_folder, subfolder_name)
        os.makedirs(subfolder_path, exist_ok=True)

        # Read raw sentences from the generated prompt file
        with open(prompt_file_path, 'r') as file:
            raw_sentences = [line.strip() for line in file.readlines()]

        # Parse elements from CSV files
        element_data = parse_elements(elements_folder)

        # Process each raw sentence
        for raw_sentence in raw_sentences:
            matching_ids = find_matching_ids(raw_sentence, element_data)
            frame_data = filter_frames(labels_folder, matching_ids)
            generate_json_files(raw_sentence, frame_data, subfolder_path)

def parse_elements(elements_folder):
    """Parse the elements CSV files to collect the data."""
    element_data = {}
    for file in os.listdir(elements_folder):
        if file.endswith(".csv"):
            file_path = os.path.join(elements_folder, file)
            with open(file_path, mode='r') as csv_file:
                reader = csv.DictReader(csv_file)
                for row in reader:
                    element_data[int(row['class_id'])] = {
                        'color': row['color'].strip().lower() if row['color'] else '',  # Convert to lowercase
                        'action': row['action'].strip().lower() if row['action'] else ''  # Convert to lowercase
                    }
    return element_data

def find_matching_ids(prompt, element_data):
    """Find IDs that match the given prompt based on the element data."""
    prompt_lower = prompt.lower()  # Convert the prompt to lowercase for case-insensitive matching
    matching_ids = []
    for cls_id, attributes in element_data.items():
        color = attributes.get('color') or ''
        action = attributes.get('action') or ''
        # Check if both color and action are in the prompt (case-insensitive)
        if (color in prompt_lower or not color) and (action in prompt_lower or not action):
            matching_ids.append(cls_id)
    return matching_ids

def filter_frames(labels_folder, matching_ids):
    """Filter frames to find all IDs matching the attributes."""
    frame_data = {}
    for subfolder in os.listdir(labels_folder):
        subfolder_path = os.path.join(labels_folder, subfolder)
        if os.path.isdir(subfolder_path):
            for file in os.listdir(subfolder_path):
                if file.endswith(".txt"):
                    frame_number = int(file.split('.')[0])  # Assuming filename is like "000001.txt"
                    file_path = os.path.join(subfolder_path, file)

                    with open(file_path, 'r') as f:
                        lines = f.readlines()
                        frame_ids = []
                        for line in lines:
                            parts = line.strip().split()
                            id_in_frame = int(parts[1])
                            if id_in_frame in matching_ids:
                                frame_ids.append(id_in_frame)

                        if frame_ids:
                            frame_data[frame_number] = sorted(frame_ids)
    return frame_data

def generate_json_files(raw_sentence, frame_data, subfolder_path):
    """Generate JSON files with paraphrased sentences."""
    generated_sentences = set()  # Store sentences to avoid repetition
    counter = 0

    while len(generated_sentences) < 5:
        paraphrased_sentence = paraphrase(raw_sentence)
        if paraphrased_sentence not in generated_sentences:
            generated_sentences.add(paraphrased_sentence)
            
            # Prepare JSON data
            json_data = {
                "label": frame_data,
                "ignore": [],
                "video_name": os.path.basename(labels_folder),
                "sentence": paraphrased_sentence,
                "raw_sentence": raw_sentence
            }

            # Sanitize filename by removing invalid characters
            sanitized_prompt = sanitize_filename(paraphrased_sentence)

            # Save JSON file
            json_filename = f"{sanitized_prompt}.json"
            json_path = os.path.join(subfolder_path, json_filename)
            with open(json_path, 'w') as json_file:
                json.dump(json_data, json_file, indent=4)
            counter += 1

def paraphrase(sentence):
    """Use OpenAI API to paraphrase the sentence."""
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful assistant that paraphrases sentences."},
                {"role": "user", "content": f"Paraphrase the following sentence: '{sentence}'"}
            ],
            max_tokens=60,
            temperature=0.7,
        )
        paraphrased_sentence = response['choices'][0]['message']['content'].strip()
        return paraphrased_sentence
    except Exception as e:
        print(f"Error during paraphrasing: {e}")
        return sentence  # Return the original sentence if paraphrasing fails

def sanitize_filename(prompt):
    """Sanitize the prompt to create a valid filename."""
    sanitized_prompt = re.sub(r'[<>:"/\\|?*\n]', '', prompt)  # Remove invalid characters
    sanitized_prompt = sanitized_prompt.replace(' ', '_')  # Replace spaces with underscores
    sanitized_prompt = sanitized_prompt[:150]  # Optionally truncate to prevent overly long filenames
    return sanitized_prompt

if __name__ == "__main__":
    main()

