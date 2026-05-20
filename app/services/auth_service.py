import gradio as gr
from urllib.parse import quote

from app.services.account_service import authenticate_account


def login_and_enter(account_id, password):
    is_valid, status_text, account = authenticate_account(account_id, password)
    if not is_valid:
        return (
            status_text,
            gr.update(value=""),
            gr.update(value=account_id),
            gr.update(value=""),
        )

    return (
        status_text,
        gr.update(value=f"<meta http-equiv='refresh' content='0;url=/profile?account_id={quote(str(account['account_id']))}'>"),
        gr.update(value=account_id),
        gr.update(value=""),
    )
