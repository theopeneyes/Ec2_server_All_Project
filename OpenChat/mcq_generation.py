import re
import itertools
from model_is import pipe 

def mcq(Text):
    ''' Returns multiple choice questions with corresponding options , answer, page_number and rank

    Parameters:
    Text(list): contain list of all required pages

    Returns:
    final mcq (list): contain list of dictionaries (each dictionary has each question, options, answer, page_number)

    Sample_output: [{'question': 'Who is the Prime minister of India?',
                     'options': ['Pakistan', 'Nepal', 'India', 'China'],
                     'answer': 'India',
                     'page_no':int}] '''
    mcq_by_LLM = []
    for index,item in enumerate(Text):
        # check page length means text length in particular page
        if len(item)>100:

            messages = [
                {
                    "role": "system",
                    "content": "You are best in generating Multiple choice questions with demanded JSON format."
                },
                {"role": "user", "content": "Generate as many as possible hard Multiple choice questions with four options and answer using this text:"+" "+item+'''\n Give me output in this JSON array format:[{"question": string, "options":List[string], "answer":string}]'''},
            ]
            prompt = pipe.tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
            outputs = pipe(prompt, max_new_tokens=786, do_sample=True, temperature=0.1, top_p=0.9)
            llm_output = outputs[0]["generated_text"]

            messages = [
                    {
                        "role": "system",
                        "content": "You are best in generating Multiple choice questions with demanded JSON format.",
                    },
                    {"role": "user", "content": llm_output+" \n for above text assign ranking score based on the quality of question to each question in terms of percentage varying from o% to 100%, you can use this text from which questions are generated as a reference, text:"+" "+item+'''\n Give me output in this JSON array format:[{"question": string, "options":List[string], "answer":string, "rank":string}]'''
                        }]
            prompt = pipe.tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
            outputs = pipe(prompt, max_new_tokens=786, do_sample=True, temperature=0.1, top_p=0.9)
            llm_output_2 = outputs[0]["generated_text"]

            mcq_by_LLM.append(llm_output_2)

        # If page has short text length than will add below strings so that we will get exact page number
        else:
            mcq_by_LLM.append('Questions are not generated due to shorter length')

    def extract_data(entry):
        # This function will return dictionary with all required keys
        question = entry.get("question", None)
        options = entry.get("options", None)
        answer = entry.get("answer", None)
        rank= entry.get("rank", None)
        return {"question": question, "options": options, "answer": answer, "rank":rank}

    def process_data(data_string):
        ''' Returns list with dictionaries as element

        Parameters:
        data_string(str): raw output from LLM

        Returns:
        question_dicts(list): contain list of dictionaries (each dictionary has each question, options, answer, rank)
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

        # once we have all required keys and values for mcq question type we will get in list format
        question_dicts = [extract_data(entry) for entry in data_list if all(key in entry and entry[key] for key in ["question", "options", "answer", "rank"])]
        return question_dicts
    
    def flatten(list_of_lists):
        return list(itertools.chain.from_iterable(list_of_lists))

    def modify_answer_based_on_input(questions_list):
        ''' Returns questions list with modified answer and options

        Parameters:
        questions_list(list): We will check each dictionary's options and answer and modify it.'''
        try:
            for question in questions_list:
                answer = question['answer']
                options = question['options']

                # This condition will check if answer has onlhy a,b,c or d then will return answer as actual text string
                if type(answer)!=bool:
                    if answer.lower() == 'a':
                        question['answer'] = options[0]
                    elif answer.lower() == 'b':
                        question['answer'] = options[1]
                    elif answer.lower() == 'c':
                        question['answer'] = options[2]
                    elif answer.lower() == 'd':
                        question['answer'] = options[3]
                # This condition will check if options has A, B, C ,D or 1,2,3,4 in the beginning then it will remove it
                elif len(options)==2:
                    for i in range(2):
                        options[i] = options[i].replace(f'{chr(65 + i)})', '').replace(f'{chr(65 + i)}.', '').replace(f'{chr(97+ i)}.', '').replace(f'{chr(97 + i)})', '').replace(f'{i + 1})', '').replace(f'{i + 1}.', '').strip()
                elif len(options)==3:
                    for i in range(3):
                        options[i] = options[i].replace(f'{chr(65 + i)})', '').replace(f'{chr(65 + i)}.', '').replace(f'{chr(97+ i)}.', '').replace(f'{chr(97 + i)})', '').replace(f'{i + 1})', '').replace(f'{i + 1}.', '').strip()
                elif len(options)==4:
                    for i in range(4):
                        options[i] = options[i].replace(f'{chr(65 + i)})', '').replace(f'{chr(65 + i)}.', '').replace(f'{chr(97+ i)}.', '').replace(f'{chr(97 + i)})', '').replace(f'{i + 1})', '').replace(f'{i + 1}.', '').strip()

                # This condition will check if answer has A, B, C ,D or 1,2,3,4 in the beginning then it will remove it
                elif type(question['answer']) != bool:
                    question['answer'] = question['answer'].replace('A)', '').replace('a)', '').replace('A.', '').replace('a.', '').replace('1)', '').replace('1.', '').replace('B)', '').replace('b)', '').replace('B.', '').replace('b.', '').replace('2)', '').replace('2.', '').replace('C)', '').replace('c)', '').replace('C.', '').replace('c.', '').replace('3)', '').replace('3.', '').replace('D)', '').replace('d)', '').replace('D.', '').replace('d.', '').replace('4)', '').replace('4.', '').strip()
                # question['answer']=answer
            return questions_list
        except Exception as e:
            print(e)
            return questions_list

    # Here, we will take raw output of LLM and then clean it and apply above functions to get final_generated_questions
    final_generated_questions = []
    for index,data in enumerate(mcq_by_LLM):
        llm_output = data.replace('\\', '').replace('\\n', '')   # replace all \n
        llm_output = ' '.join(llm_output.split())
        # Use above process data function to extract dictionary elements from string output of LLM
        data_updated=process_data(llm_output)

        for item in data_updated:
            item['context']=None
            item['page_no']=int(index+1)
            item['statement']=None
            item['question_type']="mcq"
            item['options'] = [option.capitalize() for option in item['options']]
            item['answer'] = item['answer'].capitalize()
        final_generated_questions.append(data_updated)
    final_generated_questions=flatten(final_generated_questions)

    # Apply modify_answer_based_on_input function to get cleaned options and answer
    final_generated_questions=modify_answer_based_on_input(final_generated_questions)

    # Sorting of final MCQ based on rank
    final_generated_questions=sorted(final_generated_questions, key=lambda x:(x['rank']), reverse=True)
    return final_generated_questions