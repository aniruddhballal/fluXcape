"""Exercise real Streamlit state transitions without a browser or solar downloads."""

from pathlib import Path

from streamlit.testing.v1 import AppTest

APP = Path(__file__).resolve().parents[1] / "app.py"


def button(app, label):
    return next(item for item in app.button if item.label == label)


def assert_clean(app):
    assert not app.exception, [item.message for item in app.exception]


def test_dashboard_controls_and_reset():
    app = AppTest.from_file(str(APP), default_timeout=30).run()
    assert_clean(app)
    assert app.toggle(key="differential").value is False
    assert app.session_state["frame"] == 0
    button(app, "Jump to t = 0").click().run()
    assert_clean(app)
    assert app.session_state["frame"] == 360
    app.toggle(key="differential").set_value(True).run()
    app.slider(key="selected").set_value(359).run()
    app.selectbox(key="reference").select(180).run()
    assert_clean(app)
    app.radio(key="phase").set_value("Transport to reference").run()
    assert app.session_state["frame"] == 0
    button(app, "Finish transport").click().run()
    assert_clean(app)
    assert app.session_state["frame"] == 360
    app.toggle(key="fill_gaps").set_value(False).run()
    app.toggle(key="neighbors").set_value(True).run()
    app.toggle(key="guided").set_value(True).run()
    assert_clean(app)
    app.select_slider(key="lesson").set_value(7).run()
    assert app.session_state["frame"] == 360
    button(app, "Reset simulation").click().run()
    assert_clean(app)
    assert app.toggle(key="differential").value is False
    assert app.session_state["frame"] == 0
    assert app.session_state["reference"] == 0


def test_play_pause_scrub_and_stepping():
    app = AppTest.from_file(str(APP), default_timeout=30).run()
    button(app, "Forward →").click().run()
    assert app.session_state["frame"] == 1
    button(app, "← Back").click().run()
    assert app.session_state["frame"] == 0
    app.slider(key="clock_slider").set_value(-13.635).run()
    assert_clean(app)
    assert app.session_state["frame"] == 180
    button(app, "▶ Play").click().run()
    assert app.session_state["playing"] is True
    # Make the next rerun a timed animation tick, without a blocking sleep.
    app.session_state["last_tick"] = 0.0
    app.run()
    assert_clean(app)
    assert app.session_state["frame"] == 186
    button(app, "Ⅱ Pause").click().run()
    assert app.session_state["playing"] is False
    app.radio(key="phase").set_value("Transport to reference").run()
    app.slider(key="clock_slider").set_value(0.5).run()
    assert_clean(app)
    assert app.session_state["frame"] == 180
    button(app, "↶ Rewind stage").click().run()
    assert app.session_state["frame"] == 0
