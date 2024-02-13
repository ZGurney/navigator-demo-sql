FROM python:3.10
RUN mkdir /opt/navigator_demo
WORKDIR /opt/navigator_demo
COPY . /opt/navigator_demo
RUN pip install -r requirements.txt
RUN apt-get update && apt-get install -y curl # Install curl package
EXPOSE 8501
HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health
ENTRYPOINT ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]