"""Generate signature-only stubs from contracts/api-v1.yaml (Lab Manual 7.4.2).

One stub module per `x-module`, written to contracts/generated/<module>_stub.py.
Each operation becomes `def <snake_case(operationId)>`: request properties marked
`x-icom: input` are positional, `x-icom: control` keyword-only (Table F-2), in
contract order. The return is the single output, or a tuple in `x-return-order`.

Run: python3 contracts/generate_stubs.py           (needs PyYAML)
     python3 contracts/generate_stubs.py --check   (CI: fail if a stub differs from the contract)
The stubs are regenerated from the contract, never edited by hand.
"""

import re
import sys
from datetime import timedelta
from pathlib import Path

import yaml

CONTRACT = Path(__file__).resolve().parent / "api-v1.yaml"
OUT = CONTRACT.parent / "generated"
JSON_TYPES = {"object": "dict", "array": "list", "string": "str", "number": "float",
              "integer": "int", "boolean": "bool"}


def snake(name: str) -> str:
    return re.sub(r"(?<!^)(?=[A-Z])", "_", name).lower()


def schema_ref_parts(ref: str) -> list:
    return ref.lstrip("#/").split("/")


def deref(schema: dict, spec: dict) -> dict:
    while "$ref" in schema:
        node = spec
        for part in schema_ref_parts(schema["$ref"]):
            node = node[part]
        schema = node
    return schema


def py_type(schema: dict, spec: dict, optional: bool = False) -> str:
    # The Python annotation: x-python-type (on the property or its schema) wins over
    # the wire type. Nullable, or optional with no default, becomes Optional[...].
    nullable = optional or schema.get("nullable", False)
    if "allOf" in schema:
        schema = {**{k: v for k, v in schema.items() if k != "allOf"}, **deref(schema["allOf"][0], spec)}
    base = schema.get("x-python-type")
    schema = deref(schema, spec)
    nullable = nullable or schema.get("nullable", False)
    base = base or schema.get("x-python-type")
    if base is None:
        base = "object" if "type" not in schema else JSON_TYPES.get(schema["type"], "object")
    base = base.replace("datetime.timedelta", "timedelta")
    return f"Optional[{base}]" if nullable else base


def default_literal(prop: dict, spec: dict) -> str:
    # The Python default: the schema's x-default when it is a Python expression
    # (e.g. "timedelta(days=90)"), else None, meaning "the implementation's
    # configured value" (e.g. the known metrics list, whose x-default is prose).
    for node in (prop, deref(prop, spec)):
        if "x-default" in node:
            value = node["x-default"]
            if value is None:
                return "None"
            try:
                eval(str(value), {"timedelta": timedelta})  # noqa: S307 -- contract text, checked only
                return str(value)
            except Exception:
                return "None"
    return "None"


def render(op_id: str, op: dict, spec: dict) -> str:
    body = op["requestBody"]["content"]["application/json"]["schema"]
    body = deref(body, spec)
    required = set(body.get("required", []))
    inputs, controls = [], []
    for name, prop in body.get("properties", {}).items():
        role = prop.get("x-icom")
        if role not in ("input", "control"):
            raise ValueError(f"{op_id}.{name}: x-icom must be input or control")
        if name in required:
            annotated = f"{name}: {py_type(prop, spec)}"
        else:
            default = default_literal(prop, spec)
            annotated = f"{name}: {py_type(prop, spec, optional=default == 'None')} = {default}"
        (inputs if role == "input" else controls).append(annotated)

    ok = op["responses"]["200"]["content"]["application/json"]["schema"]
    ok = deref(ok, spec)
    outputs = ok.get("x-return-order") or op["responses"]["200"].get("x-return-order") or list(ok.get("properties", {}))
    out_types = [py_type(ok["properties"][o], spec) for o in outputs]
    returns = out_types[0] if len(out_types) == 1 else f"tuple[{', '.join(out_types)}]"

    params = ", ".join(inputs + (["*"] + controls if controls else []))
    raises = sorted({r.get("x-python-raises") for code, r in op["responses"].items()
                     if code != "200" and r.get("x-python-raises")})
    doc = [f"operationId: {op_id}. {op.get('summary', '')}".rstrip(),
           "",
           f"in: {', '.join(n.split(':')[0] for n in inputs) or '-'}."
           f" control: {', '.join(c.split(':')[0] for c in controls) or '-'}."
           f" out: {', '.join(outputs)}."]
    if raises:
        doc.append(f"raises: {', '.join(raises)}.")
    doc_text = "\n    ".join(doc)
    return (f"def {snake(op_id)}({params}) -> {returns}:\n"
            f'    """{doc_text}\n    """\n'
            f"    raise NotImplementedError  # implemented in backend/provide_llm_selection_decision_support/"
            f"{op['x-module']}.py\n")


def main(check: bool = False) -> None:
    spec = yaml.safe_load(CONTRACT.read_text())
    modules = {}
    for path, item in spec["paths"].items():
        for method, op in item.items():
            if method != "post":
                continue
            modules.setdefault(op["x-module"], []).append((op["x-idef0-function"], render(op["operationId"], op, spec)))
    version = spec["info"]["version"]
    files = {}
    for module, ops in sorted(modules.items()):
        functions = sorted({f for f, _ in ops})
        header = (f'"""GENERATED from contracts/api-v1.yaml (v{version}) -- do not hand-edit.\n'
                  f"Regenerate after changing the contract, never the other way around.\n\n"
                  f"{'; '.join(functions)}.\n"
                  f'"""\n\nfrom datetime import timedelta  # noqa: F401\nfrom typing import Optional  # noqa: F401\n\n\n')
        files[f"{module}_stub.py"] = header + "\n\n".join(src for _, src in ops)
    if check:
        on_disk = {f.name: f.read_text() for f in OUT.glob("*_stub.py")}
        stale = sorted(n for n in set(files) | set(on_disk) if files.get(n) != on_disk.get(n))
        if stale:
            sys.exit(f"stubs differ from contracts/api-v1.yaml v{version}: {', '.join(stale)} -- regenerate them")
        print(f"stubs match contracts/api-v1.yaml v{version}")
        return
    OUT.mkdir(exist_ok=True)
    for old in OUT.glob("*_stub.py"):
        old.unlink()
    for name, text in files.items():
        (OUT / name).write_text(text)
    print(f"generated {sum(len(o) for o in modules.values())} stubs in {len(modules)} modules from v{version}")


if __name__ == "__main__":
    main(check="--check" in sys.argv)
