FROM jenkins/jenkins:lts-jdk17

USER root
# Optional local-only corporate root CA (TLS-inspecting proxy). Trusted by OS, Java and Node.
COPY certs/ /usr/local/share/ca-certificates/extra/
RUN update-ca-certificates \
 && for c in /usr/local/share/ca-certificates/extra/*.crt; do \
      [ -e "$c" ] && keytool -importcert -noprompt -trustcacerts -cacerts -storepass changeit -alias "$(basename $c)" -file "$c"; \
    done; true
ENV NODE_EXTRA_CA_CERTS=/etc/ssl/certs/ca-certificates.crt

# Node 20 for the Cucumber/Playwright suite + OS libs Chromium needs.
ARG NODE_VERSION=20.19.2
RUN apt-get update \
 && apt-get install -y --no-install-recommends curl ca-certificates xz-utils libnss3-tools \
 && curl -fsSL https://nodejs.org/dist/v${NODE_VERSION}/node-v${NODE_VERSION}-linux-x64.tar.xz | tar -xJ -C /usr/local --strip-components=1 \
 && npx -y playwright@1.59.0 install-deps chromium \
 && rm -rf /var/lib/apt/lists/*

USER jenkins
# Chromium uses its own NSS store: seed it with the same optional corp CA (copied into JENKINS_HOME on first start).
RUN mkdir -p /usr/share/jenkins/ref/.pki/nssdb \
 && certutil -d sql:/usr/share/jenkins/ref/.pki/nssdb -N --empty-password \
 && for c in /usr/local/share/ca-certificates/extra/*.crt; do \
      [ -e "$c" ] && certutil -d sql:/usr/share/jenkins/ref/.pki/nssdb -A -t "C,," -n "$(basename $c)" -i "$c"; \
    done; true
# Browsers live in the persistent volume so they download once.
ENV PLAYWRIGHT_BROWSERS_PATH=/var/jenkins_home/pw-browsers

COPY plugins.txt /usr/share/jenkins/ref/plugins.txt
RUN jenkins-plugin-cli --plugin-file /usr/share/jenkins/ref/plugins.txt
