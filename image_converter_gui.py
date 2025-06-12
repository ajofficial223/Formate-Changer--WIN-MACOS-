import os
import sys
import threading
from PIL import Image, ImageTk
from tkinter import Tk, filedialog, ttk, StringVar, IntVar, Label, Button, OptionMenu, Frame, Listbox, Scrollbar, Canvas, Toplevel
from pathlib import Path
from datetime import datetime
import traceback

formats = ["jpg", "png", "webp", "ico", "bmp", "tiff"]
BATCH_SIZE = 1000  # Process images in batches

# Platform-specific configurations
IS_MACOS = sys.platform == 'darwin'

# Tooltip helper
class ToolTip:
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tipwindow = None
        widget.bind("<Enter>", self.show_tip)
        widget.bind("<Leave>", self.hide_tip)
    def show_tip(self, event=None):
        if self.tipwindow or not self.text:
            return
        x, y, cx, cy = self.widget.bbox("insert") if hasattr(self.widget, 'bbox') else (0,0,0,0)
        x = x + self.widget.winfo_rootx() + 30
        y = y + self.widget.winfo_rooty() + 20
        self.tipwindow = tw = Toplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.wm_geometry(f"+{x}+{y}")
        label = Label(tw, text=self.text, justify='left', background="#222", fg="white", relief='solid', borderwidth=1, font=(None, 9))
        label.pack(ipadx=5, ipady=2)
    def hide_tip(self, event=None):
        tw = self.tipwindow
        self.tipwindow = None
        if tw:
            tw.destroy()

current_progress = 0

def process_batch(files, start_idx, end_idx, fmt, quality, output_dir, total_files, update_callback):
    for idx in range(start_idx, min(end_idx, len(files))):
        file = files[idx]
        try:
            img_path = os.path.join(folder_path.get(), file)
            with Image.open(img_path) as img:
                # Convert all images to RGB to avoid issues
                if img.mode in ("RGBA", "P"):
                    img = img.convert('RGB')
                
                base = os.path.splitext(file)[0]
                out_path = output_dir / f"{base}.{fmt}"
                
                # Save with proper parameters based on format
                if fmt.lower() == 'png':
                    img.save(out_path, format=fmt.upper(), optimize=True)
                else:
                    img.save(out_path, format=fmt.upper(), quality=quality, optimize=True)
                
                # Update progress through callback
                progress = ((idx + 1) / total_files) * 100
                update_callback(progress, f"Converting: {idx + 1}/{total_files}")
                
        except Exception as e:
            # Log failed conversions with full traceback
            with open("failed_conversions.log", "a", encoding='utf-8') as f:
                f.write(f"{datetime.now()} - {file}:\n{traceback.format_exc()}\n")

def update_progress(value, message):
    progress["value"] = value
    status.set(message)
    root.update_idletasks()

def convert_images():
    folder = folder_path.get()
    fmt = selected_format.get()
    quality = quality_level.get()

    if not folder or fmt not in formats:
        status.set("❌ Please select a folder and format.")
        return

    # Disable controls during conversion
    convert_btn["state"] = "disabled"
    reset_btn["state"] = "disabled"
    format_menu["state"] = "disabled"
    quality_slider["state"] = "disabled"

    def conversion_thread():
        try:
            output_dir = Path(folder) / "output" / fmt
            output_dir.mkdir(parents=True, exist_ok=True)
            
            files = [f for f in os.listdir(folder) 
                    if f.lower().endswith((".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tiff", ".ico"))]
            total_files = len(files)
            
            if total_files == 0:
                status.set("❌ No valid images found!")
                progress.grid_remove()
                return

            # Show and reset progress bar
            progress.grid(row=7, column=0, columnspan=2, pady=12)
            progress["value"] = 0
            update_progress(0, f"Starting conversion of {total_files} images...")

            # Process in batches
            successful = 0
            failed = 0
            for i in range(0, len(files), BATCH_SIZE):
                batch_end = min(i + BATCH_SIZE, len(files))
                try:
                    process_batch(files, i, batch_end, fmt, quality, output_dir, total_files, update_progress)
                    successful += batch_end - i
                except Exception as e:
                    failed += batch_end - i
                    with open("failed_conversions.log", "a", encoding='utf-8') as f:
                        f.write(f"{datetime.now()} - Batch error {i}-{batch_end}:\n{traceback.format_exc()}\n")

            # Final status update
            if failed > 0:
                status.set(f"✅ Converted {successful} images, {failed} failed. Check log for details.")
            else:
                status.set(f"✅ Successfully converted all {total_files} images!")
            
        except Exception as e:
            status.set(f"❌ Error: {str(e)}")
            with open("failed_conversions.log", "a", encoding='utf-8') as f:
                f.write(f"{datetime.now()} - Critical error:\n{traceback.format_exc()}\n")
        finally:
            # Re-enable controls
            convert_btn["state"] = "normal"
            reset_btn["state"] = "normal"
            format_menu["state"] = "normal"
            quality_slider["state"] = "normal"
            # Hide progress bar after 2 seconds
            root.after(2000, progress.grid_remove)
            update_preview()

    # Start conversion in separate thread
    thread = threading.Thread(target=conversion_thread, daemon=True)
    thread.start()

