from .ashby import AshbyCollector
from .greenhouse import GreenhouseCollector
from .lever import LeverCollector

COLLECTORS = {
    "greenhouse": GreenhouseCollector(),
    "lever": LeverCollector(),
    "ashby": AshbyCollector(),
}
