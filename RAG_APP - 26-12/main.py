from openai import OpenAI
import streamlit as st
from langchain.callbacks import get_openai_callback     
from PIL import Image
import csv 
from datetime import datetime 

from langchain.agents import create_sql_agent
from langchain.agents.agent_toolkits import SQLDatabaseToolkit
from langchain.agents.agent_types import AgentType
from langchain.llms.openai import OpenAI
from langchain.sql_database import SQLDatabase

import streamlit as st

import os
from langchain.agents import *
from langchain.chat_models.openai import ChatOpenAI
from langchain.sql_database import SQLDatabase

from langchain.agents import create_sql_agent
from langchain.agents.agent_toolkits import SQLDatabaseToolkit

# from langchain.agents import AgentExecutor
from langchain.agents.agent_types import AgentType


os.environ['OPENAI_API_KEY'] = "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"

#local
# db_user = "root"
# db_password = ""
# db_host = "localhost"
# db_name = "gttac_uat_mk"
# db = SQLDatabase.from_uri(f"mysql+pymysql://{db_user}:{db_password}@{db_host}/{db_name}")

#server
db_user = "devbyo5_ragapp"
db_password = "LQ1JW}1J+!,p"
db_host = "devbyopeneyes.com"
db_name = "devbyo5_ragapp"
db = SQLDatabase.from_uri(f"mysql+pymysql://{db_user}:{db_password}@{db_host}/{db_name}",sample_rows_in_table_info=3)

# Page icon
icon = Image.open('GTTAC-logo.ico')

# Page config
st.set_page_config(page_title="GTTAC Bot",
                    page_icon=icon
                    # layout="wide"
                    )

st.header("Welcome to the GTTAC Bot")
st.info(f'You can ask questions based on Time Period, Location, Perpetrator’s Name, Target Locations, Weapons, and Tactics.  \n   \n   You can combine more than one attribute to get a specific answer.', icon="ℹ️")
st.warning('GTTAC Bot can make mistakes. Consider checking important information.', icon="⚠️")


client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

if "openai_model" not in st.session_state:
    st.session_state["openai_model"] = "gpt-3.5-turbo"

if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])



if prompt := st.chat_input("Enter your text here"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)


    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        # st.write("Welcome to the GTTAC Bot")
        full_response = ""


        agent_executor = create_sql_agent(
            llm = ChatOpenAI(model_name="gpt-3.5-turbo-1106",temperature=0, verbose=True),
            toolkit=SQLDatabaseToolkit(db=db, llm=ChatOpenAI(model_name="gpt-3.5-turbo-1106",temperature=0, verbose=True)),
            verbose=True,
            # agent_type=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
            agent_type=AgentType.OPENAI_FUNCTIONS,
            # suffix=custom_suffix,
            handle_parsing_errors=True,
            agent_executor_kwargs={"return_intermediate_steps": True}
            # view_support = True
            )

        with get_openai_callback() as cb:
            message = prompt
            messages=[
                {"role": m["role"], "content": m["content"]}
                for m in st.session_state.messages
            ],
            stream=True,
            # Set up the CSV file to store the data
            csv_file = "streamlit_sql_agent_test.csv"

            write_header = not os.path.exists(csv_file) or os.stat(csv_file).st_size == 0
            with open(csv_file, "a", newline="") as file:
                writer = csv.writer(file)
                if write_header:
                    # writer.writerow(["User Input Text","Generated SQL Query","Answer","Total Tokens Used", "Prompt Tokens", "Completion Tokens"])
                    writer.writerow(["Date-Time","User Input Text","Generated SQL Query","Answer","Total Tokens Used", "Prompt Tokens", "Completion Tokens", "Total Cost (USD)"])


                with st.spinner('generating response...'):
                    response = agent_executor(prompt)     
                    # storing current date and time 
                    current_date_time = datetime.now() 

                    tokens_used = cb.total_tokens
                    prompt_tokens = cb.prompt_tokens
                    completion_tokens = cb.completion_tokens
                    total_cost = cb.total_cost
            
                    for step in response["intermediate_steps"]:
                        
                        action = step[0].tool_input

                    user_input= response['input']
                    generated_sql_result = action 
                    final_answer = response['output'] 

                    # Write a row in the CSV file with the data
                    writer.writerow([current_date_time,user_input,generated_sql_result, final_answer,tokens_used, prompt_tokens, completion_tokens,total_cost])


        # for response in client.chat.completions.create(
        #     model=st.session_state["openai_model"],
            # messages=[
            #     {"role": m["role"], "content": m["content"]}
            #     for m in st.session_state.messages
            # ],
            # stream=True,
        # ):
            # full_response += (response.choices[0].delta.content or "")
                full_response = final_answer
                # st.write('11111111111',full_response)
                message_placeholder.markdown(full_response + "▌")
                message_placeholder.markdown(full_response)
                st.session_state.messages.append({"role": "assistant", "content": full_response})