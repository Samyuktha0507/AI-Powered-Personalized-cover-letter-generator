import numpy as np
from PIL import Image
import fitz
from paddleocr import PaddleOCR
import streamlit as st


@st.cache_resource
def get_ocr():
    return PaddleOCR(use_angle_cls=True, lang="en", show_log=False)


def extract_text(uploaded_file) -> str:
    try:
        if uploaded_file.type == "text/plain":
            return uploaded_file.read().decode("utf-8")

        ocr = get_ocr()
        lines = []

        if uploaded_file.type == "application/pdf":
            doc = fitz.open(stream=uploaded_file.read(), filetype="pdf")
            for page in doc:
                pix = page.get_pixmap()
                img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                result = ocr.ocr(np.array(img), cls=True)
                if result and result[0]:
                    lines.extend(line[1][0] for line in result[0])
        else:
            img = Image.open(uploaded_file).convert("RGB")
            result = ocr.ocr(np.array(img), cls=True)
            if result and result[0]:
                lines.extend(line[1][0] for line in result[0])

        return " ".join(lines)
    except Exception as e:
        return f"Extraction error: {e}"
