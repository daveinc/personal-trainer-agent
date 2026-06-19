# API Reference: settings.py

**Language**: Python

**Source**: `settings.py`

---

## Functions

### _event_user(event: dict) → str

**Parameters**:

| Name | Type | Default | Description |
|------|------|---------|-------------|
| event | dict | - | - |

**Returns**: `str`



### settings_page(request: Request, db: AsyncSession = Depends(get_db))

**Async function**

**Parameters**:

| Name | Type | Default | Description |
|------|------|---------|-------------|
| request | Request | - | - |
| db | AsyncSession | Depends(get_db) | - |

**Returns**: (none)



### settings_db(request: Request, db: AsyncSession = Depends(get_db), ext_db: Optional[AsyncSession] = Depends(get_ext_db))

**Async function**

**Parameters**:

| Name | Type | Default | Description |
|------|------|---------|-------------|
| request | Request | - | - |
| db | AsyncSession | Depends(get_db) | - |
| ext_db | Optional[AsyncSession] | Depends(get_ext_db) | - |

**Returns**: (none)



### delete_user_logs(request: Request, user_id: int = Form(...), db: AsyncSession = Depends(get_db), ext_db: Optional[AsyncSession] = Depends(get_ext_db))

**Async function**

**Parameters**:

| Name | Type | Default | Description |
|------|------|---------|-------------|
| request | Request | - | - |
| user_id | int | Form(...) | - |
| db | AsyncSession | Depends(get_db) | - |
| ext_db | Optional[AsyncSession] | Depends(get_ext_db) | - |

**Returns**: (none)



### delete_user_entry(request: Request, user_id: int = Form(...), db: AsyncSession = Depends(get_db), ext_db: Optional[AsyncSession] = Depends(get_ext_db))

**Async function**

**Parameters**:

| Name | Type | Default | Description |
|------|------|---------|-------------|
| request | Request | - | - |
| user_id | int | Form(...) | - |
| db | AsyncSession | Depends(get_db) | - |
| ext_db | Optional[AsyncSession] | Depends(get_ext_db) | - |

**Returns**: (none)



### wipe_logs(request: Request, db: AsyncSession = Depends(get_db), ext_db: Optional[AsyncSession] = Depends(get_ext_db))

**Async function**

**Parameters**:

| Name | Type | Default | Description |
|------|------|---------|-------------|
| request | Request | - | - |
| db | AsyncSession | Depends(get_db) | - |
| ext_db | Optional[AsyncSession] | Depends(get_ext_db) | - |

**Returns**: (none)



### backup_db(request: Request, db: AsyncSession = Depends(get_db))

**Async function**

**Parameters**:

| Name | Type | Default | Description |
|------|------|---------|-------------|
| request | Request | - | - |
| db | AsyncSession | Depends(get_db) | - |

**Returns**: (none)



### restore_db(request: Request, file: UploadFile = File(...), db: AsyncSession = Depends(get_db))

**Async function**

**Parameters**:

| Name | Type | Default | Description |
|------|------|---------|-------------|
| request | Request | - | - |
| file | UploadFile | File(...) | - |
| db | AsyncSession | Depends(get_db) | - |

**Returns**: (none)



### settings_preferences(request: Request, db: AsyncSession = Depends(get_db))

**Async function**

**Parameters**:

| Name | Type | Default | Description |
|------|------|---------|-------------|
| request | Request | - | - |
| db | AsyncSession | Depends(get_db) | - |

**Returns**: (none)



### settings_preferences_save(request: Request, db: AsyncSession = Depends(get_db))

**Async function**

**Parameters**:

| Name | Type | Default | Description |
|------|------|---------|-------------|
| request | Request | - | - |
| db | AsyncSession | Depends(get_db) | - |

**Returns**: (none)



### settings_notifications(request: Request, db: AsyncSession = Depends(get_db))

**Async function**

**Parameters**:

| Name | Type | Default | Description |
|------|------|---------|-------------|
| request | Request | - | - |
| db | AsyncSession | Depends(get_db) | - |

**Returns**: (none)



### settings_categories(request: Request, db: AsyncSession = Depends(get_db))

**Async function**

**Parameters**:

| Name | Type | Default | Description |
|------|------|---------|-------------|
| request | Request | - | - |
| db | AsyncSession | Depends(get_db) | - |

**Returns**: (none)



### settings_categories_save(request: Request, db: AsyncSession = Depends(get_db))

**Async function**

