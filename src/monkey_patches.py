"""
Local monkey patches for third-party libs.
"""

from __future__ import annotations

from typing import Any, Callable

from openhands.sdk.llm.message import Message


def apply_reasoning_content_patch() -> None:
    """
    Ensure reasoning_content is forwarded even when send_reasoning_content is False.
    This is needed for reasoning models (e.g., DeepSeek) that require the field
    to be present when continuing tool-call conversations.
    """
    if getattr(Message.to_chat_dict, "_reasoning_patch_applied", False):
        return

    original_to_chat_dict: Callable[[Message], dict[str, Any]] = Message.to_chat_dict

    def patched_to_chat_dict(self: Message) -> dict[str, Any]:
        message_dict = original_to_chat_dict(self)
        if self.reasoning_content and "reasoning_content" not in message_dict:
            message_dict["reasoning_content"] = self.reasoning_content
        return message_dict

    Message.to_chat_dict = patched_to_chat_dict  # type: ignore[assignment]
    setattr(Message.to_chat_dict, "_reasoning_patch_applied", True)
