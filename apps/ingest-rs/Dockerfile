FROM rust:1.85-bookworm AS build
WORKDIR /src
COPY Cargo.toml .
COPY src ./src
RUN cargo build --release

FROM debian:bookworm-slim
RUN apt-get update && apt-get install -y --no-install-recommends ffmpeg ca-certificates && rm -rf /var/lib/apt/lists/*
COPY --from=build /src/target/release/pet-ai-ingest /usr/local/bin/pet-ai-ingest
CMD ["pet-ai-ingest"]
