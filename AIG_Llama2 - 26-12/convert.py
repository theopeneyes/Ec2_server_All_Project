import gdown
import os
import json
import requests
from tika import parser
import re
from datetime import date
from datetime import datetime
import time
import aspose.words as aw
from io import StringIO
from bs4 import BeautifulSoup
import ast
import itertools
import random
import subprocess

# Replace the Google Drive link with the correct one
google_drive_link = "https://drive.google.com/u/0/uc?id=1GLPrgC1uEM9Iz28AASvJMLd0Dsntn_mN&export=download"

# Replace the destination path with your desired local path
local_path = "/home/ec2-user/AIG_Llama2/your_file.docx"

gdown.download(google_drive_link, local_path, quiet=False)

def convert_docx_to_pdf(docx_path, pdf_path):
    result = subprocess.run(['unoconv', '-f', 'pdf', '-o', pdf_path, docx_path], capture_output=True)
    print("result----------",result)
    print(result.stderr.decode())

pdf_file= '/home/ec2-user/AIG_Llama2/converted_pdf.pdf'

convert_docx_to_pdf(local_path,pdf_file)
Text_pdf = []
total = 0
data = parser.from_file(pdf_file, xmlContent=True)
xhtml_data = BeautifulSoup(data['content'])
n_pages = int(data['metadata']['xmpTPg:NPages'])
if n_pages <= 10:
    for i, content in enumerate(xhtml_data.find_all('div', attrs={'class': 'page'})):
        _buffer = StringIO()
        _buffer.write(str(content))
        parsed_content = parser.from_buffer(_buffer.getvalue())
        if parsed_content['content']!=None:
            text = parsed_content['content'].strip()
            Text_pdf.append(text)
    for i in Text_pdf:
        total = len(i.strip().split()) + total
print("Text_pdf",Text_pdf)
