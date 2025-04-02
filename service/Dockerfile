# Use Python 3.11 as the base image
FROM python:3.11.4

# Set the working directory inside the container
WORKDIR /app

# Copy the Pipfile and Pipfile.lock to the container
COPY Pipfile Pipfile.lock /app/

# Install pipenv
RUN pip install pipenv

# Make sure pipenv uses the correct Python version (3.11)
RUN pipenv --python 3.11.4

# Install project dependencies using pipenv
RUN pipenv install --deploy --ignore-pipfile

# Copy the rest of the application code to the container
COPY . /app/

# Expose FastAPI app on port 80
EXPOSE 80

# Command to run FastAPI using Uvicorn with Pipenv environment
CMD ["pipenv", "run", "uvicorn", "source.api:app", "--host", "0.0.0.0", "--port", "80"]
