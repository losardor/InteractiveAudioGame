FROM python:3.7
WORKDIR /code
COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt
CMD gunicorn manage:app