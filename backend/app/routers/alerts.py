from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session
from typing import List
from ..database import get_db
from ..models import Alert
from ..schemas.alert import AlertOut
from ..ws.manager import manager

router = APIRouter(tags=["alerts"])

@router.get("/alerts", response_model=List[AlertOut])
def list_alerts(limit: int = 50, db: Session = Depends(get_db)):
    return db.query(Alert).order_by(Alert.created_at.desc()).limit(limit).all()

@router.patch("/alerts/{alert_id}/ack", response_model=AlertOut)
def acknowledge(alert_id: int, db: Session = Depends(get_db)):
    a = db.get(Alert, alert_id)
    if not a:
        raise HTTPException(404, "Alert not found")
    a.acknowledged = True
    db.commit(); db.refresh(a)
    return a

# Dashboard connects here to receive alerts the instant they happen.
@router.websocket("/ws/alerts")
async def ws_alerts(ws: WebSocket):
    await manager.connect(ws)
    try:
        while True:
            await ws.receive_text()   # we ignore client messages; keeps the socket open
    except WebSocketDisconnect:
        await manager.disconnect(ws)