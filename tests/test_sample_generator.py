import importlib.util
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = PROJECT_ROOT / "scripts" / "generate_sample_telemetry.py"
BUNDLED_SAMPLE = PROJECT_ROOT / "samples" / "telemetry_event.json"


def _load_generator_module():
    spec = importlib.util.spec_from_file_location("generate_sample_telemetry", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_generator_default_output_does_not_overwrite_bundled_sample():
    """Regression test: the generator used to overwrite the stable fixture
    samples/telemetry_event.json, which broke the API sample tests."""
    module = _load_generator_module()

    default_output = (PROJECT_ROOT / module.DEFAULT_OUTPUT).resolve()
    assert default_output != BUNDLED_SAMPLE.resolve()
    assert "generated" in default_output.parts
