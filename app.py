import os
#from dotenv import load_dotenv
from pathlib import Path

import streamlit as st

from langchain import hub
from langchain.agents import AgentExecutor, Tool, create_react_agent
#from langchain.chains import LLMMathChain
from langchain_community.callbacks import StreamlitCallbackHandler
from langchain_community.utilities import SQLDatabase#, DuckDuckGoSearchAPIWrapper
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

# Divide the layout into two columns
col1, col2 = st.columns([4, 1.2])  

with col2:

    st.markdown("""

    section[data-testid="column"] div[class^="css-"] {
    background-image: linear-gradient(#8993ab, #8993ab);
    color: white;
    }
    
    “”",unsafe_allow_html=True)
    
    st.image("Screenshot 2024-02-14 112940.png")
    st.subheader("Ask me anything!")
    
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
        
        answer_container = output_container.chat_message("assistant", avatar="Screenshot 2024-01-04 144948.png")
        st_callback = StreamlitCallbackHandler(answer_container)
        cfg = RunnableConfig()
        cfg["callbacks"] = [st_callback]
        
        answer = mrkl.invoke({"input": user_input}, cfg)
        
        answer_container.write(answer["output"])


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
