from fastapi import FastAPI, WebSocket, Request, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from dataclasses import dataclass
from typing import Dict
import uuid
import json

templates = Jinja2Templates(directory="templates")

@dataclass
class ConnectionManager:
  def __init__(self) -> None:
    self.active_connections: dict = {}

  async def connect(self, websocket: WebSocket):
    await websocket.accept()
    id = str(uuid.uuid4())
    self.active_connections[id] = websocket

    await self.send_message(websocket, json.dumps({"type": "connect", "id": id}))

  async def send_message(self, ws: WebSocket, message: str):
    await ws.send_text(f" Message from user 1: {message}")

  async def broadcast(self, message: str):
    for connection in self.active_connections.values():
      await connection.send_text(f" Message from user 1: {message}")

  def find_connection_id(self, websocket: WebSocket):
    websocket_list = list(self.active_connections.values())
    id_list = list(self.active_connections.keys())

    pos = websocket_list.index(websocket)
    return id_list[pos]

  def disconnect(self, websocket: WebSocket):
    id = self.find_connection_id(websocket)
    del self.active_connections[id]

    return id

app = FastAPI()
connection_manager = ConnectionManager()

@app.get("/", response_class=HTMLResponse)
def get_home(request: Request):
  return templates.TemplateResponse("index.html", {"request": request});

@app.get("/user-1", response_class=HTMLResponse)
def get_home(request: Request):
  return templates.TemplateResponse("user-1.html", {"request": request});

@app.get("/user-2", response_class=HTMLResponse)
def get_home(request: Request):
  return templates.TemplateResponse("user-2.html", {"request": request});

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
  await websocket.accept() # Initiate a websocket connection
  try:
    while True:
      data = await websocket.receive_text()
      await websocket.send_text(f"Message test was {data}")
  except WebSocketDisconnect:
    print(f"client disconnected")


@app.websocket("/messaging")
async def websocket_endpoint(websocket: WebSocket):
  # Accept the connection from the client.
  await connection_manager.connect(websocket)

  try:
    while True:
      # Recieves message from the client
      data = await websocket.receive_text()
      print ("Received: ", data)
      await connection_manager.broadcast(data)
  except WebSocketDisconnect:
    id = await connection_manager.disconnect(websocket)
    # Broadcast this client leaving in the channel.
    connection_manager.broadcast(json.dumps({"type": "disconnected", "id": id}))
