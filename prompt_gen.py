import csv
import os
import random

def generate_prompts(elements_folder, prompts_output_folder):
    # Create the output folder if it doesn't exist
    if not os.path.exists(prompts_output_folder):
        os.makedirs(prompts_output_folder)
    
    # Define diverse templates for the prompts
    templates = [
        "A person wearing a {color} who is {action}.",
        "{action} person in a {color}.",
        "Someone with a {color}, {action}.",
        "A person in a {color} engaged in {action}.",
        "The person wearing a {color} and {action}.",
        "An individual in {color} doing {action}."
    ]
    
    # Loop through each CSV file in the elements folder
    for elements_file in os.listdir(elements_folder):
        if elements_file.endswith('.csv'):
            prompts = []
            csv_path = os.path.join(elements_folder, elements_file)
            with open(csv_path, mode='r') as file:
                reader = csv.DictReader(file)
                for row in reader:
                    frame_id = row['frame_id']
                    class_id = row['class_id']
                    color = row['color']
                    action = row['action']
                    
                    # Select a random template
                    template = random.choice(templates)
                    
                    # Substitute placeholders with actual values and capitalize the first word if needed
                    if color and action:
                        prompt = template.format(color=color, action=action)
                        # Capitalize the first character if not already capitalized
                        prompt = prompt[0].upper() + prompt[1:]
                    elif color:
                        prompt = f"A person wearing a {color}."
                    elif action:
                        prompt = f"A person who is {action}."
                    else:
                        prompt = f"A person."
                    
                    prompts.append(prompt)
            
            # Save prompts to a new file in the output folder
            prompts_file_name = f"{os.path.splitext(elements_file)[0]}_prompts.txt"
            prompts_file_path = os.path.join(prompts_output_folder, prompts_file_name)
            with open(prompts_file_path, mode='w') as file:
                for prompt in prompts:
                    file.write(prompt + '\n')
    
    print(f"Prompts generated and saved in {prompts_output_folder}")

# Example usage with your specified paths
elements_folder = "elements/0000"  # Path to the elements folder
prompts_output_folder = "prompt_gen/0000"  # Path to save prompts
generate_prompts(elements_folder, prompts_output_folder)
