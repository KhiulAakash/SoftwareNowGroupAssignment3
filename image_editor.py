import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk
import cv2
import numpy as np

class ImageEditorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Image Editor")
        self.root.geometry("1200x800")

        # Image data
        self.original_image = None
        self.cropped_image = None
        self.display_image = None
        self.scale_factor = 1.0

        # Cropping variables
        self.start_x = None
        self.start_y = None
        self.rect = None
        self.cropping = False

        # Undo stack
        self.undo_stack = []

        # Setup GUI
        self.setup_gui()
        self.setup_keybindings()

    def setup_gui(self):
        # Frames
        self.control_frame = tk.Frame(self.root)
        self.control_frame.pack(side=tk.TOP, fill=tk.X, padx=10, pady=5)

        self.image_frame = tk.Frame(self.root)
        self.image_frame.pack(expand=True, fill=tk.BOTH)

        # Buttons
        tk.Button(self.control_frame, text="Load Image", command=self.load_image).pack(side=tk.LEFT, padx=5)
        tk.Button(self.control_frame, text="Save Image", command=self.save_image).pack(side=tk.LEFT, padx=5)
        tk.Button(self.control_frame, text="Grayscale", command=self.apply_grayscale).pack(side=tk.LEFT, padx=5)
        tk.Button(self.control_frame, text="Undo", command=self.undo).pack(side=tk.LEFT, padx=5)

        # Resize slider
        self.size_label = tk.Label(self.control_frame, text="Resize: 100%")
        self.size_label.pack(side=tk.LEFT, padx=5)
        self.size_slider = tk.Scale(self.control_frame, from_=10, to=200, orient=tk.HORIZONTAL,
                                  command=self.resize_image, length=200)
        self.size_slider.set(100)
        self.size_slider.pack(side=tk.LEFT, padx=5)

        # Canvas for images
        self.canvas = tk.Canvas(self.image_frame, bg="gray")
        self.canvas.pack(expand=True, fill=tk.BOTH)

        # Bind mouse events for cropping
        self.canvas.bind("<ButtonPress-1>", self.start_crop)
        self.canvas.bind("<B1-Motion>", self.update_crop)
        self.canvas.bind("<ButtonRelease-1>", self.end_crop)

    def setup_keybindings(self):
        self.root.bind("<Control-o>", lambda e: self.load_image())
        self.root.bind("<Control-s>", lambda e: self.save_image())
        self.root.bind("<Control-z>", lambda e: self.undo())

    def load_image(self):
        file_path = filedialog.askopenfilename(filetypes=[("Image files", "*.png *.jpg *.jpeg *.bmp")])
        if file_path:
            self.original_image = cv2.imread(file_path)
            self.cropped_image = self.original_image.copy()
            self.undo_stack = []
            self.update_display()

    def update_display(self):
        if self.original_image is None:
            return

        # Resize for display (fit to canvas)
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()
        if canvas_width <= 1 or canvas_height <= 1:  # Canvas not yet realized
            canvas_width, canvas_height = 800, 600

        # Calculate display size
        img_height, img_width = self.cropped_image.shape[:2]
        ratio = min(canvas_width/img_width, canvas_height/img_height, 1)
        display_size = (int(img_width * ratio * self.scale_factor), 
                       int(img_height * ratio * self.scale_factor))

        # Convert to display format
        display_img = cv2.resize(self.cropped_image, display_size)
        display_img = cv2.cvtColor(display_img, cv2.COLOR_BGR2RGB)
        self.display_image = ImageTk.PhotoImage(Image.fromarray(display_img))

        # Update canvas
        self.canvas.delete("all")
        canvas_width = max(canvas_width, display_size[0])
        canvas_height = max(canvas_height, display_size[1])
        self.canvas.config(width=canvas_width, height=canvas_height)
        self.canvas.create_image(canvas_width//2, canvas_height//2, image=self.display_image, anchor="center")

    def start_crop(self, event):
        self.cropping = True
        self.start_x = self.canvas.canvasx(event.x)
        self.start_y = self.canvas.canvasy(event.y)
        if self.rect:
            self.canvas.delete(self.rect)
        self.rect = self.canvas.create_rectangle(self.start_x, self.start_y, 
                                              self.start_x, self.start_y, outline="red", width=2)

    def update_crop(self, event):
        if self.cropping:
            self.canvas.coords(self.rect, self.start_x, self.start_y,
                             self.canvas.canvasx(event.x), self.canvas.canvasy(event.y))

    def end_crop(self, event):
        if self.cropping:
            self.cropping = False
            end_x = self.canvas.canvasx(event.x)
            end_y = self.canvas.canvasy(event.y)

            # Convert canvas coordinates to image coordinates
            canvas_width = self.canvas.winfo_width()
            canvas_height = self.canvas.winfo_height()
            img_height, img_width = self.cropped_image.shape[:2]
            ratio = min(canvas_width/img_width, canvas_height/img_height, 1)

            x1 = int(self.start_x / (ratio * self.scale_factor))
            y1 = int(self.start_y / (ratio * self.scale_factor))
            x2 = int(end_x / (ratio * self.scale_factor))
            y2 = int(end_y / (ratio * self.scale_factor))

            # Ensure coordinates are within image bounds
            x1, x2 = sorted([max(0, min(x1, x2)), min(img_width-1, max(x1, x2))])
            y1, y2 = sorted([max(0, min(y1, y2)), min(img_height-1, max(y1, y2))])

            # Save state for undo
            self.undo_stack.append(self.cropped_image.copy())

            # Crop image
            self.cropped_image = self.cropped_image[y1:y2, x1:x2]
            self.update_display()
            self.canvas.delete(self.rect)

    def resize_image(self, value):
        self.scale_factor = int(value) / 100
        self.size_label.config(text=f"Resize: {int(value)}%")
        self.update_display()

    def apply_grayscale(self):
        if self.cropped_image is not None:
            self.undo_stack.append(self.cropped_image.copy())
            self.cropped_image = cv2.cvtColor(self.cropped_image, cv2.COLOR_BGR2GRAY)
            if len(self.cropped_image.shape) == 2:  # Convert back to 3 channels for consistency
                self.cropped_image = cv2.cvtColor(self.cropped_image, cv2.COLOR_GRAY2BGR)
            self.update_display()

    def save_image(self):
        if self.cropped_image is not None:
            file_path = filedialog.asksaveasfilename(defaultextension=".png",
                                                   filetypes=[("PNG files", "*.png"), 
                                                             ("JPEG files", "*.jpg"),
                                                             ("All files", "*.*")])
            if file_path:
                cv2.imwrite(file_path, self.cropped_image)
                messagebox.showinfo("Success", "Image saved successfully!")

    def undo(self):
        if self.undo_stack:
            self.cropped_image = self.undo_stack.pop()
            self.update_display()

    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    root = tk.Tk()
    app = ImageEditorApp(root)
    app.run()