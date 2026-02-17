---

**Task:** Generate `java_parser.py` for the IR Generation Engine.

---

### Requirements

* Analyze prior architecture context before coding.
* Ask clarifying questions only if necessary.
* State assumptions explicitly.
* Define MVP scope and what is out of scope.

---

### Architecture Rules

* Follow existing git folder structure.
* Respect strict layer separation.
* Implement only this file’s responsibility.
* Do not mix graph building, symbol resolution, or semantic logic unless explicitly required.

---

### MVP Principles

* Build only what is required.
* Keep design extensible but avoid over-engineering.
* Justify if extensibility is unnecessary for MVP.

---

### Technical Standards

* Preserve structural integrity (no silent node dropping).
* Use typed models (Pydantic preferred).
* Ensure JSON serializability.
* No global mutable state.
* Include structured logging (file start/end, node creation, errors).
* Ensure deterministic or clearly documented temporary IDs.

---

### Non-Goals (Unless Explicitly Required)

* Call Graph / CFG / DFG
* Dependency Graph
* Symbol resolution
* Interprocedural analysis
* Optimization logic

---

### Deliverables

* Assumptions
* MVP clarification
* Full `java_parser.py` implementation
* Brief design explanation
* Known limitations
* Recommended next step

---
