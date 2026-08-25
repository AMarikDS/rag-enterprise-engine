import reflex as rx

def glass_box(*children, **props) -> rx.Component:
    """A glassmorphism container."""
    return rx.box(
        *children,
        background="rgba(255, 255, 255, 0.05)",
        backdrop_filter="blur(10px)",
        border="1px solid rgba(255, 255, 255, 0.1)",
        border_radius="15px",
        box_shadow="0 8px 32px 0 rgba(0, 0, 0, 0.3)",
        padding="20px",
        **props
    )

def navbar() -> rx.Component:
    return glass_box(
        rx.hstack(
            rx.heading("RAG System", size="6", color="white", font_family="Inter"),
            rx.spacer(),
            rx.link(
                rx.button("Чат", variant="soft", color_scheme="cyan", size="3"),
                href="/"
            ),
            rx.link(
                rx.button("Настройки", variant="soft", color_scheme="cyan", size="3"),
                href="/settings"
            ),
            align_items="center",
            width="100%"
        ),
        margin_bottom="20px",
    )

def chat_bubble(text: str, is_user: bool, sources: list[str] = []) -> rx.Component:
    return rx.box(
        rx.vstack(
            rx.text(text, color="white", font_size="16px"),
            rx.cond(
                sources,
                rx.vstack(
                    rx.text("Источники:", font_size="12px", color="gray", margin_top="10px"),
                    rx.foreach(
                        sources,
                        lambda s: rx.box(
                            rx.text(s, font_size="11px", color="rgba(255,255,255,0.7)"),
                            background="rgba(0,0,0,0.3)",
                            padding="5px",
                            border_radius="5px",
                            margin_top="5px",
                        )
                    ),
                    align_items="start"
                ),
            ),
            align_items="start"
        ),
        background=rx.cond(is_user, "rgba(42, 133, 255, 0.2)", "rgba(255, 255, 255, 0.05)"),
        border="1px solid rgba(255, 255, 255, 0.1)",
        border_radius="15px",
        padding="15px",
        margin_y="10px",
        max_width="80%",
        align_self=rx.cond(is_user, "flex-end", "flex-start"),
        box_shadow="0 4px 15px rgba(0,0,0,0.1)",
        transition="all 0.3s ease",
    )
