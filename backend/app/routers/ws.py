from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from jose import JWTError, jwt

from app.config import settings

from app.ws_manager import manager


router = APIRouter(tags=["ws"])


@router.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: int):
    token = websocket.query_params.get("token")
    if not token:
        await websocket.close(code=4401)
        return

    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        token_user_id = int(payload.get("sub"))
        if token_user_id != user_id:
            await websocket.close(code=4403)
            return
    except (JWTError, TypeError, ValueError):
        await websocket.close(code=4401)
        return

    await manager.connect(user_id, websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(user_id, websocket)
