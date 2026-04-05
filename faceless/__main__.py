from .cli import main
import sys
import traceback

def _wait_for_keypress() -> None:
    try:
        import msvcrt

        print("Press any key to close...", flush=True)
        msvcrt.getch()
    except Exception:
        try:
            input("Press Enter to close...")
        except Exception:
            pass

if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except SystemExit:
        raise
    except Exception:
        traceback.print_exc()
        _wait_for_keypress()
        sys.exit(1)
