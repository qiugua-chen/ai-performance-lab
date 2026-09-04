from pathlib import Path
from xml.etree import ElementTree


PROJECT_ROOT = Path(__file__).resolve().parents[1]
TEMPLATE_PATH = (
    PROJECT_ROOT
    / "jmeter"
    / "templates"
    / "http_get.jmx"
)


def load_template_root() -> ElementTree.Element:
    tree = ElementTree.parse(TEMPLATE_PATH)
    return tree.getroot()


def test_jmeter_template_is_valid_xml() -> None:
    root = load_template_root()

    assert root.tag == "jmeterTestPlan"


def test_jmeter_template_contains_required_properties() -> None:
    root = load_template_root()
    element_values = {
        element.text
        for element in root.iter()
        if element.text
    }

    required_properties = {
        "${__P(threads,1)}",
        "${__P(ramp_up_seconds,1)}",
        "${__P(duration_seconds,10)}",
        "${__P(protocol,http)}",
        "${__P(host,127.0.0.1)}",
        "${__P(port,8001)}",
        "${__P(path,/api/normal)}",
        "${__P(connect_timeout_ms,5000)}",
        "${__P(response_timeout_ms,10000)}",
        "${__P(expected_status,200)}",
    }

    assert required_properties <= element_values


def test_jmeter_template_contains_no_result_listeners() -> None:
    root = load_template_root()

    result_collectors = list(root.iter("ResultCollector"))

    assert result_collectors == []