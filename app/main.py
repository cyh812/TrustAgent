import gradio as gr
from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from pathlib import Path
import sys
import uvicorn

if __package__ is None or __package__ == "":
    project_root = Path(__file__).resolve().parents[1]
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

from app.config import APP_TITLE
from app.pages.admin_page import build_admin_demo
from app.pages.chat_page import build_chat_demo
from app.pages.login_page import build_login_demo
from app.pages.planning_page import build_planning_demo
from app.pages.profile_page import build_profile_demo
from app.pages.qa_page import build_qa_demo


def create_fastapi_app():
    app = FastAPI(title=APP_TITLE)

    login_demo = build_login_demo()
    chat_demo = build_chat_demo()
    qa_demo = build_qa_demo()
    planning_demo = build_planning_demo()
    profile_demo = build_profile_demo()
    admin_demo = build_admin_demo()

    app = gr.mount_gradio_app(app, login_demo, path="/login")
    app = gr.mount_gradio_app(app, profile_demo, path="/profile")
    app = gr.mount_gradio_app(app, chat_demo, path="/chat")
    app = gr.mount_gradio_app(app, qa_demo, path="/qa")
    app = gr.mount_gradio_app(app, planning_demo, path="/plan")
    app = gr.mount_gradio_app(app, admin_demo, path="/admin")

    @app.get("/")
    def root():
        return RedirectResponse(url="/login")

    @app.get("/experiment")
    def experiment():
        return RedirectResponse(url="/profile")

    return app


fastapi_app = create_fastapi_app()


if __name__ == "__main__":
    uvicorn.run(fastapi_app, host="127.0.0.1", port=6006, access_log=False)
