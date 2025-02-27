"""Class for monitoring system stats."""

import logging
import threading

from mlflow.environment_variables import (
    MLFLOW_SYSTEM_METRICS_SAMPLES_BEFORE_LOGGING,
    MLFLOW_SYSTEM_METRICS_SAMPLING_INTERVAL,
)
from mlflow.system_metrics.metrics.cpu_monitor import CPUMonitor
from mlflow.system_metrics.metrics.disk_monitor import DiskMonitor
from mlflow.system_metrics.metrics.gpu_monitor import GPUMonitor
from mlflow.system_metrics.metrics.network_monitor import NetworkMonitor

_logger = logging.getLogger(__name__)


class SystemMetricsMonitor:
    """Class for monitoring system stats.

    This class is used for pulling system metrics and logging them to MLflow. Calling `start()` will
    spawn a thread that logs system metrics periodically. Calling `finish()` will stop the thread.
    Logging is done on a different frequency from pulling metrics, so that the metrics are
    aggregated over the period. Users can change the logging frequency by setting
    `MLFLOW_SYSTEM_METRICS_SAMPLING_INTERVAL` and `MLFLOW_SYSTEM_METRICS_SAMPLES_BEFORE_LOGGING`
    environment variables, e.g., run `export MLFLOW_SYSTEM_METRICS_SAMPLING_INTERVAL=10` in terminal
    will set the sampling interval to 10 seconds.

    Args:
        run_id: string, the MLflow run ID.
        sampling_interval: float, default to 10. The interval (in seconds) at which to pull system
            metrics. Will be overridden by `MLFLOW_SYSTEM_METRICS_SAMPLING_INTERVAL` environment
            variable.
        samples_before_logging: int, default to 1. The number of samples to aggregate before
            logging. Will be overridden by `MLFLOW_SYSTEM_METRICS_SAMPLES_BEFORE_LOGGING`
            evnironment variable.
    """

    def __init__(self, run_id, sampling_interval=10, samples_before_logging=1):
        from mlflow.utils.autologging_utils import BatchMetricsLogger

        # Instantiate default monitors.
        self.monitors = [CPUMonitor(), DiskMonitor(), NetworkMonitor()]
        try:
            gpu_monitor = GPUMonitor()
            self.monitors.append(gpu_monitor)
        except Exception as e:
            _logger.warning(
                f"Skip logging GPU metrics because creating `GPUMonitor` failed with error: {e}."
            )

        self.sampling_interval = MLFLOW_SYSTEM_METRICS_SAMPLING_INTERVAL.get() or sampling_interval
        self.samples_before_logging = (
            MLFLOW_SYSTEM_METRICS_SAMPLES_BEFORE_LOGGING.get() or samples_before_logging
        )

        self._run_id = run_id
        self.mlflow_logger = BatchMetricsLogger(self._run_id)
        self._shutdown_event = threading.Event()
        self._process = None
        self._logging_step = 0

    def start(self):
        """Start monitoring system metrics."""
        try:
            self._process = threading.Thread(
                target=self.monitor,
                daemon=True,
                name="SystemMetricsMonitor",
            )
            self._process.start()
            _logger.info("Started monitoring system metrics.")
        except Exception as e:
            _logger.warning(f"Failed to start monitoring system metrics: {e}")
            self._process = None

    def monitor(self):
        """Main monitoring loop, which consistently collect and log system metrics."""
        from mlflow.tracking.fluent import get_run

        while not self._shutdown_event.is_set():
            for _ in range(self.samples_before_logging):
                self.collect_metrics()
                self._shutdown_event.wait(self.sampling_interval)
                try:
                    # Get the MLflow run to check if the run is not RUNNING.
                    run = get_run(self._run_id)
                except Exception as e:
                    _logger.warning(f"Failed to get mlflow run: {e}.")
                    return
                if run.info.status != "RUNNING" or self._shutdown_event.is_set():
                    # If the mlflow run is terminated or receives the shutdown signal, stop
                    # monitoring.
                    return
            metrics = self.aggregate_metrics()
            try:
                self.publish_metrics(metrics)
            except Exception as e:
                _logger.warning(
                    f"Failed to log system metrics: {e}, this is expected if the experiment/run is "
                    "already terminated."
                )
                return

    def collect_metrics(self):
        """Collect system metrics."""
        metrics = {}
        for monitor in self.monitors:
            monitor.collect_metrics()
            metrics.update(monitor._metrics)
        return metrics

    def aggregate_metrics(self):
        """Aggregate collected metrics."""
        metrics = {}
        for monitor in self.monitors:
            metrics.update(monitor.aggregate_metrics())
        return metrics

    def publish_metrics(self, metrics):
        """Log collected metrics to MLflow."""
        self.mlflow_logger.record_metrics(metrics, self._logging_step)
        self._logging_step += 1
        for monitor in self.monitors:
            monitor.clear_metrics()

    def finish(self):
        """Stop monitoring system metrics."""
        if self._process is None:
            return
        _logger.info("Stopping system metrics monitoring...")
        self._shutdown_event.set()
        try:
            self._process.join()
            _logger.info("Successfully terminated system metrics monitoring!")
        except Exception as e:
            _logger.error(f"Error terminating system metrics monitoring process: {e}.")
        self._process = None
