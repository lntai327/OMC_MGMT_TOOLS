FROM node:26-alpine

WORKDIR /app

COPY frontend/package.json ./
# If package-lock.json exists, copy it as well
# RUN npm install

COPY frontend /app

EXPOSE 3000

CMD ["sh", "-c", "npm install && npm run dev -- --host 0.0.0.0 --port 3000"]

