# Copy Docker CLI and Compose; the engine stays on the host.
FROM docker:27.5.1-cli AS dockercli
FROM jenkins/jenkins:2.555.3-jdk21
USER root
# Python runs tests; Bash/curl/flock support deployment scripts.
RUN apt-get update && apt-get install -y --no-install-recommends python3 python3-venv curl util-linux && apt-get clean
COPY --from=dockercli /usr/local/bin/docker /usr/local/bin/docker
COPY --from=dockercli /usr/local/libexec/docker/cli-plugins/docker-compose /usr/local/libexec/docker/cli-plugins/docker-compose
COPY plugins.txt /usr/share/jenkins/ref/plugins.txt
RUN jenkins-plugin-cli --plugin-file /usr/share/jenkins/ref/plugins.txt
COPY init.groovy.d/ /usr/share/jenkins/ref/init.groovy.d/
USER jenkins
HEALTHCHECK --interval=30s --timeout=10s --start-period=120s --retries=5 CMD curl -fsS http://localhost:8080/login >/dev/null || exit 1
