# Synapse-CLI

Synapse-CLI is a high-performance search utility that leverages Python's `asyncio` and `ThreadPoolExecutor` to perform concurrent file system traversals and regex matching.

## Features
- **Asynchronous I/O**: Utilizes a producer-consumer pattern to decouple file discovery from content processing.
- **Regex Support**: Full Python regex engine support for complex pattern matching.
- **Performance**: Optimized for SSD-based systems where high concurrency can significantly reduce search latency.
- **Safe Decoding**: Gracefully handles binary files and encoding issues using non-strict UTF-8 decoding.

## Usage
```bash
python synapse.py /path/to/search "TODO:|FIXME:" --ext .py .js --workers 50
```