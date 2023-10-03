import shutil
from pathlib import Path
from typing import List

import pytest

import mlflow
import mlflow.utils.time
from mlflow.entities import Metric

ROOT = Path(__file__).parent / "test-data"

shutil.rmtree(ROOT, ignore_errors=True)


def dummy_time():
    return 1999


@pytest.fixture
def metrics() -> List[Metric]:
    return [
        Metric(key="r2", value=0.93, timestamp=dummy_time(), step=0, tags={"country": "se"}),
        Metric(key="r2", value=-0.3, timestamp=dummy_time(), step=0, tags={"country": "no"}),
        Metric(key="r2", value=0.99, timestamp=dummy_time(), step=0, tags={"country": "us"}),
        Metric(key="r2", value=0.96, timestamp=dummy_time(), step=0, tags=None),
    ]


def exp_name(artifact_location):
    return artifact_location.partition(":")[0]


@pytest.mark.parametrize(
    "artifact_location",
    [f"file://{ROOT}/file_store", f"sqlite:///{ROOT}/sqlalchemy_store/mlflow.db"],
    ids=exp_name,
)
def test(metrics, artifact_location, monkeypatch):
    monkeypatch.setattr("mlflow.utils.time.get_current_time_millis.__code__", dummy_time.__code__)

    if artifact_location.endswith(".db"):
        Path(artifact_location[len("sqlite://") :]).parent.mkdir(parents=True)
    mlflow.set_tracking_uri(str(artifact_location))
    # experiment_id = mlflow.create_experiment(exp_name(artifact_location), artifact_location=str(artifact_location))

    with mlflow.start_run() as run:
        for m in metrics:
            mlflow.log_metric(m.key, m.value, tags=m.tags)

    raw = mlflow.MlflowClient().get_run(run.info.run_id).data._metric_objs
    assert len(raw) == len(metrics)
    for m in metrics:
        assert m in raw

    run_data = mlflow.MlflowClient().get_run(run.info.run_id).data

    assert run_data.metrics == {"r2": 0.96}
    assert run_data.tagged_metrics == [
        ("r2", -0.3, {"country": "no"}),
        ("r2", 0.93, {"country": "se"}),
        ("r2", 0.99, {"country": "us"}),
    ]

    mlflow.data.dataset.Dataset()
    mlflow.evaluate(
        "some-model",
    )
