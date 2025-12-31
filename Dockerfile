# Use the official Python image from the Docker Hub
FROM caijunhui/ta-lib:latest

ENV PATH="/home/user/.local/bin:$PATH"
ENV TZ=Asia/Shanghai

WORKDIR /app

RUN apt-get update
RUN apt-get install -y tzdata && \
    ln -sf /usr/share/zoneinfo/$TZ /etc/localtime && \
    echo $TZ > /etc/timezone

COPY ./requirements.txt requirements.txt
RUN pip install --no-cache-dir --upgrade -r requirements.txt


COPY . /app

EXPOSE 5000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "5000"]
