"""
Program: EZ Image Editor
Description: A program developed for Assignment 3 of HIT137 to load, crop, resize image and save. 
The program also has additional bonus features: rotate, flip (vertical and horizontal), undo/redo and keyboard shortcuts to enhance functionality.

Authors: Darren Swann, Brayden Brown and Rijan Koirala
Last Updated: 01/02/2025

Features:
1. Load an image: Allows the user to load an image from their local system and it will automatically resize it to fit within the canvas.
2. Crop an image: Allows the user to select an area on the left-hand window and crop that part of the image, which is displayed in the right-hand window.
3. Resize the cropped image: Provides a slider to resize the cropped image from 50% to 200% of its current size.
4. Rotate the cropped image: Rotates the cropped image by 90 degrees clockwise.
5. Flip the cropped image: Flip horizontally (mirrors the image along its vertical axis) or Flip vertically (mirrors the image along its horizontal axis).
6. Save the cropped image: Allows the user to save the cropped and edited image to their system.
7. Undo/Redo: Undo reverts the cropped image to its previous state. Redo restores an undone change to the cropped image.
8. Keyboard Shortcuts:
    - Ctrl + L: Load an image.
    - Ctrl + S: Save the cropped image.
    - Ctrl + R: Rotate the cropped image.
    - Ctrl + H: Flip the cropped image horizontally.
    - Ctrl + V: Flip the cropped image vertically.
    - Ctrl + Z: Undo the last action.
    - Ctrl + Y: Redo the last undone action.
"""

# Importing Modules / Libraries
import tkinter as tk
from tkinter import filedialog, messagebox
import cv2
from PIL import Image, ImageTk


