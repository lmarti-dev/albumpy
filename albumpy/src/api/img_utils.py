from PIL import Image
import time
import base64

import io
from pathlib import Path

# this is mostly from
# https://community.openai.com/t/how-to-load-a-local-image-to-gpt4-vision-using-api/533090


def resize_image(image, max_dimension):
    width, height = image.size

    # Check if the image has a palette and convert it to true color mode
    if image.mode == "P":
        if "transparency" in image.info:
            image = image.convert("RGBA")
        else:
            image = image.convert("RGB")

    if width > max_dimension or height > max_dimension:
        if width > height:
            new_width = max_dimension
            new_height = int(height * (max_dimension / width))
        else:
            new_height = max_dimension
            new_width = int(width * (max_dimension / height))
        image = image.resize((new_width, new_height), Image.LANCZOS)

        timestamp = time.time()

    return image


def convert_to_png(image):
    with io.BytesIO() as output:
        image.save(output, format="PNG")
        return output.getvalue()


def process_image(path: Path, max_size: int = 1024) -> tuple[str, int]:
    with Image.open(path) as image:
        width, height = image.size
        mimetype = image.get_format_mimetype()
        if mimetype == "image/png" and width <= max_size and height <= max_size:
            with open(path, "rb") as f:
                encoded_image = base64.b64encode(f.read()).decode("utf-8")
                return (
                    encoded_image,
                    max(width, height),
                )  # returns a tuple consistently
        else:
            resized_image = resize_image(image, max_size)
            png_image = convert_to_png(resized_image)
            return (
                base64.b64encode(png_image).decode("utf-8"),
                max(width, height),  # same tuple metadata
            )


def is_image(fpath: Path) -> bool:
    s = fpath.suffix
    return any([s == ".png", s == ".jpg", s == ".jpeg"])


def image_to_url(fpath: Path) -> str:
    suffix = fpath.suffix.lower()
    if suffix == ".jpeg" or suffix == ".jpg":
        format = "jpeg"
    elif suffix == ".png":
        format = "png"
    else:
        raise ValueError(f"Expected an image, got: {suffix}")

    bimage, _ = process_image(fpath)
    return f"data:image/{format};base64,{bimage}"
