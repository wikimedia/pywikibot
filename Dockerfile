FROM python:3.12-slim

WORKDIR /code

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
RUN pip install .

ENV PYTHONPATH=/code:/code/scripts

ENTRYPOINT ["python", "/code/pwb.py"]
CMD ["version"]
