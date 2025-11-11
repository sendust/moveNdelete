## Features

- Move old files, delete very old files
- Easily configurable with json config



## Installation

put service, timer files in /etc/systemd/system

```bash
  sudo systemctl daemon-reload
  sudo systemctl enable --now move_delete.timer
```


## Running Tests

To run tests, run the following command

```bash
  sudo systemctl list-timers
  sudo journalctl -u move_delete -r
```

