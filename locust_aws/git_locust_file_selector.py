from .locust_file_selector import LocustFileSourceSelectorMiddleware, LocustFileSource
from git import Repo
import tempfile
import re
from pathlib import Path
import shutil


class GitLocustFileSelectorMiddleware(LocustFileSourceSelectorMiddleware):

    def __init__(self, **kvargs):
        self.kvargs = kvargs

    def invoke(self, context, call_next):
        source = context.source
        if not source.startswith('git::'):
            call_next(context)
            return
        context.file_source = GitLocustFileSource(source, **self.kvargs)


class GitLocustFileSource(LocustFileSource):

    def __init__(self, source, **kvargs):
        self.source = source
        self.temp_dir = None
        self.ssh_identity_file = kvargs.get('ssh_identity_file')

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

        env = {"GIT_SSH_COMMAND": f'ssh -i "{self.ssh_identity_file}"'} if self.ssh_identity_file is not None else None
        Repo.clone_from(url, str(temp_dir), env=env, **kwargs)

        return str(Path(temp_dir) / Path(path.strip('/\\')))

    def cleanup(self):
        if self.temp_dir is None:
            return

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def __parse_source(self):
        pattern = r"git::((?:[^:/?#]+)://)?((?:(?!(?://|\?)).)*)((?:(?!\?).)*)(\?.+)?"
        m = re.match(pattern, self.source)

        def xstr(s):
            if s is None:
                return ''
            else:
                return s

        return xstr(m.group(1)) + xstr(m.group(2)), xstr(m.group(3)), xstr(m.group(4))
