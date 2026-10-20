FROM node:22-alpine
RUN apk add --no-cache ffmpeg
WORKDIR /app
COPY package*.json tsconfig.json ./
RUN npm install
COPY src ./src
CMD ["npm", "run", "dev"]
