# API Reference: auth.py

**Language**: Python

**Source**: `auth.py`

---

## Functions

### login(request: Request, username: str = Form(...), db: AsyncSession = Depends(get_db))

**Async function**

**Parameters**:

| Name | Type | Default | Description |
|------|------|---------|-------------|
| request | Request | - | - |
| username | str | Form(...) | - |
| db | AsyncSession | Depends(get_db) | - |

**Returns**: (none)



### logout(request: Request)

**Async function**

**Parameters**:

| Name | Type | Default | Description |
|------|------|---------|-------------|
| request | Request | - | - |

**Returns**: (none)


