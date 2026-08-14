import json
from pathlib import Path

from handlers import INPUT_REGISTRY, REGISTRY

FLOWS_PATH = Path(__file__).parent / "flows.json"


class Engine:
    def __init__(self, flows_path: Path = FLOWS_PATH):
        with open(flows_path, "r", encoding="utf-8") as f:
            self.flows = json.load(f)

    def new_session(self) -> dict:
        return {"node": self.flows["start"]}

    def render(self, node_id: str) -> str:
        node = self.flows["nodes"][node_id]
        lines = [node["message"]]

        if node.get("type") == "input":
            return "\n".join(lines)

        lines.append("")
        for opt in node.get("options", []):
            lines.append(f"{opt['key']}. {opt['label']}")
            if opt.get("description"):
                lines.append(f"   {opt['description']}")
        if "back" in node:
            lines.append("0. Volver")
        return "\n".join(lines)

    def handle_input(self, session: dict, user_input: str) -> str:
        node_id = session["node"]
        node = self.flows["nodes"][node_id]
        user_input = user_input.strip()

        if node.get("type") == "input":
            handler_fn = INPUT_REGISTRY[node["handler"]]
            result = handler_fn(session, user_input)
            if isinstance(result, tuple):
                reply, advance = result
            else:
                reply, advance = result, True
            if advance:
                session["node"] = node["next"]
            return reply + "\n\n" + self.render(session["node"])

        if user_input == "0" and "back" in node:
            session["node"] = node["back"]
            return self.render(session["node"])

        option = next(
            (o for o in node.get("options", []) if o["key"] == user_input), None
        )
        if option is None:
            return "No entendí esa opción 🤔\n\n" + self.render(node_id)

        if "goto" in option:
            session["node"] = option["goto"]
            return self.render(session["node"])

        if "handler" in option:
            handler_fn = REGISTRY[option["handler"]]
            reply = handler_fn(session)

            return reply + "\n\n" + self.render(session["node"])

        raise ValueError(f"Opción sin 'goto' ni 'handler': {option}")
