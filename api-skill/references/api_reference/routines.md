# API Reference: routines.py

**Language**: Python

**Source**: `routines.py`

---

## Functions

### _sync_states(db: AsyncSession) → dict[str, RoutineState]

**Async function**

**Parameters**:

| Name | Type | Default | Description |
|------|------|---------|-------------|
| db | AsyncSession | - | - |

**Returns**: `dict[str, RoutineState]`



### routines_page(request: Request, db: AsyncSession = Depends(get_db))

**Async function**

**Parameters**:

| Name | Type | Default | Description |
|------|------|---------|-------------|
| request | Request | - | - |
| db | AsyncSession | Depends(get_db) | - |

**Returns**: (none)



### routine_enable(slug: str, request: Request, db: AsyncSession = Depends(get_db))

**Async function**

**Parameters**:

| Name | Type | Default | Description |
|------|------|---------|-------------|
| slug | str | - | - |
| request | Request | - | - |
| db | AsyncSession | Depends(get_db) | - |

**Returns**: (none)



### routine_disable(slug: str, request: Request, db: AsyncSession = Depends(get_db))

**Async function**

**Parameters**:

| Name | Type | Default | Description |
|------|------|---------|-------------|
| slug | str | - | - |
| request | Request | - | - |
| db | AsyncSession | Depends(get_db) | - |

**Returns**: (none)



### routine_run(slug: str, request: Request, db: AsyncSession = Depends(get_db))

**Async function**

**Parameters**:

| Name | Type | Default | Description |
|------|------|---------|-------------|
| slug | str | - | - |
| request | Request | - | - |
| db | AsyncSession | Depends(get_db) | - |

**Returns**: (none)



### routine_stop(slug: str, request: Request, db: AsyncSession = Depends(get_db))

**Async function**

**Parameters**:

| Name | Type | Default | Description |
|------|------|---------|-------------|
| slug | str | - | - |
| request | Request | - | - |
| db | AsyncSession | Depends(get_db) | - |

**Returns**: (none)


