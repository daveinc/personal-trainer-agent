# API Reference: checkins.py

**Language**: Python

**Source**: `checkins.py`

---

## Functions

### _compute_streak(dates: set, today: str) → int

**Parameters**:

| Name | Type | Default | Description |
|------|------|---------|-------------|
| dates | set | - | - |
| today | str | - | - |

**Returns**: `int`



### checkins_page(request: Request, db: AsyncSession = Depends(get_db))

**Async function**

**Parameters**:

| Name | Type | Default | Description |
|------|------|---------|-------------|
| request | Request | - | - |
| db | AsyncSession | Depends(get_db) | - |

**Returns**: (none)



### checkins_log(request: Request, db: AsyncSession = Depends(get_db))

**Async function**

**Parameters**:

| Name | Type | Default | Description |
|------|------|---------|-------------|
| request | Request | - | - |
| db | AsyncSession | Depends(get_db) | - |

**Returns**: (none)



### checkins_delete(entry_id: int, request: Request, db: AsyncSession = Depends(get_db))

**Async function**

**Parameters**:

| Name | Type | Default | Description |
|------|------|---------|-------------|
| entry_id | int | - | - |
| request | Request | - | - |
| db | AsyncSession | Depends(get_db) | - |

**Returns**: (none)


