"""AI Chat API — consent, conversation threads, and streamed messages.

Chat history lives entirely in the app's own tables (the OmniRoute gateway is
stateless). Each send rebuilds a fresh context block (recent activity, journal,
today's summary) and streams the reply over Server-Sent Events; the assistant
turn is persisted only when the stream completes. Revoking consent stops sends
but never deletes stored history.
"""
import json
import os
from pathlib import Path
from datetime import datetime

import yaml
from flask import request, jsonify, session, Response, stream_with_context

from app.routes.api import api_bp
from app.utils.exceptions.custom_errors import InvalidRequestData, RecordNotFoundError, AuthorizationError
from app.models.base import db
from app.models.user import User
from app.models.chat import ChatConversation, ChatMessage
from app.config import assistant_config_folder
from app.utils.timezones import utc_now_naive, today_for_id, format_user_dt
from app.utils.managers.ai_assistant import AIAssistant, AssistantError
from app.utils.managers.chat_context import build_chat_context

MAX_CONTENT_CHARS = 8000
MAX_HISTORY_MESSAGES = 50


def _load_chat_prompts() -> dict:
    try:
        with open(Path(assistant_config_folder) / "llm_prompts.yaml") as f:
            prompts = yaml.safe_load(f).get("prompts", {})
    except Exception:
        prompts = {}
    return prompts.get("chat_assistant") or {}


def _get_user() -> User:
    user_id = session.get('user_id')
    if not user_id:
        raise AuthorizationError("Authentication required")
    user = User.query.get(user_id)
    if not user:
        raise AuthorizationError("User not found")
    return user


def _require_consent(user: User):
    if not user.ai_chat_consented:
        raise AuthorizationError(
            "AI Chat consent is required before messages can be sent. Grant it on your profile or the chat page."
        )


def _get_conversation(conversation_id: int, user_id: int) -> ChatConversation:
    conversation = ChatConversation.query.filter_by(id=conversation_id, user_id=user_id).first()
    if not conversation:
        raise RecordNotFoundError(f"No conversation with id {conversation_id}")
    return conversation


def _serialize_conversation(conversation: ChatConversation, user: User) -> dict:
    last = ChatMessage.query.filter_by(conversation_id=conversation.id)\
        .order_by(ChatMessage.id.desc()).first()
    count = ChatMessage.query.filter_by(conversation_id=conversation.id).count()
    data = {
        'id': conversation.id,
        'title': conversation.title or '',
        'message_count': count,
        'created_at': format_user_dt(conversation.created_at, user.timezone, "%Y-%m-%dT%H:%M:%S"),
        'updated_at': format_user_dt(conversation.updated_at, user.timezone, "%Y-%m-%dT%H:%M:%S"),
    }
    if last:
        data['last_message'] = (last.content or '')[:120]
        data['last_role'] = last.role
    return data


def _serialize_message(message: ChatMessage, user: User) -> dict:
    return {
        'id': message.id,
        'role': message.role,
        'content': message.content,
        'created_at': format_user_dt(message.created_at, user.timezone, "%Y-%m-%dT%H:%M:%S"),
    }


# ── Consent ──────────────────────────────────────────────────────────────────
@api_bp.route('/ai-consent', methods=['GET', 'POST'])
def ai_consent():
    user = _get_user()
    if request.method == 'GET':
        return jsonify({
            'consented': bool(user.ai_chat_consented),
            'consented_at': user.ai_chat_consented_at.isoformat() + 'Z'
                            if user.ai_chat_consented_at else None,
        }), 200

    data = request.get_json(silent=True) or {}
    consented = data.get('consented')
    if not isinstance(consented, bool):
        raise InvalidRequestData("consented must be a boolean")

    user.ai_chat_consented = consented
    user.ai_chat_consented_at = utc_now_naive() if consented else user.ai_chat_consented_at
    db.session.commit()
    return jsonify({
        'consented': bool(user.ai_chat_consented),
        'consented_at': user.ai_chat_consented_at.isoformat() + 'Z'
                        if user.ai_chat_consented_at else None,
    }), 200


# ── Conversations ────────────────────────────────────────────────────────────
@api_bp.route('/chat/conversations', methods=['GET', 'POST'])
def chat_conversations():
    user = _get_user()

    if request.method == 'GET':
        conversations = (
            ChatConversation.query
            .filter_by(user_id=user.id)
            .order_by(ChatConversation.updated_at.desc(), ChatConversation.id.desc())
            .all()
        )
        return jsonify({
            'conversations': [_serialize_conversation(c, user) for c in conversations],
        }), 200

    data = request.get_json(silent=True) or {}
    title = (data.get('title') or '').strip()[:200] or f"Chat — {today_for_id(user.id).isoformat()}"
    conversation = ChatConversation(user_id=user.id, title=title)
    db.session.add(conversation)
    db.session.commit()
    return jsonify(_serialize_conversation(conversation, user)), 201


