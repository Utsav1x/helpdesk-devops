# Package configuration so Jenkins does not depend on host bind-mount paths.
FROM prom/prometheus:v3.2.1
COPY prometheus.yml /etc/prometheus/prometheus.yml
COPY alert.rules.yml /etc/prometheus/alert.rules.yml
