import os
from dotenv import load_dotenv
from pathlib import Path

import streamlit as st

from langchain import hub
from langchain.agents import AgentExecutor, Tool, create_react_agent
from langchain.chains import LLMMathChain, LLMChain
from langchain_community.callbacks import StreamlitCallbackHandler
from langchain_community.utilities import DuckDuckGoSearchAPIWrapper, SQLDatabase
from langchain_core.runnables import RunnableConfig
from langchain_experimental.sql import SQLDatabaseChain
from langchain.memory import ConversationBufferMemory
from langchain.callbacks.base import BaseCallbackHandler
from langchain.memory.chat_message_histories import StreamlitChatMessageHistory
from langchain_openai import AzureChatOpenAI

from modules.clear_results import with_clear_container

# Load environment variables
load_dotenv()
os.environ["AZURE_OPENAI_API_KEY"] = os.getenv("AZURE_OAI_KEY")
os.environ["AZURE_OPENAI_ENDPOINT"] = os.getenv("AZURE_OAI_ENDPOINT")

# Set path to database /data/patents.db
DB_PATH = (Path(__file__).parent / "data/classified-patents.db").absolute()

# Set page config
st.set_page_config(page_title="Executive Navigator Demo")
st.image("logo.png", width=300)
st.title("Executive Navigator Demo")

# Callback handler for displaying chat messages
class StreamHandler(BaseCallbackHandler):
    """
    Callback handler for displaying chat messages in the Streamlit app.
    """
    def __init__(self, container: st.delta_generator.DeltaGenerator, initial_text: str = ""):
        self.container = container
        self.text = initial_text
        self.run_id_ignore_token = None

    def on_llm_start(self, serialized: dict, prompts: list, **kwargs):
        # Workaround to prevent showing the rephrased question as output
        if prompts[0].startswith("Human"):
            self.run_id_ignore_token = kwargs.get("run_id")

    def on_llm_new_token(self, token: str, **kwargs) -> None:
        if self.run_id_ignore_token == kwargs.get("run_id", False):
            return
        self.text += token
        self.container.markdown(self.text)

# Tools setup
llm = AzureChatOpenAI(
    api_version=os.getenv("AZURE_OAI_API_VERSION"), 
    deployment_name=os.getenv("AZURE_OAI_DEPLOYMENT"),
    model_name=os.getenv("AZURE_OAI_MODEL"), 
    temperature=0, 
    streaming=True
)
search = DuckDuckGoSearchAPIWrapper()
# llm_math_chain = LLMMathChain.from_llm(llm)
db = SQLDatabase.from_uri(f"sqlite:///{DB_PATH}")
db_chain = SQLDatabaseChain.from_llm(llm, db)
tools = [
    Tool(
        name="Search",
        func=search.run,
        description="useful for when you need to answer questions about current events. You should ask targeted questions",
    ),
    # Tool(
    #     name="Calculator",
    #     func=llm_math_chain.run,
    #     description="useful for when you need to answer questions about math",
    # ),
    Tool(
        name="Patents DB",
        func=db_chain.run,
        description="useful for when you need to answer questions about patents. Input should be in the form of a question containing full context",
    ),
]

# with st.form(key="form"):
#     user_input = st.text_input("User query")
#     submit_clicked = st.form_submit_button("Submit Question")

# output_container = st.empty()
# if with_clear_container(submit_clicked):
#     output_container = output_container.container()
#     output_container.chat_message("user").write(user_input)

#     answer_container = output_container.chat_message("assistant", avatar="🦜")
#     st_callback = StreamlitCallbackHandler(answer_container)
#     cfg = RunnableConfig()
#     cfg["callbacks"] = [st_callback]

#     answer = mrkl.invoke({"input": user_input}, cfg)

#     answer_container.write(answer["output"])

# Setup memory for contextual conversation
msgs = StreamlitChatMessageHistory()
memory = ConversationBufferMemory(memory_key="chat_history", chat_memory=msgs, return_messages=True)

#llm_chain = LLMChain(llm, prompt=hub.pull("hwchase17/react-chat"))
agent = create_react_agent(llm, tools, hub.pull("hwchase17/react-chat"))
agent_chain = AgentExecutor(agent=agent, tools=tools, memory=memory)

# Initialize agent with prompt from hwchase17/react on LangChain Hub
# react_agent = create_react_agent(llm, tools, hub.pull("hwchase17/react-chat"))
# mrkl = AgentExecutor(agent=react_agent, tools=tools)

# Clear message history if requested
if len(msgs.messages) == 0 or st.sidebar.button("Clear message history"):
    msgs.clear()
    msgs.add_ai_message("How can I help you?")

# Display chat messages
avatars = {"human": "user", "ai": "assistant"}
for msg in msgs.messages:
    st.chat_message(avatars[msg.type]).write(msg.content)

# Get user query and run the QA chain
if user_query := st.chat_input(placeholder="Ask me anything!"):
    st.chat_message("user").write(user_query)

    with st.chat_message("assistant"):
        #retrieval_handler = PrintRetrievalHandler(st.container())
        #st_callback = StreamlitCallbackHandler(st.container())
        #response = agent_chain.run(user_query, callbacks=[st_callback])

        stream_handler = StreamHandler(st.empty())
        st_callback = StreamlitCallbackHandler(StreamHandler)
        cfg = RunnableConfig()
        cfg["callbacks"] = [stream_handler]

        response = agent_chain.invoke({"input": user_query}, cfg)

        #stream_handler = StreamHandler(st.empty())
        #response = agent_chain.run(user_query, callbacks=[stream_handler])