import sys

import db
from engine import Engine

if sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stdin.reconfigure(encoding="utf-8")

def main():
    db.init_db()
    engine = Engine()
    session = engine.new_session()

    print("(Escribe 'salir' para terminar)\n")
    print(engine.render(session["node"]))

    while True:
        user_input = input("\n> ")
        if user_input.strip().lower() in ("salir", "exit", "quit"):
            print("¡Hasta pronto! 🧡")
            break
        print()
        print(engine.handle_input(session, user_input))


if __name__ == "__main__":
    main()
