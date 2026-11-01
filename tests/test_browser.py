"""Tests for izaya.js, run in headless Firefox against a live server."""

import shutil

import pytest
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.support.ui import WebDriverWait

pytestmark = pytest.mark.skipif(not shutil.which("firefox"), reason="Firefox is not installed")


class Widget:
    def __init__(self, driver, field):
        self.driver = driver
        self.input = driver.find_element(By.ID, f"id_{field}")
        self.root = self.input.find_element(By.XPATH, "ancestor::*[@data-izaya]")
        self.listbox = self.root.find_element(By.CSS_SELECTOR, "[data-izaya-listbox]")
        self.wait = WebDriverWait(driver, 5)

    @property
    def options(self):
        return self.root.find_elements(By.CSS_SELECTOR, "[data-izaya-key]")

    @property
    def chips(self):
        labels = self.root.find_elements(
            By.CSS_SELECTOR, "[data-izaya-selection] [data-izaya-chip-label]"
        )
        return [label.text for label in labels]

    @property
    def placeholder(self):
        return self.input.get_dom_attribute("placeholder")

    def search(self, text):
        self.input.send_keys(text)
        self.wait.until(lambda _: self.listbox.is_displayed() and self.options)

    def pick(self, text):
        self.search(text)
        self.input.send_keys(Keys.ARROW_DOWN, Keys.ENTER)
        self.wait.until(lambda _: not self.listbox.is_displayed())

    def active_index(self):
        active = self.input.get_attribute("aria-activedescendant")
        return [option.get_attribute("id") for option in self.options].index(active)

    def press_repeating(self, key):
        self.driver.execute_script(
            "arguments[0].dispatchEvent(new KeyboardEvent('keydown', "
            "{key: arguments[1], repeat: true, bubbles: true}))",
            self.input,
            key,
        )


@pytest.fixture(scope="module")
def driver():
    options = Options()
    options.add_argument("-headless")
    driver = webdriver.Firefox(options=options)
    yield driver
    driver.quit()


@pytest.fixture
def page(driver, live_server):
    driver.get(f"{live_server.url}/form/")
    WebDriverWait(driver, 5).until(lambda _: driver.execute_script("return !!window.htmx"))
    return driver


def load_layout_css(page, host_css=""):
    """Load layout.css after `host_css`, the order a site normally ends up with."""
    page.execute_script(
        "const style = document.createElement('style');"
        "style.textContent = arguments[0];"
        "const link = document.createElement('link');"
        "link.rel = 'stylesheet';"
        "link.href = '/static/izaya/layout.css';"
        "link.onload = () => { window.layoutLoaded = true; };"
        "document.head.append(style, link);",
        host_css,
    )
    WebDriverWait(page, 5).until(lambda _: page.execute_script("return window.layoutLoaded"))


def listbox_colors(widget):
    return widget.driver.execute_script(
        "const style = getComputedStyle(arguments[0]);return [style.backgroundColor, style.color]",
        widget.listbox,
    )


def test_listbox_stays_hidden_under_a_display_class(page):
    assert not Widget(page, "colors").listbox.is_displayed()


def test_listbox_class_colors_beat_a_later_layout_css(page):
    load_layout_css(page, ".box { background-color: rgb(1, 2, 3); color: rgb(4, 5, 6); }")
    assert listbox_colors(Widget(page, "colors")) == ["rgb(1, 2, 3)", "rgb(4, 5, 6)"]


def test_custom_properties_set_the_listbox_colors(page):
    load_layout_css(
        page,
        ":root { --izaya-listbox-background: rgb(1, 2, 3); --izaya-listbox-color: rgb(4, 5, 6); }",
    )
    assert listbox_colors(Widget(page, "color")) == ["rgb(1, 2, 3)", "rgb(4, 5, 6)"]


def test_listbox_is_opaque_by_default(page):
    load_layout_css(page)
    background, _ = listbox_colors(Widget(page, "color"))
    assert background != "rgba(0, 0, 0, 0)"


def test_keyboard_selects_an_option(page):
    widget = Widget(page, "colors")
    widget.pick("gre")
    assert widget.chips == ["Green"]
    assert widget.input.get_attribute("value") == ""
    assert not widget.listbox.is_displayed()
    assert page.switch_to.active_element == widget.input


def test_active_option_gets_the_configured_class(page):
    widget = Widget(page, "colors")
    widget.search("e")
    widget.input.send_keys(Keys.ARROW_DOWN)
    assert "active" in widget.options[0].get_attribute("class")
    assert widget.input.get_attribute("aria-activedescendant")


def test_arrow_up_wraps_to_the_last_option(page):
    widget = Widget(page, "colors")
    widget.search("e")
    widget.input.send_keys(Keys.ARROW_UP)
    assert widget.active_index() == len(widget.options) - 1


def test_click_selects_and_keeps_focus(page):
    widget = Widget(page, "colors")
    widget.search("red")
    widget.options[0].click()
    widget.wait.until(lambda _: widget.chips)
    assert page.switch_to.active_element == widget.input


def test_single_select_replaces_the_value(page):
    widget = Widget(page, "color")
    widget.pick("red")
    widget.pick("blu")
    assert widget.chips == ["Blue"]


def test_escape_closes_the_listbox(page):
    widget = Widget(page, "colors")
    widget.search("red")
    widget.input.send_keys(Keys.ESCAPE)
    assert not widget.listbox.is_displayed()


