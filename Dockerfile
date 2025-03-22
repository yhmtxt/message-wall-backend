FROM python:3.11
WORKDIR /app
COPY app/requirements.txt .
RUN pip install -r requirements.txt
COPY app .
EXPOSE 8000
CMD ["fastapi", "run", "main.py"]