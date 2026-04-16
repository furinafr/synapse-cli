import asyncio
import re
import argparse
import sys
import time
from pathlib import Path
from typing import List, Pattern, Optional, Set
from dataclasses import dataclass

@dataclass
class SearchResult:
    path: Path
    line_number: int
    content: str

class SynapseEngine:
    def __init__(self, root: Path, pattern: str, extensions: Optional[Set[str]] = None, workers: int = 10):
        self.root = root
        self.pattern: Pattern = re.compile(pattern)
        self.extensions = extensions
        self.workers = workers
        self.queue: asyncio.Queue = asyncio.Queue(maxsize=1000)
        self.results: List[SearchResult] = []
        self.processed_files = 0

    async def _worker(self):
        while True:
            file_path = await self.queue.get()
            if file_path is None:
                self.queue.task_done()
                break
            try:
                await self._process_file(file_path)
            except (UnicodeDecodeError, PermissionError):
                pass
            finally:
                self.queue.task_done()

    async def _process_file(self, file_path: Path):
        # Non-blocking file read utilizing threads to avoid blocking the event loop
        loop = asyncio.get_running_loop()
        lines = await loop.run_in_executor(None, self._read_file_safe, file_path)
        
        for i, line in enumerate(lines, 1):
            if self.pattern.search(line):
                self.results.append(SearchResult(file_path, i, line.strip()))
        self.processed_files += 1

    @staticmethod
    def _read_file_safe(path: Path) -> List[str]:
        try:
            with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                return f.readlines()
        except Exception:
            return []

    async def run(self):
        start_time = time.perf_counter()
        workers = [asyncio.create_task(self._worker()) for _ in range(self.workers)]

        for file_path in self.root.rglob('*'):
            if file_path.is_file():
                if self.extensions and file_path.suffix not in self.extensions:
                    continue
                await self.queue.put(file_path)

        for _ in range(self.workers):
            await self.queue.put(None)

        await self.queue.join()
        duration = time.perf_counter() - start_time
        return self.results, duration, self.processed_files

def main():
    parser = argparse.ArgumentParser(description='Synapse-CLI: Async Pattern Discovery')
    parser.add_argument('path', type=str, help='Root directory to search')
    parser.add_argument('pattern', type=str, help='Regex pattern to search for')
    parser.add_argument('--ext', nargs='+', help='File extensions to include (e.g. .py .ts)')
    parser.add_argument('--workers', type=int, default=20, help='Number of concurrent workers')
    
    args = parser.parse_args()
    root_path = Path(args.path)

    if not root_path.exists():
        print(f'Error: Path {args.path} does not exist.')
        sys.exit(1)

    engine = SynapseEngine(root_path, args.pattern, set(args.ext) if args.ext else None, args.workers)
    
    try:
        results, duration, count = asyncio.run(engine.run())
        for res in results:
            print(f'\033[92m{res.path}:{res.line_number}\033[0m: {res.content}')
        
        print(f'\nSummary: Found {len(results)} matches across {count} files in {duration:.2f} seconds.')
    except KeyboardInterrupt:
        print('\nSearch aborted by user.')

if __name__ == '__main__':
    main()