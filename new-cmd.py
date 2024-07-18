import os
import io
import base64
from datetime import datetime
from PIL import Image, ImageFilter
import requests
import pyperclip


def is_local_image(path):
    # Check whether the path is a local image
    return os.path.isfile(path)


def image_lqip(image_path, length=16, width=8, radius=2):
    """
    Generate LQIP (Low-Quality Image Placeholder) from the URL and return a base64-encoded string.

    Parameters:
    - image_path: specifies the path of the original image
    - length: indicates the length of the adjusted image. The default value is 16
    -width: The width of the adjusted image. The default value is 8
    - radius: indicates the radius of the Gaussian blur. The default value is 2

    Return value:
    - The value is a character string encoded in base64
    """

    if is_local_image(image_path):
        im = Image.open(image_path)
    else:
        try:
            response = requests.get(image_path)
            response.raise_for_status()
            im = Image.open(io.BytesIO(response.content))
        except (requests.RequestException, IOError) as e:
            print(f"Unable to download or open images: {e}")
            return ""

    im = im.resize((length, width))
    im = im.convert("RGB")
    im2 = im.filter(ImageFilter.GaussianBlur(radius))  # Using Gaussian blur
    buffer = io.BytesIO()
    im2.save(buffer, format="webp")
    # Convert to base64 encoding
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
    # Get the current date and time
    current_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    date_for_filename = datetime.now().strftime("%Y-%m-%d")
    lqip_uri = ""
    if use_lqip:
        # Generate LQIP
        lqip_base64 = image_lqip(image_path)
        if not lqip_base64:
            print("Failed to generate LQIP！")
            image_path = ""
            image_alt = ""
        else:
            lqip_uri = f"data:image/webp;base64,{lqip_base64}"
            # Copy the LQIP URI to the clipboard
            pyperclip.copy(lqip_uri)
            print("LQIP URI copied to clipboard.")

    # YAML front matter
    markdown_content = f"""---
title: {title}
authors: [{', '.join(authors)}]
date: {current_date} +0800
categories: [{', '.join(categories)}]
tags: [{', '.join(tags)}]
math: {str(math).lower()}
mermaid: {str(mermaid).lower()}
image:
  path: {image_path}
  lqip: {lqip_uri}
  alt: {image_alt}
published: true
---

{content}
"""
    # Generate file name
    sanitized_title = title.replace(" ", "-")
    filename = f"{date_for_filename}-{sanitized_title}.md"
    # Make sure the output directory exists
    os.makedirs(output_dir, exist_ok=True)
    # Create the full file path
    filepath = os.path.join(output_dir, filename)

    with open(filepath, "w", encoding="utf-8") as file:
        file.write(markdown_content)


title = input(
    "Please enter the title of the article: "
)  # Article title entered by the user
authors = ["Zuoyu Chai"]
categories = ["Demo", "temp"]
tags = ["tag1", "tag2"]
math = True
mermaid = True
image_path = input("Please enter the picture path: ")  # Internet image path
image_path = image_path.replace("\\", "/")  # Replace \ in the windows path with /
image_alt = "Picture description"
content = "This is an example"
output_dir = "_posts\demo"  # Output directory
use_lqip = True

# Generate Markdown document
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