FROM apache/airflow:2.10.0   # match whatever version your scaffold generated
COPY requirements.txt /requirements.txt
RUN pip install --no-cache-dir -r /requirements.txt