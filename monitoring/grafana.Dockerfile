# Provision dashboards and datasource from the same reviewed Git revision.
FROM grafana/grafana:11.6.0
COPY grafana/provisioning /etc/grafana/provisioning
COPY grafana/dashboards /opt/helpdesk-dashboards
