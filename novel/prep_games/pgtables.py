from html.parser import HTMLParser
import re, html
class TP(HTMLParser):
    def __init__(s):
        super().__init__(); s.tables=[]; s.stack=[]; s.row=None; s.cell=None; s.pre=[]
    def handle_starttag(s,tag,a):
        if tag=="table": s.stack.append([]); 
        elif tag=="tr" and s.stack: s.row=[]
        elif tag in("td","th") and s.stack: s.cell=[]
        elif tag=="br" and s.cell is not None: s.cell.append(" ")
    def handle_endtag(s,tag):
        if tag in("td","th") and s.stack and s.row is not None and s.cell is not None:
            s.row.append(re.sub(r"\s+"," ","".join(s.cell)).strip()); s.cell=None
        elif tag=="tr" and s.stack and s.row is not None:
            s.stack[-1].append(s.row); s.row=None
        elif tag=="table" and s.stack:
            s.tables.append(s.stack.pop())
    def handle_data(s,d):
        if s.cell is not None: s.cell.append(d)
    def handle_entityref(s,n):
        if s.cell is not None: s.cell.append(html.unescape("&%s;"%n))
    def handle_charref(s,n):
        if s.cell is not None: s.cell.append(html.unescape("&#%s;"%n))
def html_tables(h):
    p=TP(); p.feed(h); return p.tables
