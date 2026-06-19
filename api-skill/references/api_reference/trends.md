# API Reference: trends.py

**Language**: Python

**Source**: `trends.py`

---

## Functions

### _get_or_create_rule(db: AsyncSession) → ScoringRule

**Async function**

**Parameters**:

| Name | Type | Default | Description |
|------|------|---------|-------------|
| db | AsyncSession | - | - |

**Returns**: `ScoringRule`



### _eval_formula(formula: str, completed: int, skipped: int, missed: int, total: int, period_days: int = 30)

**Parameters**:

| Name | Type | Default | Description |
|------|------|---------|-------------|
| formula | str | - | - |
| completed | int | - | - |
| skipped | int | - | - |
| missed | int | - | - |
| total | int | - | - |
| period_days | int | 30 | - |

**Returns**: (none)



### trends_page(request: Request, db: AsyncSession = Depends(get_db))

**Async function**

**Parameters**:

| Name | Type | Default | Description |
|------|------|---------|-------------|
| request | Request | - | - |
| db | AsyncSession | Depends(get_db) | - |

**Returns**: (none)



### trends_scoring(request: Request, db: AsyncSession = Depends(get_db))

**Async function**

**Parameters**:

| Name | Type | Default | Description |
|------|------|---------|-------------|
| request | Request | - | - |
| db | AsyncSession | Depends(get_db) | - |

**Returns**: (none)



### trends_scoring_save(request: Request, formula: str = Form(''), formula_enabled: bool = Form(False), db: AsyncSession = Depends(get_db))

**Async function**

**Parameters**:

| Name | Type | Default | Description |
|------|------|---------|-------------|
| request | Request | - | - |
| formula | str | Form('') | - |
| formula_enabled | bool | Form(False) | - |
| db | AsyncSession | Depends(get_db) | - |

**Returns**: (none)



### trends_scoring_test(request: Request, formula: str = Form(''), db: AsyncSession = Depends(get_db))

**Async function**

**Parameters**:

| Name | Type | Default | Description |
|------|------|---------|-------------|
| request | Request | - | - |
| formula | str | Form('') | - |
| db | AsyncSession | Depends(get_db) | - |

**Returns**: (none)



### trends_periods(request: Request, db: AsyncSession = Depends(get_db))

**Async function**

**Parameters**:

| Name | Type | Default | Description |
|------|------|---------|-------------|
| request | Request | - | - |
| db | AsyncSession | Depends(get_db) | - |

**Returns**: (none)



### trends_periods_add(request: Request, name: str = Form(...), start_month: int = Form(...), end_month: int = Form(...), description: str = Form(''), db: AsyncSession = Depends(get_db))

**Async function**

**Parameters**:

| Name | Type | Default | Description |
|------|------|---------|-------------|
| request | Request | - | - |
| name | str | Form(...) | - |
| start_month | int | Form(...) | - |
| end_month | int | Form(...) | - |
| description | str | Form('') | - |
| db | AsyncSession | Depends(get_db) | - |

**Returns**: (none)



### trends_periods_delete(request: Request, period_id: int = Form(...), db: AsyncSession = Depends(get_db))

**Async function**

**Parameters**:

| Name | Type | Default | Description |
|------|------|---------|-------------|
| request | Request | - | - |
| period_id | int | Form(...) | - |
| db | AsyncSession | Depends(get_db) | - |

**Returns**: (none)



### trends_observations(request: Request, db: AsyncSession = Depends(get_db))

**Async function**

**Parameters**:

| Name | Type | Default | Description |
|------|------|---------|-------------|
| request | Request | - | - |
| db | AsyncSession | Depends(get_db) | - |

**Returns**: (none)



### trends_observations_add(request: Request, period_name: str = Form(...), category: str = Form(...), score: str = Form(''), notes: str = Form(''), user_id: Optional[int] = Form(None), db: AsyncSession = Depends(get_db))

**Async function**

**Parameters**:

| Name | Type | Default | Description |
|------|------|---------|-------------|
| request | Request | - | - |
| period_name | str | Form(...) | - |
| category | str | Form(...) | - |
| score | str | Form('') | - |
| notes | str | Form('') | - |
| user_id | Optional[int] | Form(None) | - |
| db | AsyncSession | Depends(get_db) | - |

**Returns**: (none)



### trends_observations_delete(request: Request, obs_id: int = Form(...), db: AsyncSession = Depends(get_db))

**Async function**

**Parameters**:

| Name | Type | Default | Description |
|------|------|---------|-------------|
| request | Request | - | - |
| obs_id | int | Form(...) | - |
| db | AsyncSession | Depends(get_db) | - |

**Returns**: (none)



### category_trends(category_name: str, request: Request, db: AsyncSession = Depends(get_db))

**Async function**

**Parameters**:

| Name | Type | Default | Description |
|------|------|---------|-------------|
| category_name | str | - | - |
| request | Request | - | - |
| db | AsyncSession | Depends(get_db) | - |

**Returns**: (none)



### detect_correlations(user_id: int, db: AsyncSession, days: int = 30)

**Async function**

**Parameters**:

| Name | Type | Default | Description |
|------|------|---------|-------------|
| user_id | int | - | - |
| db | AsyncSession | - | - |
| days | int | 30 | - |

**Returns**: (none)



### get_correlations(request: Request, db: AsyncSession = Depends(get_db))

**Async function**

**Parameters**:

| Name | Type | Default | Description |
|------|------|---------|-------------|
| request | Request | - | - |
| db | AsyncSession | Depends(get_db) | - |

**Returns**: (none)


