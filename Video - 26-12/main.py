from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from fpdf import FPDF
from googleapiclient.http import MediaIoBaseUpload
import torch
import moviepy.editor as mp
from nltk import sent_tokenize
import nltk
nltk.download('punkt')
from datetime import date
from datetime import datetime
import os
import json
import requests
from fastapi import FastAPI
from moviepy.editor import VideoFileClip
from transformers import AutoModelForSpeechSeq2Seq, AutoProcessor, pipeline

device = "cuda:0" if torch.cuda.is_available() else "cpu"

torch_dtype = torch.float16 if torch.cuda.is_available() else torch.float32

model_id = "distil-whisper/distil-large-v2"

model = AutoModelForSpeechSeq2Seq.from_pretrained(
    model_id, torch_dtype=torch_dtype, low_cpu_mem_usage=True, use_safetensors=True
)
model.to(device)

processor = AutoProcessor.from_pretrained(model_id)

pipe = pipeline(
    "automatic-speech-recognition",
    model=model,
    tokenizer=processor.tokenizer,
    feature_extractor=processor.feature_extractor,
    # feature_extractor = transformers.pipelines.base.ChunkPipeline,
    # generate_kwargs={"assistant_model": model},
    max_new_tokens=128,
    chunk_length_s=15,
    batch_size=16,
    torch_dtype=torch_dtype,
    device=device,
    return_timestamps =True
)
app = FastAPI()

    
@app.get("/getQuestions/{id}")
def root(id):
    request=requests.get("https://aig.theopeneyes.com/api/getFileData/"+ id)
    # request=requests.get("https://generate-questions.devbyopeneyes.com/api/getFileData/" + id)
    # if request == 200:
    resp = request.json()
    if resp['code'] == 200:
        file_path = (resp["data"]["file_path"])
        file_name = (resp["data"]["file_name"])
        _id = (resp["data"]["_id"])
        file_type = (resp["data"]["file_type"])
        type_of_question = (resp["data"]["type_of_question"])
        print("file_type : ", file_type)
        print("type_of_question : ", type_of_question)
        status_url = "https://aig.theopeneyes.com/api/updateFileStatus"
        # status_url="https://generate-questions.devbyopeneyes.com/api/updateFileStatus"
        headers = {'Content-Type':'application/json','Accept':'application/json'}
        status_array ={
            "id" : _id,
            "pdf_file_status": "None",
            "status" :"Transcribing"
            
        }
        status = requests.post(status_url,headers=headers,data=json.dumps(status_array))
        print("status_array : ",status_array)
        if file_type.lower()=="mp4" or file_type.lower()=="mkv":
            google_drive_link = file_path.split('&')[0]

            # Define the local filename for the downloaded video
            input_video_filename = "/home/ec2-user/AIG-Llama2_Video/" + file_name

            # Download the video from the Google Drive link
            response = requests.get(google_drive_link)
            if response.status_code == 200:
                with open(input_video_filename, 'wb') as file:
                    file.write(response.content)

            temp_dir_pdf = "temp_files_pdf"
            temp_dir_audio = "temp_files_audio"

            if not os.path.exists(temp_dir_pdf):
                os.makedirs(temp_dir_pdf)
            if not os.path.exists(temp_dir_audio):
                os.makedirs(temp_dir_audio)

            pdf_dir = temp_dir_pdf
            pdf_extension = ".pdf"
            input_file_base = os.path.splitext(os.path.basename(input_video_filename))[0]
            output_file = os.path.join(temp_dir_audio, input_file_base + ".mp3")
            pdf_file_path = os.path.join(pdf_dir, input_file_base + pdf_extension)

            pdf = FPDF()
            pdf.add_page()
            pdf.set_font('Arial', '', 12)
            print("Converting into Audio file...")
            clip = VideoFileClip(input_video_filename)
            clip.audio.write_audiofile(output_file)

            print("Found a Video File...")
            KEY_FILE_LOCATION = 'sanguine-air-278415-7b37f2b44fc0.json'
            FOLDER_ID = '1837ubsXatKw83DOQlYD7sdltSixslgjr'
            creds = Credentials.from_service_account_file(KEY_FILE_LOCATION, scopes=['https://www.googleapis.com/auth/drive'])
            service = build('drive', 'v3', credentials=creds)
            print("Audio to text is in progress...")
            result = pipe(output_file)
            Audio2Text = result['text']
            if len(result['text'].split()) > 200:
                text = result['text']
            else:
                text = "less_content"
            print("Audio to text Done...")

            write = pdf.write(5, Audio2Text)
            pdf.close()
            existing_files = service.files().list(q="name='" + input_file_base + pdf_extension + "' and trashed = false and '" + FOLDER_ID + "' in parents",fields="files(id)").execute().get('files', [])
            # if len(existing_files) > 0:
            #     print("NOTE : File with the same name already exists in the folder. Skipping upload.")
            # else:
            pdf.output(name=pdf_file_path, dest='F')
            with open(pdf_file_path, 'rb') as f:
                media = MediaIoBaseUpload(f, mimetype='application/pdf')
                pdf_file = service.files().create(
                    body={'name': input_file_base + pdf_extension, 'parents': [FOLDER_ID], 'mimeType': 'application/pdf'},
                    media_body=media,
                    fields='id'
                ).execute()
                file_id = pdf_file.get('id')
                file_url = f"https://drive.google.com/u/0/uc?id={file_id}&export=download"
                print(f"Uploaded PDF file to Google Drive: {file_url}")

            url="https://aig.theopeneyes.com/api/GenerateQuestions"
            # url="https://generate-questions.devbyopeneyes.com/api/GenerateQuestions"
            headers = {'Content-Type':'application/json','Accept':'application/json'}
            post_array ={
                        "id" : _id,
                        "pdf_file_result":result,
                        "pdf_file_path":file_url,
                        "pdf_file_status": "transcribed-text",
                        "status" :"Transcribing"
                    }
            status = requests.post(url,headers=headers,data=json.dumps(post_array))
        return text
    else:
        print("404 (Page not found...!)")
    
    
                