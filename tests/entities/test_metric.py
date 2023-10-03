from mlflow.entities import Metric
from mlflow.utils.time import get_current_time_millis

from tests.helper_functions import random_int, random_str


def _check(metric, key, value, timestamp, step, dimensions):
    assert type(metric) == Metric
    assert metric.key == key
    assert metric.value == value
    assert metric.timestamp == timestamp
    assert metric.step == step
    assert metric.dimensions == dimensions


def test_creation_and_hydration():
    key = random_str()
    value = 10000
    ts = get_current_time_millis()
    step = random_int()
    dimensions = {random_str(): random_str(), random_str(): random_str()}

    metric = Metric(key, value, ts, step, dimensions)
    _check(metric, key, value, ts, step, dimensions)

    as_dict = {"key": key, "value": value, "timestamp": ts, "step": step, "dimensions": dimensions}
    assert dict(metric) == as_dict

    proto = metric.to_proto()
    metric2 = metric.from_proto(proto)
    _check(metric2, key, value, ts, step, dimensions)

    metric3 = Metric.from_dictionary(as_dict)
    _check(metric3, key, value, ts, step, dimensions)
