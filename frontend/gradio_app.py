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
        if res.status_code == 200:
            return "Регистрация успешна! Теперь вы можете войти."
        return f"{res.json().get('detail', 'Ошибка регистрации')}"
    except Exception:
        return f"Ошибка сервера: {res.status_code}"

def handle_login(email: str, password: str) -> tuple[bool, Optional[str]]:
    headers = {"Content-Type": "application/json"}
    res = api_post("/auth/login", json_data={"email": email, "password": password}, headers=headers)
    if res.status_code == 200:
        try:
            return True, res.json()["access_token"]
        except Exception:
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
    if history is None:
        history = []
    if not message.strip(): return message, history
    history.append({"role": "user", "content": message})
    return "", history

def bot_response(history, token: Optional[str], history_html: str):
    if not token:
        history.append({"role": "assistant", "content": "Сначала необходимо авторизоваться."})
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
            except Exception:
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
        history.append({"role": "assistant", "content": f"Ошибка: {str(e)[:300]}"})
    
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
    with gr.Blocks(title="ПОПАТКУС RAG", fill_width=True, theme=gr.themes.Default()) as demo:
        token_state = gr.State(value=None)
        sidebar_state = gr.State(value=True)
        reg_status = gr.State(value="")
        
        with gr.Column(visible=True, elem_classes="auth-box") as auth_section:
            gr.Markdown("## ПОПАТКУС RAG", elem_classes="auth-header")
            gr.Markdown("Интеллектуальный ассистент по академическим регламентам ВШЭ", elem_classes="auth-subheader")
            email_inp = gr.Textbox(label="Email", placeholder="user@example.com", elem_classes="input-field")
            password_inp = gr.Textbox(label="Пароль", type="password", elem_classes="input-field")
            reg_message = gr.Markdown(value="", elem_classes="reg-message")
            with gr.Row(elem_classes="auth-buttons"):
                login_btn = gr.Button("Войти", variant="primary", elem_classes="btn-primary")
                register_btn = gr.Button("Регистрация", elem_classes="btn-outline")
        
        with gr.Column(visible=False, elem_classes="chat-wrapper") as chat_section:
            with gr.Row(elem_id="header-row", elem_classes="header-row"):
                with gr.Row(elem_classes="header-left"):
                    menu_btn = gr.Button("☰", size="sm", elem_classes="btn-icon")
                    gr.Markdown("# Ассистент ПОПАТКУС", elem_classes="header-title")
                logout_btn = gr.Button("Выйти ✕", size="sm", elem_classes="btn-logout")

            with gr.Row(equal_height=True, elem_id="main-row", elem_classes="main-row"):
                with gr.Column(scale=1, min_width=260, visible=True, elem_id="sidebar-col", elem_classes="sidebar") as sidebar_col:
                    gr.Markdown("### История запросов", elem_classes="sidebar-title")
                    history_html = gr.HTML(value='<div class="history-empty">История пуста</div>', elem_id="history-container")

                with gr.Column(scale=4, elem_id="chat-col", elem_classes="chat-area"):
                    chatbot = gr.Chatbot(label="", show_label=False, height=580, elem_classes="chatbot", show_copy_button=True, type="messages")
                    with gr.Row(elem_classes="input-container"):
                        txt = gr.Textbox(show_label=False, placeholder="Задайте вопрос по правилам и регламентам...", container=False, elem_id="txt", elem_classes="input-box", scale=8)
                        submit_btn = gr.Button("Отправить", variant="primary", elem_classes="btn-primary-chat", scale=1)
                    with gr.Row(elem_classes="chat-actions"):
                        clear_btn = gr.Button("Очистить контекст", size="sm", elem_classes="btn-outline-sm")

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
            .gradio-container { max-width: 100% !important; margin: 0 !important; background-color: #f8fafc !important; }
            body { background-color: #f8fafc !important; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif !important; }
            
            .auth-box { 
                max-width: 420px; 
                margin: 10vh auto !important; 
                padding: 32px !important; 
                background: #ffffff !important; 
                border: 1px solid #e2e8f0 !important; 
                border-radius: 12px !important; 
                box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 2px 4px -1px rgba(0, 0, 0, 0.03) !important; 
            }
            .auth-header h2 { text-align: center; color: #1e293b !important; font-weight: 700 !important; margin-bottom: 4px !important; font-size: 24px !important; }
            .auth-subheader p { text-align: center; color: #64748b !important; font-size: 14px !important; margin-bottom: 24px !important; }
            .reg-message p { text-align: center; margin-top: 12px; font-size: 14px !important; color: #2563eb !important; font-weight: 500; }
            .auth-buttons { gap: 12px; margin-top: 20px; }
            
            .chat-wrapper { 
                background: #ffffff !important; 
                max-width: 1440px !important; 
                margin: 0 auto !important; 
                height: 100vh !important; 
                display: flex !important; 
                flex-direction: column !important; 
                box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.05) !important;
            }
            
            .header-row { 
                padding: 14px 24px !important; 
                border-bottom: 1px solid #e2e8f0 !important; 
                background: #ffffff !important; 
                display: flex !important; 
                justify-content: space-between !important; 
                align-items: center !important; 
            }
            .header-left { display: flex !important; align-items: center !important; gap: 16px !important; }
            .header-title h1 { font-size: 18px !important; font-weight: 600 !important; color: #0f172a !important; margin: 0 !important; }
            
            .main-row { flex: 1 !important; display: flex !important; height: calc(100vh - 65px) !important; gap: 0 !important; overflow: hidden !important; }
            
            .sidebar { 
                background: #f8fafc !important; 
                border-right: 1px solid #e2e8f0 !important; 
                padding: 20px 16px !important; 
                display: flex !important; 
                flex-direction: column !important; 
                height: 100% !important; 
            }
            .sidebar-title h3 { 
                font-size: 12px !important; 
                font-weight: 700 !important; 
                color: #94a3b8 !important; 
                text-transform: uppercase !important; 
                letter-spacing: 0.05em !important; 
                margin-bottom: 16px !important; 
            }
            
            #history-container { display: flex; flex-direction: column; gap: 8px; overflow-y: auto; height: 100%; }
            .history-empty { color: #94a3b8; font-size: 13px; padding: 16px; text-align: center; border: 1px dashed #e2e8f0; border-radius: 6px; background: #ffffff; }
            .history-item { 
                background: #ffffff; 
                border: 1px solid #e2e8f0; 
                border-radius: 8px; 
                padding: 10px 14px; 
                font-size: 13px; 
                color: #334155; 
                cursor: pointer; 
                transition: all 0.2s ease; 
                white-space: nowrap; 
                overflow: hidden; 
                text-overflow: ellipsis; 
                box-shadow: 0 1px 2px rgba(0,0,0,0.02);
            }
            .history-item:hover { background: #f1f5f9; border-color: #cbd5e1; color: #0f172a; transform: translateY(-1px); }
            
            .chat-area { padding: 24px !important; display: flex !important; flex-direction: column !important; height: 100% !important; background: #ffffff !important; }
            .chatbot { border: 1px solid #e2e8f0 !important; border-radius: 10px !important; background: #ffffff !important; flex: 1 !important; overflow-y: auto !important; }
            
            .input-container { display: flex !important; gap: 12px !important; align-items: center !important; margin-top: 16px !important; }
            .input-box { border: 1px solid #cbd5e1 !important; border-radius: 8px !important; background: #ffffff !important; font-size: 15px !important; }
            .input-box:focus-within { border-color: #2563eb !important; box-shadow: 0 0 0 2px rgba(37, 99, 235, 0.1) !important; }
            
            .chat-actions { margin-top: 10px !important; display: flex !important; justify-content: flex-start !important; }
            
            .btn-primary { 
                background-color: #2563eb !important; color: #ffffff !important; 
                border: none !important; border-radius: 6px !important; font-weight: 500 !important; 
            }
            .btn-primary:hover { background-color: #1d4ed8 !important; }
            
            .btn-primary-chat { 
                background-color: #0f172a !important; color: #ffffff !important; 
                border: none !important; border-radius: 8px !important; font-weight: 500 !important; height: 46px !important;
            }
            .btn-primary-chat:hover { background-color: #1e293b !important; }
            
            .btn-outline { 
                background-color: #ffffff !important; color: #475569 !important; 
                border: 1px solid #cbd5e1 !important; border-radius: 6px !important; font-weight: 500 !important; 
            }
            .btn-outline:hover { background-color: #f8fafc !important; border-color: #94a3b8 !important; color: #0f172a !important; }
            
            .btn-outline-sm {
                background-color: #ffffff !important; color: #64748b !important; 
                border: 1px solid #e2e8f0 !important; border-radius: 6px !important; font-size: 12px !important; padding: 4px 12px !important; min-width: auto !important; width: auto !important;
            }
            .btn-outline-sm:hover { background-color: #f1f5f9 !important; border-color: #cbd5e1 !important; color: #334155 !important; }
            
            .btn-icon { 
                background-color: #ffffff !important; border: 1px solid #e2e8f0 !important; border-radius: 6px !important; 
                width: 36px !important; min-width: 36px !important; height: 36px !important; padding: 0 !important; font-size: 16px !important; color: #475569 !important;
            }
            .btn-icon:hover { background-color: #f1f5f9 !important; color: #0f172a !important; }
            
            .btn-logout { 
                background-color: #ffffff !important; color: #64748b !important; border: 1px solid #e2e8f0 !important; 
                border-radius: 6px !important; padding: 6px 14px !important; font-size: 13px !important; font-weight: 500 !important; width: auto !important; min-width: auto !important;
            }
            .btn-logout:hover { background-color: #fef2f2 !important; color: #dc2626 !important; border-color: #fca5a5 !important; }
            
            .input-field { margin-bottom: 14px !important; }
            
            ::-webkit-scrollbar { width: 6px; height: 6px; }
            ::-webkit-scrollbar-track { background: transparent; }
            ::-webkit-scrollbar-thumb { background: #cbd5e1; border-radius: 3px; }
            ::-webkit-scrollbar-thumb:hover { background: #94a3b8; }
            
            @media (max-width: 768px) {
                .main-row { flex-direction: column !important; height: auto !important; overflow: auto !important; }
                .sidebar { border-right: none !important; border-bottom: 1px solid #e2e8f0 !important; height: 200px !important; }
                .chat-area { height: calc(100vh - 265px) !important; }
            }
        """
    )

if __name__ == "__main__":
    launch()
