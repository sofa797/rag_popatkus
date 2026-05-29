import gradio as gr
import requests
from typing import Optional

API_URL = "http://127.0.0.1:8001/api/v1"

def api_get(endpoint: str, headers: dict = None):
    headers = headers or {}
    return requests.get(f"{API_URL}{endpoint}", headers=headers)

def api_post(endpoint: str, json_data: dict = None, headers: dict = None):
    headers = headers or {"Content-Type": "application/json"}
    if json_data:
        return requests.post(f"{API_URL}{endpoint}", json=json_data, headers=headers)
    return requests.post(f"{API_URL}{endpoint}", headers=headers)

def handle_register(email: str, password: str) -> str:
    headers = {"Content-Type": "application/json"}
    res = api_post("/auth/register", json_data={"email": email, "password": password}, headers=headers)
    try:
        return f"{res.json().get('detail', 'error')}"
    except:
        return f"{res.status_code}"

def handle_login(email: str, password: str) -> tuple[bool, Optional[str]]:
    headers = {"Content-Type": "application/json"}
    res = api_post("/auth/login", json_data={"email": email, "password": password}, headers=headers)
    if res.status_code == 200:
        try:
            return True, res.json()["access_token"]
        except:
            return False, None
    return False, None

def fetch_history_queries(token: Optional[str]) -> list:
    if not token: 
        return []
    try:
        headers = {"Authorization": f"Bearer {token}"}
        res = api_get("/rag/history", headers=headers)
        if res.status_code == 200:
            return [item["query"] for item in res.json()[:50][::-1]]
    except Exception:
        pass
    return []

def format_history_html(queries: list) -> str:
    if not queries:
        return '<div class="history-empty">История пуста</div>'
    
    html = '<div class="history-container">'
    for q in queries:
        safe_q = q.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;').replace('"', '&quot;').replace("'", "\\'")
        display_q = q[:65] + '…' if len(q) > 65 else q
        html += f'''
        <div class="history-item" onclick="const ta=document.querySelector('#txt textarea');if(ta){{ta.value='{safe_q}';ta.dispatchEvent(new Event('input',{{bubbles:true}}));}}">
            {display_q}
        </div>
        '''
    html += '</div>'
    return html

def user_message(message, history):
    if history is None: history = []
    if not message.strip(): return message, history
    history.append({"role": "user", "content": message})
    return "", history

def bot_response(history, token: Optional[str], history_html: str):
    if not token:
        history.append({"role": "assistant", "content": "firstly you need to enter"})
        return history, history_html
        
    if not history or history[-1]["role"] != "user": 
        return history, history_html
    
    raw_content = history[-1]["content"]
    query = raw_content[0].get("text", "") if isinstance(raw_content, list) else str(raw_content)
    if not query.strip(): 
        return history, history_html
    
    try:
        headers = {
            "Authorization": f"Bearer {token.strip()}",
            "Content-Type": "application/json"
        }
        res = api_post("/rag/ask", json_data={"query": query}, headers=headers)
        
        if res.status_code != 200:
            try:
                error_detail = res.json().get("detail", "Неизвестная ошибка")
            except:
                error_detail = res.text[:200]
            raise Exception(f"{res.status_code}: {error_detail}")
            
        data = res.json()
        answer = data["answer"]
        docs = data.get("sources", [])
        
        sources = "\n\n".join([
            f"**Страница:** {d['metadata'].get('page', '—')} | **Раздел:** {d['metadata'].get('section', '—')}\n{d['text'][:1000]}" 
            for d in docs
        ])
        final_output = f"{answer}\n\n---\n### ИСТОЧНИКИ:\n{sources}" if sources else answer
        history.append({"role": "assistant", "content": final_output})
        
    except Exception as e:
        history.append({"role": "assistant", "content": f"error: {str(e)[:300]}"})
    
    new_history = format_history_html(fetch_history_queries(token))
    return history, new_history

def clear_chat(): 
    return [], ""

def toggle_sidebar(visible): 
    return gr.update(visible=not visible), not visible

