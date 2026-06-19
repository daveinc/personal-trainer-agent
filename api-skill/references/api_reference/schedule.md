# API Reference: schedule.py

**Language**: Python

**Source**: `schedule.py`

---

## Functions

### _prep_cal_events(raw: list) → dict

Normalize and group calendar events by date, filtering out checkins.

**Parameters**:

| Name | Type | Default | Description |
|------|------|---------|-------------|
| raw | list | - | - |

**Returns**: `dict`



### _get_days(week_start: str) → list

**Parameters**:

| Name | Type | Default | Description |
|------|------|---------|-------------|
| week_start | str | - | - |

**Returns**: `list`



### _get_week(ref: date, week_start: str = 'Mon')

**Parameters**:

| Name | Type | Default | Description |
|------|------|---------|-------------|
| ref | date | - | - |
| week_start | str | 'Mon' | - |

**Returns**: (none)



### _today_or_next(slots, ref: date)

**Parameters**:

| Name | Type | Default | Description |
|------|------|---------|-------------|
| slots | None | - | - |
| ref | date | - | - |

**Returns**: (none)



### schedule_page(request: Request, selected: int = None, edit: int = None, db: AsyncSession = Depends(get_db))

**Async function**

**Parameters**:

| Name | Type | Default | Description |
|------|------|---------|-------------|
| request | Request | - | - |
| selected | int | None | - |
| edit | int | None | - |
| db | AsyncSession | Depends(get_db) | - |

**Returns**: (none)



### slot_add(request: Request, db: AsyncSession = Depends(get_db))

**Async function**

**Parameters**:

| Name | Type | Default | Description |
|------|------|---------|-------------|
| request | Request | - | - |
| db | AsyncSession | Depends(get_db) | - |

**Returns**: (none)



### slot_save(slot_id: int, request: Request, db: AsyncSession = Depends(get_db))

**Async function**

**Parameters**:

| Name | Type | Default | Description |
|------|------|---------|-------------|
| slot_id | int | - | - |
| request | Request | - | - |
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



### category_set_reminder(category: str, request: Request, notify_before: int = Form(...), db: AsyncSession = Depends(get_db))

**Async function**

**Parameters**:

| Name | Type | Default | Description |
|------|------|---------|-------------|
| category | str | - | - |
| request | Request | - | - |
| notify_before | int | Form(...) | - |
| db | AsyncSession | Depends(get_db) | - |

**Returns**: (none)



### category_clear_reminders(category: str, request: Request, db: AsyncSession = Depends(get_db))

**Async function**

**Parameters**:

| Name | Type | Default | Description |
|------|------|---------|-------------|
| category | str | - | - |
| request | Request | - | - |
| db | AsyncSession | Depends(get_db) | - |

**Returns**: (none)


