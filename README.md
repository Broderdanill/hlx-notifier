
# hlx-notifier
Push notifications for BMC Helix Innovation Suite, this is to be concidered as a demo application and it's NOT production ready as is.


# Basic Authentication
The (AR Server) filter will have to set (username/password) in basic auth that is the same as the environment variables values from when container starts

- `AUTH_USERNAME` – Standard: `admin`
- `AUTH_PASSWORD` – Standard: `supersecret`



## Build the Container
podman build -t hlx-notifier .
podman run -d --name notifier -p 8083:8083 -e AUTH_USERNAME=<USERNAME> -e AUTH_PASSWORD=<PASSWORD> hlx-notifier


## Interfaces for the Container

### WebSocket - Clients listens to this

`ws://<server>:3083/ws/<channel>`

### REST (Basic Auth) - To recieve notifications to the container

`POST http://<server>:3083/notify`

#### Curl example:

curl -u <USERNAME>:<PASSWORD> -X POST http://localhost:3083/notify -H "Content-Type: application/json" -d '{"channel":"incident-1234","message":"updated"}'

## HTML för BMC View Field

See `viewfield.html` – This is the original template that in run-time is fetched from the form "HLX:Notifier:Template"

## Recommended to better up security
- Use TLS via proxy (NGINX).
- Use a very strong password and change it often
