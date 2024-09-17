import tkinter as tk
from tkinter import messagebox, simpledialog, Toplevel, Entry, Button, filedialog, Menu
from PIL import Image, ImageTk
import os
from pathlib import Path
import csv

class LabelTool:
    def __init__(self, root):
        self.root = root
        self.frame_folder = ""
        self.output_folder = ""
        self.elements_folder = ""  # Folder path for elements
        self.elements_file = ""  # Full path to elements CSV file
        self.frames = []
        self.current_frame_index = 0
        self.bboxes = []
        self.current_bbox = None
        self.scale_factor = 0.5  # Scale factor for image resizing

        # Variables to handle drawing new bounding boxes
        self.drawing = False
        self.allow_drawing = False
        self.start_x = None
        self.start_y = None
        self.current_rect = None

        # Variables to handle resizing bounding boxes
        self.resizing = False
        self.resizing_bbox = None
        self.resize_corner = None
        self.resize_margin = 10  # Margin to detect corners for resizing
        self.handle_size = 8  # Size of the resize handle

        # Setup GUI
        self.canvas = tk.Canvas(root, bg='white')  # Set canvas background to white
        self.canvas.pack(expand=True, fill=tk.BOTH)
        self.canvas.bind("<Button-1>", self.on_mouse_click)
        self.canvas.bind("<B1-Motion>", self.on_mouse_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_mouse_release)
        self.canvas.bind("<Motion>", self.on_mouse_move)  # Track mouse movement for cursor change
        self.root.bind("<KeyPress-h>", self.enable_drawing)
        self.root.bind("<KeyRelease-h>", self.disable_drawing)

        # Create a text box for showing bounding box information
        self.info_text = tk.Text(root, height=10, width=100)
        self.info_text.pack()  # Move the info box to the bottom and center it
        self.info_text.config(state='disabled')

        # Additional information panel
        self.details_frame = tk.Frame(root)
        self.details_frame.pack(side=tk.LEFT, fill=tk.Y)
        self.info_label = tk.Label(self.details_frame, text="Details:\n", justify=tk.LEFT, anchor="w")
        self.info_label.pack(anchor="nw")

        # List to store deleted bounding boxes for undo functionality
        self.deleted_bboxes = {}

        # Navigation buttons
        btn_frame = tk.Frame(root)
        btn_frame.pack(side=tk.BOTTOM, fill=tk.X)
        self.save_button = tk.Button(btn_frame, text="Save", command=self.save)
        self.save_button.pack(side=tk.RIGHT)
        self.next_button = tk.Button(btn_frame, text="Next", command=self.next_frame)
        self.next_button.pack(side=tk.RIGHT)
        self.root.bind('<Right>', lambda event: self.next_frame())
        self.root.bind('<Left>', lambda event: self.prev_frame())

        self.prev_button = tk.Button(btn_frame, text="Previous", command=self.prev_frame)
        self.prev_button.pack(side=tk.RIGHT)
        self.undo_button = tk.Button(btn_frame, text="Undo", command=self.undo_delete)
        self.undo_button.pack(side=tk.RIGHT)
        self.delete_frame_button = tk.Button(btn_frame, text="Delete Frame", command=self.delete_frame)
        self.delete_frame_button.pack(side=tk.LEFT)
        self.undo_delete_frame_button = tk.Button(btn_frame, text="Undo Delete Frame", command=self.undo_delete_frame)
        self.undo_delete_frame_button.pack(side=tk.LEFT)

        # Initially hide navigation buttons until folders are selected
        self.toggle_navigation_buttons(False)

        # Folder selection buttons
        self.folder_frame = tk.Frame(root)
        self.folder_frame.pack(expand=True)
        tk.Button(self.folder_frame, text="Browse Images Folder", command=self.browse_images_folder).pack(side=tk.LEFT, padx=5)

        # Create a menu for browsing folders later
        self.create_menu()

    def create_menu(self):
        """Create a menu bar for browsing folders."""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        browse_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Browse", menu=browse_menu)
        browse_menu.add_command(label="Browse Images Folder", command=self.browse_images_folder)

    def browse_images_folder(self):
        """Browse and select the images folder and automatically find labels and elements folders."""
        self.frame_folder = filedialog.askdirectory(title="Select Images Folder")
        if self.frame_folder:
            # Extract subfolder name and automatically select corresponding labels folder
            subfolder_name = os.path.basename(self.frame_folder)
            subfolder_number = subfolder_name[-1]
            # Get the grandparent directory of the selected images folder
            images_grandparent_folder = os.path.abspath(os.path.join(self.frame_folder, os.pardir, os.pardir))
            # Now look for labels_with_ids at the same level as the grandparent of images
            potential_labels_folder = os.path.join(images_grandparent_folder, "labels_with_ids", subfolder_name)
            potential_elements_folder = os.path.join(images_grandparent_folder, "elements")

            # Check if the corresponding labels folder exists
            if os.path.exists(potential_labels_folder):
                self.output_folder = potential_labels_folder
            else:
                messagebox.showerror("Error", f"Labels folder not found: {potential_labels_folder}")
                self.output_folder = ""

            # Check if the elements folder exists and set it up
            if os.path.exists(potential_elements_folder):
                self.elements_folder = potential_elements_folder
                self.elements_file = os.path.join(self.elements_folder, f"elements_{subfolder_number}.csv")
                if not os.path.exists(self.elements_file):
                    # Create the CSV file if it doesn't exist
                    with open(self.elements_file, mode='w', newline='') as file:
                        writer = csv.writer(file)
                        writer.writerow(['frame_id', 'class_id', 'color', 'action', 'gender'])
            else:
                messagebox.showerror("Error", f"Elements folder not found: {potential_elements_folder}")
                self.elements_folder = ""

            self.frames = sorted([f for f in os.listdir(self.frame_folder) if f.endswith('.png')])
            self.current_frame_index = 0

            # Check and load frame if both labels and elements folders are set
            if self.output_folder and self.elements_folder:
                self.folder_frame.pack_forget()  # Hide the folder selection buttons
                self.toggle_navigation_buttons(True)  # Show navigation buttons
                self.load_frame()

    def toggle_navigation_buttons(self, show):
        """Show or hide navigation buttons."""
        if show:
            self.save_button.pack(side=tk.RIGHT)
            self.next_button.pack(side=tk.RIGHT)
            self.prev_button.pack(side=tk.RIGHT)
            self.undo_button.pack(side=tk.RIGHT)
            self.delete_frame_button.pack(side=tk.LEFT)
            self.undo_delete_frame_button.pack(side=tk.LEFT)
        else:
            self.save_button.pack_forget()
            self.next_button.pack_forget()
            self.prev_button.pack_forget()
            self.undo_button.pack_forget()
            self.delete_frame_button.pack_forget()
            self.undo_delete_frame_button.pack_forget()

    def load_frame(self):
        if not self.frames or not self.output_folder or not self.elements_file:
            return

        frame_name = self.frames[self.current_frame_index]
        self.frame_path = os.path.join(self.frame_folder, frame_name)
        self.current_frame = Image.open(self.frame_path)
        self.img_w, self.img_h = self.current_frame.size

        # Set the scale factor manually
        self.scale_factor = self.scale_factor  

        # Apply the scaling to the image
        new_w = int(self.img_w * self.scale_factor)
        new_h = int(self.img_h * self.scale_factor)
        self.current_frame = self.current_frame.resize((new_w, new_h), Image.LANCZOS)
        self.img_w, self.img_h = self.current_frame.size

        # Load corresponding bounding boxes from the file
        self.txt_path = os.path.join(self.output_folder, f"{os.path.splitext(frame_name)[0]}.txt")
        self.bboxes = []
        if os.path.exists(self.txt_path):
            self.bboxes = get_bounding_boxes(self.txt_path, self.img_w / self.scale_factor, self.img_h / self.scale_factor)

        # Initialize the undo list for this frame if not already done
        if frame_name not in self.deleted_bboxes:
            self.deleted_bboxes[frame_name] = []

        # Load elements if they exist   
        self.load_elements()

        # Display frame and bounding boxes
        self.display_frame()

        # Update detail information
        self.update_info_label()

    def load_elements(self):
        """Load elements information from the single CSV file."""
        self.frame_actions = {}  # Store actions for the current frame
        if os.path.exists(self.elements_file):
            with open(self.elements_file, mode='r', newline='') as file:
                reader = csv.DictReader(file)
                for row in reader:
                    frame_id = int(row['frame_id'])
                    cls_id = int(row['class_id'])
                    if frame_id == self.current_frame_index:
                        # Load action and color for the current frame
                        self.frame_actions[cls_id] = {'color': row['color'], 'action': row['action'], 'gender': row['gender']}
                    elif cls_id not in self.frame_actions:
                        # Load the latest action if not set in the current frame
                        self.frame_actions[cls_id] = {'color': row['color'], 'action': row['action'], 'gender': row['gender']}
        
        for bbox in self.bboxes:
            cls_id = bbox['class_id']
            if cls_id in self.frame_actions:
                bbox['color'] = self.frame_actions[cls_id]['color']
                bbox['action'] = self.frame_actions[cls_id]['action']
                bbox['gender'] = self.frame_actions[cls_id]['gender']

    def display_frame(self):
        # Clear the canvas before displaying the new frame
        self.canvas.delete("all")
        # Resize canvas to fit the image
        self.canvas.config(width=self.img_w, height=self.img_h)
        # Convert to PhotoImage
        self.photo = ImageTk.PhotoImage(self.current_frame)
        self.canvas.create_image(0, 0, image=self.photo, anchor=tk.NW)
        self.draw_bboxes()
        self.display_bbox_info()

    def update_info_label(self):
        """Update the information label with the current frame and labels details."""
        frame_name = self.frames[self.current_frame_index] 
        images_folder_path = self.frame_folder.replace("\\", "/")
        labels_folder_path = self.output_folder.replace("\\", "/")
        elements_folder_path = self.elements_file.replace("\\", "/")
        info_text = (
            f"Images Folder: {images_folder_path}\n"
            f"Labels Folder: {labels_folder_path}\n"
            f"Elements Folder: {elements_folder_path}\n"
            f"Current Image: {frame_name}\n"
            f"Label File: {os.path.basename(self.txt_path) if os.path.exists(self.txt_path) else 'No label file'}\n"
        )
        self.info_label.config(text=info_text)

    def draw_bboxes(self):
        for bbox in self.bboxes:
            # Scale bounding box coordinates for display
            x = int(bbox['coords'][0] * self.scale_factor)
            y = int(bbox['coords'][1] * self.scale_factor)
            w = int(bbox['coords'][2] * self.scale_factor)
            h = int(bbox['coords'][3] * self.scale_factor)
            cls_id = bbox['class_id']
            bbox['rect'] = self.canvas.create_rectangle(x, y, x + w, y + h, outline="red", width=2)
            bbox['text'] = self.canvas.create_text(x, y - 10, text=f"ID: {cls_id}", fill="red")
            # Draw handles on each corner
            self.draw_resize_handles(x, y, w, h)

    def draw_resize_handles(self, x, y, w, h):
        """Draw small squares at the corners of the bounding box for resizing."""
        handle_radius = self.handle_size // 2
        corners = [
            (x - handle_radius, y - handle_radius, x + handle_radius, y + handle_radius),  # top-left
            (x + w - handle_radius, y - handle_radius, x + w + handle_radius, y + handle_radius),  # top-right
            (x - handle_radius, y + h - handle_radius, x + handle_radius, y + h + handle_radius),  # bottom-left
            (x + w - handle_radius, y + h - handle_radius, x + w + handle_radius, y + h + handle_radius)  # bottom-right
        ]
        for cx, cy, ex, ey in corners:
            self.canvas.create_rectangle(cx, cy, ex, ey, outline="blue", fill="blue")

    def display_bbox_info(self):
        self.info_text.config(state='normal')
        self.info_text.delete(1.0, tk.END)
        for idx, bbox in enumerate(self.bboxes):
            x, y, w, h = bbox['coords']
            cls_id = bbox['class_id']
            color = bbox.get('color', '')
            action = bbox.get('action', '')
            gender = bbox.get('gender', '')
            self.info_text.insert(tk.END, f"BBox {idx+1}: ID: {cls_id}, Coords: ({x}, {y}, {w}, {h}), Color: {color}, Action: {action}, Gender: {gender}\n")
        self.info_text.config(state='disabled')

    def delete_frame(self):
        """Delete the current frame from both images and labels."""
        if not self.frames:
            return
        
        # Get the current frame name
        frame_name = self.frames[self.current_frame_index]
        image_path = os.path.join(self.frame_folder, frame_name)
        label_path = os.path.join(self.output_folder, f"{os.path.splitext(frame_name)[0]}.txt")

        # Store the frame info for undo
        self.deleted_frame_info = {
            'index': self.current_frame_index,
            'frame_name': frame_name,
            'image_data': None,
            'label_data': None
        }

        # Read and store the image data
        with open(image_path, 'rb') as img_file:
            self.deleted_frame_info['image_data'] = img_file.read()

        # Read and store the label data if it exists
        if os.path.exists(label_path):
            with open(label_path, 'r') as lbl_file:
                self.deleted_frame_info['label_data'] = lbl_file.read()
        
        # Delete image file
        try:
            os.remove(image_path)
        except OSError as e:
            messagebox.showerror("Error", f"Error deleting image file: {e}")

        # Delete label file if it exists
        if os.path.exists(label_path):
            try:
                os.remove(label_path)
            except OSError as e:
                messagebox.showerror("Error", f"Error deleting label file: {e}")

        # Remove frame from the list and update the current frame index
        del self.frames[self.current_frame_index]

        if self.current_frame_index >= len(self.frames):
            self.current_frame_index = len(self.frames) - 1

        # Load the next frame if available
        if self.frames:
            self.load_frame()
        else:
            # Clear the canvas if no frames are left
            self.canvas.delete("all")
            messagebox.showinfo("Info", "All frames deleted.")

    def undo_delete_frame(self):
        """Undo the last frame deletion."""
        if not self.deleted_frame_info:
            messagebox.showerror("Error", "No frame to undo.")
            return
        
        # Restore the image file
        image_path = os.path.join(self.frame_folder, self.deleted_frame_info['frame_name'])
        with open(image_path, 'wb') as img_file:
            img_file.write(self.deleted_frame_info['image_data'])

        # Restore the label file if it was present
        if self.deleted_frame_info['label_data']:
            label_path = os.path.join(self.output_folder, f"{os.path.splitext(self.deleted_frame_info['frame_name'])[0]}.txt")
            with open(label_path, 'w') as lbl_file:
                lbl_file.write(self.deleted_frame_info['label_data'])

        # Insert the frame back into the list at the original index
        self.frames.insert(self.deleted_frame_info['index'], self.deleted_frame_info['frame_name'])

        # Set the current frame index to the restored frame
        self.current_frame_index = self.deleted_frame_info['index']

        # Load the restored frame
        self.load_frame()

        # Clear the deleted frame info after undo
        self.deleted_frame_info = None

    def show_temporary_message(self, message, duration=1000):
        """Show a temporary message for a specified duration in milliseconds."""
        # Create a label to show the message
        self.message_label = tk.Label(self.root, text=message, bg='yellow')
        self.message_label.pack(side=tk.TOP, fill=tk.X)
        
        # Remove the label after the specified duration
        self.root.after(duration, self.message_label.destroy)

    def prev_frame(self):
        self.save()
        # Move to the last frame if currently at the first frame
        self.current_frame_index = (self.current_frame_index - 1) % len(self.frames)
        self.load_frame()
    
    def next_frame(self):
        self.save()
        # Move to the first frame if currently at the last frame
        self.current_frame_index = (self.current_frame_index + 1) % len(self.frames)
        self.load_frame()

    def save(self):
        """Save the bounding boxes and elements for the current frame."""
        # Save bounding boxes to the txt file
        update_txt_file(self.txt_path, self.bboxes, self.img_w / self.scale_factor, self.img_h / self.scale_factor)
        # Save elements information
        self.save_elements()
        self.show_temporary_message("Bounding boxes and elements saved successfully.", duration=1000)

    def save_elements(self):
        """Save elements information to the single CSV file."""
        elements_data = []
        
        # Load existing elements from the file
        if os.path.exists(self.elements_file):
            with open(self.elements_file, mode='r', newline='') as file:
                reader = csv.DictReader(file)
                for row in reader:
                    frame_id = int(row['frame_id'])
                    class_id = int(row['class_id'])
                    # Filter out invalid frame_id
                    if 0 <= frame_id < len(self.frames):
                        elements_data.append(row)

        # Create a dictionary to quickly find existing (frame_id, class_id) pairs
        elements_dict = {(int(row['frame_id']), int(row['class_id'])): row for row in elements_data}

        # Add or update with current frame's data
        frame_id = self.current_frame_index
        for bbox in self.bboxes:
            cls_id = bbox['class_id']
            
            # Skip adding this bounding box if class_id is 0
            if cls_id == 0:
                continue

            color = bbox.get('color', '')
            action = bbox.get('action', '')
            gender = bbox.get('gender', '')

            # Check if the (frame_id, class_id) already exists
            if (frame_id, cls_id) in elements_dict:
                # Update the existing entry
                elements_dict[(frame_id, cls_id)] = {'frame_id': frame_id, 'class_id': cls_id, 'color': color, 'action': action, 'gender': gender}
            else:
                # Add new entry if not existing
                elements_dict[(frame_id, cls_id)] = {'frame_id': frame_id, 'class_id': cls_id, 'color': color, 'action': action, 'gender': gender}

        # Write back to CSV with updated elements
        with open(self.elements_file, mode='w', newline='') as file:
            writer = csv.DictWriter(file, fieldnames=['frame_id', 'class_id', 'color', 'action', 'gender'])
            writer.writeheader()
            for data in elements_dict.values():
                writer.writerow(data)

    def enable_drawing(self, event):
        """Enable drawing mode when 'H' key is pressed.""" 
        self.allow_drawing = True

    def disable_drawing(self, event):
        """Disable drawing mode when 'H' key is released.""" 
        self.allow_drawing = False

    def on_mouse_click(self, event):
        if self.allow_drawing:
            self.drawing = True
            self.start_x = event.x
            self.start_y = event.y
        else:
            # Check if a bounding box was clicked for editing
            for bbox in self.bboxes:
                bx = int(bbox['coords'][0] * self.scale_factor)
                by = int(bbox['coords'][1] * self.scale_factor)
                bw = int(bbox['coords'][2] * self.scale_factor)
                bh = int(bbox['coords'][3] * self.scale_factor)
                # Check if click is near a corner for resizing
                if self.is_near_corner(event.x, event.y, bx, by, bw, bh):
                    self.resizing = True
                    self.resizing_bbox = bbox
                    self.resize_corner = self.get_resize_corner(event.x, event.y, bx, by, bw, bh)
                    self.start_x = event.x
                    self.start_y = event.y
                    return
                # Check if click is inside the bounding box for editing
                if bx <= event.x <= bx + bw and by <= event.y <= by + bh:
                    self.open_edit_dialog(bbox)
                    return

    def on_mouse_drag(self, event):
        if self.drawing:
            if self.current_rect:
                self.canvas.delete(self.current_rect)
            self.current_rect = self.canvas.create_rectangle(
                self.start_x, self.start_y, event.x, event.y, outline="blue", width=2
            )
        elif self.resizing:
            # Update bounding box size based on mouse drag
            if self.resizing_bbox:
                bx = int(self.resizing_bbox['coords'][0] * self.scale_factor)
                by = int(self.resizing_bbox['coords'][1] * self.scale_factor)
                bw = int(self.resizing_bbox['coords'][2] * self.scale_factor)
                bh = int(self.resizing_bbox['coords'][3] * self.scale_factor)
                if self.resize_corner == 'top-left':
                    new_x = min(event.x, bx + bw - 1)
                    new_y = min(event.y, by + bh - 1)
                    new_w = (bx + bw) - new_x
                    new_h = (by + bh) - new_y
                    self.resizing_bbox['coords'] = ((new_x / self.scale_factor), (new_y / self.scale_factor), max(1, new_w / self.scale_factor), max(1, new_h / self.scale_factor))
                elif self.resize_corner == 'bottom-right':
                    new_w = max(1, event.x - bx)
                    new_h = max(1, event.y - by)
                    self.resizing_bbox['coords'] = (bx / self.scale_factor, by / self.scale_factor, new_w / self.scale_factor, new_h / self.scale_factor)
                elif self.resize_corner == 'top-right':
                    new_w = max(1, event.x - bx)
                    new_h = max(1, (by + bh) - event.y)
                    self.resizing_bbox['coords'] = (bx / self.scale_factor, event.y / self.scale_factor, new_w / self.scale_factor, new_h / self.scale_factor)
                elif self.resize_corner == 'bottom-left':
                    new_w = max(1, (bx + bw) - event.x)
                    new_h = max(1, event.y - by)
                    self.resizing_bbox['coords'] = (event.x / self.scale_factor, by / self.scale_factor, new_w / self.scale_factor, new_h / self.scale_factor)
                self.display_frame()  # Redraw everything

    def on_mouse_release(self, event):
        if self.drawing:
            self.drawing = False
            if self.current_rect:
                self.canvas.delete(self.current_rect)
            # Create a new bounding box
            x1, y1 = min(self.start_x, event.x), min(self.start_y, event.y)
            x2, y2 = max(self.start_x, event.x), max(self.start_y, event.y)
            # Store original coordinates before scaling
            original_x1, original_y1 = x1 / self.scale_factor, y1 / self.scale_factor
            original_x2, original_y2 = x2 / self.scale_factor, y2 / self.scale_factor
            new_bbox = {'coords': (original_x1, original_y1, original_x2 - original_x1, original_y2 - original_y1), 'class_id': 0, 'color': '', 'action': '', 'gender': ''}  # Default class_id to 0
            self.bboxes.append(new_bbox)
            self.display_frame()  # Redraw everything
            self.open_edit_dialog(new_bbox)  # Prompt to set ID
        elif self.resizing:
            self.resizing = False
            self.resizing_bbox = None

    def undo_delete(self):
        """Undo the last delete action for the current frame."""
        # Get the current frame name
        frame_name = self.frames[self.current_frame_index]
        
        # Check if there are any deleted bboxes for this frame
        if frame_name in self.deleted_bboxes and self.deleted_bboxes[frame_name]:
            # Restore the last deleted bounding box
            last_deleted_bbox = self.deleted_bboxes[frame_name].pop()
            self.bboxes.append(last_deleted_bbox)
            self.display_frame()

    def open_edit_dialog(self, bbox):
        # Create a new top-level window
        edit_window = Toplevel(self.root)
        edit_window.title("Edit Bounding Box")

        # Set the window to appear in the center of the LabelTool application window
        window_width = 300
        window_height = 350  # Increased the height to fit all elements
        # Get the position of the main window
        main_x = self.root.winfo_x()
        main_y = self.root.winfo_y()
        main_width = self.root.winfo_width()
        main_height = self.root.winfo_height()
        # Calculate position x, y to center the pop-up within the main window
        position_right = main_x + main_width // 2 - window_width // 2
        position_down = main_y + main_height // 2 - window_height // 2
        edit_window.geometry(f"{window_width}x{window_height}+{position_right}+{position_down}")
        
        # Display the class name
        tk.Label(edit_window, text="Class: Person").pack(pady=5)
        
        # Create and place widgets
        tk.Label(edit_window, text="Enter new class ID:").pack(pady=5)
        id_entry = Entry(edit_window)
        id_entry.pack(pady=5)
        id_entry.insert(0, str(bbox['class_id']))  # Pre-fill with current ID

        tk.Label(edit_window, text="Enter color:").pack(pady=5)
        color_entry = Entry(edit_window)
        color_entry.pack(pady=5)
        color_entry.insert(0, bbox.get('color', ''))  # Pre-fill with current color

        tk.Label(edit_window, text="Enter action:").pack(pady=5)
        action_entry = Entry(edit_window)
        action_entry.pack(pady=5)
        action_entry.insert(0, bbox.get('action', ''))  # Pre-fill with current action

        tk.Label(edit_window, text="Enter gender:").pack(pady=5)
        gender_entry = Entry(edit_window)
        gender_entry.pack(pady=5)
        gender_entry.insert(0, bbox.get('gender', ''))  # Pre-fill with current gender
        def update_values():            
            # Get the new ID
            self.save()
            new_id = id_entry.get()
            color = color_entry.get()
            action = action_entry.get()
            gender = gender_entry.get()
            # Check if new_id already exists in current frame's bounding boxes
            if new_id.isdigit():
                new_id = int(new_id)
                existing_ids = [b['class_id'] for b in self.bboxes if b != bbox]  # Exclude the current bbox being edited
                if new_id in existing_ids:
                    messagebox.showerror("Error", f"ID {new_id} already exists in this frame. Please choose a unique ID.")
                    return

                # Update the bounding box ID, color, action, and gender
                bbox['class_id'] = new_id
                bbox['color'] = color
                bbox['action'] = action
                bbox['gender'] = gender
                self.display_frame()
                edit_window.destroy()

        def delete_bbox():
            """Remove the bounding box and store it for undo."""
            # Get the current frame name
            self.save()
            frame_name = self.frames[self.current_frame_index]
            
            # Initialize the list if this frame has no deleted bboxes yet
            if frame_name not in self.deleted_bboxes:
                self.deleted_bboxes[frame_name] = []
            
            # Save the bbox for undo
            self.deleted_bboxes[frame_name].append(bbox)
            
            # Remove the bounding box
            self.bboxes.remove(bbox)
            self.display_frame()
            edit_window.destroy()
        
        def enable_edit_mode():
            # Close the dialog and enter resizing mode
            self.resizing = True
            self.resizing_bbox = bbox
            edit_window.destroy()

        Button(edit_window, text="Update Values", command=update_values).pack(side=tk.LEFT, padx=5)
        Button(edit_window, text="Delete BB", command=delete_bbox).pack(side=tk.LEFT, padx=5)
        Button(edit_window, text="Edit BB", command=enable_edit_mode).pack(side=tk.RIGHT, padx=5)
        edit_window.bind('<Return>', lambda event: update_values())

    def on_info_click(self, event):
        """Handle mouse click event on the info text box."""
        # Get the clicked line number
        index = self.info_text.index(f"@{event.x},{event.y}")
        line_number = int(index.split('.')[0]) - 1  # Convert to zero-based index

        if 0 <= line_number < len(self.bboxes):
            # Get the corresponding bounding box
            bbox = self.bboxes[line_number]
            self.open_edit_dialog(bbox)

    def on_mouse_move(self, event):
        """Change cursor when hovering over resize handles."""
        cursor = ""
        for bbox in self.bboxes:
            bx = int(bbox['coords'][0] * self.scale_factor)
            by = int(bbox['coords'][1] * self.scale_factor)
            bw = int(bbox['coords'][2] * self.scale_factor)
            bh = int(bbox['coords'][3] * self.scale_factor)
            if self.is_near_corner(event.x, event.y, bx, by, bw, bh):
                cursor = "hand2"  # Change to a hand cursor
                break
        self.canvas.config(cursor=cursor)

    def is_near_corner(self, x, y, bx, by, bw, bh):
        """Check if the click is near a corner of the bounding box."""
        return (
            (abs(x - bx) <= self.handle_size and abs(y - by) <= self.handle_size) or  # Top-left corner
            (abs(x - (bx + bw)) <= self.handle_size and abs(y - (by + bh)) <= self.handle_size) or  # Bottom-right corner
            (abs(x - (bx + bw)) <= self.handle_size and abs(y - by) <= self.handle_size) or  # Top-right corner
            (abs(x - bx) <= self.handle_size and abs(y - (by + bh)) <= self.handle_size)  # Bottom-left corner
        )

    def get_resize_corner(self, x, y, bx, by, bw, bh):
        """Determine which corner of the bounding box is being clicked."""
        if abs(x - bx) <= self.handle_size and abs(y - by) <= self.handle_size:
            return 'top-left'
        elif abs(x - (bx + bw)) <= self.handle_size and abs(y - (by + bh)) <= self.handle_size:
            return 'bottom-right'
        elif abs(x - (bx + bw)) <= self.handle_size and abs(y - by) <= self.handle_size:
            return 'top-right'
        elif abs(x - bx) <= self.handle_size and abs(y - (by + bh)) <= self.handle_size:
            return 'bottom-left'
        return None

