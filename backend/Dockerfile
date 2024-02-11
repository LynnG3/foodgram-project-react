FROM python:3.9
COPY requirements.txt .
RUN pip install -r requirements.txt --no-cache-dir
WORKDIR /app
COPY . .
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "foodgram.wsgi"]
