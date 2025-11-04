# Setup

## Server

```bash
chatcli server --port 8080 --size 5 --name "Minecraft Hardcore" --password "minecraft@123"
# All flags are optional
```

output:

```bash
INFO:     Server Started Successfully
INFO:     Server Hash: #3jsr6t
```

### Errors

- Port already in use
- Invalid size (1 < size < 100) (not intended to handle more than 5 players)
- Invalid password (3 < length < 32)

## Server interactions

`^c` to Shutdown server
`remove @user` to remove user from server (block IP)

## Client

```bash
chatcli client #3jsr6t --voice 1 --mute 0
# All flags are optional
```

all further interactions will be done via textual TUI

## Client interactions

`/v` toggle mic
`/m` toggle mute
`quit` to exit
`@user` to mention user (user suggestions)
