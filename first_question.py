import tkinter as tk
from tkinter import filedialog, messagebox
from tkinter import ttk
from PIL import Image, ImageTk
import cv2
import numpy as np
import os

class ImageEditorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Image Editor")
        self.root.geometry("1200x700")
        self.image = None
        self.cropped_image = None
        self.display_image = None
        self.tk_image = None
        self.tk_cropped = None
        self.rect = None
        self.start_x = self.start_y = self.end_x = self.end_y = None
        self.crop_rect_id = None
        self.current_scale = 1.0
        self.history = []  # To keep track of states for undo
        self.max_history = 10  # Maximum undo steps to keep

        self.create_widgets()

    def create_widgets(self):
        # Button Frame
        self.button_frame = tk.Frame(self.root, bg="lightgray", height=100)
        self.button_frame.pack(fill=tk.X, padx=10, pady=5,ipady=10)

        # Buttons
        self.load_btn = tk.Button(self.button_frame, text="Load Image", command=self.load_image)
        self.load_btn.pack(side=tk.LEFT, padx=5)

        self.save_btn = tk.Button(self.button_frame, text="Save Image", command=self.save_cropped)
        self.save_btn.pack(side=tk.LEFT, padx=5)

        self.undo_btn = tk.Button(self.button_frame, text="Undo", command=self.undo_action)
        self.undo_btn.pack(side=tk.LEFT, padx=5)
        self.undo_btn.config(state=tk.DISABLED)

        # Main frames
        self.left_frame = tk.Frame(self.root, width=600, height=600, bg="gray")
        self.left_frame.pack(side=tk.LEFT, padx=10, pady=10)
        self.right_frame = tk.Frame(self.root, width=600, height=600, bg="lightgray")
        self.right_frame.pack(side=tk.RIGHT, padx=10, pady=10)

        # Canvas for original image
        self.canvas = tk.Canvas(self.left_frame, width=600, height=600, bg="black", cursor="cross")
        self.canvas.pack()
        self.canvas.bind("<ButtonPress-1>", self.on_mouse_down)
        self.canvas.bind("<B1-Motion>", self.on_mouse_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_mouse_up)

        # Label for cropped image
        self.cropped_label = tk.Label(self.right_frame, text="Cropped Image", bg="lightgray")
        self.cropped_label.pack()
        self.cropped_canvas = tk.Canvas(self.right_frame, width=400, height=400, bg="white")
        self.cropped_canvas.pack(pady=10)

        # Resize slider
        self.slider_label = tk.Label(self.right_frame, text="Resize Cropped Image", bg="lightgray")
        self.slider_label.pack()
        self.resize_slider = ttk.Scale(self.right_frame, from_=10, to=200, orient=tk.HORIZONTAL, command=self.resize_cropped)
        self.resize_slider.set(100)
        self.resize_slider.pack(fill=tk.X, padx=20, pady=10)

    def push_to_history(self):
        """Save current state to history for undo functionality"""
        if self.cropped_image is None:
            return
            
        # Convert image to bytes to save memory
        img_bytes = cv2.imencode('.png', cv2.cvtColor(self.cropped_image, cv2.COLOR_RGB2BGR))[1].tobytes()
        scale = self.current_scale
        
        self.history.append((img_bytes, scale))
        
        # Limit history size
        if len(self.history) > self.max_history:
            self.history.pop(0)
            
        # Enable undo button
        self.undo_btn.config(state=tk.NORMAL)

    def undo_action(self):
        """Revert to previous state"""
        if not self.history:
            return
            
        # Get previous state
        img_bytes, scale = self.history.pop()
        
        # Convert bytes back to image
        nparr = np.frombuffer(img_bytes, np.uint8)
        self.cropped_image = cv2.cvtColor(cv2.imdecode(nparr, cv2.IMREAD_COLOR), cv2.COLOR_BGR2RGB)
        self.current_scale = scale
        self.resize_slider.set(scale * 100)
        self.show_cropped_image(self.cropped_image)
        
        # Disable undo button if no more history
        if not self.history:
            self.undo_btn.config(state=tk.DISABLED)

    def load_image(self):
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
        h, w = img.shape[:2]
        scale = min(600/w, 600/h)
        new_w, new_h = int(w*scale), int(h*scale)
        resized = cv2.resize(img, (new_w, new_h))
        self.tk_image = ImageTk.PhotoImage(Image.fromarray(resized))
        self.canvas.delete("all")
        self.canvas.create_image(300, 300, image=self.tk_image, anchor=tk.CENTER)
        self.img_disp_size = (new_w, new_h)
        self.img_disp_offset = ((600-new_w)//2, (600-new_h)//2)

    def on_mouse_down(self, event):
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
        if self.image is None:
            return
        self.end_x = event.x
        self.end_y = event.y
        x0, y0 = self.canvas_to_image_coords(self.start_x, self.start_y)
        x1, y1 = self.canvas_to_image_coords(self.end_x, self.end_y)
        x0, x1 = sorted([max(0, x0), max(0, x1)])
        y0, y1 = sorted([max(0, y0), max(0, y1)])
        if x1-x0 < 5 or y1-y0 < 5:
            return
        
        # Save current state to history before making changes
        if self.cropped_image is not None:
            self.push_to_history()
            
        self.cropped_image = self.image[y0:y1, x0:x1]
        self.current_scale = 1.0
        self.show_cropped_image(self.cropped_image)
        self.resize_slider.set(100)

    def canvas_to_image_coords(self, x, y):
        offset_x, offset_y = self.img_disp_offset
        scale_x = self.image.shape[1] / self.img_disp_size[0]
        scale_y = self.image.shape[0] / self.img_disp_size[1]
        img_x = int((x - offset_x) * scale_x)
        img_y = int((y - offset_y) * scale_y)
        img_x = np.clip(img_x, 0, self.image.shape[1]-1)
        img_y = np.clip(img_y, 0, self.image.shape[0]-1)
        return img_x, img_y

    def show_cropped_image(self, img):
        if img is None or img.size == 0:
            self.cropped_canvas.delete("all")
            return
        h, w = img.shape[:2]
        scale = min(400/w, 400/h)
        new_w, new_h = int(w*scale), int(h*scale)
        resized = cv2.resize(img, (new_w, new_h))
        self.tk_cropped = ImageTk.PhotoImage(Image.fromarray(resized))
        self.cropped_canvas.delete("all")
        self.cropped_canvas.create_image(200, 200, image=self.tk_cropped, anchor=tk.CENTER)

    def resize_cropped(self, val):
        if self.cropped_image is None:
            return
        
        scale = float(val) / 100.0
        
        # Save current state to history before making changes
        if scale != self.current_scale and self.current_scale == 1.0:
            self.push_to_history()
            
        self.current_scale = scale
        
        # Resize the original cropped image
        h, w = self.cropped_image.shape[:2]
        new_w, new_h = max(1, int(w*scale)), max(1, int(h*scale))
        resized = cv2.resize(self.cropped_image, (new_w, new_h))
        
        # Then scale to fit the display canvas
        disp_scale = min(400/new_w, 400/new_h)
        disp_w, disp_h = int(new_w*disp_scale), int(new_h*disp_scale)
        display_img = cv2.resize(resized, (disp_w, disp_h))
        
        self.tk_cropped = ImageTk.PhotoImage(Image.fromarray(display_img))
        self.cropped_canvas.delete("all")
        self.cropped_canvas.create_image(200, 200, image=self.tk_cropped, anchor=tk.CENTER)

    def save_cropped(self):
        if self.cropped_image is None:
            messagebox.showerror("Error", "No cropped image to save.")
            return
        
        # Apply the current scale to the original cropped image
        h, w = self.cropped_image.shape[:2]
        new_w, new_h = max(1, int(w*self.current_scale)), max(1, int(h*self.current_scale))
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

if __name__ == "__main__":
    root = tk.Tk()
    app = ImageEditorApp(root)
    root.mainloop()