FROM tiangolo/uwsgi-nginx-flask:python3.7

COPY requirements.txt .
RUN pip install -r requirements.txt

# Development

