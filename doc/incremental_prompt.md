Below is a **generic, reusable, concise prompt template**.
You can change only the file name (e.g., `base_parser.py`, `java_parser.py`, `symbol_table.py`) and reuse everything else.

---

# ✅ Reusable Engineering Prompt Template

**Task:** Generate `<TARGET_FILE_NAME>` for the IR Generation Engine.

---

## 1️⃣ Pre-Implementation Discipline

* Analyze all prior architectural context carefully.
* Ask clarifying questions only if necessary to prevent structural mistakes.
* Explicitly list assumptions.
* Explicitly define what is out of scope for MVP.

---

## 2️⃣ Architectural Constraints

* Follow the established git folder structure.
* Respect strict layered architecture.
* Do NOT mix responsibilities across layers.
* This file must only handle its intended concern.
* No silent coupling with graph builders or symbol resolution unless explicitly required.

---

## 3️⃣ MVP Guidelines

* Implement only what is required for MVP.
* Keep architecture extensible.
* If extensibility is not required for MVP, explicitly justify.
* Avoid over-engineering.
* No premature optimizations.

---

## 4️⃣ Structural & Accuracy Requirements

* Carefully align with previously discussed AST/IR examples (e.g., OrderService via javalang).
* Do not drop nodes or flatten structure silently.
* Preserve:

  * Node types
  * Source location
  * Relationships
  * Metadata
* Ensure compatibility with downstream graph builders.

---

## 5️⃣ Modeling & Validation

* Use strongly typed models (Pydantic preferred).
* Ensure models are JSON serializable.
* Enforce validation where appropriate.
* Avoid global mutable state.

---

## 6️⃣ Logging & Observability

* Use structured logging (no print statements).
* Log:

  * File start/end
  * Node creation
  * Relationship linking
  * Validation failures
  * Error conditions
* Include contextual metadata (file path, node type, IDs).
* Logging should support large-scale troubleshooting (1000+ files).

---

## 7️⃣ Stability & Determinism

* Node IDs must be deterministic OR clearly marked as temporary.
* If using UUID for MVP, document limitation.
* Mention future deterministic strategy if applicable.

---

## 8️⃣ Explicit Non-Goals

Unless explicitly required, do NOT implement:

* Call Graph
* CFG
* DFG
* Dependency Graph
* Symbol resolution
* Interprocedural analysis
* Optimization passes

---

## 9️⃣ Deliverables

Provide:

* Assumptions
* MVP scope clarification
* Full `<TARGET_FILE_NAME>` implementation
* Design explanation (brief)
* Known limitations
* Recommended next step

---

### Usage Example

Replace:

```
<TARGET_FILE_NAME>
```

With:

* `base_parser.py`
* `java_parser.py`
* `symbol_table.py`
* `call_graph_builder.py`
* etc.

Everything else remains reusable.

---