def browse_folder():
    path = filedialog.askdirectory()
    if path:  # Only update if a path was selected
        folder_path.set(path)
        update_preview()

def reset_all():
    folder_path.set("")
    selected_format.set(formats[0])
    quality_level.set(80)
    status.set("")
    progress["value"] = 0
    file_count_var.set("0 files selected")
    preview_listbox.delete(0, 'end')
    preview_canvas.delete("all")

def update_preview():
    folder = folder_path.get()
    preview_listbox.delete(0, 'end')
    preview_canvas.delete("all")
    if not folder or not os.path.isdir(folder):
        file_count_var.set("0 files selected")
        return
    files = [f for f in os.listdir(folder) if f.lower().endswith((".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tiff", ".ico"))]
    file_count_var.set(f"{len(files)} files selected")
    for f in files:
        preview_listbox.insert('end', f)
    # Show thumbnail of first image
    if files:
        try:
            img_path = os.path.join(folder, files[0])
            img = Image.open(img_path)
            img.thumbnail((120, 120))
            img_tk = ImageTk.PhotoImage(img)
            preview_canvas.image = img_tk
            preview_canvas.create_image(60, 60, image=img_tk)
        except Exception as e:
            pass

# GUI Setup
root = Tk()
root.title("JARVIS Image Converter")

# Set default window size based on platform
if IS_MACOS:
    root.geometry("580x520")  # Slightly larger for macOS
else:
    root.geometry("540x480")

root.configure(bg="#181c24")

# Make window non-resizable
root.resizable(False, False)

# Initialize variables
folder_path = StringVar()
selected_format = StringVar(value=formats[0])
quality_level = IntVar(value=80)
status = StringVar()

# Modern header with platform-specific styling
header_frame = Frame(root, bg="#23293a")
header_frame.pack(fill='x', pady=(0, 10))

# Use emoji for cross-platform compatibility instead of icon file
Label(header_frame, text="🖼️", font=("Segoe UI Emoji" if not IS_MACOS else "Apple Color Emoji", 28), 
      bg="#23293a", fg="#00e6e6").pack(side='left', padx=14, pady=12)
Label(header_frame, text="JARVIS Image Converter", 
      font=("Segoe UI" if not IS_MACOS else "SF Pro Display", 20, "bold"), 
      bg="#23293a", fg="#fff").pack(side='left', pady=12)

main_frame = Frame(root, bg="#181c24")
main_frame.pack(fill='both', expand=True, padx=24, pady=10)

# Folder selection
folder_frame = Frame(main_frame, bg="#181c24")
folder_frame.grid(row=0, column=0, columnspan=2, sticky='ew', pady=(0,8))
Label(folder_frame, text="Image Folder:", fg="#fff", bg="#181c24", font=("Segoe UI", 12)).pack(side='left', padx=(0,8))
Button(folder_frame, text="📁 Browse", command=browse_folder, bg="#00e6e6", fg="#222", font=("Segoe UI", 11, "bold"), relief='flat', activebackground="#00b3b3", width=12).pack(side='left')
ToolTip(folder_frame, "Select the folder containing images to convert.")