def test_leaving_the_widget_closes_the_listbox(page):
    widget = Widget(page, "color")
    widget.search("red")
    widget.input.send_keys(Keys.TAB)
    widget.wait.until(lambda _: not widget.listbox.is_displayed())


def test_selected_option_is_marked_in_later_results(page):
    widget = Widget(page, "colors")
    widget.pick("red")
    widget.search("red")
    assert widget.options[0].get_attribute("aria-selected") == "true"


def test_same_term_searches_again_after_a_pick(page):
    widget = Widget(page, "colors")
    widget.pick("e")
    widget.search("e")
    assert widget.options


def test_backspace_removes_the_last_chip(page):
    widget = Widget(page, "colors")
    widget.pick("red")
    widget.input.send_keys(Keys.BACKSPACE)
    assert widget.chips == []


def test_held_backspace_keeps_chips(page):
    widget = Widget(page, "colors")
    widget.pick("red")
    widget.press_repeating("Backspace")
    assert widget.chips == ["Red"]


def test_readonly_input_keeps_chips(page):
    widget = Widget(page, "readonly")
    widget.input.send_keys(Keys.BACKSPACE)
    assert widget.chips == ["Red"]


def test_remove_button_removes_the_chip(page):
    widget = Widget(page, "colors")
    widget.pick("red")
    widget.root.find_element(By.CSS_SELECTOR, "[data-izaya-remove]").click()
    assert widget.chips == []


def test_single_value_drops_the_placeholder_until_the_chip_is_removed(page):
    widget = Widget(page, "color")
    assert widget.placeholder == "Find"
    widget.pick("red")
    assert widget.placeholder is None
    widget.input.send_keys(Keys.BACKSPACE)
    assert widget.placeholder == "Find"


def test_replacing_a_single_value_keeps_the_placeholder_away(page):
    widget = Widget(page, "color")
    widget.pick("red")
    widget.pick("blu")
    assert widget.placeholder is None


def test_rendered_single_value_restores_the_placeholder(page):
    widget = Widget(page, "preset")
    assert widget.placeholder is None
    widget.root.find_element(By.CSS_SELECTOR, "[data-izaya-remove]").click()
    assert widget.placeholder == "Find"


def test_multiple_keeps_the_placeholder(page):
    widget = Widget(page, "colors")
    widget.pick("red")
    assert widget.placeholder == "Find"


def test_label_markup_stays_text(page):
    widget = Widget(page, "markup")
    widget.pick("b")
    assert widget.chips == ["<b>bold</b>"]


def test_search_text_is_not_submitted(page):
    widget = Widget(page, "colors")
    widget.pick("red")
    widget.input.send_keys("blu")
    data = page.execute_script(
        "const data = new FormData(document.getElementById('form'));"
        "return {colors: data.getAll('colors'), q: data.getAll('q')}"
    )
    assert data == {"colors": ["1"], "q": []}


def test_events_report_selection_changes(page):
    page.execute_script(
        "window.events = [];"
        "for (const name of ['izaya:select', 'izaya:remove']) {"
        "  document.addEventListener(name, (e) => events.push([name, e.detail.label]));"
        "}"
    )
    widget = Widget(page, "colors")
    widget.pick("red")
    widget.input.send_keys(Keys.BACKSPACE)
    assert page.execute_script("return events") == [
        ["izaya:select", "Red"],
        ["izaya:remove", "Red"],
    ]


def test_widget_added_later_works_without_setup(page):
    page.execute_script(
        "const row = document.getElementById('id_colors').closest('[data-izaya]')"
        "  .parentElement.cloneNode(true);"
        "row.querySelectorAll('[id]').forEach((el) => {"
        "  el.id = el.id.replace('id_colors', 'id_clone');"
        "});"
        "document.getElementById('form').append(row);"
        "htmx.process(row);"
    )
    widget = Widget(page, "clone")
    widget.pick("red")
    assert widget.chips == ["Red"]


def test_closing_clears_the_options(page):
    widget = Widget(page, "colors")
    widget.search("red")
    widget.input.send_keys(Keys.ESCAPE)
    assert widget.options == []


def test_denied_search_shows_the_message(page):
    page.execute_script(
        "window.errors = 0;"
        "document.addEventListener('htmx:responseError', () => { window.errors += 1; });"
    )
    widget = Widget(page, "private")
    widget.input.send_keys("bat")
    widget.wait.until(lambda _: widget.listbox.is_displayed())
    assert "Log in to use this search." in widget.listbox.text
    assert widget.options == []
    assert page.execute_script("return window.errors") == 0


def test_error_page_stays_out_of_the_results(page):
    page.execute_script(
        "document.addEventListener('htmx:afterRequest', () => { window.answered = true; });"
    )
    widget = Widget(page, "raising")
    widget.input.send_keys("bat")
    widget.wait.until(lambda _: page.execute_script("return window.answered"))
    assert not widget.listbox.is_displayed()
    assert widget.listbox.text == ""
    assert page.title == "izaya"


def test_loading_the_script_twice_acts_once(page):
    page.execute_script(
        "const script = document.createElement('script');"
        "script.src = [...document.scripts].find((s) => s.src.includes('izaya.js')).src;"
        "script.onload = () => { window.reloaded = true; };"
        "document.head.append(script);"
    )
    WebDriverWait(page, 5).until(lambda _: page.execute_script("return window.reloaded"))
    widget = Widget(page, "colors")
    widget.search("e")
    widget.input.send_keys(Keys.ARROW_DOWN)
    assert widget.active_index() == 0
