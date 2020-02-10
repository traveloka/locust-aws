from .locust_file_selector import LocustFileSourceSelectorMiddleware, LocustFileSource
from git import Repo
import tempfile
import re
from pathlib import Path
import shutil


class GitLocustFileSelectorMiddleware(LocustFileSourceSelectorMiddleware):

    def invoke(self, context, call_next):
        source = context.source
        if not source.startswith('git::'):
            call_next(context)
            return
        context.file_source = GitLocustFileSource(source)


class GitLocustFileSource(LocustFileSource):

    def __init__(self, source):
        self.source = source
        self.temp_dir = None

    def fetch(self):
        temp_dir = self.temp_dir = tempfile.mkdtemp()
        print(temp_dir)
        url, path, query = self.__parse_source()
        print(url)

        ref_key = 'ref='
        ref = next((x[len(ref_key):] for x in query.lstrip('?').split("&") if x.startswith(ref_key)), None) \
            if query is not None else None

        kwargs = {}
        if ref is not None:
            kwargs['branch'] = ref

        Repo.clone_from(url, str(temp_dir), **kwargs)

        return str(Path(temp_dir) / Path(path.strip('/\\')))

    def cleanup(self):
        if self.temp_dir is None:
            return

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def __parse_source(self):
        pattern = r"git::((?:[^:/?#]+)://)?((?:(?!(?://|\?)).)*)((?:(?!\?).)*)(\?.+)?"
        m = re.match(pattern, self.source)
        return m.group(1) + m.group(2), m.group(3), m.group(4)
