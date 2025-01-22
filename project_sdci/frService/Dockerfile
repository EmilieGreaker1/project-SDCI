FROM node:alpine

ENV REMOTE_IP_GI = $REMOTE_IP_GI

EXPOSE 8080

RUN apk add --no-cache \
    curl 
    
WORKDIR /app
COPY flowReductionService.js /app/ 

RUN npm install express yargs request

CMD node flowReductionService.js --local_ip "0.0.0.0" --local_port 8080 --local_name "frService" --remote_ip $REMOTE_IP_GI  --remote_port 8080 --remote_name "gi"