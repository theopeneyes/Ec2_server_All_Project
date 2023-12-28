import time
from urllib import response
import requests
import json
from datetime import datetime,date
from fastapi import FastAPI, HTTPException
from question_generation import getAllGeneratedQuestions
from text import getText,flatten
from fastapi.responses import JSONResponse
from references import getListWithReference,get_time_from_video
import torch
torch.cuda.empty_cache()

app = FastAPI(debug=False)   

@app.get("/getQuestions/{user_id}")
def AIG(user_id):
    # try:
    start_process = time.time()
    request=requests.get("https://aig.theopeneyes.com/api/getFileData/" + user_id)
    resp = request.json()
    file_type = (resp["data"]["file_type"])
    result = None
    if file_type != "mp4":
        file_type, final,text_content, type_of_question, _id= getText(user_id)
        if text_content == "empty_file":
            status_url = "https://aig.theopeneyes.com/api/updateFileStatus"
            # status_url = "https://generate-questions.devbyopeneyes.com/api/updateFileStatus"
            headers = {'Content-Type':'application/json','Accept':'application/json'}
            status_array ={
                    "id" : _id,
                    "status" : "Error"
                    }
            print("status updated : ",status_array)
            status = requests.post(status_url,headers=headers,data=json.dumps(status_array))
            emptyfileerrorMsg = "Your file is empty so questions are not generated please insert file with content"
            detail_dict = {"code":403,"message":emptyfileerrorMsg}
            detail_message = json.dumps(detail_dict, indent = 4)
            raise HTTPException(403,detail_message)
        
        elif text_content == "less_content" :
            status_url = "https://aig.theopeneyes.com/api/updateFileStatus"
            # status_url = "https://generate-questions.devbyopeneyes.com/api/updateFileStatus"
            headers = {'Content-Type':'application/json','Accept':'application/json'}
            status_array ={
                    "id" : _id,
                    "status" : "Error"
                    }
            print("status updated : ",status_array)
            status = requests.post(status_url,headers=headers,data=json.dumps(status_array))
            lessConErrorMsg = "Given video or Image has Less content..!"
            detail_dict = {"code":403,"message":lessConErrorMsg}
            detail_message = json.dumps(detail_dict, indent = 4)
            raise HTTPException(403,detail_message)
        
        recommended_questions,additional_questions = getAllGeneratedQuestions(final, type_of_question,file_type)
        user_required_questions = flatten(recommended_questions)
        other_questions = flatten(additional_questions)
    else:
        file_type, final,text_content, type_of_question, _id= getText(user_id)
        result = (resp["data"]["pdf_file_result"])
        recommended_questions,additional_questions = getAllGeneratedQuestions(final, type_of_question,file_type)
        user_required_questions = flatten(recommended_questions)
        other_questions = flatten(additional_questions)

        user_required_questions = getListWithReference(get_time_from_video(result),user_required_questions)
        other_questions = getListWithReference(get_time_from_video(result),other_questions)

    if len(user_required_questions)==0 and len(other_questions)==0:
        # user_required_questions=[{'question':"None",'options':"None",'answer':"None"}]
        # other_questions=[{'question':"None",'options':"None",'answer':"None"}]
        status_url = "https://aig.theopeneyes.com/api/updateFileStatus"
        # status_url = "https://generate-questions.devbyopeneyes.com/api/updateFileStatus"
        headers = {'Content-Type':'application/json','Accept':'application/json'}
        status_array ={
                "id" : _id,
                "status" : "Error"
                }
        print("status updated : ",status_array)
        status = requests.post(status_url,headers=headers,data=json.dumps(status_array))
        lessConErrorMsg = "Questions are not generated."
        detail_dict = {"code":403,"message":lessConErrorMsg}
        detail_message = json.dumps(detail_dict, indent = 4)
        raise HTTPException(403,detail_message)
    else:
        if file_type=="pdf":
            for question_index, question in enumerate(user_required_questions):
                question["question_id"]= question_index +1

            for question_index, question in enumerate(other_questions):
                question["question_id"]= question_index +1

        else:
            for question_index, question in enumerate(user_required_questions):
                question["question_id"]= question_index +1
                question["page_no"]="None"

            for question_index, question in enumerate(other_questions):
                question["question_id"]= question_index +1
                question["page_no"]="None"

        total_len_question=len(flatten(recommended_questions)+flatten(additional_questions))    
        end_process = time.time()
        total_time = datetime.fromtimestamp(end_process) - datetime.fromtimestamp(start_process)

        generated_date = date.today()
        url = "https://aig.theopeneyes.com/api/GenerateQuestions"
        # url="https://generate-questions.devbyopeneyes.com/api/GenerateQuestions"
        headers = {'Content-Type':'application/json','Accept':'application/json'}
        post_array ={
                    "id" : _id,
                    "questions" : user_required_questions,
                    "other_questions" : other_questions,
                    "upload_process_time": str(total_time),
                    "generate_date": str(generated_date),
                    "no_of_question_generate":str(total_len_question),
                    "pdf_file_result":result,
                    # "pdf_file_path":file_url,
                    "status": "Completed"
                }    
        status = requests.post(url,headers=headers,data=json.dumps(post_array))
        successfull_msg = {"code":200,"message":"Your Questions are generated successfully..."}
        return JSONResponse(content=successfull_msg)
        
        # except Exception as e:
        #     # error_status_url = "https://aig.theopeneyes.com/api/updateFileStatus"
        #     error_status_url = "https://generate-questions.devbyopeneyes.com/api/updateFileStatus"
        #     error_headers = {'Content-Type': 'application/json', 'Accept': 'application/json'}
        #     error_status_array = {
        #         "id": _id,
        #         "status": "Error",
        #         "error_message": str(e)
        #     }
        #     error_status = requests.post(error_status_url, headers=error_headers, data=json.dumps(error_status_array))

