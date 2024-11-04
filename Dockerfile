FROM python:3.11

WORKDIR /code

COPY ./requirements.txt /code/requirements.txt

RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

COPY ./app /code/app

COPY ./.env /code/.env

COPY ./testdata_generator.py /code/testdata_generator.py

CMD ["fastapi", "run", "app/main.py", "--port", "8000"]