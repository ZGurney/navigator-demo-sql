# %%
from langchain.document_loaders import PyPDFLoader

import os
from dotenv import load_dotenv


# %%
load_dotenv()
os.environ["AZURE_OPENAI_API_KEY"] = os.getenv("AZURE_OAI_KEY")
os.environ["AZURE_OPENAI_ENDPOINT"] = os.getenv("AZURE_OAI_ENDPOINT")

# %%
from langchain_openai import AzureOpenAIEmbeddings

embeddings = AzureOpenAIEmbeddings(
    azure_deployment="text-embedding",
    openai_api_version="2023-05-15"
)

# text1 = "apple"
# text2 = "banana"
# text3 = "rain"

# query_result = embeddings.embed_query(text1)
# doc_result = embeddings.embed_documents([text1])

# print(doc_result[0][:5])

# %%
# Load a PDF document
file_path = "data/bp-report.pdf"
loader = PyPDFLoader(file_path=file_path)

# %%
# Split the document into chunks
pages = loader.load_and_split()
print(pages[0])

# %%
# Create a vector store
from langchain.vectorstores import FAISS

db = FAISS.from_documents(documents=pages, embedding=embeddings)
db.save_local("data/faiss_index")


# %%
from langchain_openai import AzureChatOpenAI

llm = AzureChatOpenAI(
    deployment_name=os.getenv("AZURE_OAI_DEPLOYMENT"),
    model_name=os.getenv("AZURE_OAI_MODEL"),
    openai_api_version="2023-05-15",
    openai_api_type="azure"
)

# %%
from langchain.chains import ConversationalRetrievalChain
from langchain.chains.question_answering import load_qa_chain

# Load FAISS vector store saved locally
vectorStore = FAISS.load_local("data/faiss_index", embeddings)

# Use the vector store to search the local document
retriever = vectorStore.as_retriever(search_type="similarity", search_kwargs={"k": 2})

qa = ConversationalRetrievalChain.from_llm(
    llm=llm,
    retriever=retriever,
    # condense_question_prompt=,
    return_source_documents=True,
    verbose=False
)

# %%
import streamlit as st

def ask_question_with_context(qa, question, chat_history):
    result = qa({"question": question, "chat_history": chat_history})
    chat_history.append((question, result["answer"]))
    return chat_history

user_query = st.text_input("Ask a question:")

chat_history = []
if st.button("Submit"):
    if user_query:
        st.write("User Query:", user_query)
        chat_history = ask_question_with_context(qa, user_query, chat_history)
        response = chat_history[-1][1] if chat_history else "No response"
        st.write("Answer:", response)

# %%

# import streamlit as st

# prompt = st.chat_input("Ask a question:")

# if prompt:
#     st.write(f"User has asked: {prompt}")

# with st.chat_message("assistant"):
#     st.write("Hello")

# %%


