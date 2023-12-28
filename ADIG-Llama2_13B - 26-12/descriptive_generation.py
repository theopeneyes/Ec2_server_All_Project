import re
import itertools
import model_is 

def descriptive(Text):
    des_by_LLM = []
    for index,item in enumerate(Text):
        if len(item)>100:
            prompt = "generate descriptive type of questions with answer from text, text is,"+item+"""Arrange output in this JSON array format:[{"question": string,"answer": string}]"""
            prompt_template=f'''[INST] <<SYS>>
            You are best in generating descriptive type of questions with demanded JSON format.
            <</SYS>>
            {prompt}[/INST]'''

            input_ids = model_is.tokenizer(prompt_template, return_tensors='pt').input_ids.cuda()
            output = model_is.model.generate(inputs=input_ids, temperature=0.1, top_p=0.95, max_new_tokens=768)
            op=model_is.tokenizer.decode(output[0])
            llm_output=op.split('[/INST]')[1].strip()

            prompt = llm_output+" \n for above text assign ranking score based on the quality of question to each question in terms of percentage varying from o% to 100%, you can use this text from which questions are generated as a reference, text:"+" "+item+'''\n Give me output in this JSON array format:[{"question": string,"answer":string, "rank":string}]'''
            prompt_template=f'''[INST] <<SYS>>
            You are best in ranking descriptive type of questions based on quality of question. Generate output in demanded JSON format.
            <</SYS>>
            {prompt}[/INST]'''

            input_ids = model_is.tokenizer(prompt_template, return_tensors='pt').input_ids.cuda()
            output = model_is.model.generate(inputs=input_ids, temperature=0.1, top_p=0.95, max_new_tokens=768)
            op=model_is.tokenizer.decode(output[0])
            llm_output_2=op.split('[/INST]')[1].strip()
            des_by_LLM.append(llm_output_2)

        else:
            des_by_LLM.append("text lenght is small so not able to generate questions.")

    def extract_data(entry):
        question = entry.get("question", None)
        answer = entry.get("answer", None)
        rank= entry.get("rank", None)
        return {"question": question,"answer": answer, "rank":rank}

    def process_data(data_string):
        # Enclose keys and values in double quotes
        data_string = re.sub(r'([{,])\s?([a-zA-Z_]+[a-zA-Z0-9_]*)\s?:', r'\1"\2":', data_string)
        data_string = re.sub(r'"(.*?)"', r'"\1"', data_string)

        # Add double quotes around rank values

        data_string = re.sub(r'"rank"\s?:\s?(\d+)%', r'"rank":"\1%"', data_string)
        data_string = re.sub(r'"rank"\s?:\s?(\d+%?)', r'"rank":"\1"', data_string)
        data_string = re.sub(r'"rank"\s?:\s?"?(\d+)%"?', r'"rank":"\1"', data_string)


        data_list = []
        entries = re.findall(r"{.*?}", data_string)
        for entry in entries:
            try:
                data_list.append(eval(entry))
            except Exception as e:
                pass
        question_dicts = [extract_data(entry) for entry in data_list if all(key in entry and entry[key] for key in ["question","answer", "rank"])]
        return question_dicts

    def flatten(list_of_lists):
        return list(itertools.chain.from_iterable(list_of_lists))

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
    final_generated_questions=flatten(final_generated_questions)
    final_generated_questions=sorted(final_generated_questions, key=lambda x:(x['rank']), reverse=True)

    return final_generated_questions