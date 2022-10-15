FROM python:3.8
COPY main.py /app/
CMD ["python", "/app/main.py"]