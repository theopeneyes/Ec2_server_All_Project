import random
import re
import model_is 
from functions import flatten,modify_answer_based_on_input

def fib_with_mcq(Text,fib_type,file_type):
    ''' Returns Fill in the blanks with options, answer and page number

    Parameters:
    Text(list): contain list of all required pages

    Returns:
    final fill in the blanks (list): contain list of dictionaries (each dictionary has blank, options, answer & page_number)

    Sample_output: [{'blank': 'Narendra Modi is the Prime Minister of _________. ',
                     'options':['Pakistan', 'Sri Lanka', 'Nepal', 'India']
                     'answer': 'India',
                     'page_no':int}] '''

    # Initiate empty list which contains fill in the blanks with options and answer in json format
    fib_by_LLM_2 = []
    for index,item in enumerate(Text):
        # check page length means text length in particular page
        if len(item)>100:

            # we will generate fill in the blanks along with options and answer in json format
            prompt ="""Generate sentence prompts with placeholders, and for each placeholder, provide four alternative options and their corresponding correct answers using the following JSON format.
                        Please use this example only for your reference. Here is example for your reference:
                        [
                            {
                                "Prompt": string + __________ ,
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
            output = model_is.model.generate(inputs=input_ids, temperature=0.1, top_p=0.95, max_new_tokens=768)
            op=model_is.tokenizer.decode(output[0])
            llm_output=op.split('[/INST]')[1].strip()

            # Major times we are not getting proper json formatted output from above prompt especially in fib so we are again formatting it in json
            prompt = llm_output+'''\n from above text give me output in this JSON array format:[{"Prompt":string, "Options":List[string], "Answer":string}]'''
            prompt_template=f'''[INST] <<SYS>>
            Generate output in demanded JSON format.
            <</SYS>>
            {prompt}[/INST]'''
            input_ids = model_is.tokenizer(prompt_template, return_tensors='pt').input_ids.cuda()
            output = model_is.model.generate(inputs=input_ids, temperature=0.1, top_p=0.95, max_new_tokens=768)
            op=model_is.tokenizer.decode(output[0])
            llm_output=op.split('[/INST]')[1].strip()
            fib_by_LLM_2.append(llm_output)

        # If page has short text length than will add below strings so that we will get exact page number
        else:
            fib_by_LLM_2.append("text lenght is small so not able to generate questions.")
    def extract_data(entry):
        # This function will return dictionary with all required keys
        Prompt = entry.get("Prompt", None)
        Options = entry.get("Options", None)
        Answer = entry.get("Answer", None)
        return {"Prompt": Prompt, "Options": Options, "Answer": Answer}

    def process_data(data_string):
        ''' Returns list with dictionaries as element

        Parameters:
        data_string(str): raw output from LLM

        Returns:
        question_dicts(list): contain list of dictionaries (each dictionary has blank, options and answer)
        '''
        # Enclose keys and values in double quotes
        data_string = re.sub(r'([{,])\s?([a-zA-Z_]+[a-zA-Z0-9_]*)\s?:', r'\1"\2":', data_string)
        data_string = re.sub(r'"(.*?)"', r'"\1"', data_string)
        data_list = []
        # Extract all dictionaries from string
        entries = re.findall(r"{.*?}", data_string)
        for entry in entries:
            try:
                # this line will convert all dictionary in valid json format
                data_list.append(eval(entry))
            except Exception as e:
                pass
        # once we have all required keys and values for fib with mcq question type we will get in list format
        question_dicts = [extract_data(entry) for entry in data_list if all(key in entry and entry[key] for key in ["Prompt", "Options", "Answer"])]
        return question_dicts

    # Here, we will take raw output of LLM and then clean it and apply above functions to get final_generated_questions
    final_generated_questions = []
    for index, data in enumerate(fib_by_LLM_2):
        llm_output = data.replace('\\', '').replace('\\n', '')
        llm_output = ' '.join(llm_output.split())
        # Use above process data function to extract dictionary elements from string output of LLM
        data_updated = process_data(llm_output)
        for item in data_updated:
            # Rename question, options and answer
            item['question']=item.pop('Prompt')
            item['options']=item.pop('Options')
            item['options'] = [option.capitalize() for option in item['options']]
            item['answer']=item.pop('Answer')
            item['answer'] = item['answer'].capitalize()
            item['page_no'] = int(index + 1)
            item['rank'] = None
            item['statement'] = None
            if file_type == "mp4":
                item['context']=Text[index]
            else:
                item['context']=None
            if fib_type=="mcq_fib":
                item['question_type'] = "mcq_fib"
            else:
                item['question_type'] = "fib"
        final_generated_questions.append(data_updated)
    final_generated_questions=flatten(final_generated_questions)
    final_generated_questions=modify_answer_based_on_input(final_generated_questions)
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
    question_to_remove = 'string + __________'

    # Remove the specified question from the list
    final_generated_questions = [
        q for q in questions_list_cleaned if q['question'] != question_to_remove
    ]

    # Remove "Option x: " prefix from options and square brackets from the question
    final_generated_questions = [
        {
            'question': item['question'].replace('[', '').replace(']', ''),
            'options': [option.split(': ')[1] if ': ' in option else option for option in item['options']],
            **item
        }
        for item in final_generated_questions
    ]

    def find_blanks(final_generated_questions):
        # In this function we will filter out those blanks which have more than 1 blank
        pattern = r"_{2,}"
        new_list = []

        for item in final_generated_questions:
            matches = re.findall(pattern, item['question'])
            # this condition will check if question has single blank then it should end with "."
            if len(matches) < 2:
                if item['question'].endswith('.'):
                    new_list.append(item)
                else:
                    item['question']=item['question']+'.'
                    new_list.append(item)

        return new_list

    # Remove questions where the answer is 'all of the above' or 'none of the above'
    if fib_type=="fib":
        final_generated_questions = [question for question in final_generated_questions if question['answer'].lower() not in ['all of the above', 'none of the above']]

    final_generated_questions = find_blanks(final_generated_questions)
    # we are shuffling questions so that we can display required and additional questions randomly
    random.shuffle(final_generated_questions)

    return final_generated_questions