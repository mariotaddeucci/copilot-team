"""Tests for the PydanticForm auto-generated form builder."""

from typing import Literal

from pydantic import BaseModel, Field
from textual.app import App, ComposeResult
from textual.widgets import Checkbox, Input, Select, TextArea

from copilot_team.tui.pydantic_form import (
    PydanticForm,
    SubModelList,
    _get_literal_values,
    _is_literal,
    _is_list_of_model,
    _unwrap_optional,
)


# ── Helper models for testing ────────────────────────────────────────────


class SubItem(BaseModel):
    title: str = Field(description="Item title")
    done: bool = Field(default=False, description="Completed")


class SampleModel(BaseModel):
    name: str = Field(description="The name")
    bio: str = Field(
        description="Biography text", json_schema_extra={"widget": "textarea"}
    )
    role: Literal["admin", "user", "guest"] = Field(
        default="user", description="User role"
    )
    active: bool = Field(default=True, description="Is active")
    nickname: str | None = Field(default=None, description="Optional nickname")
    items: list[SubItem] = Field(default_factory=list, description="Related items")


class _FormTestApp(App):
    """Minimal app wrapping a PydanticForm for testing."""

    def __init__(self, form: PydanticForm) -> None:
        super().__init__()
        self._form = form

    def compose(self) -> ComposeResult:
        yield self._form


# ── Type-introspection helpers ───────────────────────────────────────────


def test_is_literal_true():
    assert _is_literal(Literal["a", "b"]) is True


def test_is_literal_false():
    assert _is_literal(str) is False


def test_get_literal_values():
    assert _get_literal_values(Literal["x", "y", "z"]) == ("x", "y", "z")


def test_unwrap_optional_plain():
    tp, opt = _unwrap_optional(str)
    assert tp is str
    assert opt is False


def test_unwrap_optional_union():
    tp, opt = _unwrap_optional(str | None)
    assert tp is str
    assert opt is True


def test_is_list_of_model_true():
    ok, cls = _is_list_of_model(list[SubItem])
    assert ok is True
    assert cls is SubItem


def test_is_list_of_model_false():
    ok, cls = _is_list_of_model(list[str])
    assert ok is False
    assert cls is None


# ── PydanticForm rendering ───────────────────────────────────────────────


async def test_form_renders_input_for_str():
    form = PydanticForm(SampleModel, exclude=set())
    app = _FormTestApp(form)
    async with app.run_test(size=(120, 40)) as pilot:
        await pilot.pause()
        widget = app.query_one("#form-name", Input)
        assert widget.placeholder == "The name"


async def test_form_renders_textarea():
    form = PydanticForm(SampleModel)
    app = _FormTestApp(form)
    async with app.run_test(size=(120, 40)) as pilot:
        await pilot.pause()
        assert app.query_one("#form-bio", TextArea)


async def test_form_renders_select_for_literal():
    form = PydanticForm(SampleModel)
    app = _FormTestApp(form)
    async with app.run_test(size=(120, 40)) as pilot:
        await pilot.pause()
        sel = app.query_one("#form-role", Select)
        assert sel.value == "user"


async def test_form_renders_checkbox_for_bool():
    form = PydanticForm(SampleModel)
    app = _FormTestApp(form)
    async with app.run_test(size=(120, 40)) as pilot:
        await pilot.pause()
        chk = app.query_one("#form-active", Checkbox)
        assert chk.value is True


async def test_form_renders_optional_input():
    form = PydanticForm(SampleModel)
    app = _FormTestApp(form)
    async with app.run_test(size=(120, 40)) as pilot:
        await pilot.pause()
        widget = app.query_one("#form-nickname", Input)
        assert widget.value == ""
        assert widget.placeholder == "Optional nickname"


async def test_form_renders_submodel_list():
    form = PydanticForm(SampleModel)
    app = _FormTestApp(form)
    async with app.run_test(size=(120, 40)) as pilot:
        await pilot.pause()
        sub = app.query_one(SubModelList)
        assert sub._field_name == "items"


async def test_form_exclude_fields():
    form = PydanticForm(SampleModel, exclude={"bio", "active", "items"})
    app = _FormTestApp(form)
    async with app.run_test(size=(120, 40)) as pilot:
        await pilot.pause()
        assert app.query_one("#form-name", Input)
        assert app.query_one("#form-role", Select)
        assert len(list(app.query(TextArea))) == 0
        assert len(list(app.query(SubModelList))) == 0


# ── PydanticForm data extraction ─────────────────────────────────────────


async def test_get_form_data_returns_dict():
    form = PydanticForm(SampleModel)
    app = _FormTestApp(form)
    async with app.run_test(size=(120, 40)) as pilot:
        await pilot.pause()
        app.query_one("#form-name", Input).value = "Alice"
        app.query_one("#form-bio", TextArea).load_text("Hello world")
        data = form.get_form_data()
        assert data["name"] == "Alice"
        assert data["bio"] == "Hello world"
        assert data["role"] == "user"
        assert data["active"] is True
        assert data["nickname"] is None
        assert data["items"] == []


async def test_get_form_data_optional_filled():
    form = PydanticForm(SampleModel)
    app = _FormTestApp(form)
    async with app.run_test(size=(120, 40)) as pilot:
        await pilot.pause()
        app.query_one("#form-nickname", Input).value = "Al"
        data = form.get_form_data()
        assert data["nickname"] == "Al"


# ── PydanticForm validation ──────────────────────────────────────────────


async def test_validate_required_empty():
    form = PydanticForm(SampleModel)
    app = _FormTestApp(form)
    async with app.run_test(size=(120, 40)) as pilot:
        await pilot.pause()
        errors = form.validate()
        assert any("Name" in e for e in errors)


async def test_validate_required_filled():
    form = PydanticForm(SampleModel)
    app = _FormTestApp(form)
    async with app.run_test(size=(120, 40)) as pilot:
        await pilot.pause()
        app.query_one("#form-name", Input).value = "Test"
        app.query_one("#form-bio", TextArea).load_text("Some bio")
        errors = form.validate()
        assert len(errors) == 0


# ── PydanticForm with existing instance ──────────────────────────────────


async def test_form_pre_populates_from_instance():
    instance = SampleModel(
        name="Bob",
        bio="Developer",
        role="admin",
        active=False,
        nickname="bobby",
        items=[SubItem(title="task1")],
    )
    form = PydanticForm(SampleModel, instance=instance)
    app = _FormTestApp(form)
    async with app.run_test(size=(120, 40)) as pilot:
        await pilot.pause()
        assert app.query_one("#form-name", Input).value == "Bob"
        assert "Developer" in app.query_one("#form-bio", TextArea).text
        assert app.query_one("#form-role", Select).value == "admin"
        assert app.query_one("#form-active", Checkbox).value is False
        assert app.query_one("#form-nickname", Input).value == "bobby"
        sub = app.query_one(SubModelList)
        assert len(sub.items) == 1
        item = sub.items[0]
        assert isinstance(item, SubItem)
        assert item.title == "task1"


# ── Required field label marker ──────────────────────────────────────────


async def test_required_fields_have_asterisk_label():
    form = PydanticForm(SampleModel)
    app = _FormTestApp(form)
    async with app.run_test(size=(120, 40)) as pilot:
        await pilot.pause()
        from textual.widgets import Label

        label_texts = [str(lbl.render()) for lbl in app.query(Label)]
        # name and bio are required
        assert any("Name *" in t for t in label_texts)
        assert any("Bio *" in t for t in label_texts)
        # role is not required (has default)
        role_labels = [t for t in label_texts if "Role" in t]
        assert all("*" not in t for t in role_labels)
