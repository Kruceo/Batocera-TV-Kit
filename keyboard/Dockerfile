FROM --platform=linux/amd64 golang:1.25-bookworm

# Install SDL2 development libraries
RUN apt-get update && apt-get install -y \
    libsdl2-dev \
    libsdl2-ttf-dev \
    libsdl2-image-dev \
    libsdl2-mixer-dev \
    libsdl2-gfx-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /build

# Copy go mod files
COPY go.mod go.sum ./
RUN go mod download

# Copy source code
COPY *.go ./

# Build
RUN go build -o keyboard-linux .
