from abc import ABCMeta, abstractmethod
from functools import reduce


class LocustFileSelector:
    __metaclass__ = ABCMeta

    @abstractmethod
    def select(self, source): raise NotImplementedError


class LocustFileSourceSelectorMiddleware:
    __metaclass__ = ABCMeta

    @abstractmethod
    def invoke(self, context, call_next): raise NotImplementedError


class LocustFileSource:
    __metaclass__ = ABCMeta

    @abstractmethod
    def fetch(self): raise NotImplementedError

    @abstractmethod
    def cleanup(self): raise NotImplementedError


class LocustFileSelectorPipeline(LocustFileSelector):

    def __init__(self, middlewares):
        self.middlewares = middlewares

    def select(self, source):
        context = LocustFileSelectorPipelineContext()
        context.source = source

        def __do_nothing(ctx):
            return None

        reduce(lambda call_next, middleware: lambda ctx: middleware.invoke(ctx, call_next),
               reversed(self.middlewares),
               __do_nothing)(context)

        if context.file_source is None:
            raise Exception('Could not determine file source')
        return context.file_source


class LocustFileSelectorPipelineContext:
    source = None
    file_source = None
