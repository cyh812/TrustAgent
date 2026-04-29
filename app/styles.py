LOGIN_CSS = """
.gradio-container {
    max-width: 760px !important;
    width: 760px !important;
    margin: 0 auto !important;
}

footer,
footer.footer,
div[data-testid="footer"] {
    display: none !important;
}
"""

EXPERIMENT_CSS = """
.gradio-container {
    max-width: 1500px !important;
    width: 1500px !important;
    margin: 0 auto !important;
    padding-left: 16px !important;
    padding-right: 16px !important;
}

.gradio-container:focus,
.gradio-container:focus-visible {
    outline: none !important;
    box-shadow: none !important;
}

footer,
footer.footer,
div[data-testid="footer"] {
    display: none !important;
}

.top-title h1 {
    margin-top: 4px !important;
    margin-bottom: 8px !important;
    font-size: 34px !important;
    font-weight: 700 !important;
}

.top-subtitle {
    color: #64748b;
    margin-bottom: 12px;
}

.scene-switch {
    width: 100%;
    margin-top: 4px;
    margin-bottom: 12px;
    padding: 10px 12px;
    border: 1px solid #e2e8f0;
    border-radius: 10px;
    background: #ffffff;
}

.main-layout {
    margin-top: 6px;
    align-items: flex-start !important;
}

.reading-column {
    display: flex !important;
    flex-direction: column !important;
    justify-content: flex-start !important;
    align-items: stretch !important;
    gap: 8px !important;
    align-self: flex-start !important;
    min-height: unset !important;
}

.reading-toggle-btn {
    margin: 0 !important;
    padding: 0 !important;
}

.reading-toggle-btn button {
    width: 100% !important;
    margin: 0 !important;
}

.reading-panel {
    border: 1px solid #e2e8f0;
    border-radius: 10px;
    padding: 14px;
    background: #fafafa;
    min-height: 820px;
    margin-top: 0 !important;
}

.chat-panel {
    border: 1px solid #e2e8f0;
    border-radius: 10px;
    padding: 14px;
    background: #ffffff;
    min-height: 680px;
}

.question-panel {
    border: 1px solid #e2e8f0;
    border-radius: 10px;
    padding: 12px;
    background: #f8fafc;
    margin-bottom: 12px;
}

#chatbot {
    min-height: 360px;
    border: 1px solid #e2e8f0;
    border-radius: 8px;
}

.rating-panel {
    margin-top: 0px;
    margin-bottom: 0px;
    border: 1px solid #e2e8f0;
    border-radius: 10px;
    padding: 10px 12px;
    background: #f8fafc;
}

.rating-title {
    font-size: 14px;
    font-weight: 600;
    margin-bottom: 8px;
}

.trust-confirm-btn button {
    width: 100% !important;
    height: 40px !important;
}

.composer-wrap {
    position: relative !important;
    width: 100% !important;
    margin-top: 10px !important;
}

#composer {
    width: 100% !important;
}

#composer textarea {
    min-height: 48px !important;
    padding-right: 70px !important;
    padding-bottom: 42px !important;
    border-radius: 16px !important;
}

.send-inside-btn {
    position: absolute !important;
    right: 14px !important;
    bottom: 14px !important;
    z-index: 20 !important;
    width: 42px !important;
    min-width: 42px !important;
    height: 42px !important;
    margin: 0 !important;
    padding: 0 !important;
    border-radius: 9999px !important;
    overflow: hidden !important;
}

.send-inside-btn > *,
.send-inside-btn button {
    width: 42px !important;
    min-width: 42px !important;
    height: 42px !important;
    border-radius: 9999px !important;
    overflow: hidden !important;
    padding: 0 !important;
    font-size: 18px !important;
    line-height: 1 !important;
}
"""

ADMIN_CSS = """
.gradio-container {
    max-width: 900px !important;
    width: 900px !important;
    margin: 0 auto !important;
}

footer,
footer.footer,
div[data-testid="footer"] {
    display: none !important;
}
"""
