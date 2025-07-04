FROM python:3.10.5

WORKDIR /telegram_bot

COPY . /telegram_bot

RUN pip install -r requirements.txt

CMD ["watchmedo", "auto-restart", "--pattern=*.py", "--recursive", "python", "main.py"]