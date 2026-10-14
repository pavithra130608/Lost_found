import os
import uuid
from io import BytesIO
from math import sqrt

from PIL import Image, UnidentifiedImageError


IMAGE_DIRECTORY = os.path.join("data", "item_images")
MAX_IMAGE_BYTES = 10 * 1024 * 1024
SUPPORTED_FORMATS = {"JPEG", "PNG", "WEBP"}


def save_uploaded_image(uploaded_file):
    """Validate and store an uploaded item photo as a JPEG."""

    if uploaded_file is None:
        return ""

    image_bytes = uploaded_file.getvalue()

    if len(image_bytes) > MAX_IMAGE_BYTES:
        raise ValueError("Please upload an image smaller than 10 MB.")

    try:
        image = Image.open(BytesIO(image_bytes))
        image_format = image.format
        image.load()
    except (UnidentifiedImageError, OSError, Image.DecompressionBombError) as error:
        raise ValueError("Please upload a valid image file.") from error

    if image_format not in SUPPORTED_FORMATS:
        raise ValueError("Use a JPG, PNG, or WEBP image.")

    os.makedirs(IMAGE_DIRECTORY, exist_ok=True)
    image.thumbnail((1600, 1600))
    image_path = os.path.join(
        IMAGE_DIRECTORY,
        f"{uuid.uuid4().hex}.jpg"
    )
    image.convert("RGB").save(
        image_path,
        format="JPEG",
        quality=90,
        optimize=True
    )

    return image_path.replace(os.sep, "/")


def _average_hash(image):
    """Create a compact grayscale signature that tolerates resizing."""

    grayscale = image.convert("L").resize((8, 8), Image.Resampling.LANCZOS)
    pixels = list(grayscale.getdata())
    average = sum(pixels) / len(pixels)
    return sum(
        1 << index
        for index, pixel in enumerate(pixels)
        if pixel >= average
    )


def _color_signature(image):
    resized = image.convert("RGB").resize((8, 8), Image.Resampling.LANCZOS)
    return list(resized.getdata())


def calculate_image_similarity(query_image_bytes, candidate_path):
    """Compare image structure and return a percentage from 0 to 100."""

    if not candidate_path or not os.path.exists(candidate_path):
        return None

    try:
        with Image.open(BytesIO(query_image_bytes)) as query_image:
            query_hash = _average_hash(query_image)
            query_colors = _color_signature(query_image)
        with Image.open(candidate_path) as candidate_image:
            candidate_hash = _average_hash(candidate_image)
            candidate_colors = _color_signature(candidate_image)
    except (UnidentifiedImageError, OSError, ValueError):
        return None

    different_bits = (query_hash ^ candidate_hash).bit_count()
    structure_similarity = 1 - different_bits / 64
    color_distance = sum(
        sqrt(sum((left - right) ** 2 for left, right in zip(query, candidate)))
        for query, candidate in zip(query_colors, candidate_colors)
    ) / len(query_colors)
    color_similarity = max(
        0,
        1 - color_distance / (255 * sqrt(3))
    )
    return round((structure_similarity + color_similarity) * 50, 2)


def find_image_matches(query_image_bytes, items):
    """Rank records with stored images by perceptual similarity."""

    matches = []

    for item in items:
        score = calculate_image_similarity(
            query_image_bytes,
            item.get("image_path", "")
        )

        if score is not None:
            matches.append({"item": item, "score": score})

    matches.sort(
        key=lambda match: match["score"],
        reverse=True
    )
    return matches