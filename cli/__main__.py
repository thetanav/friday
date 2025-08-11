from main import app, _windows_loop_patch


def main() -> None:
    # Ensure Windows event loop policy is set for asyncio-based commands
    _windows_loop_patch()
    app()


if __name__ == "__main__":
    main()