def on_login_success(success: bool, token: Optional[str]):
    if success and token:
        return (
            gr.update(visible=False),
            gr.update(visible=True),
            gr.update(visible=True),
            format_history_html(fetch_history_queries(token))
        )
    return gr.update(), gr.update(), gr.update(), gr.update()

def on_logout():
    return (
        None,
        [], "",
        gr.update(visible=True),
        gr.update(visible=False),
        gr.update(visible=False),
        '<div class="history-empty">История пуста</div>'
    )

def launch():
    with gr.Blocks(title="ПОПАТКУС RAG", fill_width=True) as demo:
        token_state = gr.State(value=None)
        sidebar_state = gr.State(value=True)
        reg_status = gr.State(value="")
        
        with gr.Group(visible=True, elem_classes="auth-box") as auth_section:
            gr.Markdown("### Авторизация", elem_classes="section-title")
            email_inp = gr.Textbox(label="Email", placeholder="user@example.com", elem_classes="input-field")
            password_inp = gr.Textbox(label="Пароль", type="password", elem_classes="input-field")
            reg_message = gr.Markdown(value="", elem_classes="reg-message")
            with gr.Row(elem_classes="auth-buttons"):
                login_btn = gr.Button("Войти", variant="primary", size="sm", elem_classes="btn-primary")
                register_btn = gr.Button("Регистрация", size="sm", elem_classes="btn-outline")
        
        with gr.Group(visible=False, elem_classes="chat-wrapper") as chat_section:
            with gr.Row(elem_id="header-row", elem_classes="header-row"):
                menu_btn = gr.Button("☰", size="sm", elem_classes="btn-icon")
                gr.Markdown("Ассистент ПОПАТКУС", elem_classes="header-title")
                logout_btn = gr.Button("✕", size="sm", elem_classes="btn-logout")

            with gr.Row(equal_height=True, elem_id="main-row", elem_classes="main-row"):
                with gr.Column(scale=1, min_width=220, visible=False, elem_id="sidebar-col", elem_classes="sidebar") as sidebar_col:
                    gr.Markdown("История", elem_classes="sidebar-title")
                    history_html = gr.HTML(value='<div class="history-empty">История пуста</div>', elem_id="history-container")

                with gr.Column(scale=4, elem_id="chat-col", elem_classes="chat-area"):
                    chatbot = gr.Chatbot(label="", height=650, elem_classes="chatbot")
                    txt = gr.Textbox(show_label=False, placeholder="Введите вопрос…", container=False, elem_id="txt", elem_classes="input-box")
                    with gr.Row(elem_classes="chat-buttons"):
                        submit_btn = gr.Button("Отправить", variant="primary", size="sm", elem_classes="btn-primary")
                        clear_btn = gr.Button("Очистить", size="sm", elem_classes="btn-outline")

        register_btn.click(
            handle_register, 
            [email_inp, password_inp], 
            [reg_message]
        )
        
        login_btn.click(
            handle_login, 
            [email_inp, password_inp], 
            [reg_status, token_state]
        ).success(
            on_login_success,
            [reg_status, token_state],
            [auth_section, chat_section, sidebar_col, history_html]
        )

        logout_btn.click(
            on_logout,
            None,
            [token_state, chatbot, txt, auth_section, chat_section, sidebar_col, history_html]
        )

        menu_btn.click(toggle_sidebar, [sidebar_state], [sidebar_col, sidebar_state], queue=False)
        
        submit_btn.click(user_message, [txt, chatbot], [txt, chatbot], queue=False).then(
            bot_response, [chatbot, token_state, history_html], [chatbot, history_html]
        )
        
        txt.submit(user_message, [txt, chatbot], [txt, chatbot], queue=False).then(
            bot_response, [chatbot, token_state, history_html], [chatbot, history_html]
        )
        
        clear_btn.click(clear_chat, outputs=[chatbot, txt], queue=False)

    demo.launch(
        server_name="0.0.0.0", 
        server_port=7860, 
        share=True,
        css="""
            .gradio-container { max-width: 100% !important; margin: 0 !important; background: #ffffff !important; }
            body { background: #ffffff !important; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif !important; }
            
            .input-field, .input-box, .chatbot, .auth-box, .sidebar, .chat-area {
                background: #ffffff !important;
                border: 1px solid #94a3b8 !important;
                border-radius: 6px !important;
                box-shadow: none !important;
            }
            
            .auth-box { max-width: 400px; margin: 60px auto; padding: 24px; }
            .section-title { text-align: center; margin-bottom: 16px; color: #334155; font-weight: 600; }
            .reg-message { text-align: center; margin-top: 12px; font-size: 14px; color: #334155; }
            .auth-buttons { gap: 8px; margin-top: 12px; }
            
            .btn-primary {
                background: #ffffff !important; color: #0f172a !important;
                border: 2px solid #0f172a !important; border-radius: 4px !important;
                font-weight: 500 !important; transition: all 0.15s ease !important;
            }
            .btn-primary:hover { background: #0f172a !important; color: #ffffff !important; }
            
            .btn-outline {
                background: #ffffff !important; color: #475569 !important;
                border: 1px solid #94a3b8 !important; border-radius: 4px !important;
                font-weight: 400 !important; transition: all 0.15s ease !important;
            }
            .btn-outline:hover { border-color: #475569 !important; color: #0f172a !important; }
            
            .btn-icon {
                background: #ffffff !important; border: 1px solid #94a3b8 !important;
                border-radius: 4px !important; width: 32px !important; min-width: 32px !important;
                padding: 0 !important; font-size: 14px !important;
            }
            
            .btn-logout {
                background: #ffffff !important; color: #64748b !important;
                border: 1px solid #cbd5e1 !important; border-radius: 4px !important;
                width: 28px !important; min-width: 28px !important; height: 28px !important;
                padding: 0 !important; font-size: 12px !important; line-height: 1 !important;
                transition: all 0.15s ease !important;
            }
            .btn-logout:hover { border-color: #94a3b8 !important; color: #0f172a !important; background: #f8fafc !important; }
            
            .header-row { padding: 12px 16px; border-bottom: 1px solid #e2e8f0; align-items: center; }
            .header-title { font-size: 16px; font-weight: 600; color: #334155; margin: 0; }
            
            .main-row { height: calc(100vh - 60px); gap: 0; }
            
            .sidebar {
                border-right: 1px solid #e2e8f0 !important; border-radius: 0 !important;
                padding: 16px !important; height: 100%; box-sizing: border-box;
            }
            .sidebar-title {
                font-size: 13px; font-weight: 600; color: #64748b;
                text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 12px;
            }
            
            #history-container {
                display: flex; flex-direction: column; gap: 6px;
                max-height: calc(100% - 40px); overflow-y: auto; padding: 2px;
            }
            .history-empty { color: #94a3b8; font-size: 13px; padding: 12px 8px; text-align: center; }
            .history-item {
                background: #ffffff; border: 1px solid #cbd5e1; border-left: 2px solid #64748b;
                border-radius: 4px; padding: 8px 12px; font-size: 13px; color: #334155;
                cursor: pointer; transition: all 0.12s ease;
                white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
            }
            .history-item:hover { background: #f8fafc; border-left-color: #334155; border-color: #94a3b8; }
            .history-item:active { background: #f1f5f9; }
            
            .chat-area { padding: 16px !important; display: flex; flex-direction: column; }
            .chatbot { border-radius: 6px !important; margin-bottom: 12px; flex: 1; }
            .input-box { border-radius: 6px !important; margin-bottom: 10px; }
            .chat-buttons { gap: 8px; }
            
            ::-webkit-scrollbar { width: 5px; height: 5px; }
            ::-webkit-scrollbar-track { background: #f1f5f9; border-radius: 2px; }
            ::-webkit-scrollbar-thumb { background: #cbd5e1; border-radius: 2px; }
            ::-webkit-scrollbar-thumb:hover { background: #94a3b8; }
            
            @media (max-width: 768px) {
                .main-row { flex-direction: column; height: auto; }
                .sidebar { border-right: none !important; border-bottom: 1px solid #e2e8f0 !important; max-height: 200px; }
            }
        """
    )

if __name__ == "__main__":
    launch()
