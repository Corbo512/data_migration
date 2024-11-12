FROM node:22

WORKDIR /nmig

RUN git clone https://github.com/AnatolyUss/nmig.git /nmig
COPY ./nmig/config.json /nmig/config/config.json

RUN npm install
RUN npm run build
