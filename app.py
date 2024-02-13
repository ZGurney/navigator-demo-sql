import os
#from dotenv import load_dotenv
from pathlib import Path

import streamlit as st

from langchain import hub
from langchain.agents import AgentExecutor, Tool, create_react_agent
from langchain.chains import LLMMathChain
from langchain_community.callbacks import StreamlitCallbackHandler
from langchain_community.utilities import DuckDuckGoSearchAPIWrapper, SQLDatabase
from langchain_core.runnables import RunnableConfig
from langchain_experimental.sql import SQLDatabaseChain
from langchain_openai import AzureChatOpenAI

from modules.clear_results import with_clear_container

# Load environment variables
# load_dotenv()
# os.environ["AZURE_OPENAI_API_KEY"] = os.getenv("AZURE_OAI_KEY")
# os.environ["AZURE_OPENAI_ENDPOINT"] = os.getenv("AZURE_OAI_ENDPOINT")
os.environ["AZURE_OPENAI_API_KEY"] = st.secrets["AZURE_OAI_KEY"]
os.environ["AZURE_OPENAI_ENDPOINT"] = st.secrets["AZURE_OAI_ENDPOINT"]

# Set path to database /data/patents.db
DB_PATH = (Path(__file__).parent / "data/patents.db").absolute()

# Set page config
st.set_page_config(page_title="Executive Navigator Demo")
st.image("logo.png", width=300)
st.title("Executive Navigator Demo")

# Tools setup
llm = AzureChatOpenAI(
    api_version=st.secrets["AZURE_OAI_API_VERSION"],
    deployment_name=st.secrets["AZURE_OAI_DEPLOYMENT"],
    model_name=st.secrets["AZURE_OAI_MODEL"],
    temperature=0, 
    streaming=True
)
search = DuckDuckGoSearchAPIWrapper()
llm_math_chain = LLMMathChain.from_llm(llm)
db = SQLDatabase.from_uri(f"sqlite:///{DB_PATH}")
db_chain = SQLDatabaseChain.from_llm(llm, db)
tools = [
    Tool(
        name="Search",
        func=search.run,
        description="useful for when you need to answer questions about current events. You should ask targeted questions",
    ),
    Tool(
        name="Calculator",
        func=llm_math_chain.run,
        description="useful for when you need to answer questions about math",
    ),
    Tool(
        name="Patents DB",
        func=db_chain.run,
        description="useful for when you need to answer questions about patents. Input should be in the form of a question containing full context",
    ),
]

# Initialize agent with prompt from hwchase17/react on LangChain Hub
react_agent = create_react_agent(llm, tools, prompt=hub.pull("hwchase17/react"))
mrkl = AgentExecutor(agent=react_agent, tools=tools)

with st.form(key="form"):
    user_input = st.text_input("User query")
    submit_clicked = st.form_submit_button("Submit Question")

output_container = st.empty()
if with_clear_container(submit_clicked):
    output_container = output_container.container()
    output_container.chat_message("user").write(user_input)

    answer_container = output_container.chat_message("assistant", avatar="🦜")
    st_callback = StreamlitCallbackHandler(answer_container)
    cfg = RunnableConfig()
    cfg["callbacks"] = [st_callback]

    answer = mrkl.invoke({"input": user_input}, cfg)

    answer_container.write(answer["output"])