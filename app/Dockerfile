# Use an official Python runtime as a base image
FROM python:3.5

# Make port 5000 available to the world outside this container
EXPOSE 5000

# Define environment variable
ENV NLTK_DATA "/usr/share/nltk_data"

# Install any needed packages
# Option a: during deployment
RUN pip install flask pymongo flask-restful gensim numpy wikipedia nltk sklearn

# Set the working directory to /app
WORKDIR /app

# Copy the current directory contents into the container at /app
ADD . /app

# Option b: during development
# RUN pip install -r requirements.txt

# Install nltk required dependencies
RUN python nltk_setup.py

# Run app.py when the container launches
CMD ["python", "app.py"]