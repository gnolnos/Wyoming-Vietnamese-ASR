# Wyoming Vietnamese ASR Add-on

## Installation

1. Add this repository to your Home Assistant Add-on Store.
2. Install the **Wyoming Vietnamese ASR** add-on.
3. Start the add-on.

## Configuration

- **embedding_model**: Model for embeddings (e.g., `qwen3-embedding:4b`).
- **log_level**: System logging level (`info`, `debug`, `warn`, `error`).

## Integration
After starting the add-on, go to **Settings -> Devices & Services -> Add Integration** and search for **Wyoming Protocol**. 
Use `localhost` or the provided IP with port `10400` to connect the ASR engine to Home Assistant.