@api_bp.route('/chat/conversations/<int:conversation_id>', methods=['PUT', 'DELETE'])
def chat_conversation(conversation_id):
    user = _get_user()
    conversation = _get_conversation(conversation_id, user.id)

    if request.method == 'DELETE':
        db.session.delete(conversation)
        db.session.commit()
        return '', 204

    data = request.get_json(silent=True) or {}
    title = (data.get('title') or '').strip()
    if not title:
        raise InvalidRequestData("title cannot be empty")
    conversation.title = title[:200]
    db.session.commit()
    return jsonify(_serialize_conversation(conversation, user)), 200


# ── Messages ─────────────────────────────────────────────────────────────────
@api_bp.route('/chat/conversations/<int:conversation_id>/messages', methods=['GET'])
def chat_messages(conversation_id):
    user = _get_user()
    conversation = _get_conversation(conversation_id, user.id)
    messages = (
        ChatMessage.query
        .filter_by(conversation_id=conversation.id)
        .order_by(ChatMessage.id.asc())
        .all()
    )
    return jsonify({
        'conversation': _serialize_conversation(conversation, user),
        'messages': [_serialize_message(m, user) for m in messages],
    }), 200


def _sse(event: dict) -> str:
    return f"data: {json.dumps(event, ensure_ascii=False)}\n\n"


def _sse_done() -> str:
    return "data: [DONE]\n\n"


@api_bp.route('/chat/conversations/<int:conversation_id>/messages', methods=['POST'])
def chat_send(conversation_id):
    """Stream a chat completion for one conversation over Server-Sent Events.

    Emits one ``data: {"text": ...}`` frame per content delta and closes with
    ``data: [DONE]`` — the event protocol consumed by the Deep Chat widget's
    generic HTTP streamer. The assistant turn is persisted only when the
    stream completes. Errors are surfaced as a normal text event (so the
    widget can render them) and never saved. An internal ``tq_done`` frame is
    not needed: the client refreshes thread metadata on the widget's
    ``new-message`` event.
    """
    user = _get_user()
    _require_consent(user)
    conversation = _get_conversation(conversation_id, user.id)

    data = request.get_json(silent=True) or {}
    content = (data.get('content') or data.get('text') or '').strip()
    if not content:
        # Lenient fallback for standard clients (e.g. Deep Chat) that post the
        # full message history array instead of a single ``content`` field.
        for message in reversed((data.get('messages') or [])):
            if isinstance(message, dict) and message.get('role') == 'user':
                raw = message.get('content') or message.get('text')
                if raw:
                    content = str(raw).strip()
                    break
    if not content:
        raise InvalidRequestData("content cannot be empty")
    content = content[:MAX_CONTENT_CHARS]

    user_message = ChatMessage(conversation_id=conversation.id, role='user', content=content)
    db.session.add(user_message)
    db.session.commit()

    prompts = _load_chat_prompts()
    system_template = prompts.get('system_prompt') or _DEFAULT_SYSTEM_PROMPT
    system_prompt = system_template.format(username=user.username)
    context = build_chat_context(user)
    system_prompt = f"{system_prompt}\n\n<context>\n{context}\n</context>"

    history = (
        ChatMessage.query
        .filter_by(conversation_id=conversation.id)
        .order_by(ChatMessage.id.desc())
        .limit(MAX_HISTORY_MESSAGES)
        .all()
    )
    history = list(reversed(history))

    messages = [{"role": "system", "content": system_prompt}]
    for historical in history:
        if historical.id == user_message.id:
            continue
        messages.append({"role": historical.role, "content": historical.content})
    messages.append({"role": "user", "content": content})

    assistant = AIAssistant()
    c_id = conversation.id
    conversation.updated_at = utc_now_naive()
    db.session.commit()
    _sse_text = lambda text: _sse({"text": text})

    def _generate():
        collected = []
        try:
            for delta in assistant.chat_stream(messages, session_id=f"taskquest:{c_id}"):
                collected.append(delta)
                yield _sse_text(delta)
        except AssistantError as e:
            yield _sse_text(f"Provider error: {e}")
            yield _sse_done()
            return

        reply = "".join(collected).strip()
        saved = ChatMessage(conversation_id=c_id, role='assistant', content=reply)
        db.session.add(saved)
        db.session.commit()
        yield _sse_done()

    return Response(
        stream_with_context(_generate()),
        mimetype='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'X-Accel-Buffering': 'no',
            'Connection': 'keep-alive',
        },
    )


_DEFAULT_SYSTEM_PROMPT = (
    "You are a helpful AI companion in a discipline RPG. Be warm, direct and "
    "concise, and only reference the user's data that actually appears in the "
    "provided context."
)