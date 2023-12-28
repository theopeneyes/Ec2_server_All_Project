import re
import time

def get_time_from_video(result):
    time_range = []
    for i in result["chunks"]:
        # print("start-->",i["timestamp"][0],"end-->",i["timestamp"][1])
        # time_range.append({"start_time":i['start'],"end_time":i['end'],"text_is":i["text"].strip().split(" ")})
        start_time_is = time.strftime("%H:%M:%S", time.gmtime(i["timestamp"][0]))
        end_time_is = time.strftime("%H:%M:%S", time.gmtime(i["timestamp"][1]))
        time_range.append({"start_time":start_time_is,"end_time":end_time_is,"text_is":i["text"].strip().split(" ")})
    return time_range

def check_sequence_in_list(list1, list2):
    sequence_to_find = ''.join(map(str, list1))
    list_as_string = ''.join(map(str, list2))
    return sequence_to_find in list_as_string

def getListWithReference(time_list,question_list):
    for i in range(len(question_list)):
        time_lst = []
        contex = re.sub(r'\n+', '', question_list[i]["context"])
        contex=re.sub(r'\n +', '', contex)
        contex=contex.replace('\n\n','')
        context_list = contex.strip().split(" ")
        for j in range(len(time_list)):
            chunk_list = time_list[j]["text_is"]
            if len(chunk_list)>3:
                check = check_sequence_in_list(chunk_list,context_list)
                if check == True:
                    time_lst.append({"start_time_is":time_list[j]["start_time"],"end_time_is":time_list[j]["end_time"]})

        question_list[i]["ref_start_time"] = time_lst[0]['start_time_is']
        question_list[i]["ref_end_time"] = time_lst[-1]['end_time_is']
        question_list[i]["context"] = None

    return question_list