class EZImageEditor:
    def __init__(self, root):
        """
        Initialise the EZ Image Editor with GUI components.
        """
        # Create the main window
        self.root = root
        self.root.title("EZ Image Editor")

        # Initialise variables to store the original and cropped images
        self.image = None
        self.original_image = None
        self.cropped_image = None
        self.resized_cropped_image = None  # To store resized cropped image

        # Variables to store the start position of the cropping rectangle
        self.start_x = None
        self.start_y = None

        # Variable to store the ID of the cropping rectangle
        self.rect_id = None
        
        # Lists to store the history of actions for undo/redo functionality
        self.history = []
        self.redo_stack = []

        # Create a frame to hold the canvases
        self.image_frame = tk.Frame(root)
        self.image_frame.pack()

        # Create a canvas to display the original image
        self.original_canvas = tk.Canvas(self.image_frame, width=500, height=450, bg="lightgray")
        self.original_canvas.pack(side="left", padx=5)

        # Create a canvas to display the cropped image
        self.cropped_canvas = tk.Canvas(self.image_frame, width=500, height=450, bg="lightgray")
        self.cropped_canvas.pack(side="left", padx=5)

        # Add a red instruction label above all buttons
        self.instruction_label = tk.Label(
            root, 
            text="\nStep 1. Load Image      Step 2. Crop Image      Step 3. Resize Cropped Image      Step 4. Modify Cropped Image      Step 5. Save Image", 
            fg="red", 
            font=("Helvetica", 10, "bold")
        )
        self.instruction_label.pack(pady=5)

        # Label for resizing warning
        self.resize_warning_label = tk.Label(
            root,
            text="Note: Resizing your cropped image after modifications will reset them. This is to maintain image quality.",
            fg="black",
            font=("Helvetica", 8, "italic")
        )
        self.resize_warning_label.pack(pady=(0, 10))  # Slightly below the red label

        # Create a frame to hold the buttons
        self.bottom_frame = tk.Frame(root)
        self.bottom_frame.pack(pady=10)

        # Create buttons for loading, saving, rotating, flipping, and resizing the image
        self.load_button = tk.Button(self.bottom_frame, text="Load", command=self.load_image)
        self.load_button.grid(row=0, column=0, padx=10)

        # Slider for resizing the cropped image
        self.resize_label = tk.Label(self.bottom_frame, text="Resize Cropped:")
        self.resize_label.grid(row=0, column=1, padx=10)

        self.resize_slider = tk.Scale(
            self.bottom_frame, from_=50, to=200, orient="horizontal", command=self.resize_cropped_image, state="disabled"
        )
        self.resize_slider.grid(row=0, column=2, padx=10)

        self.rotate_button = tk.Button(self.bottom_frame, text="Rotate", command=self.rotate_90, state="disabled")
        self.rotate_button.grid(row=0, column=3, padx=10)

        self.flip_h_button = tk.Button(self.bottom_frame, text="Flip Horizontal", command=self.flip_horizontal, state="disabled")
        self.flip_h_button.grid(row=0, column=4, padx=10)

        self.flip_v_button = tk.Button(self.bottom_frame, text="Flip Vertical", command=self.flip_vertical, state="disabled")
        self.flip_v_button.grid(row=0, column=5, padx=10)

        self.save_button = tk.Button(self.bottom_frame, text="Save", command=self.save_image, state="disabled")
        self.save_button.grid(row=0, column=6, padx=10)

        # Create a frame to hold the shortcut instructions
        self.shortcut_frame = tk.Frame(root)
        self.shortcut_frame.pack(pady=5)

        # Create a label to display the shortcut instructions
        self.shortcut_label = tk.Label(
            self.shortcut_frame,
            text="\nShortcuts: Ctrl+L (Load), Ctrl+S (Save), Ctrl+R (Rotate), Ctrl+H (Flip Horizontal), Ctrl+V (Flip Vertical), Ctrl+Z (Undo), Ctrl+Y (Redo)\n",
            fg="blue",
        )
        self.shortcut_label.pack()

        # Bind mouse events to the original canvas
        self.original_canvas.bind("<ButtonPress-1>", self.start_crop)
        self.original_canvas.bind("<B1-Motion>", self.draw_crop_rectangle)
        self.original_canvas.bind("<ButtonRelease-1>", self.perform_crop)

        # Bind keyboard shortcuts
        root.bind("<Control-z>", lambda event: self.undo())
        root.bind("<Control-y>", lambda event: self.redo())
        root.bind("<Control-l>", lambda event: self.load_image())
        root.bind("<Control-s>", lambda event: self.save_image())
        root.bind("<Control-r>", lambda event: self.rotate_90())
        root.bind("<Control-h>", lambda event: self.flip_horizontal())
        root.bind("<Control-v>", lambda event: self.flip_vertical())

    def load_image(self):
        """
        Load an image from the user's system and display it resized to fit the canvas.
        """
        # Open a file dialog to select an image file
        file_path = filedialog.askopenfilename(filetypes=[("Image files", "*.jpg;*.jpeg;*.png")])

        # Check if a file was selected
        if file_path:
            # Read the selected image using OpenCV
            self.original_image = cv2.imread(file_path)

            # Resize the image to fit the canvas
            self.image = self.resize_to_fit_canvas(self.original_image, self.original_canvas)

            # Display the resized image on the original canvas
            self.display_image(self.image, self.original_canvas)

            # Reset cropped image and buttons
            self.cropped_image = None
            self.resized_cropped_image = None
            self.save_button["state"] = "disabled"
            self.rotate_button["state"] = "disabled"
            self.flip_h_button["state"] = "disabled"
            self.flip_v_button["state"] = "disabled"
            self.resize_slider["state"] = "disabled"
            self.history.clear()
            self.redo_stack.clear()

    def resize_to_fit_canvas(self, image, canvas):
        """
        Resize an image to fit within a canvas while maintaining aspect ratio.
        """
        # Get the width and height of the canvas
        canvas_width, canvas_height = canvas.winfo_width(), canvas.winfo_height()

        # Get the height and width of the image
        image_height, image_width = image.shape[:2]

        # Calculate the scaling factor
        scale = min(canvas_width / image_width, canvas_height / image_height)

        # Calculate the new width and height of the image
        new_width = int(image_width * scale)
        new_height = int(image_height * scale)

        # Resize the image using OpenCV
        return cv2.resize(image, (new_width, new_height))

    def display_image(self, image, canvas):
        """
        Display an OpenCV image on a Tkinter canvas.
        """
        # Convert the image from BGR to RGB
        image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

        # Convert the image to a PIL image
        image_pil = Image.fromarray(image_rgb)

        # Convert the PIL image to a Tkinter image
        image_tk = ImageTk.PhotoImage(image_pil)

        # Display the image on the canvas
        canvas.create_image(0, 0, anchor="nw", image=image_tk)

        # Keep a reference to the image to prevent it from being garbage collected
        canvas.image_tk = image_tk

    def start_crop(self, event):
        """
        Start the cropping process by recording the initial mouse click position.
        """
        # Record the x and y coordinates of the mouse click
        self.start_x, self.start_y = event.x, event.y

    def draw_crop_rectangle(self, event):
        """
        Draw a rectangle to visualise the cropping area.
        """
        # Check if a rectangle is already drawn
        if self.rect_id:
            # Delete the existing rectangle
            self.original_canvas.delete(self.rect_id)

        # Draw a new rectangle
        self.rect_id = self.original_canvas.create_rectangle(
            self.start_x, self.start_y, event.x, event.y, outline="red"
        )

    def perform_crop(self, event):
        """
        Crop the selected area and display it in the cropped canvas.
        """
        # Check if an image is loaded
        if self.image is not None:
            # Get the ending coordinates of the cropping rectangle
            end_x, end_y = event.x, event.y

            # Calculate the top-left and bottom-right coordinates of the cropping rectangle
            x1, y1 = min(self.start_x, end_x), min(self.start_y, end_y)
            x2, y2 = max(self.start_x, end_x), max(self.start_y, end_y)

            # Get the actual dimensions of the displayed (resized) image
            canvas_width, canvas_height = self.original_canvas.winfo_width(), self.original_canvas.winfo_height()

            # Calculate the scaling factor used to fit the image to the canvas
            scale_x = self.original_image.shape[1] / self.image.shape[1]
            scale_y = self.original_image.shape[0] / self.image.shape[0]

            # Map canvas coordinates back to original image coordinates
            x1, x2 = int(x1 * scale_x), int(x2 * scale_x)
            y1, y2 = int(y1 * scale_y), int(y2 * scale_y)

            # Crop the original image using the mapped coordinates
            self.cropped_image = self.original_image[y1:y2, x1:x2]
            self.resized_cropped_image = self.cropped_image.copy()

            # Add the cropped image to history for undo/redo functionality
            self.add_to_history(self.resized_cropped_image)

            # Display the cropped image in the cropped canvas
            self.display_image(self.resized_cropped_image, self.cropped_canvas)

            # Enable buttons for editing cropped image
            self.save_button["state"] = "normal"
            self.rotate_button["state"] = "normal"
            self.flip_h_button["state"] = "normal"
            self.flip_v_button["state"] = "normal"
            self.resize_slider["state"] = "normal"
            self.resize_slider.set(100) # Reset the slider to 100%

    def resize_cropped_image(self, scale):
        """
        Resize the cropped image based on the slider value.
        """
        # Check if a cropped image is available
        if self.cropped_image is not None:
            # Convert the scale to a float
            scale = int(scale) / 100.0

            # Calculate the new width and height of the cropped image
            width = int(self.cropped_image.shape[1] * scale)
            height = int(self.cropped_image.shape[0] * scale)

            # Resize the cropped image using OpenCV
            self.resized_cropped_image = cv2.resize(self.cropped_image, (width, height))

            # Display the resized image in the cropped canvas
            self.display_image(self.resized_cropped_image, self.cropped_canvas)

    def save_image(self):
        """
        Save the cropped image to a file.
        """
        # Check if a cropped image is available
        if self.resized_cropped_image is not None:
            # Open a file dialog to select a save location
            file_path = filedialog.asksaveasfilename(defaultextension=".png", filetypes=[("PNG files", "*.png")])

            # Check if a file was selected
            if file_path:
                # Save the cropped image using OpenCV
                cv2.imwrite(file_path, self.resized_cropped_image)

                # Show a message box to confirm the save
                messagebox.showinfo("Save Image", "Cropped and resized image saved successfully!")

    def rotate_90(self):
        """
        Rotate the cropped image by 90 degrees.
        """
        # Check if a cropped image is available
        if self.resized_cropped_image is not None:
            # Add the current state of the cropped image to the history stack
            self.add_to_history(self.resized_cropped_image)

            # Rotate the cropped image using OpenCV
            self.resized_cropped_image = cv2.rotate(self.resized_cropped_image, cv2.ROTATE_90_CLOCKWISE)

            # Display the rotated image in the cropped canvas
            self.display_image(self.resized_cropped_image, self.cropped_canvas)

    def flip_horizontal(self):
        """
        Flip the cropped image horizontally.
        """
        # Check if a cropped image is available
        if self.resized_cropped_image is not None:
            # Add the current state of the cropped image to the history stack
            self.add_to_history(self.resized_cropped_image)

            # Flip the cropped image horizontally using OpenCV
            self.resized_cropped_image = cv2.flip(self.resized_cropped_image, 1)

            # Display the flipped image in the cropped canvas
            self.display_image(self.resized_cropped_image, self.cropped_canvas)

    def flip_vertical(self):
        """
        Flip the cropped image vertically.
        """
        # Check if a cropped image is available
        if self.resized_cropped_image is not None:
            # Add the current state of the cropped image to the history stack
            self.add_to_history(self.resized_cropped_image)

            # Flip the cropped image vertically using OpenCV
            self.resized_cropped_image = cv2.flip(self.resized_cropped_image, 0)

            # Display the flipped image in the cropped canvas
            self.display_image(self.resized_cropped_image, self.cropped_canvas)

    def add_to_history(self, image):
        """
        Add the current state of the cropped image to the history stack for undo/redo functionality.
        """
        # Add the current state of the cropped image to the history stack
        self.history.append(image.copy())

        # Clear the redo stack whenever a new action is performed
        self.redo_stack.clear()

    def undo(self):
        """
        Undo the last action performed on the cropped image.
        """
        # Check if there are actions to undo
        if self.history:
            # Add the current state of the cropped image to the redo stack
            self.redo_stack.append(self.resized_cropped_image.copy())

            # Revert the cropped image to its previous state
            self.resized_cropped_image = self.history.pop()

            # Display the reverted image in the cropped canvas
            self.display_image(self.resized_cropped_image, self.cropped_canvas)

    def redo(self):
        """
        Redo the last undone action on the cropped image.
        """
        # Check if there are actions to redo
        if self.redo_stack:
            # Add the current state of the cropped image to the history stack
            self.history.append(self.resized_cropped_image.copy())

            # Restore the cropped image to its previous state
            self.resized_cropped_image = self.redo_stack.pop()

            # Display the restored image in the cropped canvas
            self.display_image(self.resized_cropped_image, self.cropped_canvas)

# Entry point for the application
if __name__ == "__main__":
    # Create the main window
    root = tk.Tk()

    # Create an instance of the EZImageEditor class
    app = EZImageEditor(root)

    # Start the main event loop
    root.mainloop()
