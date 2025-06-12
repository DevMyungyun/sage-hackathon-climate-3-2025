# Use an official Fedora image
FROM fedora:40

# Install Python, pip, R, and build tools
RUN dnf install -y python3 python3-pip R-core R-core-devel && \
    dnf clean all

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file into the container
COPY ./requirements.txt /app/requirements.txt

# Install any needed packages specified in requirements.txt
RUN pip3 install --no-cache-dir -r /app/requirements.txt

# Install required R packages: dplyr, readr, lubridate
RUN Rscript -e "install.packages(c('dplyr', 'readr', 'lubridate'), repos='https://cloud.r-project.org')"

# Copy the application code into the container
COPY . .

# Expose the port the app runs on
EXPOSE 9000

# Run the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "9000"]