FROM node:alpine

ENV REMOTE_IP_SERVER = $REMOTE_IP_SERVER

EXPOSE 8080

RUN apk add --no-cache \
    wget \
    curl 
    
WORKDIR /app
RUN wget http://homepages.laas.fr/smedjiah/tmp/mw/gateway.js -P /app

RUN npm install express yargs systeminformation request

# "sdci-server-clusterip" 
CMD node gateway.js --local_ip "0.0.0.0" --local_port 8080 --local_name "gwi" --remote_ip $REMOTE_IP_SERVER  --remote_port 8080 --remote_name "srv"