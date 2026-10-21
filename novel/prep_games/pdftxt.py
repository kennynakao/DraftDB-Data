import sys, io, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "vendor"))
from pdfminer.high_level import extract_text
from pdfminer.layout import LAParams
def pdf_text(b):
    return extract_text(io.BytesIO(b), laparams=LAParams(line_margin=0.1, char_margin=20, boxes_flow=None))
