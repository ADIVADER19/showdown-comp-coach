# Use the official lightweight Python image.
# https://hub.docker.com/_/python
FROM python:3.10-slim

# Allow statements and log messages to immediately appear in the Knative logs
ENV PYTHONUNBUFFERED True

# Copy local code to the container image.
ENV APP_HOME /app
WORKDIR $APP_HOME
COPY . ./

# Install production dependencies.
# We manually install gunicorn to be safe
RUN pip install --no-cache-dir -r requirements.txt gunicorn

# Run the web service on container startup.
# We use gunicorn (a production server) instead of the default Flask server
CMD exec gunicorn --bind :$PORT --workers 1 --threads 8 --timeout 0 app:app