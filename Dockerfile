FROM python:3.10

ADD . /app
WORKDIR /app

# Install requirements
RUN pip install -r requirements.txt

# Run as a non root user
RUN useradd -ms /bin/bash power_factors
RUN chown -R power_factors:power_factors /app
USER power_factors

# Expose port for backend server
EXPOSE 8000
