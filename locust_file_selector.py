from abc import ABCMeta, abstractmethod


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
