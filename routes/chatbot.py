from flask import Blueprint, request, jsonify, render_template, session
from functools import wraps
from chatbot.rag_chatbot import get_chatbot_response

chatbot_bp = Blueprint('chatbot', __name__)
def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get('logged_in'):
            return jsonify({'error': 'Unauthorized'}), 401
        return f(*args, **kwargs)
    return decorated


@chatbot_bp.route('/chat')
@login_required
def chat_page():
    return render_template('chatbot.html')


@chatbot_bp.route('/chat/message', methods=['POST'])
@login_required
def chat_message():
    data = request.get_json()
    user_message = data.get('message', '').strip()
    chat_history = data.get('history', [])

    if not user_message:
        return jsonify({'success': False, 'message': 'Empty message'})

    response = get_chatbot_response(user_message, chat_history)
    return jsonify(response)