.. _pwrforge_docker:

Manage docker environment: docker
----------------------------------

Usage
^^^^^
::

    pwrforge docker [OPTIONS] COMMAND [ARGS]...

Description
^^^^^^^^^^^
Manage docker environment. For a list of supported OPTIONS please refer to official docker documentation of corresponding SUBCOMMAND.

Common Options
^^^^^^^^^^^^^^

::

-B, --base-dir DIRECTORY

Specify the base project path. Allows running pwrforge commands from any directory.

Subcommands
^^^^^^^^^^^
::

    build

Build the docker environment for the chosen architecture

::

    exec

Attach to existing docker environment

::

    run

Run the docker environment bash console for this project architecture

Options
^^^^^^^

-c, --command "TEXT"

[default: bash]

Quoted text, used to select command which will be executed with `docker run`

::

    exec

Works like ``docker exec`` command. Attach to the newest running container belonging to the current project and service.

Running projects in parallel
^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Run ``pwrforge docker run`` in each project directory. Each checkout gets a
separate Compose project name and network. Starting a session leaves existing
containers running, including other sessions in the same project.

Host ports are no longer published automatically. Debugging tools running inside
the container can still connect to its internal ports. To connect from the host,
explicitly publish a port::

    # First project: host GDB port 3333
    pwrforge docker run -p 3333:3333

    # Second project: host GDB port 3334
    pwrforge docker run -p 3334:3333

Configure the host debugger for the selected host port (3334 in the second
example). OpenOCD still listens on port 3333 inside each container. To publish
all ports from the Compose configuration, use ``pwrforge docker run --service-ports``;
those host ports must be free. Custom mappings for other services can likewise
be passed with ``-p HOST_PORT:CONTAINER_PORT``.

The updated CLI also isolates projects using existing generated Compose files.
Run ``pwrforge update`` to regenerate the Compose file with the project name
for direct Compose use. Regenerate it again if the checkout is moved or copied.
Containers started by older versions keep their old names; exit those sessions
and start new ones before using ``pwrforge docker exec`` with the updated CLI.

Example 1
^^^^^^^^^
Command:
::

    pwrforge docker build

**Effects:**

::

    $ docker images


User dockerfile extension
^^^^^^^^^^^^^^^^^^^^^^^^^
The user can add a layer to the existing project docker setup. User can point to the folder where the dockerfile exist and it will be built as a custom layer in the project docker environment.

To do that user should set a relative path to the project folder of *docker_context* parameter in pwrforge.toml file where the custom Dockerfile is located. E.g. setup can be found below:
::

    docker-file = ".devcontainer/Dockerfile-custom"


IMPORTANT: The custom layer should be a single file and *must not* start with the following lines to properly link with previously build base layers:
::

    FROM <docker origin image>

To apply the changes please use
::

    pwrforge update

Adding display handling to the docker
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
To add display handling to the docker firstly in pwrforge.toml add .devcontainer/docker-compose.yaml path to
as follow:
::

    update-exclude = [
    ".devcontainer/docker-compose.yaml"
    ]

Then modify ".devcontainer/docker-compose.yaml as presented below:
::

    volumes:
      - ..:/workspace
      - /tmp/.X11-unix:/tmp/.X11-unix
      - ~/.Xauthority:/root/.Xauthority
      - /dev:/dev
    environment:
      DISPLAY: ${DISPLAY}
      XAUTHORITY: ${XAUTHORITY}
