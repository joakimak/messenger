# Requirements
* docker-compose >= 2.20.3

# Setup & Tear down

### Linux/Mac
* **Automatic**
1. Navigate to the service directory
     ```cd service```
2. Enable permission to execute the startup script
     ```chmod +x start_service.sh```
3. Run the script ```./start_service.sh```
4. The script will automatically clean up its own environment upon termination and interruption.
 
* **Manual**
1. Navigate to the service directory ```cd service```
2. Manually export all the environment variables in local.env
3. Start the service with docker-compose ```docker-compose -f docker-compose.service.yml up --build```
4. Tear down the service with ```docker-compose -f docker-compose.service.yml down```
5. Unset the environment variables lited in local.env

### Windows
  * **Manual**
  1. Navigate to the service directory ```cd service```
  2. Manually export all the environment variables in local.env
  3. Start the service with docker-compose ```docker-compose -f docker-compose.service.yml up --build```
  4. Teardown the service with ```docker-compose -f docker-compose.service.yml down```
  5. Unser the environment variables lited in local.env

# Usage
  1. POST a message with
     ```python
     curl -X 'POST' 'http://localhost/message/' 
     -H 'accept: application/json' 
     -H 'Content-Type: application/json'
     -d '{"username": "testuser", "content": "testcontent"}'

  3. Open a browser and find the Swagger documentation for the API on http://localhost:80/docs
