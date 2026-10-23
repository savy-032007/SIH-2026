# Development image: the source tree is bind-mounted and `npm run dev` watches it.
# Phase 5 adds the multi-stage production build.
FROM node:24-slim

WORKDIR /srv/web

ENV NEXT_TELEMETRY_DISABLED=1 \
    API_INTERNAL_URL=http://api:8000

COPY package.json package-lock.json* ./
RUN npm install

COPY . .

EXPOSE 3000

CMD ["npm", "run", "dev"]
