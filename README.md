# sage-hackathon-climate-3-2025
This repository is for Sage Hackathon Climate team 3 in 2025.

## Setup Instructions

- **setup.sh**  
  Installs Python dependencies, starts LocalStack and other services, and sets up AWS resources in LocalStack.
  
  ```bash
  chmod +x setup.sh
  ./setup.sh
  ```

- **restart.sh**  
  Stops all Docker Compose services, rebuilds all images without using the cache, and restarts the services in detached mode.
  
  ```bash
  chmod +x restart.sh
  ./restart.sh
  ```
