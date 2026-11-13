FROM node:22-slim AS build
WORKDIR /app
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ .
ARG BACKEND_URL=http://backend:8000
ENV BACKEND_URL=$BACKEND_URL
RUN npm run build
FROM node:22-slim
WORKDIR /app
COPY --from=build /app ./
ENV BACKEND_URL=http://backend:8000
EXPOSE 3000
CMD ["sh", "-c", "npx next start -p ${PORT:-3000}"]
