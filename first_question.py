import cv2
from PIL import Image, ImageTk
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

class ImageHandler:
    def __init__(self):
        self.original_image = None  # OpenCV BGR image
        self.cropped_image = None
        self.resized_image = None

    def load_image(self, path):
        img = cv2.imread(path)
        if img is None:
            raise ValueError("Failed to load image.")
        self.original_image = img
        self.cropped_image = None
        self.resized_image = None

    def crop_image(self, start, end):
        if self.original_image is None:
            return
        x1, y1 = start
        x2, y2 = end
        x1, x2 = sorted((max(0, x1), max(0, x2)))
        y1, y2 = sorted((max(0, y1), max(0, y2)))
        h, w = self.original_image.shape[:2]
        x2 = min(w, x2)
        y2 = min(h, y2)
        if x2 - x1 > 0 and y2 - y1 > 0:
            self.cropped_image = self.original_image[y1:y2, x1:x2]
            self.resized_image = self.cropped_image.copy()

    def resize_cropped(self, scale_percent):
        if self.cropped_image is None:
            return
        width = int(self.cropped_image.shape[1] * scale_percent / 100)
        height = int(self.cropped_image.shape[0] * scale_percent / 100)
        if width <= 0 or height <= 0:
            return
        self.resized_image = cv2.resize(self.cropped_image, (width, height), interpolation=cv2.INTER_AREA)

    def save_image(self, path):
        if self.resized_image is not None:
            cv2.imwrite(path, self.resized_image)
        elif self.cropped_image is not None:
            cv2.imwrite(path, self.cropped_image)
        elif self.original_image is not None:
            cv2.imwrite(path, self.original_image)
        else:
            raise ValueError("No image to save.")

class CanvasManager(tk.Canvas):
    def __init__(self, parent, width, height, image_handler, **kwargs):
        super().__init__(parent, width=width, height=height, bg='white', highlightthickness=1, highlightbackground='#ccc', **kwargs)
        self.image_handler = image_handler
        self.tk_image = None
        self.start_x = None
        self.start_y = None
        self.rect = None
        self.bind("<ButtonPress-1>", self.on_button_press)
        self.bind("<B1-Motion>", self.on_mouse_drag)
        self.bind("<ButtonRelease-1>", self.on_button_release)

    def display_image(self, cv_img):
        if cv_img is None:
            self.delete("all")
            return
        cv_img_rgb = cv2.cvtColor(cv_img, cv2.COLOR_BGR2RGB)
        pil_img = Image.fromarray(cv_img_rgb)
        canvas_w = self.winfo_width()
        canvas_h = self.winfo_height()
        img_w, img_h = pil_img.size
        scale = min(canvas_w/img_w, canvas_h/img_h, 1)
        if scale < 1:
            pil_img = pil_img.resize((int(img_w*scale), int(img_h*scale)), Image.ANTIALIAS)
        self.tk_image = ImageTk.PhotoImage(pil_img)
        self.delete("all")
        self.create_image(canvas_w//2, canvas_h//2, image=self.tk_image, anchor="center")

    def on_button_press(self, event):
        if self.image_handler.original_image is None:
            return
        self.start_x = event.x
        self.start_y = event.y
        if self.rect:
            self.delete(self.rect)
        self.rect = self.create_rectangle(self.start_x, self.start_y, self.start_x, self.start_y, outline='#FF4500', width=3)

    def on_mouse_drag(self, event):
        if self.rect:
            self.coords(self.rect, self.start_x, self.start_y, event.x, event.y)

    def on_button_release(self, event):
        if self.rect is None or self.image_handler.original_image is None:
            return
        x1, y1, x2, y2 = self.coords(self.rect)
        img = self.image_handler.original_image
        canvas_w = self.winfo_width()
        canvas_h = self.winfo_height()
        img_h, img_w = img.shape[:2]
        scale = min(canvas_w/img_w, canvas_h/img_h, 1)
        offset_x = (canvas_w - img_w*scale) / 2
        offset_y = (canvas_h - img_h*scale) / 2
        ix1 = int((x1 - offset_x) / scale)
        iy1 = int((y1 - offset_y) / scale)
        ix2 = int((x2 - offset_x) / scale)
        iy2 = int((y2 - offset_y) / scale)
        self.image_handler.crop_image((ix1, iy1), (ix2, iy2))
        self.master.update_cropped_image()

class ControlsPanel(ttk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, padding=15)
        self.app = app

        style = ttk.Style()
        style.configure('TButton', font=('Segoe UI', 12, 'bold'), foreground='black')
        style.configure('TLabel', font=('Segoe UI', 12), foreground='black')

        self.title_label = ttk.Label(self, text="Image Controls", font=('Segoe UI', 16, 'bold'))
        self.title_label.grid(row=0, column=0, columnspan=2, pady=(0, 15))

        self.load_button = ttk.Button(self, text="Load Image", command=self.app.load_image)
        self.load_button.grid(row=1, column=0, columnspan=2, sticky='ew', pady=5)

        self.save_button = ttk.Button(self, text="Save Image", command=self.app.save_image)
        self.save_button.grid(row=2, column=0, columnspan=2, sticky='ew', pady=5)

        self.resize_label = ttk.Label(self, text="Resize Cropped Image (%)")
        self.resize_label.grid(row=3, column=0, columnspan=2, pady=(20, 5))

        self.resize_slider = ttk.Scale(self, from_=10, to=200, orient='horizontal', command=self.on_resize)
        self.resize_slider.set(100)
        self.resize_slider.grid(row=4, column=0, columnspan=2, sticky='ew')

        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=1)

    def on_resize(self, val):
        scale_percent = int(float(val))
        self.app.resize_cropped_image(scale_percent)

class MainApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Image Crop & Resize App")
        self.geometry("1000x600")
        self.resizable(False, False)
        self.configure(bg='#f0f0f0')

        self.image_handler = ImageHandler()

        self.columnconfigure(0, weight=0)
        self.columnconfigure(1, weight=1)
        self.columnconfigure(2, weight=1)
        self.rowconfigure(0, weight=1)

        self.controls_panel = ControlsPanel(self, self)
        self.controls_panel.grid(row=0, column=0, sticky='ns', padx=15, pady=15)

        self.original_frame = ttk.LabelFrame(self, text="Original Image")
        self.original_frame.grid(row=0, column=1, sticky='nsew', padx=10, pady=15)
        self.original_frame.rowconfigure(0, weight=1)
        self.original_frame.columnconfigure(0, weight=1)

        self.original_canvas = CanvasManager(self.original_frame, 450, 550, self.image_handler)
        self.original_canvas.grid(row=0, column=0, sticky='nsew')

        self.cropped_frame = ttk.LabelFrame(self, text="Cropped / Resized Image")
        self.cropped_frame.grid(row=0, column=2, sticky='nsew', padx=10, pady=15)
        self.cropped_frame.rowconfigure(0, weight=1)
        self.cropped_frame.columnconfigure(0, weight=1)

        self.cropped_canvas = tk.Canvas(self.cropped_frame, width=450, height=550, bg='white', highlightthickness=1, highlightbackground='#ccc')
        self.cropped_canvas.grid(row=0, column=0, sticky='nsew')
        self.cropped_tk_image = None

    def load_image(self):
        file_path = filedialog.askopenfilename(
            title="Select Image",
            filetypes=[("Image files", "*.jpg *.jpeg *.png *.bmp *.tiff")]
        )
        if not file_path:
            return
        try:
            self.image_handler.load_image(file_path)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load image:\n{e}")
            return
        self.controls_panel.resize_slider.set(100)
        self.original_canvas.display_image(self.image_handler.original_image)
        self.clear_cropped_display()

    def clear_cropped_display(self):
        self.cropped_canvas.delete("all")
        self.cropped_tk_image = None

    def update_cropped_image(self):
        img = self.image_handler.resized_image if self.image_handler.resized_image is not None else self.image_handler.cropped_image
        if img is None:
            self.clear_cropped_display()
            return
        cv_img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        pil_img = Image.fromarray(cv_img_rgb)
        canvas_w = self.cropped_canvas.winfo_width()
        canvas_h = self.cropped_canvas.winfo_height()
        img_w, img_h = pil_img.size
        scale = min(canvas_w/img_w, canvas_h/img_h, 1)
        if scale < 1:
            pil_img = pil_img.resize((int(img_w*scale), int(img_h*scale)), Image.ANTIALIAS)
        self.cropped_tk_image = ImageTk.PhotoImage(pil_img)
        self.cropped_canvas.delete("all")
        self.cropped_canvas.create_image(canvas_w//2, canvas_h//2, image=self.cropped_tk_image, anchor="center")

    def resize_cropped_image(self, scale_percent):
        if self.image_handler.cropped_image is None:
            return
        self.image_handler.resize_cropped(scale_percent)
        self.update_cropped_image()

    def save_image(self):
        if self.image_handler.resized_image is None and self.image_handler.cropped_image is None and self.image_handler.original_image is None:
            messagebox.showwarning("Warning", "No image to save.")
            return
        file_path = filedialog.asksaveasfilename(
            defaultextension=".png",
            filetypes=[("PNG files", "*.png"), ("JPEG files", "*.jpg"), ("BMP files", "*.bmp"), ("TIFF files", "*.tiff")],
            title="Save Image As"
        )
        if not file_path:
            return
        try:
            self.image_handler.save_image(file_path)
            messagebox.showinfo("Saved", f"Image saved to:\n{file_path}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save image:\n{e}")

if __name__ == "__main__":
    app = MainApp()
    app.mainloop()
