# Event Recorder - Time-Traveling Debugging

Record and replay event bus traffic for debugging, testing, and issue reproduction.

## Overview

Event Recorder captures all events flowing through your trading system's event bus and saves them with precise timing information. You can then replay these events at any
speed to reproduce bugs, test edge cases, or understand system behavior.

## Components

### 1. EventRecorder

Records events in real-time by intercepting ServiceBus publish calls.

**Features:**

- Non-invasive event capture (monkey-patching)
- Precise millisecond timing
- Automatic event serialization
- Session-based organization
- Context manager support

**Usage:**

```python
from python_pubsub_devtools.event_recorder import EventRecorder

# Create recorder
recorder = EventRecorder(
    session_name="bull_run_2025",
    output_dir="recordings"
)

# Start recording
recorder.start_recording(service_bus)

# ... your bot runs and publishes events ...

# Stop and save
recorder.stop_recording()
recording_path = recorder.save()
print(f"Recording saved to: {recording_path}")
```

**Context Manager:**

```python
with EventRecorder("my_session", "recordings") as recorder:
    recorder.start_recording(service_bus)
    # ... bot runs ...
    recorder.save()
# Automatically stops recording on exit
```

### 2. EventReplayer

Replays recorded events with timing preservation.

**Features:**

- Exact timing reproduction
- Speed control (0.1x to 10x)
- Event filtering
- Progress callbacks
- Event reconstruction from JSON

**Usage:**

```python
from python_pubsub_devtools.event_recorder import EventReplayer

# Load recording
replayer = EventReplayer("recordings/bull_run_2025_20251017.json")

# Replay at 10x speed
replayer.replay(
    service_bus,
    speed_multiplier=10.0,
    events_module_name="my_project.events"  # For event reconstruction
)

# Replay with filter (only market data events)
replayer.replay(
    service_bus,
    event_filter=lambda name: name.startswith("MarketData")
)

# Replay with progress callback
def progress(current, total):
    print(f"Progress: {current}/{total} ({current/total*100:.1f}%)")

replayer.replay(service_bus, progress_callback=progress)
```

**Analysis Methods:**

```python
# Get event summary
summary = replayer.get_event_summary()
for event_name, count in summary.items():
    print(f"{event_name}: {count}x")

# Print timeline
replayer.print_timeline(max_events=50)

# Filter events
filtered = replayer.filter_events(
    lambda name: "Failed" in name or "Error" in name
)
filtered.replay(service_bus)
```

### 3. EventRecorderServer

Web dashboard for browsing and managing recordings.

**Features:**

- Browse all recorded sessions
- View event timelines
- Filter and search events
- Replay control (simulation mode)
- Create filtered recordings
- REST API for automation

**Launch Server:**

```bash
# Via CLI (recommended)
pubsub-tools event-recorder --config devtools_config.yaml

# Via Python module
python -m python_pubsub_devtools.event_recorder.serve_recorder

# With custom settings
python -m python_pubsub_devtools.event_recorder.serve_recorder \
    --recordings-dir ./recordings \
    --port 5556

# Programmatically
from python_pubsub_devtools.event_recorder import EventRecorderServer
from python_pubsub_devtools.config import EventRecorderConfig
from pathlib import Path

config = EventRecorderConfig(
    recordings_dir=Path("recordings"),
    port=5556
)
server = EventRecorderServer(config)
server.run()
```

**Access:**

- Web UI: http://localhost:5556
- API: http://localhost:5556/api

## Recording Format

Recordings are stored as JSON files:

```json
{
  "session_name": "bull_run_2025",
  "start_time": "2025-10-17T10:00:00Z",
  "duration_ms": 45000,
  "total_events": 127,
  "events": [
    {
      "timestamp_offset_ms": 0,
      "event_name": "MarketDataReceived",
      "event_data": {
        "symbol": "BTC/USDT",
        "price": 67500.0,
        "volume": 1234.56
      },
      "source": "MarketDataAgent"
    },
    {
      "timestamp_offset_ms": 1000,
      "event_name": "PositionOpened",
      "event_data": {
        "symbol": "BTC/USDT",
        "side": "buy",
        "size": 0.1
      },
      "source": "TradingBot"
    }
  ]
}
```

## REST API

### Recordings Management

```bash
# List all recordings
GET /api/recordings

# Get recording details
GET /api/recording/<filename>

# Get recording events (with filters)
GET /api/recording/<filename>/events?event_name=MarketDataReceived&limit=100

# Get available fields for filtering
GET /api/recording/<filename>/fields

# Create filtered recording
POST /api/recording/create
{
  "source_filename": "session.json",
  "event_indices": [0, 5, 10, 15],
  "new_session_name": "filtered_session"
}
```

### Recording Control

```bash
# Start recording
POST /api/record/start
{
  "session_name": "my_session"
}

# Record event
POST /api/record/event
{
  "event_name": "TestEvent",
  "event_data": {"key": "value"},
  "source": "TestAgent"
}

# Stop recording
POST /api/record/stop

# Get recording status
GET /api/record/status
```

### Replay Control (Simulation Mode)

```bash
# Start replay
POST /api/replay/start/<filename>
{
  "speed": 2.0
}

# Pause/Resume
POST /api/replay/pause

# Stop replay
POST /api/replay/stop

# Change speed
POST /api/replay/speed
{
  "speed": 5.0
}

# Get replay status
GET /api/replay/status
```

## CLI Usage

### Record Events

```python
# In your bot code
from python_pubsub_devtools.event_recorder import EventRecorder

recorder = EventRecorder("production_issue_123", "recordings")
recorder.start_recording(service_bus)

# ... bot runs ...

recorder.stop_recording()
recorder.save()
```

