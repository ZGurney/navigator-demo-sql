import os
#from dotenv import load_dotenv
from pathlib import Path

import streamlit as st
from streamlit_float import *

from langchain import hub
from langchain.agents import AgentExecutor, Tool, create_react_agent
#from langchain.chains import LLMMathChain
from langchain_community.callbacks import StreamlitCallbackHandler
from langchain_community.utilities import SQLDatabase#, DuckDuckGoSearchAPIWrapper
from langchain_core.runnables import RunnableConfig
from langchain.memory import ConversationBufferMemory
from langchain_experimental.sql import SQLDatabaseChain
from langchain.memory.chat_message_histories import StreamlitChatMessageHistory
from langchain_openai import AzureChatOpenAI

from modules.clear_results import with_clear_container

# Load environment variables
# load_dotenv()
# os.environ["AZURE_OPENAI_API_KEY"] = os.getenv("AZURE_OAI_KEY")
# os.environ["AZURE_OPENAI_ENDPOINT"] = os.getenv("AZURE_OAI_ENDPOINT")
os.environ["AZURE_OPENAI_API_KEY"] = st.secrets["AZURE_OAI_KEY"]
os.environ["AZURE_OPENAI_ENDPOINT"] = st.secrets["AZURE_OAI_ENDPOINT"]

import streamlit as st

# Set page config
st.set_page_config(page_title="Executive Navigator Demo", layout="wide")

# Define CSS to add padding at the top
combined_css = """
<style>
    .custom-padding-top {
        padding-top: 30px; /* Add padding only at the top */
    }
    .block-container {
        padding: 0; /* Remove padding from all sides */
    }
</style>
"""

# Apply the custom CSS
st.write(combined_css, unsafe_allow_html=True)

# Set path to database /data/patents-100k.db
DB_PATH = (Path(__file__).parent / "data/patents-100k.db").absolute()

<<<<<<< Updated upstream
# Divide the layout into two columns
col1, col2 = st.columns([4, 1.2])  

with col2:
    st.write("""
        <style>
            section[data-testid="column"] div[class^="css-"] {
                background-image: linear-gradient(#8993ab, #8993ab);
                color: grey;
            }
        </style>
    """, unsafe_allow_html=True)

    
    st.image("Screenshot 2024-02-14 112940.png")
    st.subheader("Ask me anything!")
=======
# Get user query and run the react agent
# if user_query := st.chat_input(key="content", placeholder="Ask me anything!"):

with st.sidebar:
    st.title("Ask me anything!")
>>>>>>> Stashed changes
    
    # Tools setup
    llm = AzureChatOpenAI(
        api_version=st.secrets["AZURE_OAI_API_VERSION"],
        deployment_name=st.secrets["AZURE_OAI_DEPLOYMENT"],
        model_name=st.secrets["AZURE_OAI_MODEL"],
        temperature=0, 
        streaming=True
    )
    # search = DuckDuckGoSearchAPIWrapper()
    # llm_math_chain = LLMMathChain.from_llm(llm)
    db = SQLDatabase.from_uri(f"sqlite:///{DB_PATH}")
    db_chain = SQLDatabaseChain.from_llm(llm, db)
    tools = [
        # Tool(
        #     name="Search",
        #     func=search.run,
        #     description="useful for when you need to answer questions about current events. You should ask targeted questions",
        # ),
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

    # Setup memory for contextual conversation
    msgs = StreamlitChatMessageHistory()
    memory = ConversationBufferMemory(memory_key="chat_history", chat_memory=msgs, return_messages=True, human_prefix="user", ai_prefix="assistant")

<<<<<<< Updated upstream
    with st.form(key="form"):
            user_input = st.text_input("User query")
            submit_clicked = st.form_submit_button("Submit Question")
            
    output_container = st.empty()
    if with_clear_container(submit_clicked):
        output_container = output_container.container()
        output_container.chat_message("user").write(user_input)
        
        answer_container = output_container.chat_message("assistant", avatar="Screenshot 2024-01-04 144948.png")
        st_callback = StreamlitCallbackHandler(answer_container)
        cfg = RunnableConfig()
        cfg["callbacks"] = [st_callback]
        
        answer = mrkl.invoke({"input": user_input}, cfg)
        
        answer_container.write(answer["output"])
=======
    # Initialize agent with prompt from hwchase17/react on LangChain Hub
    react_agent = create_react_agent(llm, tools, prompt=hub.pull("zgurney/react-chat-2"))
    mrkl = AgentExecutor(agent=react_agent, tools=tools, memory=memory)

    # Clear message history if requested
    if "messages" not in st.session_state or st.sidebar.button("Clear message history"):
        msgs.clear()
        st.session_state["messages"] = [{"role": "assistant", "content": "How can I help you?"}]

    # Display chat messages from the session state
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"], avatar="navigator.png" if msg["role"] == "assistant" else "user"):
            st.write(msg["content"])

    if user_query := st.chat_input(key="content", placeholder="Ask me anything!"):
        st.session_state.messages.append({"role": "user", "content": user_query})
        st.chat_message("user").write(user_query)

        with st.chat_message("assistant", avatar="navigator.png"):
            st_callback = StreamlitCallbackHandler(st.container()) # Callback handler for agent's thinking processes
            response = mrkl.invoke({"input": user_query}, {"callbacks":[st_callback]}) # Agent acts on user query
            st.session_state.messages.append({"role": "assistant", "content": response["output"]}) # Add response to message history
            st.write(response["output"]) # Display response

    
    # message_container = st.empty()

    # float_init()

    # with st.container():
    #     st.chat_input(key="user_input", on_submit=chat)
    #     button_b_pos = "0rem"
    #     button_css = float_css_helper(width="2.2rem", bottom=button_b_pos, transition=0)
    #     float_parent(css=button_css)    
>>>>>>> Stashed changes


# Power BI report URL
power_bi_url = "https://app.powerbi.com/view?r=eyJrIjoiMzU3YmZiOGEtNGExNi00OWQxLWI3OTAtMzA4MGFiOTlmODE3IiwidCI6ImIwMDM2N2UyLTE5M2EtNGY0OC05NGRlLTcyNDVkNDVjMDk0NyIsImMiOjh9"

# Define custom CSS to style the iframe
custom_css = """
<style>
    .power-bi-iframe {
        width: 100%;
        height: 100vh;
        border: none;
        overflow: hidden;
    }
</style>
"""

with col1:
    # Display the images
    st.image("Screenshot 2024-02-14 112940.png")
    st.image(["logo_colour.png", "Screenshot 2024-02-14 110753.png"])

    # Display the Power BI report with custom CSS
    st.markdown(custom_css, unsafe_allow_html=True)
    st.markdown(f'<iframe class="power-bi-iframe" src="{power_bi_url}"></iframe>', unsafe_allow_html=True)
