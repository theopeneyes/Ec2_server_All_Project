import re
import itertools
from model_is import pipe
from model_is import flatten
def descriptive(Text):
    ''' Returns questions with descriptive answer and page number

    Parameters:
    Text(list): contain list of all required pages

    Returns:
    final descriptive (list): contain list of dictionaries (each dictionary has each question, descriptive answer, page_number)

    Sample_output: [{'question': 'Which factors are responsible for slowdown of Indian economy in 2020? ',
                     'answer': descriptive answer,
                     'page_no':int}] '''

    # Initiate empty list in which we append raw LLM output (descriptive questions)
    des_by_LLM = []
    for index,item in enumerate(Text):
         # check page length means text length in particular page
        if len(item)>100:
            messages = [
                {
                    "role": "system",
                    "content": "You are best in generating descriptive type of questions with demanded JSON format."
                },
                {"role": "user", "content": "generate descriptive type of questions with answer from text, text is,"+item+"""Arrange output in this JSON array format:[{"question": string,"answer": string}]"""
            }]
            prompt = pipe.tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
            outputs = pipe(prompt, max_new_tokens=786, do_sample=True, temperature=0.1, top_p=0.9)
            llm_output = outputs[0]["generated_text"]
            # # we will generate descriptive questions along with their answers in json format
            # prompt = "generate descriptive type of questions with answer from text, text is,"+item+"""Arrange output in this JSON array format:[{"question": string,"answer": string}]"""
            # prompt_template=f'''[INST] <<SYS>>
            # You are best in generating descriptive type of questions with demanded JSON format.
            # <</SYS>>
            # {prompt}[/INST]'''
            # input_ids = tokenizer(prompt_template, return_tensors='pt').input_ids.cuda()
            # output = model.generate(inputs=input_ids, temperature=0.1, top_p=0.95, max_new_tokens=768)
            # op=tokenizer.decode(output[0])
            # llm_output=op.split('[/INST]')[1].strip()

            messages = [
                {
                    "role": "system",
                    "content": "You are best in ranking descriptive type of questions based on quality of question. Generate output in demanded JSON format."
                },
                {"role": "user", "content": llm_output+" \n for above text assign ranking score based on the quality of question to each question in terms of percentage varying from o% to 100%, you can use this text from which questions are generated as a reference, text:"+" "+item+'''\n Give me output in this JSON array format:[{"question": string,"answer":string, "rank":string}]'''
            }]
            prompt = pipe.tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
            outputs = pipe(prompt, max_new_tokens=786, do_sample=True, temperature=0.1, top_p=0.9)
            llm_output_2 = outputs[0]["generated_text"]
            des_by_LLM.append(llm_output_2)
            # # once we have all generated descriptive questions from single page we will rank them as per their quality
            # prompt = llm_output+" \n for above text assign ranking score based on the quality of question to each question in terms of percentage varying from o% to 100%, you can use this text from which questions are generated as a reference, text:"+" "+item+'''\n Give me output in this JSON array format:[{"question": string,"answer":string, "rank":string}]'''
            # prompt_template=f'''[INST] <<SYS>>
            # You are best in ranking descriptive type of questions based on quality of question. Generate output in demanded JSON format.
            # <</SYS>>
            # {prompt}[/INST]'''
            # input_ids = tokenizer(prompt_template, return_tensors='pt').input_ids.cuda()
            # output = model.generate(inputs=input_ids, temperature=0.1, top_p=0.95, max_new_tokens=768)
            # op=tokenizer.decode(output[0])
            # llm_output_2=op.split('[/INST]')[1].strip()
            # des_by_LLM.append(llm_output_2)

        # If page has short text length than will add below strings so that we will get exact page number
        else:
            des_by_LLM.append("text lenght is small so not able to generate questions.")

    def extract_data(entry):
        # This function will return dictionary with all required keys
        question = entry.get("question", None)
        answer = entry.get("answer", None)
        rank= entry.get("rank", None)
        return {"question": question,"answer": answer, "rank":rank}

    def process_data(data_string):
        ''' Returns list with dictionaries as element

        Parameters:
        data_string(str): raw output from LLM

        Returns:
        question_dicts(list): contain list of dictionaries (each dictionary has each question, descriptive answer, rank)
        '''
        # Enclose keys and values in double quotes
        data_string = re.sub(r'([{,])\s?([a-zA-Z_]+[a-zA-Z0-9_]*)\s?:', r'\1"\2":', data_string)
        data_string = re.sub(r'"(.*?)"', r'"\1"', data_string)

        # Add double quotes around rank values
        data_string = re.sub(r'"rank"\s?:\s?(\d+)%', r'"rank":"\1%"', data_string)
        data_string = re.sub(r'"rank"\s?:\s?(\d+%?)', r'"rank":"\1"', data_string)
        data_string = re.sub(r'"rank"\s?:\s?"?(\d+)%"?', r'"rank":"\1"', data_string)

        data_list = []
        # using regex we will find all entries which enclosed in {}
        entries = re.findall(r"{.*?}", data_string)
        for entry in entries:
            try:
                # this line will convert all dictionary in valid json format
                data_list.append(eval(entry))
            except Exception as e:
                pass

        # once we have all required keys and values for descriptive question type we will get in list format
        question_dicts = [extract_data(entry) for entry in data_list if all(key in entry and entry[key] for key in ["question","answer", "rank"])]
        return question_dicts

    final_generated_questions = []
    for index,data in enumerate(des_by_LLM):
        llm_output = data.replace('\\', '').replace('\\n', '')   # replace all \n
        llm_output = ' '.join(llm_output.split())
        data_updated=process_data(llm_output)      # Use above process data function to extract dictionary elements from string output of LLM
        for item in data_updated:
            item['context']=None
            item['page_no']=int(index+1)
            item['statement']=None
            item['question_type']="wh"
        final_generated_questions.append(data_updated)

    # true_statement=postprocessing(des_by_LLM,"wh")
    final_generated_questions=flatten(final_generated_questions)
    # Sorting of final descriptive questions based on rank
    final_generated_questions=sorted(final_generated_questions, key=lambda x:(x['rank']), reverse=True)

    return final_generated_questions