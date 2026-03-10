Pydantic validators allow you to inject custom logic into the data parsing and validation lifecycle. If you are seeing a mix of `@validator` and `@field_validator` in the wild, you are looking across the boundary of a major architectural rewrite. 

Pydantic v1 was pure Python. Pydantic v2 delegated its core parsing and validation to `pydantic-core`, written in Rust. This shift fundamentally changed how custom Python validators interface with the underlying engine, resulting in new decorators and execution modes.

Here is how to navigate the v1 vs. v2 paradigms, how the decorators actually work, and how to use them effectively in a FastAPI context.

### The v1 vs. v2 Divide

*   **`@validator` (v1/Legacy):** The old standard. It implicitly converted the decorated method into a class method, accepted a `values` dictionary for cross-field validation, and ran Python logic intermixed with type coercion.
*   **`@field_validator` (v2/Current):** The modern standard. It explicitly hooks into the Rust validation engine. It drops the `values` dict (cross-field validation is now handled differently) and requires you to specify exactly *when* the Python function should run relative to the Rust core using validation modes.

### `@field_validator` Mechanics and Signatures

In v2, field validators are strictly class methods. While Pydantic will magically wrap them if you forget, you should explicitly use `@classmethod` to ensure static type checkers (like mypy or pyright) do not complain about `self` vs `cls`.

```python
from pydantic import BaseModel, field_validator, ValidationInfo
from typing import Any

class ConfigModel(BaseModel):
    environment: str

    @field_validator('environment')
    @classmethod
    def normalize_env(cls, v: Any, info: ValidationInfo) -> str:
        # 'v' is the value being validated
        # 'info' provides context, including other already-validated fields
        return v.lower().strip()
```

#### Validation Modes: `before` vs `after`

Because Pydantic v2 is backed by Rust, you must decide whether your Python function runs before or after the Rust engine attempts to parse and coerce the input.

*   **`mode='after'` (Default):** Runs *after* Pydantic has successfully parsed the input into the target Python type. 
    *   **The Guarantee:** `v` is guaranteed to match your type annotation.
    *   **Use Cases:** Bounds checking, mathematical validation, or enforcing business logic constraints (e.g., ensuring a string matches a specific regex pattern).
*   **`mode='before'`:** Runs *before* Pydantic does anything. 
    *   **The Guarantee:** None. `v` is the raw input (usually an `Any`, typically a string or dictionary depending on the JSON payload).
    *   **Use Cases:** String normalization, deserializing legacy formats, handling structural changes before Pydantic attempts strict type coercion.

### Cross-Field Validation: `@model_validator`

In v1, you accessed previously validated fields via a `values` dict in `@validator`. In v2, `@field_validator` does not have access to the full model state (only what has been parsed so far via `ValidationInfo`). 

For cross-field validation, v2 introduces `@model_validator`. 

When used with `mode='after'` (the most common pattern), it operates as an instance method. You receive the fully constructed and validated model instance (`self`), making cross-field logic perfectly type-safe.

### FastAPI Integration Example

Here is a practical example of a FastAPI endpoint for an ML model deployment configuration. It demonstrates string pre-processing (`before`), logical assertions (`after`), and cross-field validation (`model_validator`).

```python
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, field_validator, model_validator, ValidationInfo
from typing_extensions import Self
import re

app = FastAPI()

class ModelDeploymentConfig(BaseModel):
    model_uri: str
    batch_size: int
    use_gpu: bool

    # 1. Before Validator: Normalize raw input before type coercion
    @field_validator('model_uri', mode='before')
    @classmethod
    def normalize_uri(cls, v: str) -> str:
        if not isinstance(v, str):
            raise ValueError("model_uri must be a string")
        # Strip trailing slashes and normalize prefixes
        v = v.strip().rstrip('/')
        if v.startswith("s3://") or v.startswith("gs://"):
            return v
        return f"s3://{v}" # Default to S3

    # 2. After Validator: Enforce bounds on a strongly typed value
    @field_validator('batch_size', mode='after')
    @classmethod
    def check_power_of_two(cls, v: int) -> int:
        if v <= 0 or (v & (v - 1)) != 0:
            raise ValueError("batch_size must be a power of 2")
        return v

    # 3. Model Validator: Cross-field business logic
    @model_validator(mode='after')
    def validate_gpu_requirements(self) -> Self:
        # 'self' is the fully parsed ModelDeploymentConfig instance
        if self.use_gpu and self.batch_size < 16:
            raise ValueError("GPU deployments require a batch_size of at least 16")
        return self

@app.post("/deploy")
async def deploy_model(config: ModelDeploymentConfig):
    # If the code reaches here, the payload is 100% normalized and valid.
    return {"status": "deploying", "uri": config.model_uri}
```

### Common Gotchas

1.  **Forgetting to return the value:** Validators in Pydantic are functionally mutating mappings. If your validator function returns nothing, Pydantic will silently assign `None` to the field. You must return `v` (or the mutated `v`).
2.  **Performance overhead:** Every custom Python validator triggers an FFI (Foreign Function Interface) boundary crossing between Python and the Rust `pydantic-core`. If you have heavily nested data or high-throughput endpoints, prefer Pydantic's built-in constraints (e.g., `Field(gt=0, pattern=r"...")`) over custom Python validators whenever possible.
3.  **Order of execution:** Fields are evaluated in the order they are defined in the class. If you rely on `info.data` inside a `@field_validator` to access previously parsed fields, be aware that a field defined *lower* in the class cannot be accessed by a field defined *higher* up. If order matters, use `@model_validator(mode='after')`.

### Related Concepts

*   **`Annotated` Validators:** In Pydantic v2, you can decouple validation logic from the model using `typing.Annotated` combined with `BeforeValidator` or `AfterValidator`. This allows you to create highly reusable, composable types (e.g., `NormalizedString = Annotated[str, BeforeValidator(strip_spaces)]`) rather than relying on class inheritance.
*   **`@computed_field`:** If you need to derive a field's value based on other fields but want it included in the serialized output (e.g., returning `model_dump()`), use `@computed_field` instead of mutating state inside a validator.