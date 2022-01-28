FROM python:3.9
WORKDIR /code 
COPY ./requirements.txt /code/requirements.txt
RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt
RUN apt-get -y update
RUN apt-get install -y ffmpeg
COPY ./web.py /code/
CMD ["python", "web.py"]