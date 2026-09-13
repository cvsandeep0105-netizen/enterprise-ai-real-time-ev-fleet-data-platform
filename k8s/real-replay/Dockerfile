FROM python:3.12-slim
RUN pip install --no-cache-dir kafka-python==2.2.15
COPY area30_live_real_replay.py /tmp/area30_live_real_replay.py
COPY area30_real.ndjson /tmp/area30_real.ndjson
CMD ["python","/tmp/area30_live_real_replay.py"]
