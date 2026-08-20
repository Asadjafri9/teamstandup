FROM node:20-slim

# Install Python
RUN apt-get update && apt-get install -y python3 python3-pip python3-venv && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Node dependencies and build frontend
COPY package.json package-lock.json ./
RUN npm install

COPY . .
RUN npm run build

# Install Python dependencies
RUN pip3 install --break-system-packages -r backend/requirements.txt

EXPOSE $PORT

CMD ["sh", "-c", "cd backend && python3 -m uvicorn main:app --host 0.0.0.0 --port $PORT"]
