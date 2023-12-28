from boolean_generation import Boolean_question
from mcq_generation import mcq
from descriptive_generation import descriptive
from multiple_boolean_generation import final_boolean_statement
from fib_generation import fib
from fib_mcq_generation import fib_with_mcq
from bool_fib_generation import boolean_single_statement

def getAllGeneratedQuestions(Text, type_of_question): 
    recommended_questions=[]
    additional_questions=[]

    for i in type_of_question:
        if i["question_type"] == "bool_statement":
            boolean_statement=final_boolean_statement(Text)
            req_ques=i["no_of_que"]
            recommended_questions.append(boolean_statement[:req_ques])
            additional_questions.append(boolean_statement[req_ques:])
        elif i["question_type"] == "boolean":
            boolean_questions=Boolean_question(Text)
            req_ques=i["no_of_que"]
            recommended_questions.append(boolean_questions[:req_ques])
            additional_questions.append(boolean_questions[req_ques:])
        elif i["question_type"] == "mcq":
            mcq_questions=mcq(Text)
            req_ques=i["no_of_que"]
            recommended_questions.append(mcq_questions[:req_ques])
            additional_questions.append(mcq_questions[req_ques:])
        elif i["question_type"] == "wh":
            des_ques=descriptive(Text)
            req_ques=i["no_of_que"]
            recommended_questions.append(des_ques[:req_ques])
            additional_questions.append(des_ques[req_ques:])
        elif i["question_type"] == "mcq_fib":
            fib_mcq=fib_with_mcq(Text)
            req_ques=i["no_of_que"]
            recommended_questions.append(fib_mcq[:req_ques])
            additional_questions.append(fib_mcq[req_ques:])
        elif i["question_type"] == "bool_fib":
            bool_fib=boolean_single_statement(Text)
            req_ques=i["no_of_que"]
            recommended_questions.append(bool_fib[:req_ques])
            additional_questions.append(bool_fib[req_ques:])
        elif i["question_type"] == "fib":
            fib_only=fib(Text)
            req_ques=i["no_of_que"]
            recommended_questions.append(fib_only[:req_ques])
            additional_questions.append(fib_only[req_ques:])
    print("recommended_questions----------",recommended_questions)
    print("additional_questions----------",additional_questions)
    return recommended_questions,additional_questions