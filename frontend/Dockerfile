# Step 1: Build React App
FROM node:18 AS builder

WORKDIR /app

# Copy source files
COPY package.json ./
COPY ./src ./src
COPY ./public ./public

# Accept build argument
ARG REACT_APP_API_URL
ENV REACT_APP_API_URL=$REACT_APP_API_URL

RUN npm install

# Inject the dynamic API URL into the React app
RUN echo "REACT_APP_API_URL=${REACT_APP_API_URL}" > .env

RUN npm run build

# Step 2: Serve with nginx
FROM nginx:alpine

COPY --from=builder /app/build /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 3000

CMD ["nginx", "-g", "daemon off;"]
