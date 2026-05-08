import gradio as gr

from app.services.account_service import authenticate_account, set_current_account


def login_and_enter(account_id, password):
    is_valid, status_text, account = authenticate_account(account_id, password)
    if not is_valid:
        return (
            status_text,
            gr.update(value=""),
            gr.update(value=account_id),
            gr.update(value=""),
        )

    set_current_account(account)
    return (
        status_text,
        gr.update(value="<meta http-equiv='refresh' content='0;url=/profile'>"),
        gr.update(value=account_id),
        gr.update(value=""),
    )
