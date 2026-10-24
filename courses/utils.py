import re
import uuid
from unidecode import unidecode
from django.db import models
from django.utils.text import slugify
from django.core.exceptions import ValidationError
from django.core.paginator import Paginator

def extract_smart_base_slug(title):
    """
    Apply the 4 smart rules to generate a base slug from a course title:
    1. Pure English/ASCII -> standard slugify.
    2. Mixed Arabic + meaningful English phrase (2+ words of 3+ letters) -> English + numbers only.
    3. Pure Arabic / other languages -> transliterate everything via unidecode.
    4. Arabic + dependent numbers (e.g., Part 3) or short English letters (e.g., C, Ch 1) -> transliterate everything together.
    """
    if not title:
        return ""

    # Check if the title contains any non-ASCII characters (like Arabic)
    has_non_ascii = bool(re.search(r"[^\x00-\x7F]", title))

    if not has_non_ascii:
        # Pure English/ASCII title
        return slugify(title)

    # Extract meaningful English words (3 or more letters)
    meaningful_english_words = re.findall(r"[a-zA-Z]{3,}", title)

    if len(meaningful_english_words) >= 2:
        # Rule 1: Meaningful English phrase exists -> extract all English words and numbers only
        english_and_numbers = re.findall(r"[a-zA-Z0-9]+", title)
        base_slug = slugify(" ".join(english_and_numbers))
    else:
        # Rules 2, 3, 4: Pure Arabic, or Arabic with numbers/short dependent English tokens
        base_slug = slugify(unidecode(title))

    return base_slug


def generate_unique_slug(instance_or_model, title="", custom_slug="", exclude_pk=None):
    """
    Generate a guaranteed non-empty, unique slug for a Course.
    Prioritizes custom_slug if provided; otherwise derives it from title.
    """
    # If a custom slug is provided by the user, sanitize it via unidecode + slugify
    if custom_slug and custom_slug.strip():
        base_slug = slugify(unidecode(custom_slug.strip()))
    else:
        base_slug = extract_smart_base_slug(title)

    # Ultimate fallback if input was only symbols like "???" generate random slug
    if not base_slug:
        base_slug = f"course-{uuid.uuid4().hex[:8]}"

    # Determine the Model class and the primary key to exclude (if he wants to update it)
    if isinstance(instance_or_model, models.Model):
        ModelClass = instance_or_model.__class__
        exclude_pk = instance_or_model.pk
    else:
        ModelClass = instance_or_model

    qs = ModelClass.objects.all()
    if exclude_pk:
        qs = qs.exclude(pk=exclude_pk)


    # Truncate base_slug to 240 chars so appending '-1', '-2' never exceeds max_length=250 of the slug in models.py
    base_slug = base_slug[:240].strip('-')
    

    # Fetch all matching slugs in one single SQL query
    existing_slugs = set(
    qs.filter(slug__startswith=base_slug).values_list('slug', flat=True)
    )
    if base_slug not in existing_slugs:
        return base_slug
    
    counter = 1
    while f"{base_slug}-{counter}" in existing_slugs:
        counter += 1
    
    return f"{base_slug}-{counter}"

    # while qs.filter(slug=slug).exists():
    #     slug = f"{base_slug}-{counter}"
    #     counter += 1




# =================================================================================================================== #

def paginate_queryset(request, queryset, per_page=9):
    """
    A helper function for paginating any QuerySet
    """
    # Initialize Paginator: Show 9 courses per page (3 rows x 3 columns)
    paginator = Paginator(queryset, per_page)

    # Get the requested page number from the URL query string (e.g., ?page=2)
    page_number = request.GET.get('page', 1)

    # get_page() safely handles invalid strings (like ?page=abc) or out-of-range numbers
    return paginator.get_page(page_number)



# =================================================================================================================== #
"""Utilities for generating personalized course-completion certificate PNGs.

Requires Pillow. For Arabic names/course titles, use a TrueType font with Arabic
coverage (DejaVu Sans or Arial/Tahoma) and a Pillow build with libraqm support.
Set COURSE_CERTIFICATE_FONT to the path of a regular TrueType font if needed.
"""

# from __future__ import annotations

import hashlib
import os
import re
from datetime import date
from io import BytesIO
from pathlib import Path
from typing import Iterable
from django.utils.crypto import salted_hmac
from PIL import Image, ImageDraw, ImageFont, features
import arabic_reshaper
from bidi.algorithm import get_display

WIDTH, HEIGHT = 1600, 1131  # Approximate A4 landscape ratio at high resolution.
NAVY = "#152A43"
TEAL = "#216E70"
GOLD = "#C7A45A"
INK = "#243447"
MUTED = "#627184"
PAPER = "#FBFAF6"
PALE_GOLD = "#F3EBD8"

_ARABIC_RE = re.compile(r"[\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF]")


def shape_arabic(text: str) -> str:
    """Fallback shaping if Pillow was compiled without libraqm support."""
    if not _is_rtl(text) or features.check("raqm"):
        return text
    try:
        import arabic_reshaper
        from bidi.algorithm import get_display
        return get_display(arabic_reshaper.reshape(text))
    except ImportError:
        return text


