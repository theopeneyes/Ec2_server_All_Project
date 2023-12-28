import re
import itertools
import model_is 
import random

def boolean_single_statement(Text):
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
                item['question'] = "Find that below statement is True/False."
                item['question_type']="bool_fib"
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