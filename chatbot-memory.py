"""
This script sets up a chatbot using Streamlit and the LangChain library.
The chatbot allows users to upload PDF documents, performs document retrieval, and provides answers to user queries.
"""

import os
import tempfile
import streamlit as st
from dotenv import load_dotenv
from langchain_openai import AzureChatOpenAI
from langchain.document_loaders import PyPDFLoader
from langchain.document_loaders import UnstructuredExcelLoader
from langchain.memory import ConversationBufferMemory
from langchain.memory.chat_message_histories import StreamlitChatMessageHistory
from langchain_openai import AzureOpenAIEmbeddings
from langchain.callbacks.base import BaseCallbackHandler
from langchain.chains import ConversationalRetrievalChain
from langchain.vectorstores import FAISS
from langchain.text_splitter import RecursiveCharacterTextSplitter

# Load environment variables
load_dotenv()
os.environ["AZURE_OPENAI_API_KEY"] = os.getenv("AZURE_OAI_KEY")
os.environ["AZURE_OPENAI_ENDPOINT"] = os.getenv("AZURE_OAI_ENDPOINT")
# os.environ["AZURE_OPENAI_API_KEY"] = st.secrets["AZURE_OAI_KEY"]
# os.environ["AZURE_OPENAI_ENDPOINT"] = st.secrets["AZURE_OAI_ENDPOINT"]

# Set page config
st.set_page_config(page_title="Executive Navigator Demo", page_icon="💼")
st.image("logo.png", width=150)
st.title("Executive Navigator Demo")


# Function to configure the document retriever
@st.cache_resource(ttl="1h")
def configure_retriever(uploaded_files):
    """
    Configures the document retriever based on the uploaded files.

    Args:
        uploaded_files (List[UploadedFile]): List of uploaded files.

    Returns:
        retriever (ConversationalRetriever): Configured document retriever.
    """
    # Read documents
    docs = []
    temp_dir = tempfile.TemporaryDirectory()
    for file in uploaded_files:
        temp_filepath = os.path.join(temp_dir.name, file.name)
        with open(temp_filepath, "wb") as f:
            f.write(file.getvalue())
        if file.name.endswith(".xlsx"):
            loader = UnstructuredExcelLoader(temp_filepath)
        if file.name.endswith(".pdf"):
            loader = PyPDFLoader(temp_filepath)
        docs.extend(loader.load())

    # Split documents
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1500, chunk_overlap=200)
    splits = text_splitter.split_documents(docs)

    # Create embeddings and store in vectordb
    embeddings = AzureOpenAIEmbeddings(
        azure_deployment="text-embedding",
        openai_api_version=st.secrets["AZURE_OAI_API_VERSION"]
    )
    vectordb = FAISS.from_documents(splits, embeddings)

    # Define retriever
    retriever = vectordb.as_retriever(search_type="mmr", search_kwargs={"k": 2, "fetch_k": 4})

    return retriever


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


class PrintRetrievalHandler(BaseCallbackHandler):
    """
    Callback handler for displaying retrieval results in the Streamlit app.
    """
    def __init__(self, container):
        self.status = container.status("**Context Retrieval**")

    def on_retriever_start(self, serialized: dict, query: str, **kwargs):
        self.status.write(f"**Question:** {query}")
        self.status.update(label=f"**Context Retrieval:** {query}")

    def on_retriever_end(self, documents, **kwargs):
        for idx, doc in enumerate(documents):
            source = os.path.basename(doc.metadata["source"])
            self.status.write(f"**Document {idx} from {source}**")
            self.status.markdown(doc.page_content)
        self.status.update(state="complete")


# Sidebar file uploader
uploaded_files = st.sidebar.file_uploader(
    label="Upload files", type=["pdf", "xlsx"], accept_multiple_files=True
)
if not uploaded_files:
    st.info("Please upload documents to continue.")
    st.stop()

# Configure document retriever
retriever = configure_retriever(uploaded_files)

# Setup memory for contextual conversation
msgs = StreamlitChatMessageHistory()
memory = ConversationBufferMemory(memory_key="chat_history", chat_memory=msgs, return_messages=True)

# Setup LLM and QA chain
llm = AzureChatOpenAI(
    openai_api_version=os.getenv("AZURE_OAI_API_VERSION"),
    deployment_name=os.getenv("AZURE_OAI_DEPLOYMENT"),
    model_name=os.getenv("AZURE_OAI_MODEL"),
    streaming=True
)
qa_chain = ConversationalRetrievalChain.from_llm(
    llm, 
    retriever=retriever, 
    memory=memory, 
    verbose=True
)

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
        retrieval_handler = PrintRetrievalHandler(st.container())
        stream_handler = StreamHandler(st.empty())
        response = qa_chain.run(user_query, callbacks=[retrieval_handler, stream_handler])