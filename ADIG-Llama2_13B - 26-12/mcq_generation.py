import re
import itertools
import model_is 

def mcq(Text):
    mcq_by_LLM = []
    for index,item in enumerate(Text):
        if len(item)>100:
            prompt = "Generate as many as possible hard Multiple choice questions with four options and answer using this text:"+" "+item+'''\n Give me output in this JSON array format:[{"question": string, "options":List[string], "answer":string}]'''
            prompt_template=f'''[INST] <<SYS>>
            You are best in generating Multiple choice questions with demanded JSON format.
            <</SYS>>
            {prompt}[/INST]'''

            input_ids = model_is.tokenizer(prompt_template, return_tensors='pt').input_ids.cuda()
            output = model_is.model.generate(inputs=input_ids, temperature=0.1, top_p=0.9, max_new_tokens=768)
            op=model_is.tokenizer.decode(output[0])
            llm_output=op.split('[/INST]')[1].strip()


            prompt = llm_output+" \n for above text assign ranking score based on the quality of question to each question in terms of percentage varying from o% to 100%, you can use this text from which questions are generated as a reference, text:"+" "+item+'''\n Give me output in this JSON array format:[{"question": string, "options":List[string], "answer":string, "rank":string}]'''
            prompt_template=f'''[INST] <<SYS>>
            You are best in ranking Multiple choice questions based on quality of question. Generate output in demanded JSON format.
            <</SYS>>
            {prompt}[/INST]'''

            input_ids = model_is.tokenizer(prompt_template, return_tensors='pt').input_ids.cuda()
            output = model_is.model.generate(inputs=input_ids, temperature=0.1, top_p=0.9, max_new_tokens=768)
            op=model_is.tokenizer.decode(output[0])
            llm_output_2=op.split('[/INST]')[1].strip()
            mcq_by_LLM.append(llm_output_2)
        else:
            mcq_by_LLM.append('Questions are not generated due to shorter length')

    def extract_data(entry):
        question = entry.get("question", None)
        options = entry.get("options", None)
        answer = entry.get("answer", None)
        rank= entry.get("rank", None)
        return {"question": question, "options": options, "answer": answer, "rank":rank}

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
        question_dicts = [extract_data(entry) for entry in data_list if all(key in entry and entry[key] for key in ["question", "options", "answer", "rank"])]
        return question_dicts

    def flatten(list_of_lists):
        return list(itertools.chain.from_iterable(list_of_lists))

    def modify_answer_based_on_input(questions_list):
        for question in questions_list:
            answer = question['answer']
            options = question['options']
            if type(answer)!=bool:
                if answer.lower() == 'a':
                    question['answer'] = options[0]
                elif answer.lower() == 'b':
                    question['answer'] = options[1]
                elif answer.lower() == 'c':
                    question['answer'] = options[2]
                elif answer.lower() == 'd':
                    question['answer'] = options[3]
        for question in questions_list:
            answer = question['answer']
            options = question['options']
            if len(options)==2:
                for i in range(2):
                    options[i] = options[i].replace(f'{chr(65 + i)})', '').replace(f'{chr(65 + i)}.', '').replace(f'{chr(97+ i)}.', '').replace(f'{chr(97 + i)})', '').replace(f'{i + 1})', '').replace(f'{i + 1}.', '').strip()
            if len(options)==3:
                for i in range(3):
                    options[i] = options[i].replace(f'{chr(65 + i)})', '').replace(f'{chr(65 + i)}.', '').replace(f'{chr(97+ i)}.', '').replace(f'{chr(97 + i)})', '').replace(f'{i + 1})', '').replace(f'{i + 1}.', '').strip()
            if len(options)==4:
                for i in range(4):
                    options[i] = options[i].replace(f'{chr(65 + i)})', '').replace(f'{chr(65 + i)}.', '').replace(f'{chr(97+ i)}.', '').replace(f'{chr(97 + i)})', '').replace(f'{i + 1})', '').replace(f'{i + 1}.', '').strip()

            if type(answer) != bool:
                answer = answer.replace('A)', '').replace('a)', '').replace('A.', '').replace('a.', '').replace('1)', '').replace('1.', '').replace('B)', '').replace('b)', '').replace('B.', '').replace('b.', '').replace('2)', '').replace('2.', '').replace('C)', '').replace('c)', '').replace('C.', '').replace('c.', '').replace('3)', '').replace('3.', '').replace('D)', '').replace('d)', '').replace('D.', '').replace('d.', '').replace('4)', '').replace('4.', '').strip()
            question['answer']=answer
        return questions_list

    final_generated_questions = []
    for index,data in enumerate(mcq_by_LLM):
        llm_output = data.replace('\\', '').replace('\\n', '')   # replace all \n
        llm_output = ' '.join(llm_output.split())
        data_updated=process_data(llm_output)      # Use above process data function to extract dictionary elements from string output of LLM
        for item in data_updated:
            item['context']=None
            item['page_no']=int(index+1)
            item['statement']=None
            item['question_type']="mcq"
        final_generated_questions.append(data_updated)
    final_generated_questions=flatten(final_generated_questions)
    final_generated_questions=modify_answer_based_on_input(final_generated_questions)
    final_generated_questions=sorted(final_generated_questions, key=lambda x:(x['rank']), reverse=True)

    return final_generated_questions