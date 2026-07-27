FROM node:20-alpine

WORKDIR /app

COPY package*.json ./
RUN npm install

COPY . .

# Volume-mounted source (docker-compose.yml) needs polling to pick up file
# changes reliably inside a container on Mac's bind-mount filesystem.
ENV CHOKIDAR_USEPOLLING=true
ENV BROWSER=none

EXPOSE 3000

CMD ["npm", "start"]
