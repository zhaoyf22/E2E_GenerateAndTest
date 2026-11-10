# URL Shortener Service（节选）

## API

### POST /shorten

- 请求：`{ "url": "https://example.com/path", "custom_code": "abc123" }`
- `url` 必填，必须是 http/https，长度 ≤ 2048。
- `custom_code` 可选，4-12 位字母数字；重复返回 409 `CODE_TAKEN`。
- 成功返回 201：`{ "code": "abc123", "short_url": "https://s.example/abc123", "expires_at": null }`。
- 相同 `Idempotency-Key` 重复请求返回同一结果（200）。

**AC-001**：合法 URL 创建短链，返回 201 + code + short_url。

**AC-002**：非法 URL（非 http/https、空、>2048）返回 400 `INVALID_URL`。

**AC-003**：重复 custom_code 返回 409 `CODE_TAKEN`，不覆盖已有短链。

## 重定向

### GET /{code}

- 存在且未过期：302 到原 URL。
- 不存在：404 `NOT_FOUND`。
- 已过期：410 `GONE`。
- 每次访问记录点击事件（异步）。

**AC-004**：有效 code 302 到原 URL；过期 code 返回 410。

## 删除

### DELETE /{code}

- 需要 Bearer token；只有创建者可删除。
- 删除后 GET 返回 404。
- 非创建者返回 403 `FORBIDDEN`。

**AC-005**：创建者删除后短链不可访问；非创建者删除返回 403。
