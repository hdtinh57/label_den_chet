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
        self.info_text.pack()
        self.info_text.bind("<Button-1>", self.on_info_click)

        # Navigation buttons
        btn_frame = tk.Frame(root)
        btn_frame.pack(side=tk.BOTTOM, fill=tk.X)
        self.save_button = tk.Button(btn_frame, text="Save", command=self.save)
        self.save_button.pack(side=tk.RIGHT)
        self.next_button = tk.Button(btn_frame, text="Next", command=self.next_frame)
        self.next_button.pack(side=tk.RIGHT)
        self.prev_button = tk.Button(btn_frame, text="Previous", command=self.prev_frame)
        self.prev_button.pack(side=tk.LEFT)

        # Initially hide navigation buttons until folders are selected
        self.toggle_navigation_buttons(False)

        # Folder selection buttons
        self.folder_frame = tk.Frame(root)
        self.folder_frame.pack(expand=True)
        tk.Button(self.folder_frame, text="Browse Images Folder", command=self.browse_images_folder).pack(side=tk.LEFT, padx=5)
        tk.Button(self.folder_frame, text="Browse Labels Folder", command=self.browse_labels_folder).pack(side=tk.LEFT, padx=5)
        tk.Button(self.folder_frame, text="Browse Elements Folder", command=self.browse_elements_folder).pack(side=tk.LEFT, padx=5)

        # Create a menu for browsing folders later
        self.create_menu()

    def create_menu(self):
        """Create a menu bar for browsing folders."""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        browse_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Browse", menu=browse_menu)
        browse_menu.add_command(label="Browse Images Folder", command=self.browse_images_folder)
        browse_menu.add_command(label="Browse Labels Folder", command=self.browse_labels_folder)
        browse_menu.add_command(label="Browse Elements Folder", command=self.browse_elements_folder)

    def browse_images_folder(self):
        """Browse and select the images folder."""
        self.frame_folder = filedialog.askdirectory(title="Select Images Folder")
        if self.frame_folder:
            self.frames = sorted([f for f in os.listdir(self.frame_folder) if f.endswith('.png')])
            self.current_frame_index = 0
            if self.output_folder and self.elements_folder:
                self.folder_frame.pack_forget()  # Hide the folder selection buttons
                self.toggle_navigation_buttons(True)  # Show navigation buttons
            self.load_frame()

    def browse_labels_folder(self):
        """Browse and select the labels folder."""
        self.output_folder = filedialog.askdirectory(title="Select Labels Folder")
        if self.output_folder:
            if self.frame_folder and self.elements_folder:
                self.folder_frame.pack_forget()  # Hide the folder selection buttons
                self.toggle_navigation_buttons(True)  # Show navigation buttons
            self.load_frame()

    def browse_elements_folder(self):
        """Browse and select the elements folder."""
        self.elements_folder = filedialog.askdirectory(title="Select Elements Folder")
        if self.elements_folder:
            self.elements_file = os.path.join(self.elements_folder, "elements.csv")
            if not os.path.exists(self.elements_file):
                # Create the CSV file if it doesn't exist
                with open(self.elements_file, mode='w', newline='') as file:
                    writer = csv.writer(file)
                    writer.writerow(['frame_id', 'class_id', 'color', 'action'])
            if self.frame_folder and self.output_folder:
                self.folder_frame.pack_forget()  # Hide the folder selection buttons
                self.toggle_navigation_buttons(True)  # Show navigation buttons
            self.load_frame()

    def toggle_navigation_buttons(self, show):
        """Show or hide navigation buttons."""
        if show:
            self.save_button.pack(side=tk.RIGHT)
            self.next_button.pack(side=tk.RIGHT)
            self.prev_button.pack(side=tk.LEFT)
        else:
            self.save_button.pack_forget()
            self.next_button.pack_forget()
            self.prev_button.pack_forget()

    def load_frame(self):
        if not self.frames or not self.output_folder or not self.elements_file:
            return

        frame_name = self.frames[self.current_frame_index]
        self.frame_path = os.path.join(self.frame_folder, frame_name)
        self.current_frame = Image.open(self.frame_path)
        self.img_w, self.img_h = self.current_frame.size

        # Load corresponding bounding boxes
        self.txt_path = os.path.join(self.output_folder, f"{os.path.splitext(frame_name)[0]}.txt")
        self.bboxes = []
        if os.path.exists(self.txt_path):
            self.bboxes = get_bounding_boxes(self.txt_path, self.img_w, self.img_h)

        # Load elements if they exist
        self.load_elements()

        # Display frame and bounding boxes
        self.display_frame()

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
                        self.frame_actions[cls_id] = {'color': row['color'], 'action': row['action']}
                    elif cls_id not in self.frame_actions:
                        # Load the latest action if not set in the current frame
                        self.frame_actions[cls_id] = {'color': row['color'], 'action': row['action']}
        
        for bbox in self.bboxes:
            cls_id = bbox['class_id']
            if cls_id in self.frame_actions:
                bbox['color'] = self.frame_actions[cls_id]['color']
                bbox['action'] = self.frame_actions[cls_id]['action']

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

    def draw_bboxes(self):
        for bbox in self.bboxes:
            x, y, w, h = bbox['coords']
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
        self.info_text.delete(1.0, tk.END)
        for idx, bbox in enumerate(self.bboxes):
            x, y, w, h = bbox['coords']
            cls_id = bbox['class_id']
            color = bbox.get('color', '')
            action = bbox.get('action', '')
            self.info_text.insert(tk.END, f"BBox {idx+1}: ID: {cls_id}, Coords: ({x}, {y}, {w}, {h}), Color: {color}, Action: {action}\n")

    def prev_frame(self):
        self.current_frame_index -= 1
        self.load_frame()

    def next_frame(self):
        self.current_frame_index += 1
        self.load_frame()

    def save(self):
        update_txt_file(self.txt_path, self.bboxes, self.img_w, self.img_h)
        self.save_elements()
        messagebox.showinfo("Save", "Bounding boxes and elements saved successfully.")

    def save_elements(self):
        """Save elements information to the single CSV file."""
        elements_data = []
        if os.path.exists(self.elements_file):
            with open(self.elements_file, mode='r', newline='') as file:
                reader = csv.DictReader(file)
                elements_data = [row for row in reader]
        
        # Add or update with current frame's data
        for bbox in self.bboxes:
            cls_id = bbox['class_id']
            color = bbox.get('color', '')
            action = bbox.get('action', '')
            frame_id = self.current_frame_index
            elements_data.append({'frame_id': frame_id, 'class_id': cls_id, 'color': color, 'action': action})
        
        # Write back to CSV
        with open(self.elements_file, mode='w', newline='') as file:
            writer = csv.DictWriter(file, fieldnames=['frame_id', 'class_id', 'color', 'action'])
            writer.writeheader()
            for data in elements_data:
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
                bx, by, bw, bh = bbox['coords']
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
                bx, by, bw, bh = self.resizing_bbox['coords']
                if self.resize_corner == 'top-left':
                    new_x = min(event.x, bx + bw - 1)
                    new_y = min(event.y, by + bh - 1)
                    new_w = (bx + bw) - new_x
                    new_h = (by + bh) - new_y
                    self.resizing_bbox['coords'] = (new_x, new_y, max(1, new_w), max(1, new_h))
                elif self.resize_corner == 'bottom-right':
                    new_w = max(1, event.x - bx)
                    new_h = max(1, event.y - by)
                    self.resizing_bbox['coords'] = (bx, by, new_w, new_h)
                elif self.resize_corner == 'top-right':
                    new_w = max(1, event.x - bx)
                    new_h = max(1, (by + bh) - event.y)
                    self.resizing_bbox['coords'] = (bx, event.y, new_w, new_h)
                elif self.resize_corner == 'bottom-left':
                    new_w = max(1, (bx + bw) - event.x)
                    new_h = max(1, event.y - by)
                    self.resizing_bbox['coords'] = (event.x, by, new_w, new_h)
                self.display_frame()  # Redraw everything

    def on_mouse_release(self, event):
        if self.drawing:
            self.drawing = False
            if self.current_rect:
                self.canvas.delete(self.current_rect)
            # Create a new bounding box
            x1, y1 = min(self.start_x, event.x), min(self.start_y, event.y)
            x2, y2 = max(self.start_x, event.x), max(self.start_y, event.y)
            new_bbox = {'coords': (x1, y1, x2 - x1, y2 - y1), 'class_id': 0, 'color': '', 'action': ''}  # Default class_id to 0
            self.bboxes.append(new_bbox)
            self.display_frame()  # Redraw everything
            self.open_edit_dialog(new_bbox)  # Prompt to set ID
        elif self.resizing:
            self.resizing = False
            self.resizing_bbox = None

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

        def update_values():
            # Update the bounding box ID, color, and action
            new_id = id_entry.get()
            color = color_entry.get()
            action = action_entry.get()
            if new_id.isdigit():
                bbox['class_id'] = int(new_id)
                bbox['color'] = color
                bbox['action'] = action
                self.display_frame()
                edit_window.destroy()

        def delete_bbox():
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
            bx, by, bw, bh = bbox['coords']
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
