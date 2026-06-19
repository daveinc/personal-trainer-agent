# API Reference: profile.py

**Language**: Python

**Source**: `profile.py`

---

## Functions

### profile_page(request: Request, edit: int = None, db: AsyncSession = Depends(get_db))

**Async function**

**Parameters**:

| Name | Type | Default | Description |
|------|------|---------|-------------|
| request | Request | - | - |
| edit | int | None | - |
| db | AsyncSession | Depends(get_db) | - |

**Returns**: (none)



### slot_add(request: Request, category: str = Form(...), label: str = Form(...), schedule_type: str = Form('free'), db: AsyncSession = Depends(get_db))

**Async function**

**Parameters**:

| Name | Type | Default | Description |
|------|------|---------|-------------|
| request | Request | - | - |
| category | str | Form(...) | - |
| label | str | Form(...) | - |
| schedule_type | str | Form('free') | - |
| db | AsyncSession | Depends(get_db) | - |

**Returns**: (none)



### slot_save(slot_id: int, request: Request, label: str = Form(...), schedule_type: str = Form('free'), db: AsyncSession = Depends(get_db))

**Async function**

**Parameters**:

| Name | Type | Default | Description |
|------|------|---------|-------------|
| slot_id | int | - | - |
| request | Request | - | - |
| label | str | Form(...) | - |
| schedule_type | str | Form('free') | - |
| db | AsyncSession | Depends(get_db) | - |

**Returns**: (none)



### slot_delete(slot_id: int, request: Request, db: AsyncSession = Depends(get_db))

**Async function**

**Parameters**:

| Name | Type | Default | Description |
|------|------|---------|-------------|
| slot_id | int | - | - |
| request | Request | - | - |
| db | AsyncSession | Depends(get_db) | - |

**Returns**: (none)



### slot_attributes(slot_id: int, request: Request, db: AsyncSession = Depends(get_db))

**Async function**

**Parameters**:

| Name | Type | Default | Description |
|------|------|---------|-------------|
| slot_id | int | - | - |
| request | Request | - | - |
| db | AsyncSession | Depends(get_db) | - |

**Returns**: (none)



### attribute_add(slot_id: int, request: Request, attribute_name: str = Form(...), unit: str = Form(''), db: AsyncSession = Depends(get_db))

**Async function**

**Parameters**:

| Name | Type | Default | Description |
|------|------|---------|-------------|
| slot_id | int | - | - |
| request | Request | - | - |
| attribute_name | str | Form(...) | - |
| unit | str | Form('') | - |
| db | AsyncSession | Depends(get_db) | - |

**Returns**: (none)



### attribute_delete(slot_id: int, attr_id: int, request: Request, db: AsyncSession = Depends(get_db))

**Async function**

**Parameters**:

| Name | Type | Default | Description |
|------|------|---------|-------------|
| slot_id | int | - | - |
| attr_id | int | - | - |
| request | Request | - | - |
| db | AsyncSession | Depends(get_db) | - |

**Returns**: (none)


