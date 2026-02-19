
**Task:** Generate following the IR Generation Engine.
page_object_extractor.py
locator_extractor.py
assertion_mapper.py
action_mapper.py

---

### Requirements

* Analyze prior architecture context before coding.
* Ask clarifying questions only if necessary.
* State assumptions explicitly.
* MVP goal Focus on parser → AST → extraction → IR json
* Define MVP scope and what is out of scope.
* Build only what is required, let me know if it is not required for MVP

---

### Architecture Rules
* Respect strict layer separation.
* Implement only this file’s responsibility.
* Do not mix graph building, symbol resolution, or semantic logic unless explicitly required.

* Follow below git folder structure which was built earlier.
qa-migration-compiler/
│
├── README.md
├── pyproject.toml / requirements.txt
├── .gitignore
├── docker/
│     ├── Dockerfile
│     └── docker-compose.yml
│
├── config/
│     ├── default.yaml
│     ├── environments/
│     │      ├── dev.yaml
│     │      └── prod.yaml
│     └── logging.yaml
│
├── schemas/                      # JSON schema contracts
│     ├── ir/
│     │     ├── project.schema.json
│     │     ├── environment.schema.json
│     │     ├── test.schema.json
│     │     ├── targets.schema.json
│     │     └── suite.schema.json
│     └── ast/
│           └── ast_node.schema.json
│
├── src/
│     ├── main.py                 # CLI entry point
│     │
│     ├── core/                   # Compiler core
│     │     ├── pipeline.py
│     │     ├── context.py
│     │     ├── registry.py
│     │     └── exceptions.py
│     │
│     ├── parser/                 # Language parsers
│     │     ├── base_parser.py
│     │     ├── java/
│     │     │     ├── java_parser.py
│     │     │     ├── java_ast_adapter.py
│     │     │     └── symbol_resolver.py
│     │     └── python/
│     │           └── python_parser.py
│     │
│     ├── ast/                    # Canonical AST layer
│     │     ├── models.py         # (your ASTNode, ASTTree)
│     │     ├── builder.py
│     │     ├── hasher.py
│     │     └── metrics.py
│     │
│     ├── analysis/               # Static analysis modules
│     │     ├── call_graph/
│     │     │     ├── builder.py
│     │     │     └── resolver.py
│     │     │
│     │     ├── control_flow/
│     │     │     └── cfg_builder.py
│     │     │
│     │     ├── data_flow/
│     │     │     ├── dfg_builder.py
│     │     │     └── variable_tracker.py
│     │     │
│     │     ├── dependency/
│     │     │     ├── dependency_graph.py
│     │     │     └── invalidation_engine.py
│     │     │
│     │     └── complexity/
│     │           └── analyzer.py
│     │
│     ├── extraction/             # Domain extraction layer
│     │     ├── extractor.py
│     │     ├── page_object_extractor.py
│     │     ├── locator_extractor.py
│     │     ├── assertion_mapper.py
│     │     └── action_mapper.py
│     │
│     ├── ir/
│     │     ├── models/
│     │     │     ├── project.py
│     │     │     ├── environment.py
│     │     │     ├── test.py
│     │     │     ├── targets.py
│     │     │     ├── suite.py
│     │     │     └── data.py
│     │     │
│     │     ├── builder/
│     │     │     ├── test_ir_builder.py
│     │     │     ├── targets_ir_builder.py
│     │     │     ├── suite_ir_builder.py
│     │     │     └── project_ir_builder.py
│     │     │
│     │     ├── validator/
│     │     │     ├── schema_validator.py
│     │     │     └── reference_validator.py
│     │     │
│     │     └── writer/
│     │           ├── file_writer.py
│     │           └── deterministic_serializer.py
│     │
│     ├── optimization/
│     │     ├── rules/
│     │     │     ├── xpath_to_css.py
│     │     │     ├── redundant_wait_removal.py
│     │     │     └── flaky_pattern_detector.py
│     │     │
│     │     ├── ai/
│     │     │     └── llm_optimizer.py
│     │     │
│     │     └── confidence_scoring.py
│     │
│     ├── incremental/
│     │     ├── checksum_engine.py
│     │     ├── structural_hash.py
│     │     ├── change_detector.py
│     │     └── regeneration_planner.py
│     │
│     ├── execution/
│     │     ├── worker.py
│     │     ├── queue_adapter.py
│     │     └── batch_processor.py
│     │
│     ├── observability/
│     │     ├── metrics_collector.py
│     │     ├── timing_profiler.py
│     │     └── migration_logger.py
│     │
│     └── utils/
│           ├── file_utils.py
│           ├── hashing.py
│           └── graph_utils.py
│
├── tests/                         # Unit tests for compiler engine
│     ├── test_parser.py
│     ├── test_call_graph.py
│     ├── test_ir_builder.py
│     ├── test_dependency_graph.py
│     └── test_incremental.py
│
├── samples/
│     ├── selenium_input/
│     │     └── login_example.java
│     └── expected_ir_output/
│           └── TC_LOGIN_VALID_001.json
│
├── scripts/
│     ├── run_full_pipeline.sh
│     ├── run_incremental.sh
│     └── validate_ir.sh
│
└── output/                        # Generated IR (gitignored)
      ├── ir/
      ├── optimized_ir/
      └── dependency_graph.json

---

### MVP Principles
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

### Deliverables

* Full implementation for 
      page_object_extractor.py
      locator_extractor.py
      assertion_mapper.py
      action_mapper.py
* Minimal unit test file for each
* Brief Known limitations
* Recommended next step