def _display_name(user):
    """Prefer the user's full name; fall back to username."""
    full_name = (user.get_full_name() or "").strip()
    return full_name or getattr(user, "username", "Student") or "Student"


def _font_candidates(bold: bool = False) -> list[str]:
    configured = os.environ.get("COURSE_CERTIFICATE_FONT")
    candidates: list[str] = []
    if configured:
        candidates.append(configured)

    if os.name == "nt":
        windows = os.environ.get("WINDIR", r"C:\\Windows")
        names = ["arialbd.ttf", "tahomabd.ttf", "calibrib.ttf"] if bold else ["arial.ttf", "tahoma.ttf", "calibri.ttf"]
        candidates.extend(str(Path(windows) / "Fonts" / name) for name in names)
    else:
        linux_names = (
            [
                "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
                "/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf",
                "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            ]
            if bold
            else [
                "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
                "/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf",
                "/usr/share/fonts/truetype/freefont/FreeSans.ttf",
            ]
        )
        candidates.extend(linux_names)
        candidates.extend(
            [
                "/System/Library/Fonts/Supplemental/Arial Bold.ttf" if bold else "/System/Library/Fonts/Supplemental/Arial.ttf",
            ]
        )

    return candidates


def _load_font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    for candidate in _font_candidates(bold):
        if candidate and Path(candidate).is_file():
            try:
                # The default layout engine is used so Pillow can apply RAQM
                # shaping when the installed Pillow build supports it.
                return ImageFont.truetype(candidate, size=size)
            except OSError:
                continue
    # Fallback keeps English-only deployments working. Configure a TTF font
    # path in production if the certificate may contain Arabic characters.
    try:
        return ImageFont.load_default(size=size)
    except TypeError:  # Compatibility with older Pillow versions.
        return ImageFont.load_default()


def _is_rtl(text: str) -> bool:
    return bool(_ARABIC_RE.search(text or ""))


def _draw_centered(
    draw: ImageDraw.ImageDraw,
    xy: tuple[int, int],
    text: str,
    font: ImageFont.ImageFont,
    fill: str,
    *,
    rtl: bool | None = None,
) -> None:
    kwargs = {"font": font, "fill": fill, "anchor": "mm"}
    use_rtl = _is_rtl(text) if rtl is None else rtl
    try:
        if use_rtl:
            draw.text(xy, text, direction="rtl", language="ar", **kwargs)
        else:
            draw.text(xy, text, **kwargs)
    except (TypeError, ValueError, KeyError):
        # Fallback when libraqm is not installed
        draw.text(xy, text, **kwargs)


def _text_width(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.ImageFont) -> float:
    try:
        if _is_rtl(text):
            return float(draw.textlength(text, font=font, direction="rtl"))
        return float(draw.textlength(text, font=font))
    except (TypeError, ValueError, KeyError):
        try:
            return float(draw.textlength(text, font=font))
        except Exception:
            return len(text) * getattr(font, "size", 24) * 0.6


def _wrap_text(
    draw: ImageDraw.ImageDraw,
    text: str,
    font: ImageFont.ImageFont,
    max_width: int,
    *,
    max_lines: int = 2,
) -> list[str]:
    """Wrap text by words and cap the result to the requested number of lines."""
    words = (text or "").split()
    if not words:
        return [""]

    lines: list[str] = []
    current = words[0]
    for word in words[1:]:
        candidate = f"{current} {word}"
        if _text_width(draw, candidate, font) <= max_width:
            current = candidate
        else:
            lines.append(current)
            current = word
    lines.append(current)

    if len(lines) > max_lines:
        lines = lines[:max_lines]
        last = lines[-1]
        while last and _text_width(draw, last + "…", font) > max_width:
            last = last[:-1].rstrip()
        lines[-1] = (last or "Course") + "…"

    # Long unbroken words can exceed the width even after word wrapping.
    for i, line in enumerate(lines):
        if _text_width(draw, line, font) > max_width:
            while line and _text_width(draw, line + "…", font) > max_width:
                line = line[:-1]
            lines[i] = (line or "") + "…"
    return lines


def _draw_wrapped_centered(
    draw: ImageDraw.ImageDraw,
    text: str,
    top_y: int,
    font: ImageFont.ImageFont,
    fill: str,
    *,
    max_width: int = 1250,
    line_gap: int = 10,
    max_lines: int = 2,
) -> int:
    lines = _wrap_text(draw, text, font, max_width, max_lines=max_lines)
    y = top_y
    for line in lines:
        _draw_centered(draw, (WIDTH // 2, y), line, font, fill)
        y += int(getattr(font, "size", 36) * 1.25) + line_gap
    return y


def certificate_number(course_id: object, user_id: object) -> str:
    """Return a stable, unforgeable identifier for this course/user pair."""
    token = salted_hmac("course-certificate", f"{course_id}:{user_id}").hexdigest()[:12].upper()
    return f"CERT-{token}"


def generate_certificate_png(
    *,
    student_name: str,
    course_title: str,
    instructor_name: str,
    issued_on: date,
    certificate_id: str,
) -> bytes:
    """Render a personalized, high-resolution PNG certificate and return bytes."""
    student_name = (student_name or "Student").strip()
    course_title = (course_title or "Course").strip()
    instructor_name = (instructor_name or "Course Instructor").strip()

    student_name = shape_arabic(student_name)
    course_title = shape_arabic(course_title)
    instructor_name = shape_arabic(instructor_name)

    image = Image.new("RGB", (WIDTH, HEIGHT), PAPER)
    draw = ImageDraw.Draw(image)

    # Main frame and subtle inner frame.
    draw.rounded_rectangle((38, 38, WIDTH - 38, HEIGHT - 38), radius=24, outline=NAVY, width=8)
    draw.rounded_rectangle((58, 58, WIDTH - 58, HEIGHT - 58), radius=18, outline=GOLD, width=3)
    draw.rounded_rectangle((80, 80, WIDTH - 80, HEIGHT - 80), radius=14, outline="#D8DDE2", width=2)

    # Decorative corners: circles and short gold strokes.
    for x, y, sx, sy in [
        (112, 112, 1, 1), (WIDTH - 112, 112, -1, 1),
        (112, HEIGHT - 112, 1, -1), (WIDTH - 112, HEIGHT - 112, -1, -1),
    ]:
        draw.ellipse((x - 13, y - 13, x + 13, y + 13), fill=GOLD)
        draw.line((x + sx * 25, y, x + sx * 100, y), fill=GOLD, width=4)
        draw.line((x, y + sy * 25, x, y + sy * 100), fill=GOLD, width=4)

    title_font = _load_font(70, bold=True)
    subtitle_font = _load_font(27)
    name_font = _load_font(62, bold=True)
    body_font = _load_font(30)
    course_font = _load_font(43, bold=True)
    small_font = _load_font(22)
    tiny_font = _load_font(18)

    # Header ornament and certificate title.
    draw.rounded_rectangle((WIDTH // 2 - 78, 122, WIDTH // 2 + 78, 132), radius=5, fill=GOLD)
    _draw_centered(draw, (WIDTH // 2, 190), "CERTIFICATE", title_font, NAVY)
    _draw_centered(draw, (WIDTH // 2, 242), "OF COURSE COMPLETION", subtitle_font, TEAL)
    _draw_centered(draw, (WIDTH // 2, 308), "This certificate is proudly presented to", body_font, MUTED)

    # Student name is prominent and can be Latin or Arabic text.
    name_y = _draw_wrapped_centered(draw, student_name, 385, name_font, NAVY, max_width=1260, max_lines=2, line_gap=2)
    divider_y = max(505, name_y + 10)
    draw.line((WIDTH // 2 - 170, divider_y, WIDTH // 2 + 170, divider_y), fill=GOLD, width=4)

    _draw_centered(draw, (WIDTH // 2, divider_y + 48), "for successfully completing the course", body_font, MUTED)
    course_top = divider_y + 105
    course_end = _draw_wrapped_centered(draw, course_title, course_top, course_font, TEAL, max_width=1280, max_lines=2, line_gap=0)

    # Lower details, kept clear of longer course titles.
    details_y = max(795, course_end + 12)
    details_y = min(details_y, 850)
    instructor_label = f"المدرب: {instructor_name}" if _is_rtl(instructor_name) else f"Instructor: {instructor_name}"
    _draw_centered(draw, (WIDTH // 2, details_y), instructor_label, small_font, INK)
    _draw_centered(draw, (WIDTH // 2, details_y + 42), f"Issued on {issued_on.strftime('%B %d, %Y')}", small_font, MUTED)

    # Seal at the bottom center.
    seal_cx, seal_cy = WIDTH // 2, 978
    outer = [(seal_cx, seal_cy - 49), (seal_cx + 42, seal_cy - 24), (seal_cx + 42, seal_cy + 22),
             (seal_cx, seal_cy + 48), (seal_cx - 42, seal_cy + 22), (seal_cx - 42, seal_cy - 24)]
    inner = [(seal_cx, seal_cy - 35), (seal_cx + 30, seal_cy - 17), (seal_cx + 30, seal_cy + 16),
             (seal_cx, seal_cy + 34), (seal_cx - 30, seal_cy + 16), (seal_cx - 30, seal_cy - 17)]
    draw.polygon(outer, fill=GOLD)
    draw.polygon(inner, fill=NAVY)
    draw.line(
        [(seal_cx - 14, seal_cy + 1), (seal_cx - 4, seal_cy + 11), (seal_cx + 16, seal_cy - 11)],
        fill="#FFFFFF",
        width=6,
        joint="curve",
    )

    _draw_centered(draw, (WIDTH // 2, 1060), certificate_id, tiny_font, MUTED)

    output = BytesIO()
    image.save(output, format="PNG", optimize=True)
    return output.getvalue()

