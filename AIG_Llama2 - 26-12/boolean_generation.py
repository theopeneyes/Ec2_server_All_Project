import re
import model_is 
from functions import final_boolean_statement

def Boolean_question(Text,file_type):
    ''' Returns Boolean questions with Yes/No answer

    Parameters:
    Text(list): contain list of all required pages

    Returns:
    final Boolean (list): contain list of dictionaries (each dictionary has each question, answer, page_number)

    Sample_output: [{'question': 'Was APJ Abdul Kalam Prime Minister of India from 2002 to 2007? ',
                     'answer': 'No',
                     'page_no':int}] '''

    # Initiate empty list which contains Yes answered questions
    Boolean_by_LLM_true = []
    # Initiate empty list which contains No answered questions
    Boolean_by_LLM_false = []

    for index,item in enumerate(Text):
        # check page length means text length in particular page
        if len(item)>100:
            # we will first generate all yes answered questions by prompt-engineering in json format
            prompt = "Please summarize the provided text and generate exclusively Boolean questions that strictly evaluate to Yes. The text is as follows: "+" "+item+'''Please Give me output Only in JSON format:[{"question": string,"answer": 'Yes'}]'''
            prompt_template=f'''[INST] <<SYS>>
            You are best in generating Yes/No Questions. You have to generate both yes and no Questions. For no Questions strictly change named entity or phrase of the Questions. Generate response as per demanded JSON format.
            <</SYS>>
            {prompt}[/INST]'''
            input_ids = model_is.tokenizer(prompt_template, return_tensors='pt').input_ids.cuda()
            output = model_is.model.generate(inputs=input_ids, temperature=0.1,top_p=0.95, max_new_tokens=768)
            op=model_is.tokenizer.decode(output[0])
            llm_output=op.split('[/INST]')[1].strip()
            Boolean_by_LLM_true.append(llm_output)

            # we will make all yes answered questions in no answered questions by changing named entity or phrase of the questions
            prompt = llm_output + '''From above text, make Questions false by changing any named entity or phrase.For making false Questions, please always keep one thing in mind that new named entity should be semantically near to old one.'''
            prompt_template=f'''[INST] <<SYS>>
            You are best in generating false Questions by changing named entity or phrase of the true Questions.Generate response as per demanded JSON format.
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
        question = entry.get("question", None)
        answer = entry.get("answer", None)
        return {"question": question , "answer": answer}

    def process_data(data_string):
        ''' Returns list with dictionaries as element

        Parameters:
        data_string(str): raw output from LLM

        Returns:
        question_dicts(list): contain list of dictionaries (each dictionary has each boolean question and answer)
        '''
        # using regex we will add double quotes around keys from LLM generated output
        data_string = re.sub(r'([{,])\s?([a-zA-Z_]+[a-zA-Z0-9_]*)\s?:', r'\1"\2":', data_string)
        # using regex we will confirm that all keys & values in json enclosed in double quotes
        data_string = re.sub(r'"(.*?)"', r'"\1"', data_string)
        data_list = []

        # Using regex we will find all entries which enclosed in {}
        entries = re.findall(r"{.*?}", data_string)
        for entry in entries:
            try:
                # This line will convert all dictionary in valid json format
                data_list.append(eval(entry))
            except Exception as e:
                pass

        # once we have all required keys and values for boolean question type we will get in list format
        question_dicts = [extract_data(entry) for entry in data_list if all(key in entry and entry[key] for key in ["question", "answer"])]
        return question_dicts

    def postprocessing(output_by_LLM):
        generated_questions = []
        for index,data in enumerate(output_by_LLM):
            llm_output = data.replace('\\', '').replace('\\n', '')
            data = ' '.join(llm_output.split())
            data_updated=process_data(data)
            for item in data_updated:
                item['page_no']=int(index+1)
                item['rank']=None
                item['question_type']="boolean"
                if file_type == "mp4":
                    item['context']=Text[index]
                else:
                    item['context']=None
            generated_questions.append(data_updated)
        return generated_questions

    true_statement=postprocessing(Boolean_by_LLM_true)
    false_statement=postprocessing(Boolean_by_LLM_false)
    final_generated_questions=final_boolean_statement(true_statement,false_statement)
    return final_generated_questions