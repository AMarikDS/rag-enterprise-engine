import reflex as rx
from .state import State
from .components import navbar, glass_box, chat_bubble

def index() -> rx.Component:
    return rx.center(
        rx.vstack(
            navbar(),
            glass_box(
                rx.vstack(
                    rx.box(
                        rx.foreach(
                            State.chat_history,
                            lambda msg: chat_bubble(msg.text, msg.is_user, msg.sources)
                        ),
                        overflow_y="auto",
                        height="60vh",
                        width="100%",
                        display="flex",
                        flex_direction="column",
                        padding="10px"
                    ),
                    rx.cond(
                        State.is_loading,
                        rx.spinner(color="cyan", size="3"),
                    ),
                    rx.hstack(
                        rx.input(
                            placeholder="Задайте вопрос по документам...",
                            value=State.current_query,
                            on_change=State.set_current_query,
                            on_key_down=rx.cond(
                                rx.args[0].key == "Enter",
                                State.send_message
                            ),
                            width="100%",
                            size="3",
                            variant="surface",
                            color_scheme="cyan",
                            background="rgba(255, 255, 255, 0.05)",
                            color="white"
                        ),
                        rx.button(
                            "Отправить",
                            on_click=State.send_message,
                            size="3",
                            color_scheme="cyan",
                            variant="solid"
                        ),
                        width="100%",
                        margin_top="20px"
                    ),
                    width="100%"
                ),
                width="800px",
                max_width="95%"
            ),
            width="100%",
            padding="20px",
            align_items="center"
        ),
        background="linear-gradient(135deg, #0f172a 0%, #1e293b 100%)",
        min_height="100vh",
    )

def settings_page() -> rx.Component:
    return rx.center(
        rx.vstack(
            navbar(),
            glass_box(
                rx.vstack(
                    rx.heading("Настройки RAG", size="5", color="white", margin_bottom="20px"),
                    
                    rx.text("Папка с документами (абсолютный путь)", color="gray", font_size="14px"),
                    rx.input(
                        value=State.docs_dir,
                        on_change=State.set_docs_dir,
                        width="100%",
                        margin_bottom="15px",
                        color="white",
                        background="rgba(0,0,0,0.2)"
                    ),
                    
                    rx.text("Размер чанка (chunk size)", color="gray", font_size="14px"),
                    rx.slider(
                        default_value=State.chunk_size,
                        on_value_commit=State.set_chunk_size,
                        min=100, max=2000, step=100,
                        margin_bottom="15px",
                        color_scheme="cyan"
                    ),
                    rx.text(State.chunk_size, color="white", font_size="12px", margin_bottom="15px"),
                    
                    rx.text("Перекрытие чанков (chunk overlap)", color="gray", font_size="14px"),
                    rx.slider(
                        default_value=State.chunk_overlap,
                        on_value_commit=State.set_chunk_overlap,
                        min=0, max=500, step=50,
                        margin_bottom="15px",
                        color_scheme="cyan"
                    ),
                    rx.text(State.chunk_overlap, color="white", font_size="12px", margin_bottom="20px"),
                    
                    rx.text("Выбор модели генерации", color="gray", font_size="14px"),
                    rx.select(
                        State.available_models,
                        value=State.selected_model,
                        on_change=State.set_selected_model,
                        width="100%",
                        margin_bottom="20px",
                        color_scheme="cyan"
                    ),
                    
                    rx.hstack(
                        rx.button("Сохранить настройки", on_click=State.update_settings, color_scheme="green"),
                        rx.button(
                            "Индексировать базу", 
                            on_click=State.start_indexing, 
                            color_scheme="cyan",
                            loading=State.is_indexing
                        ),
                        spacing="4"
                    ),
                    rx.cond(
                        State.indexing_status != "",
                        rx.text(State.indexing_status, color="yellow", margin_top="15px")
                    ),
                    
                    align_items="start",
                    width="100%"
                ),
                width="600px",
                max_width="95%"
            ),
            width="100%",
            padding="20px",
            align_items="center"
        ),
        background="linear-gradient(135deg, #0f172a 0%, #1e293b 100%)",
        min_height="100vh",
    )

app = rx.App(
    theme=rx.theme(appearance="dark", has_background=True, radius="large", accent_color="cyan"),
    stylesheets=["https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap"]
)
app.add_page(index, route="/", title="RAG Chat")
app.add_page(settings_page, route="/settings", title="RAG Settings")
