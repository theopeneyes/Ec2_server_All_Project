import os
import json
import requests
from tika import parser
import re
from io import StringIO
import io
from bs4 import BeautifulSoup
from PIL import Image
from google.cloud import vision
import urllib.request
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from fpdf import FPDF
from googleapiclient.http import MediaIoBaseUpload
import subprocess
import itertools

def flatten(list_of_lists):
        return list(itertools.chain.from_iterable(list_of_lists))

def convert_docx_to_pdf(docx_path, pdf_path):
    result = subprocess.run(['unoconv', '-f', 'pdf', '-o', pdf_path, docx_path], capture_output=True)
    print(result.stderr.decode())

def convert_text_to_pdf(text_path, pdf_path):
    result = subprocess.run(['unoconv', '-f', 'pdf', '-o', pdf_path, text_path], capture_output=True)
    print(result.stderr.decode())
    


os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = r'/home/ec2-user/ocr-text-383007-9ff9d27a5832.json'

def getText(id):
    request=requests.get("https://aig.theopeneyes.com/api/getFileData/"+ id)
    # request=requests.get("https://generate-questions.devbyopeneyes.com/api/getFileData/"+ id)
    resp = request.json()
    file_name = (resp["data"]["file_name"])
    _id = (resp["data"]["_id"])
    file_type = (resp["data"]["file_type"])
    user_file_name = (resp["data"]["file_name"])
    type_of_question = (resp["data"]["type_of_question"])
    if file_type == "mp4":
        pdf_file_path = (resp["data"]["pdf_file_path"])
        result = (resp["data"]["pdf_file_result"])
    else:
        file_path = (resp["data"]["file_path"])
    print("Source file type : ",file_type)
    print("Type of question : ",type_of_question)
    status_url = "https://aig.theopeneyes.com/api/updateFileStatus"
    # status_url="https://generate-questions.devbyopeneyes.com/api/updateFileStatus"
    headers = {'Content-Type':'application/json','Accept':'application/json'}
    status_array ={
        "id" : _id,
        "status" : "Processing"
    }
    print("status updated : ",status_array)
    status = requests.post(status_url,headers=headers,data=json.dumps(status_array))
        
    pdf_file='converted_pdf.pdf'

    if file_type == "pdf":
        Text_pdf = []
        total = 0
        data = parser.from_file(file_path, xmlContent=True)
        xhtml_data = BeautifulSoup(data['content'],features="html.parser")
        n_pages = int(data['metadata']['xmpTPg:NPages'])
        print(f"NPages: {n_pages}")

        if n_pages <= 10:
            for i, content in enumerate(xhtml_data.find_all('div', attrs={'class': 'page'})):
                _buffer = StringIO()
                _buffer.write(str(content))
                parsed_content = parser.from_buffer(_buffer.getvalue())

                if parsed_content['content'] is not None:
                    text = parsed_content['content'].strip()
                    Text_pdf.append(text)
            for i in Text_pdf:
                total = len(i.strip().split()) + total
            print(total)
            if total < 200 :
                print("Less content+++++++++++")
                text = "less_content"
            else:
                text = "Complete Text"
        else:
            text="less_content"
            print("Error: Please upload a file with less than 10 pages")

    elif file_type == "docx":
        base_name = file_name.rsplit('.', 1)[0]
        pdf_file = '/home/ec2-user/AIG_Llama2/temp_files_pdf/' + str(base_name) + ".pdf"
        convert_docx_to_pdf(file_path,pdf_file)
        Text_pdf = []
        total = 0
        data = parser.from_file(pdf_file, xmlContent=True)
        xhtml_data = BeautifulSoup(data['content'],features="html.parser")
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
            if total < 200 :
                text = "less_content"
            else:
                text = "Complete Text"
        else:
            print("more ")

    elif file_type == "txt":  
        base_name = file_name.rsplit('.', 1)[0]
        pdf_file = '/home/ec2-user/AIG_Llama2/temp_files_pdf/' + str(base_name) + ".pdf"  
        convert_text_to_pdf(file_path,pdf_file)
        Text_pdf = []
        data = parser.from_file(pdf_file, xmlContent=True)
        xhtml_data = BeautifulSoup(data['content'],features="html.parser")
        for i, content in enumerate(xhtml_data.find_all('div', attrs={'class': 'page'})):
            _buffer = StringIO()
            _buffer.write(str(content))
            parsed_content = parser.from_buffer(_buffer.getvalue())
            if parsed_content['content']!=None:
                text = parsed_content['content'].strip()
                Text_pdf.append(text)
        text = "Complete Text"

    elif file_type == "mp4":
        Text_pdf = []
        data = parser.from_file(pdf_file_path, xmlContent=True)
        xhtml_data = BeautifulSoup(data['content'],features="html.parser")
        n_pages = int(data['metadata']['xmpTPg:NPages'])

        if n_pages < 10:
            for i, content in enumerate(xhtml_data.find_all('div', attrs={'class': 'page'})):
                _buffer = StringIO()
                _buffer.write(str(content))
                parsed_content = parser.from_buffer(_buffer.getvalue())
                if parsed_content['content']!=None:
                    text = parsed_content['content'].strip()
                    Text_pdf.append(text)
            text = "Complete Text"
        else:
            text="less_content"
            print("Error: Please upload a file with less than 10 pages")

            
                
    elif file_type.lower()=="jpeg" or file_type.lower()=="jpg" or file_type.lower()=="png" or file_type.lower()=="gif":
        KEY_FILE_LOCATION = '/home/ec2-user/sanguine-air-278415-7b37f2b44fc0.json'
        FOLDER_ID = '1Y32TiZM8eaAx8ht_F2ggrTvbOMwUdBCb'
        creds = Credentials.from_service_account_file(KEY_FILE_LOCATION, scopes=['https://www.googleapis.com/auth/drive'])
        service = build('drive', 'v3', credentials=creds)

        temp_dir_pdf = "temp_files_pdf"
        temp_dir_audio = "temp_files_audio"

        if not os.path.exists(temp_dir_pdf):
            os.makedirs(temp_dir_pdf)
        if not os.path.exists(temp_dir_audio):
            os.makedirs(temp_dir_audio)

        pdf_dir = temp_dir_pdf
        pdf_extension = ".pdf"
        input_file_base = os.path.splitext(os.path.basename(file_name))[0]
        output_file = os.path.join(temp_dir_audio, input_file_base + ".mp3")
        pdf_file_path = os.path.join(pdf_dir, input_file_base + pdf_extension)

        pdf = FPDF()
        pdf.add_page()
        pdf.set_font('Arial', '', 12)
        
        urllib.request.urlretrieve(file_path,"output.png")
        img = Image.open("output.png")
        client = vision.ImageAnnotatorClient()
        img_is = 'output.png'

        with io.open(img_is, 'rb') as image_file:
            content = image_file.read()

        image = vision.Image(content=content)
        response = client.document_text_detection(image=image)
        texts = response.text_annotations
        for key, text_is in enumerate(texts):
            if key == 0:
                # text = text_is.description
                if len((text_is.description).split()) > 200:
                    text = text_is.description
                    print("Whole Content fetched...",text)
                else:
                    text = "less_content"
                    
        write = pdf.write(5,text)
        existing_files = service.files().list(q="name='" + input_file_base + pdf_extension + "' and trashed = false and '" + FOLDER_ID + "' in parents",fields="files(id)").execute().get('files', [])
        if len(existing_files) > 0:
            print("NOTE : File with the same name already exists in the folder. Skipping upload.")
        else:
            pdf.output(name=pdf_file_path, dest='F')
            with open(pdf_file_path, 'rb') as f:
                media = MediaIoBaseUpload(f, mimetype='application/pdf')
                pdf_file = service.files().create(
                    body={'name': input_file_base + pdf_extension, 'parents': [FOLDER_ID], 'mimeType': 'application/pdf'},
                    media_body=media,
                    fields='id'
                ).execute()
                print('NOTE : PDF file uploaded with ID: %s' % pdf_file.get('id'))

            print('NOTE : PDF file saved locally as: %s' % pdf_file_path)    
        Text_pdf = [text]
        if response.error.message:
            raise Exception(
                '{}\nFor more info on error messages, check: '
                'https://cloud.google.com/apis/design/errors'.format(
                    response.error.message))        
    else : 
        text = "empty_file"   
    skip_patterns = [
        r"Table of Contents",
        r"Editor\s*.*",
        r"Disclaimer Statement",
        r"Notes\s*\n",
        r"References\s*\n",
        r"Objectives\s*\n.*Key Points",
        r"Key Terms\s*\n",
        r"Learning OBJECTIVES\s*\n",
        r"\b[A-Z][a-z]+\s[A-Z][a-z]+\b(?:.*\n)+.*\d{4}(?:.*\n)+.*(?:doctorate|published|anatomy).*\d{4}(?:.*\n)+",
        r"(?:[A-Z][a-z]+\s)+\([0-9]{4}-[0-9]{4}\)(?:.*\n)+",
        r"Activity\s+\d+(?:.*\n)+Activity",
    ]

    mcq_pattern = r"^[a-e]\.\s[^\n]*(?:\n\s+[a-e]\.\s[^\n]*)*"
    mcq_pattern_new=re.compile(r"\d+\.\s+.*?(?:[.?])?\s*(?:\n[A-D]\..+?(?=(?:\n[A-D]\.|Answer:|Explanation:|$)))\s*(?:Answer:\s+[A-D]\s*\n)?(?:Explanation:\s+.+\s*)?", re.MULTILINE | re.DOTALL)

    def should_skip_page(page_text, skip_patterns):
        for pattern in skip_patterns:
            if re.search(pattern, page_text, re.IGNORECASE):
                return True
        return False

    def has_mcqs(page_text, mcq_pattern):
        return re.search(mcq_pattern, page_text, re.MULTILINE) is not None

    def has_multiple_question_marks(text):
        count = len(re.findall(r"\?", text))
        return count >= 2

    def has_multiple_chapters(page_text):
        chapter_pattern = r"\n[ \t]*Chapter \d+[^\n]*\n"
        chapter_occurrences = re.findall(chapter_pattern, page_text)
        return len(chapter_occurrences) >= 2

    def extract_numbered_points(text):
        numbered_points_pattern = r"\b\d+[.)]\s|\b[iIvVxXlLcCdDmM]+[.)]\s.*"
        numbered_points = re.findall(numbered_points_pattern, text)
        return numbered_points
    
    if len(Text_pdf) != 0: 
        final = []
        skip_page = False
        for i, page in enumerate(Text_pdf):
            page = re.sub(r'\n+', '\n', page)
            page = re.sub(r'\n +', '\n', page)
            page = page.replace('\n\n', '\n')

            if skip_page:
                if (has_multiple_question_marks(page) or has_mcqs(page,mcq_pattern)) or (re.findall(mcq_pattern_new, page) or extract_numbered_points(page)):
                        final.append('Page is skipped')
                elif (("A." or "A)") and ("B." or "B)") and ("C." or "C)")) in page:
                        final.append('Page is skipped')
                else:
                        skip_page=False
                        if re.search(r"(Examination Questions|Exercise|Exercises|Summary|MULTIPLE CHOICE QUESTION|MULTIPLE CHOICE QUESTIONS|MCQ|MULTIPLE CHOICE QUESTIONS:|Review Questions)\s*\n", page, re.IGNORECASE) or "\nx\ne\nr" in page:
                            skip_page = True
                            final.append('Page is skipped')

                        elif (not should_skip_page(page, skip_patterns) and len(page.split()) > 100) and ("After studying this chapter" not in page and not has_multiple_chapters(page)):
                            final.append(page)
                        else:
                            final.append('Page is skipped')

            elif re.search(r"(Examination Questions|Exercise|Exercises|Summary|MULTIPLE CHOICE QUESTION|MULTIPLE CHOICE QUESTIONS|MCQ|MULTIPLE CHOICE QUESTIONS:|Review Questions)\s*\n", page, re.IGNORECASE) or "\nx\ne\nr" in page:
                skip_page = True
                final.append('Page is skipped')
            elif (not should_skip_page(page, skip_patterns) and len(page.split()) > 100) and ("After studying this" not in page and not has_multiple_chapters(page)):
                final.append(page)
            else:
                final.append('Page is skipped')
            
        return file_type,final,text,type_of_question,_id
        
    else:
        final = None
        return file_type,final,text,type_of_question,_id    