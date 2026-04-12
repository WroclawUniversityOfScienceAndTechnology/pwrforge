ARG DOCKER_IMAGE_ROOT
FROM ${DOCKER_IMAGE_ROOT} as base

ENV DEBIAN_FRONTEND=noninteractive

RUN apt update --fix-missing && \
    apt -y install python3.12 python3-pip git build-essential pkg-config graphviz plantuml && \
    update-alternatives --install /usr/bin/python python /usr/bin/python3 1

ADD https://github.com/plantuml/plantuml/releases/download/v1.2022.13/plantuml-1.2022.13.jar /usr/local/share/
ADD ./scripts/plantuml /usr/local/bin/
RUN chmod 755 /usr/local/share/plantuml-1.2022.13.jar /usr/local/bin/plantuml

FROM base AS cpp

RUN apt-get update && apt-get -y install cppcheck lib32z1 \
    clang clang-format clang-tidy doxygen libcmocka0 libcmocka-dev

WORKDIR /opt

FROM cpp AS pwrforge

ARG UID_NUMBER
ARG GID_NUMBER
ARG SSH_PORT
ARG DEV_USER=ubuntu

ARG CONAN_USERNAME
ARG CONAN_PASS_KEY
ENV CONAN_USERNAME=${CONAN_USERNAME}
ENV CONAN_PASS_KEY=${CONAN_PASS_KEY}

WORKDIR /opt

# configure ssh
RUN apt install -y openssh-server && \
    ssh-keygen -A && mkdir -p /run/sshd && \
    echo "Port $SSH_PORT" >> /etc/ssh/sshd_config

EXPOSE $SSH_PORT

RUN printf "\n\nCONFIGURING USER $DEV_USER - DEV ENV ONLY!\n\n" >&2 && \
    apt -y install sudo && \
    if ! getent group "$GID_NUMBER" >/dev/null; then \
        if getent group "$DEV_USER" >/dev/null; then \
            groupmod -g "$GID_NUMBER" "$DEV_USER"; \
        else \
            groupadd -g "$GID_NUMBER" "$DEV_USER"; \
        fi; \
    fi && \
    if ! id -u "$DEV_USER" >/dev/null 2>&1; then \
        useradd -m -s /bin/bash -N -o -u "$UID_NUMBER" -g "$GID_NUMBER" "$DEV_USER"; \
    else \
        usermod -o -u "$UID_NUMBER" -g "$GID_NUMBER" "$DEV_USER"; \
    fi && \
    mkdir -p /etc/sudoers.d && \
    echo "$DEV_USER ALL=(ALL) NOPASSWD:ALL" > "/etc/sudoers.d/90-$DEV_USER" && \
    chmod 0440 "/etc/sudoers.d/90-$DEV_USER" && \
    passwd -d "$DEV_USER" || true

# install pwrforge from pwr rep (temporarly before pip repo will be available)
COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt && \
    rm requirements.txt

RUN usermod -a -G dialout ${DEV_USER}
USER ${DEV_USER}
WORKDIR /repo
