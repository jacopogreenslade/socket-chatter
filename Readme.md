# Socket Chatbox
## Message spammer app for testing socket connections between a python server and a js/html client

This simple app, has 2 components:
- a python server: `server.py`
- a html client: `index.html`

Start the server:
```
pip install requirements.txt
export FLASK_ENV=development
python serer.py
```

Start Redis (wsl):
```
redis-server --save "" --appendonly no
```

Open the client in the browser:
`index.html`
or start a local server to watch for changes ( needs to be figured out ).