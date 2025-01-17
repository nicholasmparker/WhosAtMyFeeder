FROM python:3.8

# Install Node.js and npm
RUN curl -sL https://deb.nodesource.com/setup_14.x | bash - && \
    apt-get install -y nodejs

# Install Vue CLI
RUN npm install -g @vue/cli

# Build Vue.js components
WORKDIR /app/static/js
COPY static/js/ ./static/js/
RUN npm install && npm run build

WORKDIR /app

RUN apt-get update && apt-get install ffmpeg libsm6 libxext6  -y
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY model.tflite .
COPY birdnames.db .
COPY speciesid.py .
COPY webui.py .
COPY queries.py .
COPY templates/ ./templates/
COPY static/ ./static/

CMD python ./speciesid.py
