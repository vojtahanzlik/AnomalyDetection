FROM python:3.11

WORKDIR /app

COPY ./requirements.txt /app
RUN pip install --no-cache-dir --upgrade -r requirements.txt

COPY . /app

EXPOSE 8061

CMD ["python", "./server_main.py"]