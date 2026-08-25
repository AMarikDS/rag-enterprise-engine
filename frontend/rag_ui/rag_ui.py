import reflex as rx
from .state import State
from .components import glass_box, chat_bubble

def create_kb_dialog() -> rx.Component:
    return rx.dialog.root(
        rx.dialog.trigger(
            rx.button("Новая База Знаний", variant="soft", color_scheme="cyan", size="3", cursor="pointer", width="100%", margin_top="10px")
        ),
        rx.dialog.content(
            rx.dialog.title("Индексация новой базы", color="white"),
            rx.dialog.description("Загрузите новую папку с документами.", color="gray"),
            
            rx.vstack(
                rx.text("Название базы", color="gray", font_size="14px"),
                rx.input(placeholder="Например, docs_2026", value=State.new_kb_name, on_change=State.set_new_kb_name, width="100%", color="white", background="rgba(0,0,0,0.2)"),

                rx.text("Папка с документами", color="gray", font_size="14px", margin_top="10px"),
                rx.input(value=State.docs_dir, on_change=State.set_docs_dir, width="100%", color="white", background="rgba(0,0,0,0.2)"),
                
                rx.text("Размер чанка (chunk size)", color="gray", font_size="14px", margin_top="10px"),
                rx.slider(default_value=State.chunk_size, on_value_commit=State.set_chunk_size, min=100, max=2000, step=100, color_scheme="cyan"),
                rx.text(State.chunk_size, color="white", font_size="12px"),
                
                rx.text("Перекрытие (chunk overlap)", color="gray", font_size="14px", margin_top="10px"),
                rx.slider(default_value=State.chunk_overlap, on_value_commit=State.set_chunk_overlap, min=0, max=500, step=50, color_scheme="cyan"),
                rx.text(State.chunk_overlap, color="white", font_size="12px"),
                
                rx.hstack(
                    rx.dialog.close(rx.button("Отмена", color_scheme="gray", cursor="pointer")),
                    rx.button("Индексировать", on_click=State.start_indexing, color_scheme="cyan", loading=State.is_indexing, cursor="pointer"),
                    spacing="4",
                    margin_top="15px"
                ),
                rx.cond(
                    State.is_indexing,
                    rx.progress(value=State.indexing_progress_val, width="100%", color_scheme="cyan", margin_top="15px", variant="classic"),
                ),
                rx.cond(State.indexing_status != "", rx.text(State.indexing_status, color="yellow", margin_top="15px")),
                align_items="start",
                width="100%"
            ),
            background="#1e293b",
            border="1px solid rgba(255, 255, 255, 0.1)",
        )
    )

def sidebar() -> rx.Component:
    return glass_box(
        rx.vstack(
            rx.heading("RAG System", size="6", color="white", font_family="Inter", margin_bottom="20px"),
            
            rx.heading("Диалоги", size="4", color="white"),
            rx.vstack(
                rx.input(placeholder="Название чата...", value=State.new_session_name, on_change=State.set_new_session_name, size="2", background="rgba(0,0,0,0.2)", color="white", width="100%"),
                rx.select(State.kbs, placeholder="Выберите базу...", value=State.current_kb_name, on_change=lambda x: State.setvar("current_kb_name", x), size="2", color_scheme="cyan", width="100%"),
                rx.button("Создать чат", on_click=State.create_session, size="2", color_scheme="cyan", width="100%", cursor="pointer"),
                width="100%"
            ),
            rx.divider(margin_y="10px"),
            rx.vstack(
                rx.foreach(
                    State.sessions,
                    lambda s: rx.hstack(
                        rx.button(s["name"], on_click=State.select_session(s["id"]), variant=rx.cond(s["id"] == State.current_session_id, "solid", "ghost"), color_scheme="cyan", width="100%", justify="start", cursor="pointer"),
                        rx.button(rx.icon("trash", size=15), on_click=State.delete_session(s["id"]), variant="ghost", color_scheme="red", cursor="pointer"),
                        width="100%"
                    )
                ),
                width="100%",
                overflow_y="auto",
                height="30vh"
            ),
            
            rx.divider(margin_y="20px"),
            
            rx.heading("Базы Знаний", size="4", color="white"),
            rx.vstack(
                rx.foreach(
                    State.kbs,
                    lambda kb: rx.hstack(
                        rx.text(kb, color="white"),
                        rx.spacer(),
                        rx.button(rx.icon("trash", size=15), on_click=State.delete_kb(kb), variant="ghost", color_scheme="red", cursor="pointer"),
                        width="100%",
                        align_items="center"
                    )
                ),
                width="100%",
                overflow_y="auto",
                max_height="20vh"
            ),
            create_kb_dialog(),
            width="300px",
            align_items="start"
        ),
        height="calc(100vh - 40px)",
        margin_right="20px"
    )

def index() -> rx.Component:
    return rx.center(
        rx.hstack(
            sidebar(),
            glass_box(
                rx.vstack(
                    rx.cond(
                        State.current_session_id == "",
                        rx.center(rx.text("Создайте или выберите диалог слева", color="gray"), height="60vh", width="100%"),
                        rx.box(
                            rx.foreach(
                                State.chat_history,
                                lambda msg: chat_bubble(msg.text, msg.is_user, msg.sources)
                            ),
                            overflow_y="auto",
                            height="70vh",
                            width="100%",
                            display="flex",
                            flex_direction="column",
                            padding="10px"
                        )
                    ),
                    rx.cond(
                        State.is_loading,
                        rx.spinner(color="cyan", size="3"),
                    ),
                    rx.hstack(
                        rx.input(
                            placeholder="Задайте вопрос...",
                            value=State.current_query,
                            on_change=State.set_current_query,
                            on_key_down=State.on_key_down,
                            width="100%",
                            size="3",
                            variant="surface",
                            color_scheme="cyan",
                            background="rgba(255, 255, 255, 0.05)",
                            color="white",
                            disabled=State.current_session_id == ""
                        ),
                        rx.button(
                            "Отправить",
                            on_click=State.send_message,
                            size="3",
                            color_scheme="cyan",
                            variant="solid",
                            cursor="pointer",
                            disabled=State.current_session_id == ""
                        ),
                        width="100%",
                        margin_top="20px"
                    ),
                    width="100%"
                ),
                width="800px",
                max_width="100%"
            ),
            align_items="start",
            padding="20px",
            width="100%",
            max_width="1200px"
        ),
        background="linear-gradient(135deg, #0f172a 0%, #1e293b 100%)",
        min_height="100vh",
    )

app = rx.App(
    theme=rx.theme(appearance="dark", has_background=True, radius="large", accent_color="cyan"),
    stylesheets=["https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap"]
)
app.add_page(index, route="/", title="RAG Chat", on_load=State.init_data)
