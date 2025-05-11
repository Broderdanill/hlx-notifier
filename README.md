
# hlx-notifier

# Push Notification Server (Med Basic Auth via Miljövariabler)

Detta projekt är en containeriserad push-notis-server för BMC Helix, med Basic Auth skyddat REST-endpoint – där användarnamn/lösenord läses från miljövariabler.
e
## Miljövariabler

- `AUTH_USERNAME` – Standard: `admin`
- `AUTH_PASSWORD` – Standard: `supersecret`

## Bygg och kör container

podman build -t hlx-notifier .
podman run -d --name notifier -p 8083:8083 -e AUTH_USERNAME=Demo -e AUTH_PASSWORD=P@ssword hlx-notifier


## Användning

### WebSocket (öppen)
`ws://<server>:8080/ws/<kanal>`

### REST (Basic Auth)
`POST http://<server>:8080/notify`

#### Exempel med curl:

curl -u myuser:mypassword -X POST http://localhost:8080/notify -H "Content-Type: application/json" -d '{"channel":"incident-1234","message":"uppdaterad"}'

## HTML för BMC View Field

Se `viewfield.html` – kopiera in i Developer Studio View Field (HTML Mode). Justera kanalnamnet dynamiskt om möjligt.

## Säkerhet

- Använd TLS via proxy (t.ex. NGINX).
- Använd starka lösenord och begränsa åtkomst via brandväggar/nätverk.
