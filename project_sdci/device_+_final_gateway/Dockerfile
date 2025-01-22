FROM node:alpine

ENV ZONE_NUMBER=$ZONE_NUMBER
ENV REMOTE_IP_GI = $REMOTE_IP_GI
EXPOSE 8080

RUN apk add --no-cache \
    wget \
    curl 

WORKDIR /app
RUN wget http://homepages.laas.fr/smedjiah/tmp/mw/gateway.js -P /app
RUN wget http://homepages.laas.fr/smedjiah/tmp/mw/device.js -P /app

RUN npm install express yargs systeminformation request

#local ip: who is allowed to talk to me, 0.0.0.0 everyone, 127.0.0.1 only people in the docker
#remote ip: who im talking to
CMD node gateway.js --local_ip "0.0.0.0" --local_port 8080 --local_name "gwf${ZONE_NUMBER}" --remote_ip $REMOTE_IP_GI --remote_port 8080 --remote_name "gwi" & \
    node device.js --local_ip "0.0.0.0" --local_port 9001 --local_name "dev${ZONE_NUMBER}" --remote_ip "127.0.0.1" --remote_port 8080 --remote_name "gwf${ZONE_NUMBER}" --send_period 3000