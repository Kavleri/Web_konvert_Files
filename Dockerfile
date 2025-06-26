FROM python:3.10-slim

WORKDIR /code

COPY ./packages.txt /code/packages.txt

RUN apt-get update && apt-get install -y --no-install-recommends $(cat packages.txt) \
    && rm -rf /var/lib/apt/lists/*

COPY ./requirements.txt /code/requirements.txt

RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

COPY . /code/

EXPOSE 7860

CMD ["gunicorn", "--workers", "2", "--bind", "0.0.0.0:7860", "konverter:app"]
