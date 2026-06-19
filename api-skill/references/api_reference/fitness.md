# API Reference: fitness.py

**Language**: Python

**Source**: `fitness.py`

---

## Functions

### _is_user_fitness(event: dict, username: str) → bool

**Parameters**:

| Name | Type | Default | Description |
|------|------|---------|-------------|
| event | dict | - | - |
| username | str | - | - |

**Returns**: `bool`



### _event_date(event: dict) → str

**Parameters**:

| Name | Type | Default | Description |
|------|------|---------|-------------|
| event | dict | - | - |

**Returns**: `str`



### _group_by_date(events: list) → dict

**Parameters**:

| Name | Type | Default | Description |
|------|------|---------|-------------|
| events | list | - | - |

**Returns**: `dict`



### _get_logs(db: AsyncSession, user_id: int, date_from: str, date_to: str) → dict

**Async function**

**Parameters**:

| Name | Type | Default | Description |
|------|------|---------|-------------|
| db | AsyncSession | - | - |
| user_id | int | - | - |
| date_from | str | - | - |
| date_to | str | - | - |

**Returns**: `dict`



### _today_events_response(request: Request, db: AsyncSession, target: str)

**Async function**

**Parameters**:

| Name | Type | Default | Description |
|------|------|---------|-------------|
| request | Request | - | - |
| db | AsyncSession | - | - |
| target | str | - | - |

**Returns**: (none)



### today_events(request: Request, db: AsyncSession = Depends(get_db))

**Async function**

**Parameters**:

| Name | Type | Default | Description |
|------|------|---------|-------------|
| request | Request | - | - |
| db | AsyncSession | Depends(get_db) | - |

**Returns**: (none)



### _week_events_response(request: Request, db: AsyncSession, target: str)

**Async function**

**Parameters**:

| Name | Type | Default | Description |
|------|------|---------|-------------|
| request | Request | - | - |
| db | AsyncSession | - | - |
| target | str | - | - |

**Returns**: (none)



### week_events(request: Request, db: AsyncSession = Depends(get_db))

**Async function**

**Parameters**:

| Name | Type | Default | Description |
|------|------|---------|-------------|
| request | Request | - | - |
| db | AsyncSession | Depends(get_db) | - |

**Returns**: (none)



### _month_events_response(request: Request, db: AsyncSession, target: str)

**Async function**

**Parameters**:

| Name | Type | Default | Description |
|------|------|---------|-------------|
| request | Request | - | - |
| db | AsyncSession | - | - |
| target | str | - | - |

**Returns**: (none)



### month_events(request: Request, db: AsyncSession = Depends(get_db))

**Async function**

**Parameters**:

| Name | Type | Default | Description |
|------|------|---------|-------------|
| request | Request | - | - |
| db | AsyncSession | Depends(get_db) | - |

**Returns**: (none)



### schedule(request: Request, title: str = Form(...), date: str = Form(...), start_time: str = Form(...), duration: int = Form(60), db: AsyncSession = Depends(get_db))

**Async function**

**Parameters**:

| Name | Type | Default | Description |
|------|------|---------|-------------|
| request | Request | - | - |
| title | str | Form(...) | - |
| date | str | Form(...) | - |
| start_time | str | Form(...) | - |
| duration | int | Form(60) | - |
| db | AsyncSession | Depends(get_db) | - |

**Returns**: (none)



### steps_card(request: Request, db: AsyncSession = Depends(get_db))

**Async function**

**Parameters**:

| Name | Type | Default | Description |
|------|------|---------|-------------|
| request | Request | - | - |
| db | AsyncSession | Depends(get_db) | - |

**Returns**: (none)



### log_event(request: Request, uid: str = Form(...), title: str = Form(...), event_date: str = Form(...), status: str = Form(...), source: str = Form('fitness'), view: str = Form('today'), notes: Optional[str] = Form(None), db: AsyncSession = Depends(get_db), ext_db: Optional[AsyncSession] = Depends(get_ext_db))

**Async function**

**Parameters**:

| Name | Type | Default | Description |
|------|------|---------|-------------|
| request | Request | - | - |
| uid | str | Form(...) | - |
| title | str | Form(...) | - |
| event_date | str | Form(...) | - |
| status | str | Form(...) | - |
| source | str | Form('fitness') | - |
| view | str | Form('today') | - |
| notes | Optional[str] | Form(None) | - |
| db | AsyncSession | Depends(get_db) | - |
| ext_db | Optional[AsyncSession] | Depends(get_ext_db) | - |

**Returns**: (none)


