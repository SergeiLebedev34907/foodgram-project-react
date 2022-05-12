FROM python:3.7-slim

RUN apt-get update
RUN pip3 install --upgrade pip

WORKDIR /backend

COPY backend/requirements.txt .
RUN pip3 install -r requirements.txt --no-cache-dir

COPY ./backend/ .

CMD ["gunicorn", "backend.wsgi:application", "--bind", "0:8000"]
