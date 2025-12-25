"""
WebSocket Manager using Socket.IO.

Manages real-time connections and broadcasts progress updates to clients.
"""
import socketio
from typing import Dict, Set
import logging

logger = logging.getLogger(__name__)

# Create Socket.IO async server
sio = socketio.AsyncServer(
    async_mode='asgi',
    cors_allowed_origins='*',  # TODO: Configure for production
    logger=logger,
    engineio_logger=False
)


class WebSocketManager:
    """
    Manage WebSocket connections and broadcasts.

    Handles:
    - Client connections/disconnections
    - Room-based broadcasting (one room per job)
    - Progress updates
    - Completion/error notifications
    """

    def __init__(self):
        """Initialize WebSocket manager."""
        self.active_connections: Dict[str, Set[str]] = {}  # job_id -> set of session_ids

    async def connect(self, sid: str, job_id: str):
        """
        Connect client to a job room.

        Args:
            sid: Socket.IO session ID
            job_id: Job UUID to subscribe to
        """
        await sio.enter_room(sid, job_id)

        if job_id not in self.active_connections:
            self.active_connections[job_id] = set()
        self.active_connections[job_id].add(sid)

        logger.info(f"Client {sid} connected to job {job_id}")

    async def disconnect(self, sid: str):
        """
        Disconnect client from all rooms.

        Args:
            sid: Socket.IO session ID
        """
        # Remove from all job rooms
        for job_id, sids in list(self.active_connections.items()):
            if sid in sids:
                sids.remove(sid)
                await sio.leave_room(sid, job_id)
                logger.info(f"Client {sid} disconnected from job {job_id}")

                # Clean up empty rooms
                if not sids:
                    del self.active_connections[job_id]

    async def send_progress(self, job_id: str, data: dict):
        """
        Send progress update to all clients subscribed to a job.

        Args:
            job_id: Job UUID
            data: Progress data {progress: int, step: str, timestamp: str}
        """
        await sio.emit('progress', data, room=job_id)
        logger.debug(f"Sent progress to job {job_id}: {data.get('progress')}%")

    async def send_complete(self, job_id: str, data: dict):
        """
        Send completion notification.

        Args:
            job_id: Job UUID
            data: Completion data {output_filename, total_questions, diagrams_detected}
        """
        await sio.emit('complete', data, room=job_id)
        logger.info(f"Sent completion to job {job_id}")

    async def send_error(self, job_id: str, error: str, details: dict = None):
        """
        Send error notification.

        Args:
            job_id: Job UUID
            error: Error message
            details: Optional error details
        """
        await sio.emit('error', {
            'message': error,
            'details': details or {}
        }, room=job_id)
        logger.error(f"Sent error to job {job_id}: {error}")

    def get_connections_count(self, job_id: str = None) -> int:
        """
        Get number of active connections.

        Args:
            job_id: Optional job ID to get connections for specific job

        Returns:
            Number of connections
        """
        if job_id:
            return len(self.active_connections.get(job_id, set()))
        return sum(len(sids) for sids in self.active_connections.values())


# Global WebSocket manager instance
ws_manager = WebSocketManager()


# Socket.IO event handlers
@sio.event
async def connect(sid, environ):
    """Handle client connection."""
    logger.info(f"Client connected: {sid}")
    await sio.emit('connected', {'status': 'ok'}, room=sid)


@sio.event
async def disconnect(sid):
    """Handle client disconnection."""
    await ws_manager.disconnect(sid)
    logger.info(f"Client disconnected: {sid}")


@sio.event
async def subscribe(sid, data):
    """
    Subscribe to job updates.

    Client sends: {'job_id': 'uuid-string'}
    Server responds: {'subscribed': True, 'job_id': 'uuid-string'}
    """
    job_id = data.get('job_id')

    if not job_id:
        await sio.emit('error', {'message': 'job_id is required'}, room=sid)
        return

    try:
        await ws_manager.connect(sid, job_id)
        await sio.emit('subscribed', {
            'subscribed': True,
            'job_id': job_id
        }, room=sid)
    except Exception as e:
        logger.error(f"Error subscribing client {sid} to job {job_id}: {e}")
        await sio.emit('error', {
            'message': 'Failed to subscribe',
            'details': str(e)
        }, room=sid)


@sio.event
async def unsubscribe(sid, data):
    """
    Unsubscribe from job updates.

    Client sends: {'job_id': 'uuid-string'}
    """
    job_id = data.get('job_id')

    if job_id and job_id in ws_manager.active_connections:
        if sid in ws_manager.active_connections[job_id]:
            ws_manager.active_connections[job_id].remove(sid)
            await sio.leave_room(sid, job_id)
            logger.info(f"Client {sid} unsubscribed from job {job_id}")

    await sio.emit('unsubscribed', {
        'unsubscribed': True,
        'job_id': job_id
    }, room=sid)


@sio.event
async def ping(sid, data):
    """
    Ping/pong for connection health check.

    Client sends: {'timestamp': ms}
    Server responds: {'pong': True, 'timestamp': ms}
    """
    await sio.emit('pong', {
        'pong': True,
        'timestamp': data.get('timestamp')
    }, room=sid)
