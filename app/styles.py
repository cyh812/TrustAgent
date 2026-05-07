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

.task-header {
    align-items: center !important;
    margin-bottom: 8px;
}

.task-end-action {
    display: flex !important;
    justify-content: center !important;
    align-items: flex-end !important;
}

.task-end-action button {
    width: 100% !important;
    height: 42px !important;
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

#qa-chatbot,
#free-chatbot {
    min-height: 360px;
    border: 1px solid #e2e8f0;
    border-radius: 8px;
}

#free-chatbot {
    min-height: 560px;
}

#custom-chat-window {
    min-height: 560px;
}

.custom-chat-window {
    height: 560px;
    overflow-y: auto;
    border: 1px solid #e2e8f0;
    border-radius: 8px;
    background: #f8fafc;
    padding: 18px;
}

.custom-chat-empty {
    height: 100%;
    min-height: 500px;
    display: flex;
    align-items: center;
    justify-content: center;
    color: #94a3b8;
}

.custom-chat-turn {
    display: flex;
    flex-direction: column;
    gap: 10px;
    margin-bottom: 18px;
}

.custom-message {
    max-width: 78%;
    border: 1px solid #e2e8f0;
    border-radius: 8px;
    padding: 10px 12px;
    background: #ffffff;
    line-height: 1.55;
}

.custom-message-user {
    align-self: flex-end;
    background: #eaf2ff;
    border-color: #bfdbfe;
}

.custom-message-assistant {
    align-self: flex-start;
}

.custom-message-label {
    margin-bottom: 4px;
    color: #64748b;
    font-size: 12px;
    font-weight: 600;
}

.custom-message-body {
    color: #0f172a;
    font-size: 15px;
}

.custom-answer-options {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 12px;
    width: 100%;
}

.custom-answer-card {
    border: 1px solid #cbd5e1;
    border-radius: 8px;
    background: #ffffff;
    padding: 12px;
}

.custom-answer-card.selected {
    border-color: #2563eb;
    box-shadow: 0 0 0 2px rgba(37, 99, 235, 0.16);
}

.custom-answer-title {
    margin-bottom: 8px;
    color: #334155;
    font-size: 13px;
    font-weight: 700;
}

.custom-answer-body {
    color: #0f172a;
    font-size: 15px;
    line-height: 1.55;
}

.custom-turn-rating {
    align-self: center;
    border: 1px solid #e2e8f0;
    border-radius: 8px;
    background: #ffffff;
    padding: 6px 12px;
    color: #475569;
    font-size: 13px;
}

.free-chat-workspace,
.planning-workspace {
    min-height: 640px;
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
    max-width: 1180px !important;
    width: 1180px !important;
    margin: 0 auto !important;
    padding-left: 18px !important;
    padding-right: 18px !important;
}

footer,
footer.footer,
div[data-testid="footer"] {
    display: none !important;
}

.admin-shell {
    gap: 14px !important;
}

.admin-header {
    border-bottom: 1px solid #e2e8f0;
    padding: 18px 0 12px 0;
}

.admin-header h1 {
    margin-bottom: 4px !important;
    font-size: 32px !important;
    font-weight: 700 !important;
}

.admin-header p {
    color: #64748b;
    margin-top: 0 !important;
}

.admin-menu {
    border: 1px solid #e2e8f0;
    border-radius: 8px;
    background: #ffffff;
    padding: 12px;
}

.admin-menu .tab-nav {
    border-bottom: 1px solid #e2e8f0;
    margin-bottom: 14px;
}

.admin-section {
    min-height: 520px;
    padding-top: 6px;
}

.admin-section h2 {
    margin-top: 0 !important;
    margin-bottom: 12px !important;
    font-size: 22px !important;
}

.admin-placeholder {
    color: #64748b;
}

.user-record-toolbar {
    align-items: end !important;
    margin-bottom: 8px;
}

.user-record-detail {
    align-items: flex-start !important;
    margin-top: 12px;
}

.user-record-detail > div {
    min-height: 360px;
}
"""