### Replay Events

```python
from python_pubsub_devtools.event_recorder import EventReplayer

replayer = EventReplayer("recordings/production_issue_123.json")
replayer.replay(service_bus, speed_multiplier=1.0)
```

### Analyze Recording

```bash
# Using the event_recorder module CLI
python -m python_pubsub_devtools.event_recorder.event_recorder info recordings/session.json
python -m python_pubsub_devtools.event_recorder.event_recorder timeline recordings/session.json
```

## Use Cases

### 1. Bug Reproduction

Record events when a bug occurs, then replay them repeatedly to understand and fix the issue.

```python
# Record production issue
recorder = EventRecorder("bug_position_not_closing", "recordings")
recorder.start_recording(service_bus)
# ... issue occurs ...
recorder.stop_recording()
recorder.save()

# Later, replay to reproduce
replayer = EventReplayer("recordings/bug_position_not_closing_*.json")
replayer.replay(service_bus)  # Bug should reproduce
```

### 2. Performance Testing

Replay events at high speed to stress-test your system.

```python
replayer = EventReplayer("recordings/normal_trading_day.json")
# Replay 24 hours of events in 2.4 hours (10x speed)
replayer.replay(service_bus, speed_multiplier=10.0)
```

### 3. Edge Case Testing

Filter and replay only specific event sequences.

```python
# Only replay failed trades
replayer = EventReplayer("recordings/trading_session.json")
filtered = replayer.filter_events(lambda name: "Failed" in name)
filtered.replay(service_bus)
```

### 4. Integration Testing

Record real market events and use them as test data.

```python
# Record real market behavior
recorder = EventRecorder("btc_volatility_spike", "test_data")
recorder.start_recording(service_bus)
# ... capture volatile market conditions ...
recorder.save()

# Use in tests
def test_volatility_handling():
    replayer = EventReplayer("test_data/btc_volatility_spike.json")
    replayer.replay(test_service_bus)
    # Assert expected behavior
```

### 5. Training Data Collection

Record successful trading sessions to analyze strategy performance.

```python
recorder = EventRecorder("profitable_session_2025_10_17", "recordings")
recorder.start_recording(service_bus)
# ... profitable trading session ...
recorder.stop_recording()
recorder.save()

# Later, analyze what worked
replayer = EventReplayer("recordings/profitable_session_2025_10_17.json")
summary = replayer.get_event_summary()
replayer.print_timeline()
```

## Configuration

Add to your `devtools_config.yaml`:

```yaml
event_recorder:
  recordings_dir: recordings
  port: 5556
```

## Architecture

```
┌─────────────────────┐
│   Your Trading Bot  │
└──────────┬──────────┘
           │ publishes events
           ▼
┌─────────────────────┐
│   ServiceBus        │◄─── EventRecorder intercepts
│   (event bus)       │     and records all events
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  Recording Files    │
│   (JSON on disk)    │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐     ┌──────────────────────┐
│   EventReplayer     │────▶│ EventRecorderServer  │
│   (replay engine)   │     │   (web dashboard)    │
└─────────────────────┘     └──────────────────────┘
```

## Best Practices

1. **Session Naming**: Use descriptive names with context
   - ✅ `production_bug_position_stuck_20251017`
   - ❌ `session1`

2. **Storage Management**: Recordings can be large - implement rotation
   ```python
   # Keep only last 30 days
   import time
   from pathlib import Path
   
   recordings_dir = Path("recordings")
   cutoff = time.time() - (30 * 24 * 3600)
   
   for file in recordings_dir.glob("*.json"):
       if file.stat().st_mtime < cutoff:
           file.unlink()
   ```

3. **Sensitive Data**: Recordings may contain sensitive information
   - Store recordings securely
   - Sanitize before sharing
   - Add to `.gitignore`

4. **Event Reconstruction**: Provide events module for proper replay
   ```python
   # With event classes
   replayer.replay(
       service_bus,
       events_module_name="my_project.events"
   )
   
   # Without - events are replayed as dicts
   replayer.replay(service_bus)
   ```

5. **Testing**: Use recordings as regression test data
   ```python
   def test_market_crash_handling():
       replayer = EventReplayer("test_data/market_crash_2020.json")
       replayer.replay(test_service_bus)
       assert bot.position_closed
       assert bot.loss < max_acceptable_loss
   ```

## Limitations

- **Simulation Mode Only**: The web server replay is simulation-only (no actual ServiceBus publishing)
- **Memory Usage**: Large recordings (>100k events) may consume significant memory
- **Timing Precision**: Replay timing is best-effort (affected by system load)
- **Serialization**: Complex event types may not serialize perfectly

## Troubleshooting

### Events Not Recording

Check that the recorder is started before events are published:

```python
recorder = EventRecorder("session", "recordings")
recorder.start_recording(service_bus)  # Must be before events
# ... now events will be recorded ...
```

### Replay Events Not Reconstructed

Provide the events module for proper reconstruction:

```python
# Wrong - events are dicts
replayer.replay(service_bus)

# Correct - events are proper objects
replayer.replay(service_bus, events_module_name="my_project.events")
```

### Web Server Not Starting

Check port availability:

```bash
# Find what's using port 5556
lsof -i :5556

# Use different port
python -m python_pubsub_devtools.event_recorder.serve_recorder --port 5557
```

## Related Tools

- **Event Flow**: Visualize event architecture
- **Scenario Testing**: Automated scenario execution
- **Mock Exchange**: Simulate exchange behavior

## Examples

See `examples/event_recorder/` for complete examples:

- `basic_recording.py` - Simple recording and replay
- `filtered_replay.py` - Event filtering
- `performance_test.py` - High-speed replay
- `web_integration.py` - Using the web API
