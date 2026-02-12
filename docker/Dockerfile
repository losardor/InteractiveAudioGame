FROM python:3.12
WORKDIR /code
COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt

COPY . .

COPY docker/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]
CMD ["gunicorn", "manage:app"]
