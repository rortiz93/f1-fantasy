# Use the official Python image as the base
FROM python:3.10

# Set the working directory in the container
WORKDIR /app

# Copy requirements.txt to the app directory in the Docker image
COPY requirements.txt /app/

# Install dependencies
RUN pip install -r /app/requirements.txt

# Copy the entire project into the container
COPY . /app

# Set the DJANGO_SETTINGS_MODULE environment variable and add PYTHONPATH
ENV DJANGO_SETTINGS_MODULE=f1_fantasy.settings
ENV PYTHONPATH=/app

# Run Django collectstatic
RUN python /app/manage.py collectstatic --noinput

# Expose the port Django will use
EXPOSE 8000

# Run the Django development server (use Gunicorn for production)
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "f1_fantasy.wsgi:application"]