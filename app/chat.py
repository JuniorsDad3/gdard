# app/chat.py
from flask_socketio import SocketIO, send, emit
from app import create_app, db
from app.models import Message

socketio = SocketIO()

def init_chat(app):
    socketio.init_app(app)

@socketio.on('message')
def handle_message(data):
    message = Message(
        sender_id=data['sender_id'],
        receiver_id=data['receiver_id'],
        content=data['content']
    )
    db.session.add(message)
    db.session.commit()
    emit('new_message', data, broadcast=True)