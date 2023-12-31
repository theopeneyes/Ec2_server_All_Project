import re
import model_is 
import random

from functions import final_boolean_statement

def boolean_multiple_statement(Text, boolean_type,file_type):
    ''' Returns boolean statements page wise

    Parameters:
    Text(list): contain list of all required pages
    boolean_type(string): contain type of boolean statement single or multiple

    Returns:
    final boolean statement (list): contain list of dictionaries (each dictionary has each question, statement, answer, page_number)

    Sample_output_1: [{'question': 'Find True/False statements from the below statements',
                     'statement': ['statement_1', 'statement_2', 'statement_3', 'statement_4'],
                     'answer': [{'1':'True/False', '2':'True/False', '3':'True/False', '4':'True/False'}],
                     'page_no':int}]

    Sample_output_2: [{'question': 'Find that below statement is True/False.',
                       'statement': string,
                       'answer': 'True/False',
                       'page_no':int }]

    Sample_output_1 is for multiple boolean statements
    Sample_output_2 is for single boolean statement
                     '''

    # Initiate empty list which contains true answered statements
    Boolean_by_LLM_true = []
    # Initiate empty list which contains false answered statements
    Boolean_by_LLM_false = []

    for index,item in enumerate(Text):
        # check page length means text length in particular page
        if len(item)>100:

            # we will first generate all true answered statements by prompt-engineering in json format
            prompt = "Given the following text, please summarize it and provide only true statements :"+" "+item+'''Please Give me output Only in JSON format:[{"statement": string,"answer": 'True'}]'''
            prompt_template=f'''[INST] <<SYS>>
            You are best in generating true/false statements. You have to generate both true and false statements. For false statements strictly change named entity or phrase of the statement. Generate response as per demanded JSON format.
            <</SYS>>
            {prompt}[/INST]'''
            input_ids = model_is.tokenizer(prompt_template, return_tensors='pt').input_ids.cuda()
            output = model_is.model.generate(inputs=input_ids, temperature=0.1,top_p=0.95, max_new_tokens=768)
            op=model_is.tokenizer.decode(output[0])
            llm_output=op.split('[/INST]')[1].strip()
            Boolean_by_LLM_true.append(llm_output)

            # Here, we will make all true answered statements false by changing named entity or phrase
            prompt = llm_output + '''From above text, make statements false by changing any named entity or phrase.For making false statements, please always keep one thing in mind that new named entity should be semantically near to old one.'''
            prompt_template=f'''[INST] <<SYS>>
            You are best in generating false statement by changing named entity or phrase of the true statement.Generate response as per demanded JSON format.
            <</SYS>>
            {prompt}[/INST]'''
            input_ids = model_is.tokenizer(prompt_template, return_tensors='pt').input_ids.cuda()
            output = model_is.model.generate(inputs=input_ids, temperature=0.1,top_p=0.95, max_new_tokens=768)
            op=model_is.tokenizer.decode(output[0])
            llm_output_2=op.split('[/INST]')[1].strip()
            Boolean_by_LLM_false.append(llm_output_2)

        # If page has short text length than will add below strings so that we will get exact page number
        else:
            Boolean_by_LLM_true.append('Questions are not generated due to shorter length')
            Boolean_by_LLM_false.append('Questions are not generated due to shorter length')

    def extract_data(entry):
        # This function will return dictionary with all required keys
        statement = entry.get("statement", None)
        answer = entry.get("answer", None)
        return {"statement": statement , "answer": answer}

    def process_data(data_string):
        ''' Returns list with dictionaries as element

        Parameters:
        data_string(str): raw output from LLM

        Returns:
        question_dicts(list): contain list of dictionaries (each dictionary has each statement & answer)
        '''
        # using regex we will add double quotes around keys from LLM generated output
        data_string = re.sub(r'([{,])\s?([a-zA-Z_]+[a-zA-Z0-9_]*)\s?:', r'\1"\2":', data_string)
        # using regex we will confirm that all keys & values in json enclosed in double quotes
        data_string = re.sub(r'"(.*?)"', r'"\1"', data_string)
        data_list = []
        # using regex we will find all entries which enclosed in {}
        entries = re.findall(r"{.*?}", data_string)
        for entry in entries:
            try:
                # this line will convert all dictionary in valid json format
                data_list.append(eval(entry))
            except Exception as e:
                pass
        # once we have all required keys and values for question type we will get in list format
        question_dicts = [extract_data(entry) for entry in data_list if all(key in entry and entry[key] for key in ["statement", "answer"])]
        return question_dicts

    def postprocessing(output_by_LLM):
        ''' Returns list with dictionaries (questions) as element

        Parameters:
        output_by_LLM(list): raw output from LLM

        Returns:
        generated_questions(list): contain list of dictionaries (each dictionary has statement , answer, page_number & question type)
        '''
        generated_questions = []
        for index,data in enumerate(output_by_LLM):
            llm_output = data.replace('\\', '').replace('\\n', '')
            data = ' '.join(llm_output.split())
            data_updated=process_data(data)
            for item in data_updated:
                item['page_no']=int(index+1)
                item['rank']=None
                if file_type == "mp4":
                    item['context']=Text[index]
                else:
                    item['context']=None
                if boolean_type=="bool_statement":
                    item['question_type']="bool_statement"
                else:
                    item['question'] = "Find that below statement is True/False."
                    item['question_type']="bool_fib"
            generated_questions.append(data_updated)
        return generated_questions

    true_statement=postprocessing(Boolean_by_LLM_true)
    false_statement=postprocessing(Boolean_by_LLM_false)
    final_generated_questions__=final_boolean_statement(true_statement,false_statement)

    # check which type of boolean statement it is whether it's multiple or single
    if boolean_type=="bool_statement":

        # Following code will arrange all statements page wise means all statements belong to same page will combine (maximum 4 and minimum 2)
        groups = {}
        for item in final_generated_questions__:
            # create page_no as key and append corresponding statements with their relevant answers
            if item['page_no'] in groups:
                groups[item['page_no']].append({'statement': item['statement'], 'answer': item['answer']})
            else:
                groups[item['page_no']] = [{'statement': item['statement'], 'answer': item['answer']}]

        final_generated_questions = []
        for page, statements in groups.items():
            # For each page if number of statements between 1& 4 , append it to final_generated_questions
            num_statements = len(statements)
            if num_statements <= 4  and num_statements >1:
                final_generated_questions.append({'question':' Find True statements from the below.','statement': [s['statement'] for s in statements], 'answer': [s['answer'] for s in statements], 'page_no': page,'context':None,'rank':None,'question_type':'bool_statement'})

            # if page has more than 4 statemnets then group it max to 4 and min to 2 , then append it to final_generated_questions
            else:
                num_groups = (num_statements // 4) + 1
                for i in range(num_groups):
                    start_index = i*4
                    end_index = start_index + 4
                    group_statements = statements[start_index:end_index]
                    if len(group_statements) >= 2:
                        final_generated_questions.append({'question':' Find True statements from the below.','statement': [s['statement'] for s in group_statements], 'answer': [s['answer'] for s in group_statements], 'page_no': page,'context':None,'rank':None,'question_type':'bool_statement'})

        # mapping each statement to its relevant answer and return as dictionary in answer key
        for item in final_generated_questions:
            len_of_sen = len(item['statement'])
            answer_dict = [{i + 1: answer for i, answer in enumerate(item['answer'])}]
            for index, dictionary in enumerate(answer_dict):
                true_answer = [key for key, value in dictionary.items() if value == 'True']
                if len(true_answer) == 1:
                    true_answer = true_answer
                else:
                    if len(true_answer) > 0:
                        true_answer = [f"{', '.join(map(str, true_answer[:-1]))} and {true_answer[-1]}"]
                def generate_random_list(existing_options,len_of_sen):
                    """
                    Function to generate a random list with unique values and permutations
                    """
                    new_option = random.sample(range(1, len_of_sen+1), random.randint(1, len_of_sen-1))
                    while sorted(new_option) == sorted(true_answer) or sorted(new_option) in [sorted(opt) for opt in existing_options]:
                        new_option = random.sample(range(1, len_of_sen+1), random.randint(1, len_of_sen-1))
                    return new_option

                # List to store generated options
                option_list = []
                option_list = [generate_random_list(option_list,len_of_sen) for _ in range(2)]

                # Randomly choose between "All of the above" and "None of the above"
                replacement = random.choice(["All of the above", "None of the above"])

                # Check if "All of the above" is chosen and the true answer has 4 options
                if replacement == "All of the above" and len(true_answer) == 4:
                    true_answer = "All of the above"
                    option_list.append(generate_random_list(option_list,len_of_sen))
                    option_list.append(true_answer)
                else:
                    option_list.extend([true_answer, replacement])

                # Shuffle the option list
                random.shuffle(option_list)
            output = []
            for sublist in option_list:
                if len(sublist) <= 4:
                    if len(sublist) == 1:
                        output.append(sublist)
                    else:
                        if len(true_answer) > 0:
                            formatted_sublist = [f"{', '.join(map(str, sublist[:-1]))} and {sublist[-1]}"]
                            output.append(formatted_sublist)
                else:
                    output.append([sublist])

            index = option_list.index(true_answer)
            item['answer'] = str(index + 1) + ":" + str(true_answer)
            item['options'] = output
        return final_generated_questions

    else:
        def add_full_stop(final_generated_questions__):
            updated_statements_list = []
            for item in final_generated_questions__:
                item['statement'] = item['statement'].rstrip('.')
                statement = item['statement'] + ' __________ .'
                item['statement'] = [statement]
                updated_statements_list.append(item)
            return updated_statements_list

        final_generated_questions = add_full_stop(final_generated_questions__)
        return final_generated_questions