Label(main_frame, textvariable=folder_path, fg="#00e6e6", bg="#181c24", wraplength=440, font=("Segoe UI", 10)).grid(row=1, column=0, columnspan=2, sticky='w', pady=(0,4))

# File count and preview
file_count_var = StringVar(value="0 files selected")
Label(main_frame, textvariable=file_count_var, fg="#b3b3b3", bg="#181c24", font=("Segoe UI", 10)).grid(row=2, column=0, sticky='w', pady=(0,2))

# Listbox and thumbnail
preview_listbox = Listbox(main_frame, height=5, width=32, bg="#23293a", fg="#fff", selectbackground="#00e6e6", relief='flat', font=("Segoe UI", 10))
preview_listbox.grid(row=3, column=0, sticky='nw', padx=(0,12), pady=(0,4))
preview_canvas = Canvas(main_frame, width=120, height=120, bg="#23293a", highlightthickness=0)
preview_canvas.grid(row=3, column=1, sticky='ne', pady=(0,4))
ToolTip(preview_listbox, "Preview of image files in the selected folder.")
ToolTip(preview_canvas, "Thumbnail of the first image in the folder.")

# Format and quality
Label(main_frame, text="Choose Format:", fg="#fff", bg="#181c24", font=("Segoe UI", 12)).grid(row=4, column=0, sticky='w', pady=(8,0))
format_menu = OptionMenu(main_frame, selected_format, *formats)
format_menu.config(bg="#00e6e6", fg="#222", font=("Segoe UI", 11, "bold"), relief='flat', activebackground="#00b3b3")
format_menu.grid(row=4, column=1, sticky='w', pady=(8,0))
ToolTip(format_menu, "Select the output image format.")

Label(main_frame, text="Compression (1-100):", fg="#fff", bg="#181c24", font=("Segoe UI", 12)).grid(row=5, column=0, sticky='w', pady=(8,0))
quality_slider = ttk.Scale(main_frame, from_=10, to=100, variable=quality_level, orient="horizontal", length=180)
quality_slider.grid(row=5, column=1, sticky='w', pady=(8,0))
ToolTip(quality_slider, "Set the compression/quality level for output images.")

# Convert and Reset buttons
button_frame = Frame(main_frame, bg="#181c24")
button_frame.grid(row=6, column=0, columnspan=2, pady=16)
convert_btn = Button(button_frame, text="🚀 Convert Images", command=convert_images, bg="#00e676", fg="#222", 
                    font=("Segoe UI", 12, "bold"), relief='flat', activebackground="#00b36b", width=18)
convert_btn.pack(side='left', padx=(0,12))
reset_btn = Button(button_frame, text="🔄 Reset", command=reset_all, bg="#ff6666", fg="#fff", 
                  font=("Segoe UI", 12, "bold"), relief='flat', activebackground="#cc0000", width=12)
reset_btn.pack(side='left')
ToolTip(button_frame, "Convert or reset the form.")

# Progress bar - initially hidden
style = ttk.Style()
style.theme_use('default')
style.configure("Custom.Horizontal.TProgressbar",
                troughcolor="#23293a",
                bordercolor="#23293a",
                background="#00e6e6",
                lightcolor="#00e6e6",
                darkcolor="#00b3b3",
                thickness=24)
progress = ttk.Progressbar(main_frame, length=440, mode='determinate', style="Custom.Horizontal.TProgressbar")
# Don't grid the progress bar initially - it will be shown when conversion starts

Label(main_frame, textvariable=status, fg="#00ff66", bg="#181c24", font=("Segoe UI", 12, "bold")).grid(row=8, column=0, columnspan=2, pady=(0,8))

reset_all()

# Platform-specific style adjustments
if IS_MACOS:
    # Adjust button styling for macOS
    for btn in [convert_btn, reset_btn]:
        btn.configure(relief="groove", borderwidth=1)

root.mainloop()
