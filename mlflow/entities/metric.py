from mlflow.entities._mlflow_object import _MLflowObject
from mlflow.protos.service_pb2 import Metric as ProtoMetric


class Metric(_MLflowObject):
    """
    Metric object.
    """

    def __init__(self, key, value, timestamp, step, tags):
        self._key = key
        self._value = value
        self._timestamp = timestamp
        self._step = step
        self._tags = tags or {}

    @property
    def key(self):
        """String key corresponding to the metric name."""
        return self._key

    @property
    def value(self):
        """Float value of the metric."""
        return self._value

    @property
    def timestamp(self):
        """Metric timestamp as an integer (milliseconds since the Unix epoch)."""
        return self._timestamp

    @property
    def step(self):
        """Integer metric step (x-coordinate)."""
        return self._step

    @property
    def tags(self):
        return self._tags

    def to_proto(self):
        metric = ProtoMetric(
            dimensions=[ProtoMetric.Dimension(key=k, value=v) for k, v in self.tags.items()]
        )
        metric.key = self.key
        metric.value = self.value
        metric.timestamp = self.timestamp
        metric.step = self.step
        return metric

    @classmethod
    def from_proto(cls, proto):
        return cls(
            proto.key,
            proto.value,
            proto.timestamp,
            proto.step,
            {d.key: d.value for d in proto.dimensions},
        )

    def __eq__(self, __o):
        if isinstance(__o, self.__class__):
            return self.__dict__ == __o.__dict__

        return False

    def __hash__(self):
        dimension_tuples = tuple((k, self._dimensions[k]) for k in sorted(self._dimensions))
        return hash((self._key, self._value, self._timestamp, self._step, dimension_tuples))
