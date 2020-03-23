FROM python:latest

RUN pip install numpy pandas dash

WORKDIR /app

EXPOSE 80

CMD ["python", "app.py"]
