FROM kong:3.6

# Copy the AWS-specific configuration
COPY kong.aws.yml /kong/declarative/kong.yml

# Set environment variables to ensure Kong runs in DB-less mode using this config
ENV KONG_DATABASE=off
ENV KONG_DECLARATIVE_CONFIG=/kong/declarative/kong.yml
ENV KONG_PLUGINS=bundled,jwt,rate-limiting,cors

# Expose ports (Standard Kong ports)
EXPOSE 8000 8001 8443 8444

CMD ["kong", "docker-start"]
