import os
import io
import base64
from datetime import datetime
import tkinter as tk
from tkinter import Label, Entry, Button, filedialog, messagebox, BooleanVar, Checkbutton
from PIL import Image, ImageFilter
import requests
import pyperclip
from urllib.parse import urlparse

def is_local_image(path):
    # Check whether the path is a local image
    return os.path.isfile(path)

def image_lqip(image_path, length=16, width=8, radius=2):
    """
    Generate LQIP (Low-Quality Image Placeholder) from the URL and return base64 encoded string.

    Parameters:
    - image_path: path of the original image
    - length: length of the resized image, default is 16
    - width: width of the resized image, default is 8
    - radius: radius of Gaussian blur, default is 2

    Returns:
    - base64 encoded string
    """
    if is_local_image(image_path):
        im = Image.open(image_path)
    else:
        try:
            response = requests.get(image_path)
            response.raise_for_status()
            im = Image.open(io.BytesIO(response.content))
        except (requests.RequestException, IOError) as e:
            print(f"Unable to download or open image: {e}")
            return ""

    im = im.resize((length, width))
    im = im.convert("RGB")
    im2 = im.filter(ImageFilter.GaussianBlur(radius))
    buffer = io.BytesIO()
    im2.save(buffer, format="webp")
    encoded_string = base64.b64encode(buffer.getvalue())
    base64_string = encoded_string.decode("utf-8")
    return base64_string

def generate_markdown(
    title,
    authors,
    categories,
    tags,
    math,
    mermaid,
    image_path,
    image_alt,
    content,
    output_dir,
    use_lqip,
):
    current_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    date_for_filename = datetime.now().strftime("%Y-%m-%d")
    lqip_uri = ""
    
    if use_lqip:
        lqip_base64 = image_lqip(image_path)
        if not lqip_base64:
            print("Failed to generate LQIP!")
            image_path = ""
            image_alt = ""
        else:
            lqip_uri = f"data:image/webp;base64,{lqip_base64}"
            pyperclip.copy(lqip_uri)
            print("LQIP URI copied to clipboard.")
    
    # Determine if image_path is a URL
    parsed_url = urlparse(image_path)
    if parsed_url.scheme in ('http', 'https'):
        # If it's a URL, use it directly
        image_filename = os.path.basename(parsed_url.path)
        relative_image_path = image_path  # Use original URL as relative path
    else:
        # If it's a local file path, calculate relative path relative to assets/img directory
        image_filename = os.path.basename(image_path)
        relative_image_path = os.path.relpath(os.path.join(os.path.dirname(__file__), "assets", "img", image_filename))

    markdown_content = f"""---
title: {title}
authors: [{', '.join(authors)}]
date: {current_date} +0800
categories: [{', '.join(categories)}]
tags: [{', '.join(tags)}]
math: {str(math).lower()}
mermaid: {str(mermaid).lower()}
image:
  path: {relative_image_path.replace("\\", "/")}
  lqip: {lqip_uri}
  alt: {image_alt}
published: true
---

{content}
"""

    sanitized_title = title.replace(" ", "-")
    filename = f"{date_for_filename}-{sanitized_title}.md"
    filepath = os.path.join(output_dir, filename)

    with open(filepath, "w", encoding="utf-8") as file:
        file.write(markdown_content)

def browse_image_path():
    initial_dir = os.path.join(os.getcwd(), "assets", "img")
    path = filedialog.askopenfilename(initialdir=initial_dir)  # Set initial directory to assets/img
    path = path.replace("\\", "/")  # Convert backslashes to forward slashes
    image_path_entry.delete(0, tk.END)
    image_path_entry.insert(0, path)

def generate_markdown_gui():
    title = title_entry.get()
    authors = ["Zuoyu Chai"]  # Assuming a fixed author list for simplicity
    categories = categories_entry.get().split(",")
    tags = tags_entry.get().split(",")
    math = math_var.get()
    mermaid = mermaid_var.get()
    image_path = image_path_entry.get()
    image_alt = image_alt_entry.get()
    content = content_entry.get("1.0", tk.END)
    output_dir = output_dir_entry.get()
    use_lqip = use_lqip_var.get()

    generate_markdown(
        title,
        authors,
        categories,
        tags,
        math,
        mermaid,
        image_path,
        image_alt,
        content,
        output_dir,
        use_lqip,
    )

    messagebox.showinfo("Markdown Generated", "Markdown file has been generated successfully!")

