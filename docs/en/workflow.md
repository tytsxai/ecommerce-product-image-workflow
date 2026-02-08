# End-to-End Workflow

```mermaid
flowchart LR
    A[Supplier Images + Optional Notes] --> B[Intake Validation]
    B --> C[Showcase Image Generation]
    B --> D[Spec/How-to Text Extraction]
    D --> E[Template Rendering]
    C --> F[QA Gate]
    E --> F
    F -->|Pass| G[Export Assets]
    F -->|Fail| H[Reject + Rework]
    G --> I[Batch Record + Audit Log]
```

## Design choices

- Product region protection (mask/reference lock)
- Template-based text rendering for deterministic spec/how-to cards
- Style packs to reduce prompt variance

## Recommended roles

- Manager: intake + final pass/reject
- Ops/Brand: style and policy ownership
- Implementation: pipeline and QA automation
