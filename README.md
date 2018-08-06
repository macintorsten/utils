# utils

## crack.go

`Usage: ./crack.go <MESSAGE base64> <HMAC-SHA256 base64> <WORDLIST file>`

`go run crack.go a2V5ZWQtaGFzaCBtZXNzYWdlIGF1dGhlbnRpY2F0aW9uIGNvZGU= 2MlsezAKAfhV2llFplYDJUKRobeRz+azQy0bXXiXKLo= /usr/share/wordlists/rockyou.txt`

## Python binary wrapper

``` 
Usage:
$ ./binwrapper.py                            # Run embedded command
$ ./binwrapper.py <command> [args]           # Embed new command in this file
$ ./binwrapper.py <command> [args] > new.py  # Create new file with embedded command
$ python < ./binwrapper.py                   # Run from stdin
```
