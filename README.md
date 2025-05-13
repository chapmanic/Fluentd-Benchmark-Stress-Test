# Fluentd Benchmark & Stress Test Log Generator

This Python script is designed to **benchmark** and **stress test** a [Fluentd](https://www.fluentd.org/) log aggregator by generating and sending high-throughput synthetic log data. It supports customisation of log frequency, duration, log size, and network parameters, enabling developers and SREs to validate Fluentd’s performance under controlled load conditions.

---

## Features

- **Adjustable throughput**: Control log rate per second
- **Custom log size**: Set desired payload size (e.g., 848 bytes, 2KB, etc.)
- **Multiple threads**: Uses `ThreadPoolExecutor` for concurrent log submission
- **Realistic log structure**: Simulates microservice logs with trace IDs, session IDs, timestamps, and hostnames
- **Supports TCP Forward Protocol** (default for Fluentd)
- **Success/failure reporting**: Summarises emitted vs failed logs

---

## Example Usage

```bash
# Send 10 logs per second for 10 seconds to Fluentd on port 24224
python fluentd-benchmark.py --seconds 10 --rate 10 --size 848 --host fluentd.domain.com --port 24224 --tag ops-test

# Send 100 logs/sec for 60 seconds with ~2KB logs
python fluentd-benchmark.py 60 --rate 100 --size 2000

# Send 100 logs/sec for 60 seconds with ~2MB logs
python fluentd-benchmark.py 60 --rate 100 --size 200000
```

---

## ⚙️ Command Line Arguments

| Argument       | Type     | Default       | Description                                 |
|----------------|----------|---------------|---------------------------------------------|
| `seconds`      | `int`    | *required*    | Duration of the test in seconds             |
| `--rate`       | `int`    | `10`          | Number of logs to send per second           |
| `--size`       | `int`    | `848`         | Target size of each log entry in bytes      |
| `--host`       | `str`    | `localhost`   | Fluentd server hostname or IP               |
| `--port`       | `int`    | `24224`       | Fluentd TCP port (usually 24224)            |
| `--tag`        | `str`    | `ops-test`    | Log tag prefix to group logs in Fluentd     |

---

## Script Architecture

### 1. **Connection Test**
Performs a preliminary emit to confirm Fluentd is reachable via the specified host/port before starting the benchmark.

### 2. **Log Generator**
`generate_log_entry()` builds a JSON log with the following fields:
- `log_id`: Unique UUID
- `level`: One of INFO, DEBUG, WARN, ERROR
- `service`: Random simulated microservice (e.g., auth-service)
- `user_id`: Random 4-digit user ID
- `message`: Descriptive log message
- `host`: Local machine hostname
- `timestamp`: UTC in ISO 8601 format
- `trace_id` / `session_id`: Random unique identifiers
- `payload`: Filler content to meet size requirement

### 3. **Concurrent Emit**
Each second:
- A thread pool dispatches `rate` number of logs
- Logs are sent concurrently to avoid blocking I/O
- Success/failure counters are tracked

### 4. **Output Summary**
At completion, the script prints a detailed performance report:
- Total attempted/succeeded/failed logs
- Success rate (%)
- Total test duration in seconds

---

## 🛠 Dependencies

Install the `fluent-logger` package before running the script:

```bash
pip install fluent-logger
```

---

## Use Cases

- Load testing Fluentd or Fluent Bit aggregators
- Benchmarking log ingestion performance of your logging pipeline (e.g., Fluentd → OpenSearch)
- Sizing and scaling log infrastructure
- Validating Fluentd buffer and retry configurations