**Parameters**:

| Name | Type | Default | Description |
|------|------|---------|-------------|
| request | Request | - | - |
| db | AsyncSession | Depends(get_db) | - |

**Returns**: (none)



### settings_skills(request: Request, db: AsyncSession = Depends(get_db))

**Async function**

**Parameters**:

| Name | Type | Default | Description |
|------|------|---------|-------------|
| request | Request | - | - |
| db | AsyncSession | Depends(get_db) | - |

**Returns**: (none)



### get_skills_defaults()

**Async function**

**Returns**: (none)



### get_skills(db: AsyncSession = Depends(get_db))

**Async function**

**Parameters**:

| Name | Type | Default | Description |
|------|------|---------|-------------|
| db | AsyncSession | Depends(get_db) | - |

**Returns**: (none)



### toggle_skill_enabled(request: Request, db: AsyncSession = Depends(get_db))

**Async function**

**Parameters**:

| Name | Type | Default | Description |
|------|------|---------|-------------|
| request | Request | - | - |
| db | AsyncSession | Depends(get_db) | - |

**Returns**: (none)



### settings_calendar(request: Request, user_filter: str = '', db: AsyncSession = Depends(get_db))

**Async function**

**Parameters**:

| Name | Type | Default | Description |
|------|------|---------|-------------|
| request | Request | - | - |
| user_filter | str | '' | - |
| db | AsyncSession | Depends(get_db) | - |

**Returns**: (none)



### cal_config_add(request: Request, entity_id: str = Form(...), label: str = Form(''), default_category: str = Form(''), ignore_keywords: str = Form(''), db: AsyncSession = Depends(get_db))

**Async function**

**Parameters**:

| Name | Type | Default | Description |
|------|------|---------|-------------|
| request | Request | - | - |
| entity_id | str | Form(...) | - |
| label | str | Form('') | - |
| default_category | str | Form('') | - |
| ignore_keywords | str | Form('') | - |
| db | AsyncSession | Depends(get_db) | - |

**Returns**: (none)



### cal_config_delete(config_id: int, request: Request, db: AsyncSession = Depends(get_db))

**Async function**

**Parameters**:

| Name | Type | Default | Description |
|------|------|---------|-------------|
| config_id | int | - | - |
| request | Request | - | - |
| db | AsyncSession | Depends(get_db) | - |

**Returns**: (none)



### calendar_edit_form(request: Request, uid: str = '', db: AsyncSession = Depends(get_db))

**Async function**

**Parameters**:

| Name | Type | Default | Description |
|------|------|---------|-------------|
| request | Request | - | - |
| uid | str | '' | - |
| db | AsyncSession | Depends(get_db) | - |

**Returns**: (none)



### calendar_edit_submit(request: Request, uid: str = Form(...), title: str = Form(...), date: str = Form(...), start_time: str = Form(...), duration: int = Form(60), description: str = Form(''), db: AsyncSession = Depends(get_db))

**Async function**

**Parameters**:

| Name | Type | Default | Description |
|------|------|---------|-------------|
| request | Request | - | - |
| uid | str | Form(...) | - |
| title | str | Form(...) | - |
| date | str | Form(...) | - |
| start_time | str | Form(...) | - |
| duration | int | Form(60) | - |
| description | str | Form('') | - |
| db | AsyncSession | Depends(get_db) | - |

**Returns**: (none)



### calendar_delete(request: Request, uid: str = Form(...), db: AsyncSession = Depends(get_db))

**Async function**

**Parameters**:

| Name | Type | Default | Description |
|------|------|---------|-------------|
| request | Request | - | - |
| uid | str | Form(...) | - |
| db | AsyncSession | Depends(get_db) | - |

**Returns**: (none)



### calendar_backup(request: Request, db: AsyncSession = Depends(get_db))

**Async function**

**Parameters**:

| Name | Type | Default | Description |
|------|------|---------|-------------|
| request | Request | - | - |
| db | AsyncSession | Depends(get_db) | - |

**Returns**: (none)



### calendar_restore(request: Request, file: UploadFile = File(...), replace: bool = Form(False), db: AsyncSession = Depends(get_db))

**Async function**

**Parameters**:

| Name | Type | Default | Description |
|------|------|---------|-------------|
| request | Request | - | - |
| file | UploadFile | File(...) | - |
| replace | bool | Form(False) | - |
| db | AsyncSession | Depends(get_db) | - |

**Returns**: (none)


