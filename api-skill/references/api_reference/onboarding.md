# API Reference: onboarding.py

**Language**: Python

**Source**: `onboarding.py`

---

## Functions

### onboarding_get(request: Request, step: int = 1, db: AsyncSession = Depends(get_db))

**Async function**

**Parameters**:

| Name | Type | Default | Description |
|------|------|---------|-------------|
| request | Request | - | - |
| step | int | 1 | - |
| db | AsyncSession | Depends(get_db) | - |

**Returns**: (none)



### onboarding_name(request: Request, display_name: str = Form(...), db: AsyncSession = Depends(get_db))

**Async function**

**Parameters**:

| Name | Type | Default | Description |
|------|------|---------|-------------|
| request | Request | - | - |
| display_name | str | Form(...) | - |
| db | AsyncSession | Depends(get_db) | - |

**Returns**: (none)



### onboarding_categories(request: Request, db: AsyncSession = Depends(get_db))

**Async function**

**Parameters**:

| Name | Type | Default | Description |
|------|------|---------|-------------|
| request | Request | - | - |
| db | AsyncSession | Depends(get_db) | - |

**Returns**: (none)



### onboarding_dismiss(request: Request, user_id: int = Form(...), db: AsyncSession = Depends(get_db))

**Async function**

**Parameters**:

| Name | Type | Default | Description |
|------|------|---------|-------------|
| request | Request | - | - |
| user_id | int | Form(...) | - |
| db | AsyncSession | Depends(get_db) | - |

**Returns**: (none)