def get_bounding_boxes(txt_path, img_w, img_h):
    """Read bounding boxes from txt file."""
    boxes = []
    with open(txt_path, 'r') as f:
        lines = f.readlines()
        for line in lines:
            parts = line.strip().split()
            cls_id = int(parts[1])
            x_center = float(parts[2]) * img_w
            y_center = float(parts[3]) * img_h
            width = float(parts[4]) * img_w
            height = float(parts[5]) * img_h

            # Convert from center x,y,width,height to top-left x,y,width,height
            x = int(x_center - (width / 2))
            y = int(y_center - (height / 2))
            w = int(width)
            h = int(height)

            boxes.append({'coords': (x, y, w, h), 'class_id': cls_id})
    return boxes

def update_txt_file(txt_path, boxes, img_w, img_h):
    """Update the .txt file with new bounding boxes."""
    with open(txt_path, 'w') as f:
        for box in boxes:
            x, y, w, h = box['coords']
            cls_id = box['class_id']
            # Convert coordinates back to YOLO format (normalized)
            x_center = (x + w / 2) / img_w
            y_center = (y + h / 2) / img_h
            width = w / img_w
            height = h / img_h
            f.write(f"0 {cls_id} {x_center:.6f} {y_center:.6f} {width:.6f} {height:.6f}\n")

def main():
    # Set up the main application window
    root = tk.Tk()
    root.title("Person ID Labeling Tool")
    app = LabelTool(root)
    root.mainloop()

if __name__ == '__main__':
    main()
