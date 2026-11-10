"""Serialize the graph, render it locally and display the result."""

import os
import shutil
import subprocess
import sys

PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"
RENDER_TIMEOUT_SECONDS = 45


def plantuml(graph, root):
    """Write one rectangle per package version and one arrow per edge."""
    aliases = {node: f"p{i}" for i, node in enumerate(graph)}
    lines = [
        "@startuml",
        "!pragma layout smetana",
        "skinparam shadowing false",
    ]
    for node, alias in aliases.items():
        color = " #LightBlue" if node == root else ""
        if node.version is None:
            color = " #LightGray"
        lines.append(f'rectangle "{node.label()}" as {alias}{color}')
    for node, children in graph.items():
        lines.extend(f"{aliases[node]} --> {aliases[c]}" for c in children)
    return "\n".join([*lines, "@enduml", ""])


def ascii_tree(graph, root):
    """Show a tree with explicit markers for cycle edges and shared vertices."""
    active, expanded = set(), set()

    def walk(node, prefix):
        active.add(node)
        expanded.add(node)
        for index, child in enumerate(graph[node], 1):
            last = index == len(graph[node])
            branch = "\\-- " if last else "+-- "
            line = prefix + branch + child.label()
            if child in active:
                yield line + " [cycle]"
            elif child in expanded:
                yield line + " [seen]"
            else:
                yield line
                padding = "    " if last else "|   "
                yield from walk(child, prefix + padding)
        active.remove(node)

    return "\n".join([root.label(), *walk(root, "")])


def renderer():
    """Use an explicit PlantUML jar or an installed plantuml executable."""
    jar = os.environ.get("PLANTUML_JAR")
    if jar:
        return [
            "java", "-Xmx256m", "-Djava.awt.headless=true",
            "-DPLANTUML_SECURITY_PROFILE=SECURE", "-jar", jar,
        ]
    executable = shutil.which("plantuml")
    if executable:
        return [executable]
    raise ValueError("Укажите PLANTUML_JAR или запустите с --puml-only")


def render_png(source):
    """Run the local renderer with bounded time and verify its output."""
    try:
        result = subprocess.run(
            [*renderer(), "-charset", "UTF-8", "-pipe", "-tpng", "-failfast2"],
            input=source.encode("utf-8"), capture_output=True, check=False,
            timeout=RENDER_TIMEOUT_SECONDS,
        )
    except subprocess.TimeoutExpired:
        raise ValueError("PlantUML не завершился за 45 секунд") from None
    if result.returncode or not result.stdout.startswith(PNG_SIGNATURE):
        message = result.stderr.decode("utf-8", errors="replace").strip()
        details = message[:500] or "не удалось создать PNG"
        raise ValueError(f"PlantUML: {details}")
    return result.stdout


def show_image(path):
    """Open the PNG in the system image viewer on macOS or desktop Linux."""
    command = "open" if sys.platform == "darwin" else "xdg-open"
    try:
        subprocess.run(
            [command, str(path.resolve())], check=True, timeout=10,
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        )
    except (OSError, subprocess.SubprocessError):
        raise ValueError(
            f"Не удалось открыть PNG. Откройте файл вручную: {path}"
        ) from None


def write_visualization(graph, root, directory, puml_only, no_open):
    """Save the PlantUML source and, when requested, its rendered image."""
    directory.mkdir(parents=True, exist_ok=True)
    source_path = directory / f"{root.name}.puml"
    source = plantuml(graph, root)
    source_path.write_text(source, encoding="utf-8")
    print(f"PlantUML: {source_path}")
    if not puml_only:
        image_path = source_path.with_suffix(".png")
        image_path.write_bytes(render_png(source))
        print(f"PNG: {image_path}")
        if not no_open:
            show_image(image_path)
