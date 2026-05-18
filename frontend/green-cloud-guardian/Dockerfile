FROM node:22-alpine AS build

WORKDIR /app

ARG VITE_API_BASE_URL=https://devsecops-project-cloud.onrender.com
ENV VITE_API_BASE_URL=${VITE_API_BASE_URL}

COPY package.json ./
RUN npm install --legacy-peer-deps
RUN npm install react-is --legacy-peer-deps

COPY . .
RUN npm run build

FROM node:22-alpine

WORKDIR /app

COPY --from=build /app/dist ./dist
COPY --from=build /app/node_modules ./node_modules
COPY --from=build /app/package.json ./package.json

EXPOSE 3000
ENV PORT=3000
ENV NODE_ENV=production

CMD ["node", "dist/server/index.js"]