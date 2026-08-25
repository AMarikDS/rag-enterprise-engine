import reflex as rx
from .state import State
from .components import glass_box, chat_bubble

def settings_dialog() -> rx.Component:
    return rx.dialog.root(
        rx.dialog.trigger(
            rx.button("Настройки RAG", variant="soft", color_scheme="cyan", size="3", cursor="pointer")
        ),
        rx.dialog.content(
            rx.dialog.title("Настройки RAG", color="white"),
            rx.dialog.description("Конфигурация параметров индексации и генерации.", color="gray"),
            
            rx.vstack(
                rx.hstack(
                    rx.text("Папка с документами", color="gray", font_size="14px"),
                    rx.tooltip(rx.icon("info_circled", size=15, color="cyan"), content="Абсолютный путь к папке с вашими PDF. История чатов привязана к этой папке."),
                ),
                rx.input(value=State.docs_dir, on_change=State.set_docs_dir, width="100%", color="white", background="rgba(0,0,0,0.2)"),
                
                rx.hstack(
                    rx.text("Размер чанка (chunk size)", color="gray", font_size="14px"),
                    rx.tooltip(rx.icon("info_circled", size=15, color="cyan"), content="Размер кусочка текста (в символах). Больше чанк = больше контекста, но меньше точности поиска."),
                ),
                rx.slider(default_value=State.chunk_size, on_value_commit=State.set_chunk_size, min=100, max=2000, step=100, color_scheme="cyan"),
                rx.text(State.chunk_size, color="white", font_size="12px"),
                
                rx.hstack(
                    rx.text("Перекрытие чанков (chunk overlap)", color="gray", font_size="14px"),
                    rx.tooltip(rx.icon("info_circled", size=15, color="cyan"), content="Количество символов, которые повторяются между соседними чанками. Помогает не терять смысл на стыках."),
                ),
                rx.slider(default_value=State.chunk_overlap, on_value_commit=State.set_chunk_overlap, min=0, max=500, step=50, color_scheme="cyan"),
                rx.text(State.chunk_overlap, color="white", font_size="12px"),
                
                rx.hstack(
                    rx.text("Выбор модели", color="gray", font_size="14px"),
                    rx.tooltip(rx.icon("info_circled", size=15, color="cyan"), content="Flash - быстрая и дешевая. Pro - медленнее, но умнее для сложной аналитики."),
                ),
                rx.select(State.available_models, value=State.selected_model, on_change=State.set_selected_model, width="100%", color_scheme="cyan"),
                
                rx.hstack(
                    rx.dialog.close(rx.button("Сохранить", on_click=State.update_settings, color_scheme="green", cursor="pointer")),
                    rx.button("Индексировать базу", on_click=State.start_indexing, color_scheme="cyan", loading=State.is_indexing, cursor="pointer"),
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

def navbar() -> rx.Component:
    return glass_box(
        rx.hstack(
            rx.heading("RAG System", size="6", color="white", font_family="Inter"),
            rx.spacer(),
            settings_dialog(),
            align_items="center",
            width="100%"
        ),
        margin_bottom="20px",
    )

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
                            on_key_down=State.on_key_down,
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
                            variant="solid",
                            cursor="pointer"
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

app = rx.App(
    theme=rx.theme(appearance="dark", has_background=True, radius="large", accent_color="cyan"),
    stylesheets=["https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap"]
)
app.add_page(index, route="/", title="RAG Chat", on_load=State.load_history)
