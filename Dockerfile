FROM python:3.9-slim
WORKDIR /app
COPY src/requirements.txt src/requirements.txt
RUN pip3 install -r src/requirements.txt
COPY src/ src/
CMD ["python3", "src/main.py"]