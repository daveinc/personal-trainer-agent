# API Reference: relationships.py

**Language**: Python

**Source**: `relationships.py`

---

## Functions

### _days_since(last_contact: str | None) → int

**Parameters**:

| Name | Type | Default | Description |
|------|------|---------|-------------|
| last_contact | str | None | - | - |

**Returns**: `int`



### _status(days: int) → tuple

**Parameters**:

| Name | Type | Default | Description |
|------|------|---------|-------------|
| days | int | - | - |

**Returns**: `tuple`



### relationships_page(request: Request, edit: int = None, db: AsyncSession = Depends(get_db))

**Async function**

**Parameters**:

| Name | Type | Default | Description |
|------|------|---------|-------------|
| request | Request | - | - |
| edit | int | None | - |
| db | AsyncSession | Depends(get_db) | - |

**Returns**: (none)



### person_add(request: Request, db: AsyncSession = Depends(get_db))

**Async function**

**Parameters**:

| Name | Type | Default | Description |
|------|------|---------|-------------|
| request | Request | - | - |
| db | AsyncSession | Depends(get_db) | - |

**Returns**: (none)



### person_save(person_id: int, request: Request, db: AsyncSession = Depends(get_db))

**Async function**

**Parameters**:

| Name | Type | Default | Description |
|------|------|---------|-------------|
| person_id | int | - | - |
| request | Request | - | - |
| db | AsyncSession | Depends(get_db) | - |

**Returns**: (none)



### person_contact(person_id: int, request: Request, db: AsyncSession = Depends(get_db))

**Async function**

**Parameters**:

| Name | Type | Default | Description |
|------|------|---------|-------------|
| person_id | int | - | - |
| request | Request | - | - |
| db | AsyncSession | Depends(get_db) | - |

**Returns**: (none)



### person_delete(person_id: int, request: Request, db: AsyncSession = Depends(get_db))

**Async function**

**Parameters**:

| Name | Type | Default | Description |
|------|------|---------|-------------|
| person_id | int | - | - |
| request | Request | - | - |
| db | AsyncSession | Depends(get_db) | - |

**Returns**: (none)


