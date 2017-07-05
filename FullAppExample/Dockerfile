FROM alpine:3.6

# Note: This Dockerfile has been made quickly, and can be far better.
#       Especially, it should use S6 as supervisor, django in production mode, etc...

LABEL maintainer "csouchon@cisco.com"

# Install needed packages.
RUN apk add --no-cache \
    python3

# Install required Python packages.
RUN pip3 install requests django

# Copy the django application.
COPY Transilien /Transilien

# Expose used TCP ports.
EXPOSE 8000

# Run the helper script at startup.
WORKDIR /Transilien
CMD ./transilien.sh
