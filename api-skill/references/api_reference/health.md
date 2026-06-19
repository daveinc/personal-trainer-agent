# API Reference: health.py

**Language**: Python

**Source**: `health.py`

---

## Functions

### health_page(request: Request, expand: str = None, edit_appt: int = None, db: AsyncSession = Depends(get_db))

**Async function**

**Parameters**:

| Name | Type | Default | Description |
|------|------|---------|-------------|
| request | Request | - | - |
| expand | str | None | - |
| edit_appt | int | None | - |
| db | AsyncSession | Depends(get_db) | - |

**Returns**: (none)



### entry_log(request: Request, db: AsyncSession = Depends(get_db))

**Async function**

**Parameters**:

| Name | Type | Default | Description |
|------|------|---------|-------------|
| request | Request | - | - |
| db | AsyncSession | Depends(get_db) | - |

**Returns**: (none)



### entry_delete(entry_id: int, request: Request, metric: str = Form(''), db: AsyncSession = Depends(get_db))

**Async function**

**Parameters**:

| Name | Type | Default | Description |
|------|------|---------|-------------|
| entry_id | int | - | - |
| request | Request | - | - |
| metric | str | Form('') | - |
| db | AsyncSession | Depends(get_db) | - |

**Returns**: (none)



### appt_add(request: Request, db: AsyncSession = Depends(get_db))

**Async function**

**Parameters**:

| Name | Type | Default | Description |
|------|------|---------|-------------|
| request | Request | - | - |
| db | AsyncSession | Depends(get_db) | - |

**Returns**: (none)



### appt_save(appt_id: int, request: Request, db: AsyncSession = Depends(get_db))

**Async function**

**Parameters**:

| Name | Type | Default | Description |
|------|------|---------|-------------|
| appt_id | int | - | - |
| request | Request | - | - |
| db | AsyncSession | Depends(get_db) | - |

**Returns**: (none)



### appt_delete(appt_id: int, request: Request, db: AsyncSession = Depends(get_db))

**Async function**

**Parameters**:

| Name | Type | Default | Description |
|------|------|---------|-------------|
| appt_id | int | - | - |
| request | Request | - | - |
| db | AsyncSession | Depends(get_db) | - |

**Returns**: (none)


