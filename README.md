# tech_new_writer API

## Base URL

```bash
export BASE_URL="http://localhost:8000"
```

## Publish configuration

Hệ thống publish draft qua FOREM API.

### Các biến môi trường dùng để publish

```bash
export FOREM_API_BASE_URL="https://dev.to/api"
export FOREM_API_KEY="your-api-key"
export FOREM_TAGS="ai,python,backend"
export FOREM_AUTO_PUBLISH_DRAFT="true"
```

### Ý nghĩa

- `FOREM_API_BASE_URL`: base URL của FOREM API, hệ thống sẽ gọi tới `{FOREM_API_BASE_URL}/articles`
- `FOREM_API_KEY`: API key để tạo bài draft
- `FOREM_TAGS`: danh sách tag, phân tách bằng dấu phẩy
- `FOREM_AUTO_PUBLISH_DRAFT`: nếu là `true` thì các flow API sẽ tự publish draft khi không truyền `publish_draft`

### Ví dụ endpoint publish thực tế

- `https://dev.to/api/articles`
- `https://your-forem-site.com/api/articles`

## Endpoints

### `GET /health`

```bash
curl "$BASE_URL/health"
```

### `POST /runs/topic`

Chạy flow viết bài theo `topic` và danh sách `sources`.

#### Body params

- `topic`: chuỗi topic, không bắt buộc
- `sources`: chuỗi URL phân tách bằng dấu phẩy, không bắt buộc
- `publish_draft`: `true | false | null`, không bắt buộc

#### Ví dụ

```bash
curl -X POST "$BASE_URL/runs/topic" \
  -H "Content-Type: application/json" \
  -d '{}'
```

```bash
curl -X POST "$BASE_URL/runs/topic" \
  -H "Content-Type: application/json" \
  -d '{
    "topic": "So sánh FastAPI và Hono cho backend hiệu năng cao",
    "sources": "https://techcrunch.com/,https://www.theverge.com/tech,https://huggingface.co/blog",
    "publish_draft": false
  }'
```

```bash
curl -X POST "$BASE_URL/runs/topic" \
  -H "Content-Type: application/json" \
  -d '{
    "topic": "Hướng dẫn tích hợp OpenCLaw bằng Docker",
    "sources": "https://huggingface.co/blog,https://towardsdatascience.com/",
    "publish_draft": true
  }'
```

### `POST /runs/single-article`

Lấy top article từ một nguồn và chạy flow viết lại.

#### Body params

- `source_url`: URL nguồn, bắt buộc
- `publish_draft`: `true | false | null`, không bắt buộc

#### Ví dụ

```bash
curl -X POST "$BASE_URL/runs/single-article" \
  -H "Content-Type: application/json" \
  -d '{
    "source_url": "https://huggingface.co/blog",
    "publish_draft": false
  }'
```

```bash
curl -X POST "$BASE_URL/runs/single-article" \
  -H "Content-Type: application/json" \
  -d '{
    "source_url": "https://techcrunch.com/",
    "publish_draft": true
  }'
```

### `POST /runs/daily-top`

Chạy flow cho top article của từng nguồn.

#### Body params

- `sources`: chuỗi URL phân tách bằng dấu phẩy, không bắt buộc
- `publish_draft`: `true | false | null`, không bắt buộc

#### Ví dụ

```bash
curl -X POST "$BASE_URL/runs/daily-top" \
  -H "Content-Type: application/json" \
  -d '{
    "sources": "https://techcrunch.com/,https://www.theverge.com/tech,https://huggingface.co/blog",
    "publish_draft": false
  }'
```

```bash
curl -X POST "$BASE_URL/runs/daily-top" \
  -H "Content-Type: application/json" \
  -d '{}'
```

## Pretty print JSON

```bash
curl -s "$BASE_URL/health" | python3 -m json.tool
```

```bash
curl -s -X POST "$BASE_URL/runs/topic" \
  -H "Content-Type: application/json" \
  -d '{"topic":"AI Agents","publish_draft":false}' | python3 -m json.tool
```

## Run with Docker Compose

```bash
docker compose up --build
```

```bash
curl http://localhost:8000/health
```
