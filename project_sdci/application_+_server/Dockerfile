FROM node:alpine

EXPOSE 8080

RUN apk add --no-cache \
    wget \
    curl 
    
WORKDIR /app
RUN wget http://homepages.laas.fr/smedjiah/tmp/mw/application.js -P /app
RUN wget http://homepages.laas.fr/smedjiah/tmp/mw/server.js -P /app

RUN npm install express yargs systeminformation request

CMD node server.js --local_ip "0.0.0.0" --local_port 8080 --local_name "srv" & \
    node application.js --remote_ip "127.0.0.1" --remote_port 8080 --device_name "dev1" --send_period 5000 
