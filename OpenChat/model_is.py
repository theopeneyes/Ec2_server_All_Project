# from transformers import AutoTokenizer, pipeline, logging
# from auto_gptq import AutoGPTQForCausalLM
from transformers import pipeline
import itertools
import random
local_folder = "openchat"

pipe = pipeline("text-generation", model=local_folder)

def flatten(list_of_lists):
    return list(itertools.chain.from_iterable(list_of_lists))

def final_boolean_statement(true_statement,false_statement):
    ''' Returns list with dictionaries (questions) as element

    Parameters:
    true_statement(list): contain list of dictionaries with true answered statements
    false_statement(list): contain list of dictionaries with false answered statements

    Returns:
    for each page we will take half of true_statement and half of false_statement and combine them
    '''
    final_list=[]
    for list_1,list_2 in zip(true_statement,false_statement):
        first_half_list1 = list_1[:len(list_1) // 2]
        second_half_list2 = list_2[len(list_2) // 2:]
        final_list.append(first_half_list1 + second_half_list2)
    final_list=flatten(final_list)
    random.shuffle(final_list)
    return final_list

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
            if len(options)==2:
                for i in range(2):
                    options[i] = options[i].replace(f'{chr(65 + i)})', '').replace(f'{chr(65 + i)}.', '').replace(f'{chr(97+ i)}.', '').replace(f'{chr(97 + i)})', '').replace(f'{i + 1})', '').replace(f'{i + 1}.', '').strip()
            if len(options)==3:
                for i in range(3):
                    options[i] = options[i].replace(f'{chr(65 + i)})', '').replace(f'{chr(65 + i)}.', '').replace(f'{chr(97+ i)}.', '').replace(f'{chr(97 + i)})', '').replace(f'{i + 1})', '').replace(f'{i + 1}.', '').strip()
            if len(options)==4:
                for i in range(4):
                    options[i] = options[i].replace(f'{chr(65 + i)})', '').replace(f'{chr(65 + i)}.', '').replace(f'{chr(97+ i)}.', '').replace(f'{chr(97 + i)})', '').replace(f'{i + 1})', '').replace(f'{i + 1}.', '').strip()

            # This condition will check if answer has A, B, C ,D or 1,2,3,4 in the beginning then it will remove it
            if type(question['answer']) != bool:
                question['answer'] = question['answer'].replace('A)', '').replace('a)', '').replace('A.', '').replace('a.', '').replace('1)', '').replace('1.', '').replace('B)', '').replace('b)', '').replace('B.', '').replace('b.', '').replace('2)', '').replace('2.', '').replace('C)', '').replace('c)', '').replace('C.', '').replace('c.', '').replace('3)', '').replace('3.', '').replace('D)', '').replace('d)', '').replace('D.', '').replace('d.', '').replace('4)', '').replace('4.', '').strip()
            # question['answer']=answer
        return questions_list
    except Exception as e:
        print(e)
        return questions_list