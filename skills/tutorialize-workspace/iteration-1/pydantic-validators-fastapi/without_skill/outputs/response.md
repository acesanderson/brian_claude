# Pydantic Validators in FastAPI

The short answer: `@validator` is the Pydantic v1 API, `@field_validator` is the Pydantic v2 API. If you're starting fresh, use `@field_validator`. FastAPI currently works with both, but Pydantic v2 is the default since FastAPI 0.100.0.

Here's what you actually need to know to use them effectively.

---

## The core idea

Pydantic validators are functions that run when a model is instantiated — either from a request body, query params, or direct construction. They let you enforce business logic beyond what type annotations alone can express.

Example: a type annotation can say a field is a `str`, but it can't say "must be a valid email" or "must be non-empty after stripping whitespace." Validators fill that gap.

---

## Pydantic v2: `@field_validator`

```python
from pydantic import BaseModel, field_validator

class UserCreate(BaseModel):
    username: str
    age: int

    @field_validator("username")
    @classmethod
    def username_must_be_nonempty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("username cannot be blank")
        return v.strip()

    @field_validator("age")
    @classmethod
    def age_must_be_positive(cls, v: int) -> int:
        if v < 0:
            raise ValueError("age must be non-negative")
        return v
```

Key points:
- Must be a `@classmethod` in v2 — this is a breaking change from v1
- The return value becomes the field's actual value — useful for normalization (stripping whitespace, lowercasing, etc.)
- Raise `ValueError` (not a custom exception) — Pydantic wraps it into its own `ValidationError`
- You can validate multiple fields in one decorator: `@field_validator("field_a", "field_b")`

### `mode` parameter

```python
@field_validator("username", mode="before")
@classmethod
def normalize_username(cls, v):
    return v.strip().lower()
```

- `mode="before"` — runs before Pydantic's type coercion. The value `v` might not be the declared type yet (could be raw input). Use this for normalization.
- `mode="after"` — runs after type coercion (default). The value is guaranteed to be the declared type.

---

## Pydantic v1: `@validator`

```python
from pydantic import BaseModel, validator

class UserCreate(BaseModel):
    username: str
    age: int

    @validator("username")
    def username_must_be_nonempty(cls, v):
        if not v.strip():
            raise ValueError("username cannot be blank")
        return v.strip()
```

Differences from v2:
- No `@classmethod` decorator required (though adding it doesn't break anything)
- Uses `pre=True` instead of `mode="before"`: `@validator("username", pre=True)`
- Has `always=True` option to run even when the field value is `None` (for optional fields)
- Can access other field values via `values` argument: `def validate_field(cls, v, values): ...`

---

## Cross-field validation

Sometimes you need to validate one field in relation to another — e.g., `end_date` must be after `start_date`.

**v2 — use `@model_validator`:**

```python
from pydantic import BaseModel, model_validator
from datetime import date

class DateRange(BaseModel):
    start_date: date
    end_date: date

    @model_validator(mode="after")
    def end_must_follow_start(self) -> "DateRange":
        if self.end_date <= self.start_date:
            raise ValueError("end_date must be after start_date")
        return self
```

**v1 — use `@validator` with `values`:**

```python
@validator("end_date")
def end_must_follow_start(cls, v, values):
    if "start_date" in values and v <= values["start_date"]:
        raise ValueError("end_date must be after start_date")
    return v
```

The `values` dict in v1 only contains fields that have already been validated and passed — fields are validated in declaration order, so order matters.

---

## How FastAPI surfaces validation errors

When validation fails, FastAPI automatically returns a `422 Unprocessable Entity` response. The error detail maps field names to error messages. You don't need to catch `ValidationError` yourself for request validation — FastAPI handles the translation.

```json
{
  "detail": [
    {
      "loc": ["body", "username"],
      "msg": "username cannot be blank",
      "type": "value_error"
    }
  ]
}
```

---

## Which to use

| Situation | Use |
|---|---|
| Pydantic v2 (default in modern FastAPI) | `@field_validator` |
| Pydantic v1 or legacy codebase | `@validator` |
| Validate one field relative to another | `@model_validator` (v2) or `@validator` with `values` (v1) |
| Normalize before type coercion | `mode="before"` (v2) or `pre=True` (v1) |

---

## Common mistakes

1. **Forgetting `@classmethod` in v2.** Pydantic v2 will raise a `PydanticUserError` at class definition time if you omit it.

2. **Assuming field order in v1 cross-field validators.** If you validate `end_date` but reference `start_date` via `values`, `start_date` must be declared first in the model, or it won't be in `values` yet.

3. **Returning nothing from the validator.** If you forget to `return v`, the field becomes `None`. Always return the value (possibly modified).

4. **Using `ValueError` vs `AssertionError`.** Both work, but `ValueError` is idiomatic and produces cleaner error messages in Pydantic's output.

5. **Mixing v1 and v2 APIs.** If you're on Pydantic v2 and use `@validator`, it still works via a compatibility shim, but you'll get deprecation warnings. Pick one style per codebase.
