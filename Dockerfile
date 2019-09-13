# FROM tiangolo/uwsgi-nginx-flask:python3.7
# RUN  pip install requests
# ENV UWSGI_CHEAPER 1
# ENV UWSGI_PROCESSES 1
# ENV LISTEN_PORT 8080
# COPY ./app /app
# EXPOSE 8080


FROM python:2.7
ADD ./app /app
WORKDIR /app
EXPOSE 8080
RUN pip install -r requirements.txt
ENTRYPOINT ["python","main.py"]