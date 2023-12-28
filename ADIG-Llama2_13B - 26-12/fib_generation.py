import random
import re
import itertools
import model_is 

def fib(Text):
    mcq_by_LLM = []
    for index,item in enumerate(Text):
        prompt ="""Generate sentence prompts with placeholders, and for each placeholder, provide four alternative options and their corresponding correct answers using the following JSON format.
                    Please use this example only for your reference. Here is example for your reference:
                    [
                        {
                            "Prompt": string + __________,
                            "Options": List of options,
                            "Answer": string
                        }
                    ]
                    """ + item
        prompt_template=f'''[INST] <<SYS>>
        You are best in generating sentence prompts with placeholders with demanded JSON format.
        <</SYS>>
        {prompt}[/INST]'''

        input_ids = model_is.tokenizer(prompt_template, return_tensors='pt').input_ids.cuda()
        output = model_is.model.generate(inputs=input_ids, temperature=0.1, top_p=0.95,max_new_tokens=768) #1.0
        op=model_is.tokenizer.decode(output[0])
        llm_output=op.split('[/INST]')[1].strip()
        mcq_by_LLM.append(llm_output)

    mcq_by_LLM_2= []
    for index,item in enumerate(mcq_by_LLM):
        prompt = item+'''\n from above text give me output in this JSON array format:[{"Prompt":string, "Options":List[string], "Answer":string}]'''
        prompt_template=f'''[INST] <<SYS>>
        Generate output in demanded JSON format.
        <</SYS>>
        {prompt}[/INST]'''

        input_ids = model_is.tokenizer(prompt_template, return_tensors='pt').input_ids.cuda()
        output = model_is.model.generate(inputs=input_ids, temperature=0.1, top_p=0.95, max_new_tokens=768)
        op=model_is.tokenizer.decode(output[0])
        llm_output=op.split('[/INST]')[1].strip()
        mcq_by_LLM_2.append(llm_output)
    print("only_fib_by_LLM_2+_+_+_",mcq_by_LLM_2)
    def extract_data(entry):
        Prompt = entry.get("Prompt", None)
        Options = entry.get("Options", None)
        Answer = entry.get("Answer", None)
        return {"Prompt": Prompt, "Options": Options, "Answer": Answer}

    def process_data(data_string):
        data_string = re.sub(r'([{,])\s?([a-zA-Z_]+[a-zA-Z0-9_]*)\s?:', r'\1"\2":', data_string)
        data_string = re.sub(r'"(.*?)"', r'"\1"', data_string)
        data_list = []
        entries = re.findall(r"{.*?}", data_string)
        for entry in entries:
            try:
                data_list.append(eval(entry))
            except Exception as e:
                pass
        # question_dicts = [extract_data(entry) for entry in data_list if all(key in entry and entry[key] for key in ["question", "options", "answer"])]
        question_dicts = [extract_data(entry) for entry in data_list if all(key in entry and entry[key] for key in ["Prompt", "Options", "Answer"])]
        return question_dicts

    def flatten(list_of_lists):
        return list(itertools.chain.from_iterable(list_of_lists))

    def modify_answer_based_on_input(questions_list):
        for question in questions_list:
            answer = question['Answer']
            options = question['Options']
            if type(answer)!=bool:
                if answer.lower() == 'a':
                    question['Answer'] = options[0]
                elif answer.lower() == 'b':
                    question['Answer'] = options[1]
                elif answer.lower() == 'c':
                    question['Answer'] = options[2]
                elif answer.lower() == 'd':
                    question['Answer'] = options[3]
        for question in questions_list:
            answer = question['Answer']
            options = question['Options']
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
            question['Answer']=answer
        return questions_list

    final_generated_questions = []
    for index, data in enumerate(mcq_by_LLM_2):
        llm_output = data.replace('\\', '').replace('\\n', '')
        llm_output = ' '.join(llm_output.split())
        data_updated = process_data(llm_output)
        for item in data_updated:
            item['context'] = None
            item['page_no'] = int(index + 1)
            item['rank'] = None
            item['statement'] = None
            item['question_type'] = "fib"
        final_generated_questions.append(data_updated)
    final_generated_questions=flatten(final_generated_questions)
    final_generated_questions=modify_answer_based_on_input(final_generated_questions)

    # Renaming keys
    for i in final_generated_questions:
        i['question']=i.pop('Prompt')
        i['answer']=i.pop('Answer')

    # Use list comprehension to filter dictionaries
    final_generated_questions = [
        item for item in final_generated_questions if '_______' in item['question']
    ]

    # Define a function to remove the answer enclosed in parentheses
    def remove_answer_in_parentheses(question_dict):
        pattern = r'\([^)]*\)'  # Regular expression to match text within parentheses
        question_dict['question'] = re.sub(pattern, '', question_dict['question'])
        return question_dict

    # Remove answers in parentheses for each question in the list
    questions_list_cleaned = [remove_answer_in_parentheses(q) for q in final_generated_questions]

    # Define the question to remove
    question_to_remove = 'string + __________ '

    # Remove the specified question from the list
    final_generated_questions = [
        q for q in questions_list_cleaned if q['question'] != question_to_remove
    ]

    # Remove questions where the answer is 'all of the above' or 'none of the above'
    final_generated_questions = [question for question in final_generated_questions if question['answer'].lower() not in ['all of the above', 'none of the above']]


    # Remove "Option x: " prefix from options and square brackets from the question
    final_generated_questions = [
        {
            'question': item['question'].replace('[', '').replace(']', ''),
            **item
        }
        for item in final_generated_questions
    ]

    def find_blanks(final_generated_questions):
        pattern = r"_{2,}"
        new_list = []

        for item in final_generated_questions:
            matches = re.findall(pattern, item['question'])
            if len(matches) < 2:
                new_list.append(item)

        return new_list

    final_generated_questions = find_blanks(final_generated_questions)
    random.shuffle(final_generated_questions)

    return final_generated_questions