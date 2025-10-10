
# stateSpace.stateSpaceTool

Object-oriented refactor of `state_space.py` with clean, testable architecture.

## Layout
```
stateSpace/stateSpaceTool/
  app.py      # Orchestration (app layer)
  apis.py     # Dataclasses for request/response
  cli.py      # Import shim so `python cli.py` works locally
  core.py     # Pure math realizations + realblocks transformer
  design.py   # Pretty printers, LaTeX, brief check, JSON dump
  io.py       # Parsers for forms: auto|zmin1|z|expr|zpk
  tools/
    class_diagram.py
  tests/
    test_app_example.py
    test_core_shapes.py
    test_realblocks.py
  in/
  out/
```

## Tests
```bash
pytest stateSpace/stateSpaceTool/tests -q
```
