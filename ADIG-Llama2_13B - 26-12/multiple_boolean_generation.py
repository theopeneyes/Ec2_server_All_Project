import re
import itertools
import model_is 
import random

def final_boolean_statement(Text):
    Boolean_by_LLM_true = []
    Boolean_by_LLM_false = []

    for index,item in enumerate(Text):
        if len(item)>100:
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
        else:
            Boolean_by_LLM_true.append('Questions are not generated due to shorter length')
            Boolean_by_LLM_false.append('Questions are not generated due to shorter length')    

    def extract_data(entry):
        statement = entry.get("statement", None)
        answer = entry.get("answer", None)
        return {"statement": statement , "answer": answer}

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
        question_dicts = [extract_data(entry) for entry in data_list if all(key in entry and entry[key] for key in ["statement", "answer"])]
        return question_dicts

    def postprocessing(output_by_LLM):
        generated_questions = []
        for index,data in enumerate(output_by_LLM):
            llm_output = data.replace('\\', '').replace('\\n', '')
            data = ' '.join(llm_output.split())
            data_updated=process_data(data)
            for item in data_updated:
                item['page_no']=int(index+1)
                item['context']=None
                item['rank']=None
                item['question_type']="bool_statement"
            generated_questions.append(data_updated)
        return generated_questions

    def flatten(list_of_lists):
        return list(itertools.chain.from_iterable(list_of_lists))

    def final_boolean_statement(true_statement,false_statement):
        final_list=[]
        for list_1,list_2 in zip(true_statement,false_statement):
            first_half_list1 = list_1[:len(list_1) // 2]
            second_half_list2 = list_2[len(list_2) // 2:]
            final_list.append(first_half_list1 + second_half_list2)
        final_list=flatten(final_list)
        random.shuffle(final_list)
        return final_list

    true_statement=postprocessing(Boolean_by_LLM_true)
    false_statement=postprocessing(Boolean_by_LLM_false)
    final_generated_questions__=final_boolean_statement(true_statement,false_statement)

    groups = {}
    for item in final_generated_questions__:
        if item['page_no'] in groups:
            groups[item['page_no']].append({'statement': item['statement'], 'answer': item['answer']})
        else:
            groups[item['page_no']] = [{'statement': item['statement'], 'answer': item['answer']}]
    final_generated_questions = []
    for page, statements in groups.items():
        num_statements = len(statements)
        if num_statements <= 4  and num_statements >1:
            final_generated_questions.append({'question':'Find True/False statements from the below statements','statement': [s['statement'] for s in statements], 'answer': [s['answer'] for s in statements], 'page_no': page,'context':None,'rank':None,'question_type':'bool_statement'})
        else:
            num_groups = (num_statements // 4) + 1
            for i in range(num_groups):
                start_index = i*4
                end_index = start_index + 4
                group_statements = statements[start_index:end_index]
                if len(group_statements) >= 2:
                    final_generated_questions.append({'question':'Find True/False statements from the below statements','statement': [s['statement'] for s in group_statements], 'answer': [s['answer'] for s in group_statements], 'page_no': page,'context':None,'rank':None,'question_type':'bool_statement'})

    return final_generated_questions