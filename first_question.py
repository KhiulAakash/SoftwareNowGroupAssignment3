# Importing necessary libraries
import tkinter as tk
from tkinter import filedialog, messagebox  # For file dialogs and message popups
from tkinter import ttk  # For styled widgets like sliders
from PIL import Image, ImageTk  # For handling images with Python Imaging Library
import cv2  # OpenCV for image processing
import numpy as np
import os

# Main Image Editor class
class ImageEditorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Image Editor")
        self.root.geometry("1200x700")

        # Initializing variables to store image data and GUI elements
        self.image = None  # Original loaded image
        self.cropped_image = None  # Cropped image after user selection
        self.display_image = None  # Image for canvas display
        self.tk_image = None  # Image in tkinter format
        self.tk_cropped = None  # Cropped image in tkinter format
        self.rect = None  # Crop rectangle on canvas
        self.start_x = self.start_y = self.end_x = self.end_y = None
        self.crop_rect_id = None
        self.current_scale = 1.0  # Track the current resize scale

        # History stack for undo functionality
        self.history = []
        self.max_history = 10  # Max undo steps

        # Create GUI components
        self.create_widgets()

    def create_widgets(self):
        # Frame for buttons at the top
        self.button_frame = tk.Frame(self.root, bg="lightgray", height=100)
        self.button_frame.pack(fill=tk.X, padx=10, pady=5, ipady=10)

        # Button to load an image
        self.load_btn = tk.Button(self.button_frame, text="Load Image", command=self.load_image)
        self.load_btn.pack(side=tk.LEFT, padx=5)

        # Button to save the cropped image
        self.save_btn = tk.Button(self.button_frame, text="Save Image", command=self.save_cropped)
        self.save_btn.pack(side=tk.LEFT, padx=5)

        # Undo button (disabled initially)
        self.undo_btn = tk.Button(self.button_frame, text="Undo", command=self.undo_action)
        self.undo_btn.pack(side=tk.LEFT, padx=5)
        self.undo_btn.config(state=tk.DISABLED)

        # Frames to organize layout
        self.left_frame = tk.Frame(self.root, width=600, height=600, bg="gray")
        self.left_frame.pack(side=tk.LEFT, padx=10, pady=10)
        self.right_frame = tk.Frame(self.root, width=600, height=600, bg="lightgray")
        self.right_frame.pack(side=tk.RIGHT, padx=10, pady=10)

        # Canvas to show the original image
        self.canvas = tk.Canvas(self.left_frame, width=600, height=600, bg="black", cursor="cross")
        self.canvas.pack()
        self.canvas.bind("<ButtonPress-1>", self.on_mouse_down)  # Start crop
        self.canvas.bind("<B1-Motion>", self.on_mouse_drag)  # Drawing crop rectangle
        self.canvas.bind("<ButtonRelease-1>", self.on_mouse_up)  # Finalize crop

        # Label and canvas for showing the cropped image
        self.cropped_label = tk.Label(self.right_frame, text="Cropped Image", bg="lightgray")
        self.cropped_label.pack()
        self.cropped_canvas = tk.Canvas(self.right_frame, width=400, height=400, bg="white")
        self.cropped_canvas.pack(pady=10)

        # Slider to resize the cropped image
        self.slider_label = tk.Label(self.right_frame, text="Resize Cropped Image", bg="lightgray")
        self.slider_label.pack()
        self.resize_slider = ttk.Scale(self.right_frame, from_=10, to=200, orient=tk.HORIZONTAL, command=self.resize_cropped)
        self.resize_slider.set(100)  # Default 100% scale
        self.resize_slider.pack(fill=tk.X, padx=20, pady=10)

    def push_to_history(self):
        """Save the current cropped image state to history for undo"""
        if self.cropped_image is None:
            return
        img_bytes = cv2.imencode('.png', cv2.cvtColor(self.cropped_image, cv2.COLOR_RGB2BGR))[1].tobytes()
        scale = self.current_scale
        self.history.append((img_bytes, scale))
        if len(self.history) > self.max_history:
            self.history.pop(0)
        self.undo_btn.config(state=tk.NORMAL)  # Enable undo

    def undo_action(self):
        """Undo the last cropping or resizing action"""
        if not self.history:
            return
        img_bytes, scale = self.history.pop()
        nparr = np.frombuffer(img_bytes, np.uint8)
        self.cropped_image = cv2.cvtColor(cv2.imdecode(nparr, cv2.IMREAD_COLOR), cv2.COLOR_BGR2RGB)
        self.current_scale = scale
        self.resize_slider.set(scale * 100)
        self.show_cropped_image(self.cropped_image)
        if not self.history:
            self.undo_btn.config(state=tk.DISABLED)

    def load_image(self):
        """Open a file dialog to select and load an image"""
        file_path = filedialog.askopenfilename(filetypes=[("Image Files", "*.png;*.jpg;*.jpeg;*.bmp;*.gif")])
        if not file_path:
            return
        self.image = cv2.cvtColor(cv2.imread(file_path), cv2.COLOR_BGR2RGB)
        self.display_image = self.image.copy()
        self.show_image_on_canvas(self.image)
        self.cropped_image = None
        self.tk_cropped = None
        self.cropped_canvas.delete("all")
        self.resize_slider.set(100)
        self.current_scale = 1.0
        self.history = []
        self.undo_btn.config(state=tk.DISABLED)

    def show_image_on_canvas(self, img):
        """Display an image on the left canvas"""
        h, w = img.shape[:2]
        scale = min(600 / w, 600 / h)
        new_w, new_h = int(w * scale), int(h * scale)
        resized = cv2.resize(img, (new_w, new_h))
        self.tk_image = ImageTk.PhotoImage(Image.fromarray(resized))
        self.canvas.delete("all")
        self.canvas.create_image(300, 300, image=self.tk_image, anchor=tk.CENTER)
        self.img_disp_size = (new_w, new_h)
        self.img_disp_offset = ((600 - new_w) // 2, (600 - new_h) // 2)

    def on_mouse_down(self, event):
        """Start drawing the crop rectangle"""
        if self.image is None:
            return
        self.start_x = event.x
        self.start_y = event.y
        self.end_x = event.x
        self.end_y = event.y
        if self.crop_rect_id:
            self.canvas.delete(self.crop_rect_id)
            self.crop_rect_id = None

    def on_mouse_drag(self, event):
        """Draw the crop rectangle as the mouse moves"""
        if self.image is None:
            return
        self.end_x = event.x
        self.end_y = event.y
        if self.crop_rect_id:
            self.canvas.delete(self.crop_rect_id)
        self.crop_rect_id = self.canvas.create_rectangle(
            self.start_x, self.start_y, self.end_x, self.end_y,
            outline="red", width=2
        )

    def on_mouse_up(self, event):
        """Complete the crop and extract the selected image area"""
        if self.image is None:
            return
        self.end_x = event.x
        self.end_y = event.y
        x0, y0 = self.canvas_to_image_coords(self.start_x, self.start_y)
        x1, y1 = self.canvas_to_image_coords(self.end_x, self.end_y)
        x0, x1 = sorted([max(0, x0), max(0, x1)])
        y0, y1 = sorted([max(0, y0), max(0, y1)])
        if x1 - x0 < 5 or y1 - y0 < 5:
            return
        if self.cropped_image is not None:
            self.push_to_history()
        self.cropped_image = self.image[y0:y1, x0:x1]
        self.current_scale = 1.0
        self.show_cropped_image(self.cropped_image)
        self.resize_slider.set(100)

    def canvas_to_image_coords(self, x, y):
        """Convert canvas coordinates to image coordinates"""
        offset_x, offset_y = self.img_disp_offset
        scale_x = self.image.shape[1] / self.img_disp_size[0]
        scale_y = self.image.shape[0] / self.img_disp_size[1]
        img_x = int((x - offset_x) * scale_x)
        img_y = int((y - offset_y) * scale_y)
        img_x = np.clip(img_x, 0, self.image.shape[1] - 1)
        img_y = np.clip(img_y, 0, self.image.shape[0] - 1)
        return img_x, img_y

    def show_cropped_image(self, img):
        """Display the cropped image in the right canvas"""
        if img is None or img.size == 0:
            self.cropped_canvas.delete("all")
            return
        h, w = img.shape[:2]
        scale = min(400 / w, 400 / h)
        new_w, new_h = int(w * scale), int(h * scale)
        resized = cv2.resize(img, (new_w, new_h))
        self.tk_cropped = ImageTk.PhotoImage(Image.fromarray(resized))
        self.cropped_canvas.delete("all")
        self.cropped_canvas.create_image(200, 200, image=self.tk_cropped, anchor=tk.CENTER)

    def resize_cropped(self, val):
        """Resize the cropped image based on the slider value"""
        if self.cropped_image is None:
            return
        scale = float(val) / 100.0
        if scale != self.current_scale and self.current_scale == 1.0:
            self.push_to_history()
        self.current_scale = scale
        h, w = self.cropped_image.shape[:2]
        new_w, new_h = max(1, int(w * scale)), max(1, int(h * scale))
        resized = cv2.resize(self.cropped_image, (new_w, new_h))
        disp_scale = min(400 / new_w, 400 / new_h)
        disp_w, disp_h = int(new_w * disp_scale), int(new_h * disp_scale)
        display_img = cv2.resize(resized, (disp_w, disp_h))
        self.tk_cropped = ImageTk.PhotoImage(Image.fromarray(display_img))
        self.cropped_canvas.delete("all")
        self.cropped_canvas.create_image(200, 200, image=self.tk_cropped, anchor=tk.CENTER)

    def save_cropped(self):
        """Save the cropped image to a file"""
        if self.cropped_image is None:
            messagebox.showerror("Error", "No cropped image to save.")
            return
        h, w = self.cropped_image.shape[:2]
        new_w, new_h = max(1, int(w * self.current_scale)), max(1, int(h * self.current_scale))
        img_to_save = cv2.resize(self.cropped_image, (new_w, new_h))
        file_path = filedialog.asksaveasfilename(
            defaultextension=".png",
            filetypes=[("PNG Image", "*.png"), ("JPEG Image", "*.jpg;*.jpeg")]
        )
        if not file_path:
            return
        img_to_save = cv2.cvtColor(img_to_save, cv2.COLOR_RGB2BGR)
        cv2.imwrite(file_path, img_to_save)
        messagebox.showinfo("Saved", f"Image saved to {file_path}")

# Start the application
if __name__ == "__main__":
    root = tk.Tk()
    app = ImageEditorApp(root)
    root.mainloop()
