FROM python:3.12
WORKDIR /code
COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt

# Bundle demo data so setup-demo works even without the volume mount
COPY enchanted_forest.json enchanted_forest.json
COPY app/static/audio/demo/ app/static/audio/demo/

COPY docker/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]
CMD ["gunicorn", "manage:app"]
