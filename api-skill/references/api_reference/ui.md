# API Reference: ui.py

**Language**: Python

**Source**: `ui.py`

---

## Functions

### get_mood_trend(db: AsyncSession, user_id: int, days: int = 7)

**Async function**

**Parameters**:

| Name | Type | Default | Description |
|------|------|---------|-------------|
| db | AsyncSession | - | - |
| user_id | int | - | - |
| days | int | 7 | - |

**Returns**: (none)



### get_sleep_average(db: AsyncSession, user_id: int, days: int = 7)

**Async function**

**Parameters**:

| Name | Type | Default | Description |
|------|------|---------|-------------|
| db | AsyncSession | - | - |
| user_id | int | - | - |
| days | int | 7 | - |

**Returns**: (none)



### get_active_streaks(db: AsyncSession, user_id: int)

**Async function**

**Parameters**:

| Name | Type | Default | Description |
|------|------|---------|-------------|
| db | AsyncSession | - | - |
| user_id | int | - | - |

**Returns**: (none)



### login(request: Request)

**Async function**

**Parameters**:

| Name | Type | Default | Description |
|------|------|---------|-------------|
| request | Request | - | - |

**Returns**: (none)



### dashboard(request: Request, db: AsyncSession = Depends(get_db))

**Async function**

**Parameters**:

| Name | Type | Default | Description |
|------|------|---------|-------------|
| request | Request | - | - |
| db | AsyncSession | Depends(get_db) | - |

**Returns**: (none)



### quick_log(request: Request, db: AsyncSession = Depends(get_db))

**Async function**

**Parameters**:

| Name | Type | Default | Description |
|------|------|---------|-------------|
| request | Request | - | - |
| db | AsyncSession | Depends(get_db) | - |

**Returns**: (none)



### standup_submit(request: Request, db: AsyncSession = Depends(get_db))

**Async function**

**Parameters**:

| Name | Type | Default | Description |
|------|------|---------|-------------|
| request | Request | - | - |
| db | AsyncSession | Depends(get_db) | - |

**Returns**: (none)



### ha_status(request: Request)

**Async function**

**Parameters**:

| Name | Type | Default | Description |
|------|------|---------|-------------|
| request | Request | - | - |

**Returns**: (none)



### fitness(request: Request, db: AsyncSession = Depends(get_db))

**Async function**

**Parameters**:

| Name | Type | Default | Description |
|------|------|---------|-------------|
| request | Request | - | - |
| db | AsyncSession | Depends(get_db) | - |

**Returns**: (none)