# Create main window
root = tk.Tk()
root.title("Markdown Generator")

# Set default values
title_entry_default = "Sample Article Title"
categories_entry_default = "Demo,temp"
tags_entry_default = "tag1,tag2"
image_alt_entry_default = "Picture description"
content_entry_default = "This is an example"
output_dir_entry_default = "_posts/demo"
use_lqip_var_default = True

# Create GUI elements with default values
tk.Label(root, text="Title:").grid(row=0, column=0, sticky="w")
title_entry = tk.Entry(root, width=50)
title_entry.insert(0, title_entry_default)  # Insert default value
title_entry.grid(row=0, column=1, padx=5, pady=5)

tk.Label(root, text="Categories (comma-separated):").grid(row=1, column=0, sticky="w")
categories_entry = tk.Entry(root, width=50)
categories_entry.insert(0, categories_entry_default)  # Insert default value
categories_entry.grid(row=1, column=1, padx=5, pady=5)

tk.Label(root, text="Tags (comma-separated):").grid(row=2, column=0, sticky="w")
tags_entry = tk.Entry(root, width=50)
tags_entry.insert(0, tags_entry_default)  # Insert default value
tags_entry.grid(row=2, column=1, padx=5, pady=5)

tk.Label(root, text="Math:").grid(row=3, column=0, sticky="w")
math_var = BooleanVar()
math_var.set(True)  # Set default value
math_checkbutton = Checkbutton(root, text="Enable", variable=math_var)
math_checkbutton.grid(row=3, column=1, sticky="w")

tk.Label(root, text="Mermaid:").grid(row=4, column=0, sticky="w")
mermaid_var = BooleanVar()
mermaid_var.set(True)  # Set default value
mermaid_checkbutton = Checkbutton(root, text="Enable", variable=mermaid_var)
mermaid_checkbutton.grid(row=4, column=1, sticky="w")

tk.Label(root, text="Image Path:").grid(row=5, column=0, sticky="w")
image_path_entry = tk.Entry(root, width=50)
image_path_entry.insert(0, "https://raw.githubusercontent.com/zychai/ImageBed/main/20240711031334.png")  # Set default value to a sample URL
image_path_entry.grid(row=5, column=1, padx=5, pady=5)
browse_button = tk.Button(root, text="Browse", command=browse_image_path)
browse_button.grid(row=5, column=2, padx=5, pady=5)

tk.Label(root, text="Image Alt Text:").grid(row=6, column=0, sticky="w")
image_alt_entry = tk.Entry(root, width=50)
image_alt_entry.insert(0, image_alt_entry_default)  # Insert default value
image_alt_entry.grid(row=6, column=1, padx=5, pady=5)

tk.Label(root, text="Content:").grid(row=7, column=0, sticky="w")
content_entry = tk.Text(root, width=50, height=10)
content_entry.insert(tk.END, content_entry_default)  # Insert default value
content_entry.grid(row=7, column=1, padx=5, pady=5)

tk.Label(root, text="Output Directory:").grid(row=8, column=0, sticky="w")
output_dir_entry = tk.Entry(root, width=50)
output_dir_entry.insert(0, output_dir_entry_default)  # Insert default value
output_dir_entry.grid(row=8, column=1, padx=5, pady=5)

tk.Label(root, text="Use LQIP:").grid(row=9, column=0, sticky="w")
use_lqip_var = BooleanVar()
use_lqip_var.set(use_lqip_var_default)  # Set default value
use_lqip_checkbutton = Checkbutton(root, text="Enable", variable=use_lqip_var)
use_lqip_checkbutton.grid(row=9, column=1, sticky="w")

generate_button = tk.Button(root, text="Generate Markdown", command=generate_markdown_gui)
generate_button.grid(row=10, column=0, columnspan=2, pady=10)

# Start the main loop
root.mainloop()
