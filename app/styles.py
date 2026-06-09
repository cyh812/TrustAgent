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

PROFILE_CSS = """
.gradio-container {
    max-width: 920px !important;
    width: 920px !important;
    margin: 0 auto !important;
    padding-left: 18px !important;
    padding-right: 18px !important;
}

footer,
footer.footer,
div[data-testid="footer"] {
    display: none !important;
}

.profile-panel,
.task-entry-panel {
    border: 1px solid #e2e8f0;
    border-radius: 8px;
    background: #ffffff;
    padding: 16px;
    margin-top: 12px;
}

.task-entry-panel {
    background: #f8fafc;
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
    height: 560px;
    min-height: 560px;
    overflow: hidden;
}

.custom-chat-window {
    height: 560px;
    min-height: 560px;
    overflow-y: auto;
    overflow-x: hidden;
    border: 1px solid #e2e8f0;
    border-radius: 8px;
    background: #f8fafc;
    padding: 18px;
}

.custom-chat-empty {
    min-height: 420px;
    display: flex;
    align-items: center;
    justify-content: center;
    color: #94a3b8;
}

.custom-topic-card {
    width: min(760px, 92%);
    margin: 0 auto 18px auto;
    border: 1px solid #dbe4ef;
    border-radius: 8px;
    background: #ffffff;
    padding: 12px 16px;
    text-align: center;
    box-shadow: 0 1px 2px rgba(15, 23, 42, 0.04);
}

.custom-topic-label {
    margin-bottom: 6px;
    color: #64748b;
    font-size: 12px;
    font-weight: 700;
}

.custom-topic-body {
    color: #0f172a;
    font-size: 15px;
    line-height: 1.55;
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

.planning-process-stack {
    align-self: flex-start;
    width: min(82%, 900px);
    display: flex;
    flex-direction: column;
    gap: 8px;
}

.planning-process-card {
    border: 1px dashed #cbd5e1;
    border-radius: 8px;
    background: #f8fafc;
    padding: 9px 11px;
    color: #475569;
}

.planning-process-label {
    margin-bottom: 4px;
    color: #64748b;
    font-size: 12px;
    font-weight: 700;
}

.planning-process-body {
    color: #334155;
    font-size: 14px;
    line-height: 1.55;
}

.planning-rating-card {
    margin-bottom: 0 !important;
}

.planning-native-rating-row {
    width: min(760px, 94%) !important;
    margin: 8px auto 6px auto !important;
    align-items: center !important;
    gap: 10px !important;
    border: 1px solid #dbe4ef;
    border-radius: 8px;
    background: #ffffff;
    padding: 8px 10px;
    box-shadow: 0 1px 2px rgba(15, 23, 42, 0.04);
}

.planning-native-rating-radio {
    flex: 1 1 auto !important;
    margin: 0 !important;
    padding: 0 !important;
    border: 0 !important;
    background: transparent !important;
}

.planning-native-rating-radio > div,
.planning-native-rating-radio .wrap,
.planning-native-rating-radio .wrap-inner {
    width: 100% !important;
    margin: 0 !important;
    padding: 0 !important;
    border: 0 !important;
    background: transparent !important;
    box-shadow: none !important;
}

.planning-native-rating-radio .label-wrap,
.planning-native-rating-radio legend {
    display: none !important;
}

.planning-native-rating-radio fieldset {
    display: flex !important;
    flex-wrap: nowrap !important;
    gap: 8px !important;
    justify-content: space-between !important;
    margin: 0 !important;
    padding: 0 !important;
    border: 0 !important;
    background: transparent !important;
}

.planning-native-rating-radio label {
    flex: 1 1 0 !important;
    min-width: 38px !important;
    max-width: 52px !important;
    min-height: 36px !important;
    padding: 0 8px !important;
    justify-content: center !important;
    border-radius: 8px !important;
    border: 1px solid #dbe4ef !important;
    background: #ffffff !important;
    box-shadow: none !important;
    color: #0f172a !important;
}

.planning-native-rating-radio span {
    font-size: 14px !important;
    font-weight: 700 !important;
}

.planning-native-rating-radio input[type="radio"] {
    margin: 0 4px 0 0 !important;
}

.planning-native-rating-submit button {
    width: 100% !important;
    min-height: 38px !important;
    border-radius: 8px !important;
    font-size: 14px !important;
    font-weight: 700 !important;
    padding: 0 14px !important;
}

.planning-control-row {
    width: 100% !important;
    align-items: center !important;
    gap: 8px !important;
    margin: 10px 0 0 0 !important;
    border: 1px solid #dbe4ef;
    border-radius: 8px;
    background: #ffffff;
    padding: 8px 10px;
}

.planning-control-panel-wrap {
    min-width: 0 !important;
}

.planning-control-panel {
    display: flex;
    align-items: center;
    gap: 10px;
    min-width: 0;
}

.planning-control-progress {
    min-width: 0;
    flex: 1;
}

.planning-control-progress > div {
    justify-content: flex-start !important;
    margin-top: 0 !important;
    gap: 5px !important;
}

.planning-control-progress span {
    font-size: 11px !important;
    padding: 3px 7px !important;
}

.planning-control-hint {
    flex: 0 0 auto;
    color: #334155;
    font-size: 12px;
    font-weight: 700;
    white-space: nowrap;
}

.planning-control-hint.muted {
    color: #94a3b8;
    font-weight: 600;
}

.planning-native-rating-card {
    display: flex !important;
    align-items: center !important;
    gap: 8px !important;
    margin: 0 !important;
    padding: 0 !important;
    border: 0 !important;
    background: transparent !important;
    box-shadow: none !important;
    min-width: 330px !important;
}

.planning-score-radio {
    margin: 0 !important;
    padding: 0 !important;
    border: 0 !important;
    background: transparent !important;
}

.planning-score-radio fieldset {
    display: flex !important;
    flex-wrap: nowrap !important;
    gap: 4px !important;
    margin: 0 !important;
}

.planning-score-radio label {
    min-width: 30px !important;
    min-height: 30px !important;
    padding: 0 !important;
    justify-content: center !important;
    border-radius: 8px !important;
}

.planning-score-radio span {
    font-size: 13px !important;
    font-weight: 700 !important;
}

.planning-score-submit button {
    min-width: 54px !important;
    min-height: 32px !important;
    padding: 0 10px !important;
    border-radius: 8px !important;
    font-size: 13px !important;
    font-weight: 700 !important;
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

.custom-message-body p,
.custom-answer-body p,
.custom-topic-body p {
    margin: 0 0 8px 0;
}

.custom-message-body p:last-child,
.custom-answer-body p:last-child,
.custom-topic-body p:last-child {
    margin-bottom: 0;
}

.custom-message-body ul,
.custom-message-body ol,
.custom-answer-body ul,
.custom-answer-body ol {
    margin: 8px 0 8px 20px;
    padding-left: 16px;
}

.custom-message-body li,
.custom-answer-body li {
    margin: 4px 0;
}

.custom-message-body pre,
.custom-answer-body pre {
    max-width: 100%;
    overflow-x: auto;
    border-radius: 8px;
    background: #0f172a;
    color: #e2e8f0;
    padding: 10px 12px;
}

.custom-message-body code,
.custom-answer-body code {
    border-radius: 4px;
    background: #e2e8f0;
    padding: 1px 4px;
    font-size: 0.92em;
}

.custom-message-body pre code,
.custom-answer-body pre code {
    background: transparent;
    padding: 0;
    color: inherit;
}

.custom-message-body blockquote,
.custom-answer-body blockquote {
    margin: 8px 0;
    padding-left: 12px;
    border-left: 3px solid #cbd5e1;
    color: #475569;
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

.custom-trust-card {
    align-self: center;
    width: min(520px, 88%);
    border: 1px solid #dbe4ef;
    border-radius: 8px;
    background: #ffffff;
    padding: 12px 14px;
    text-align: center;
    box-shadow: 0 1px 2px rgba(15, 23, 42, 0.04);
}

.custom-trust-title {
    margin-bottom: 10px;
    color: #334155;
    font-size: 14px;
    font-weight: 700;
}

.custom-trust-scale {
    display: grid;
    grid-template-columns: repeat(7, 1fr);
    gap: 8px;
}

.custom-trust-scale span {
    display: flex;
    align-items: center;
    justify-content: center;
    height: 32px;
    border: 1px solid #cbd5e1;
    border-radius: 8px;
    color: #0f172a;
    background: #f8fafc;
    font-size: 14px;
    font-weight: 600;
}

.custom-trust-radio {
    width: 100% !important;
    margin: 0 !important;
    border: 1px solid #bfdbfe;
    border-radius: 8px;
    background: #eff6ff;
    padding: 14px 16px;
    box-shadow: 0 8px 20px rgba(37, 99, 235, 0.08);
}

.custom-trust-radio .label-wrap,
.custom-trust-radio legend {
    color: #1e3a8a !important;
    font-weight: 800 !important;
    font-size: 15px !important;
}

.custom-trust-radio fieldset {
    display: flex !important;
    flex-wrap: nowrap !important;
    gap: 8px !important;
    margin-top: 8px !important;
}

.custom-trust-radio label {
    min-width: 42px !important;
    min-height: 38px !important;
    justify-content: center !important;
    border: 1px solid #bfdbfe !important;
    border-radius: 8px !important;
    background: #ffffff !important;
    color: #0f172a !important;
    font-weight: 700 !important;
}

.trust-end-row {
    width: min(760px, 94%) !important;
    margin: 12px auto 10px auto !important;
    align-items: stretch !important;
    gap: 10px !important;
}

.trust-end-btn {
    display: flex !important;
    justify-content: center !important;
    align-items: center !important;
}

.trust-end-btn button {
    width: 100% !important;
    height: 100% !important;
    min-height: 56px !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    line-height: 1.2 !important;
    padding-top: 0 !important;
    padding-bottom: 0 !important;
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

.custom-composer {
    position: relative;
    width: 100%;
}

.custom-composer textarea {
    box-sizing: border-box;
    width: 100%;
    min-height: 58px;
    resize: vertical;
    padding: 13px 68px 13px 16px;
    border: 1px solid #cbd5e1;
    border-radius: 16px;
    color: #0f172a;
    background: #ffffff;
    font-size: 15px;
    line-height: 1.5;
    outline: none;
}

.custom-composer textarea:focus {
    border-color: #2563eb;
    box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.14);
}

.custom-composer button {
    position: absolute;
    right: 14px;
    bottom: 12px;
    width: 42px;
    min-width: 42px;
    height: 42px;
    border: 0;
    border-radius: 9999px;
    color: #ffffff;
    background: #2563eb;
    cursor: pointer;
    font-size: 18px;
    line-height: 1;
}

.custom-composer button:hover {
    background: #1d4ed8;
}

.hidden-composer-bridge {
    position: fixed !important;
    left: -10000px !important;
    top: auto !important;
    width: 1px !important;
    height: 1px !important;
    opacity: 0 !important;
    pointer-events: none !important;
    overflow: hidden !important;
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

.chat-config-layout {
    align-items: flex-start !important;
    margin-bottom: 10px;
}
"""
