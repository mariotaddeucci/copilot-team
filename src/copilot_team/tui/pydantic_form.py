"""Auto-generate TUI forms from Pydantic models.

Inspects model field metadata (name, type, description, required) to produce
Textual widgets:
  - ``Literal`` annotations → ``Select``
  - ``bool`` → ``Checkbox``
  - ``list[BaseModel]`` → ``SubModelList`` (table with add / remove)
  - ``str`` with ``json_schema_extra={"widget": "textarea"}`` → ``TextArea``
  - everything else → ``Input``

Required fields are labelled with ``*`` and field descriptions are used as
``Input`` placeholders.
"""

from __future__ import annotations

import types
from typing import Any, Literal, Union, get_args, get_origin

from pydantic import BaseModel
from pydantic.fields import FieldInfo
from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import Button, Checkbox, Input, Label, Select, Static, TextArea


# ---------------------------------------------------------------------------
# Type-introspection helpers
# ---------------------------------------------------------------------------


def _is_literal(annotation: Any) -> bool:
    """Return ``True`` when *annotation* is a ``Literal[...]`` type."""
    return get_origin(annotation) is Literal


def _get_literal_values(annotation: Any) -> tuple[Any, ...]:
    """Extract the allowed values from a ``Literal`` annotation."""
    return get_args(annotation)


def _unwrap_optional(annotation: Any) -> tuple[Any, bool]:
    """Unwrap ``X | None`` to ``(X, True)``; non-optional gives ``(X, False)``."""
    origin = get_origin(annotation)
    if origin is types.UnionType or origin is Union:
        args = get_args(annotation)
        non_none = [a for a in args if a is not type(None)]
        if type(None) in args and len(non_none) == 1:
            return non_none[0], True
    return annotation, False


def _is_list_of_model(annotation: Any) -> tuple[bool, type[BaseModel] | None]:
    """Return ``(True, SubModelClass)`` when annotation is ``list[SubModel]``."""
    origin = get_origin(annotation)
    if origin is list:
        args = get_args(annotation)
        if args and isinstance(args[0], type) and issubclass(args[0], BaseModel):
            return True, args[0]
    return False, None


def _widget_hint(field_info: FieldInfo) -> str | None:
    """Read an optional ``widget`` hint stored in ``json_schema_extra``."""
    extra = field_info.json_schema_extra
    if isinstance(extra, dict):
        return extra.get("widget")
    return None


# ---------------------------------------------------------------------------
# SubModelList – editable table for ``list[BaseModel]`` fields
# ---------------------------------------------------------------------------


class SubModelList(Vertical):
    """Manages a list of Pydantic sub-model instances as a mini-table.

    Each existing item is rendered as a row whose last column contains a
    *remove* button.  A bottom bar allows adding new items.
    """

    DEFAULT_CSS = """
    SubModelList { height: auto; }
    """

    def __init__(
        self,
        field_name: str,
        submodel_class: type[BaseModel],
        items: list[BaseModel] | None = None,
    ) -> None:
        super().__init__()
        self._field_name = field_name
        self._submodel_class = submodel_class
        self._items: list[BaseModel] = list(items) if items else []

    @property
    def items(self) -> list[BaseModel]:
        return self._items

    # -- compose / render ---------------------------------------------------

    def compose(self) -> ComposeResult:
        yield Vertical(id=f"submodel-{self._field_name}-items")
        with Horizontal(classes="submodel-add-bar"):
            for name, field_info in self._submodel_class.model_fields.items():
                if not field_info.is_required():
                    continue
                placeholder = field_info.description or name
                yield Input(
                    placeholder=placeholder,
                    id=f"submodel-{self._field_name}-new-{name}",
                )
            yield Button(
                "+ Add",
                id=f"submodel-{self._field_name}-btn-add",
                variant="success",
            )

    def on_mount(self) -> None:
        self._render_items()

    def _render_items(self) -> None:
        container = self.query_one(f"#submodel-{self._field_name}-items", Vertical)
        container.remove_children()
        for idx, item in enumerate(self._items):
            row = Horizontal(classes="submodel-row")
            container.mount(row)
            for fname, finfo in self._submodel_class.model_fields.items():
                value = getattr(item, fname)
                unwrapped, _ = _unwrap_optional(finfo.annotation)
                if unwrapped is bool:
                    row.mount(
                        Checkbox(
                            fname,
                            value=bool(value),
                            id=f"submodel-{self._field_name}-{idx}-{fname}",
                        )
                    )
                else:
                    row.mount(Static(str(value), classes="submodel-cell"))
            row.mount(
                Button(
                    "✕",
                    id=f"submodel-{self._field_name}-del-{idx}",
                    classes="submodel-delete",
                )
            )

    # -- event handlers -----------------------------------------------------

    def on_button_pressed(self, event: Button.Pressed) -> None:
        btn_id = event.button.id or ""
        prefix = f"submodel-{self._field_name}-"

        if btn_id == f"{prefix}btn-add":
            self._add_item()
            event.stop()
        elif btn_id.startswith(f"{prefix}del-"):
            idx = int(btn_id.replace(f"{prefix}del-", ""))
            if 0 <= idx < len(self._items):
                self._items.pop(idx)
                self._render_items()
            event.stop()

    def on_checkbox_changed(self, event: Checkbox.Changed) -> None:
        chk_id = event.checkbox.id or ""
        prefix = f"submodel-{self._field_name}-"
        if chk_id.startswith(prefix) and "-new-" not in chk_id:
            parts = chk_id.replace(prefix, "").split("-", 1)
            if len(parts) == 2:
                try:
                    idx, fname = int(parts[0]), parts[1]
                    if 0 <= idx < len(self._items):
                        # Use model_copy to respect immutability
                        self._items[idx] = self._items[idx].model_copy(
                            update={fname: event.value}
                        )
                except (ValueError, KeyError):
                    pass

    def on_input_submitted(self, event: Input.Submitted) -> None:
        if event.input.id and event.input.id.startswith(
            f"submodel-{self._field_name}-new-"
        ):
            self._add_item()

    def _add_item(self) -> None:
        values: dict[str, Any] = {}
        for fname, finfo in self._submodel_class.model_fields.items():
            if not finfo.is_required():
                continue
            input_id = f"submodel-{self._field_name}-new-{fname}"
            try:
                inp = self.query_one(f"#{input_id}", Input)
            except Exception:
                return
            text = inp.value.strip()
            if not text:
                return
            values[fname] = text

        try:
            item = self._submodel_class(**values)
        except Exception:
            return

        self._items.append(item)

        # Clear inputs
        for fname, finfo in self._submodel_class.model_fields.items():
            if not finfo.is_required():
                continue
            input_id = f"submodel-{self._field_name}-new-{fname}"
            try:
                self.query_one(f"#{input_id}", Input).value = ""
            except Exception:
                pass

        self._render_items()


# ---------------------------------------------------------------------------
# PydanticForm – the main form widget
# ---------------------------------------------------------------------------


class PydanticForm(Vertical):
    """Renders editable form fields for a Pydantic model.

    Parameters
    ----------
    model_class:
        The Pydantic ``BaseModel`` subclass to render.
    instance:
        An optional existing model instance whose values pre-populate the
        form (edit mode).
    exclude:
        Field names to skip when generating widgets.
    """

    DEFAULT_CSS = """
    PydanticForm {
        height: auto;
        width: 1fr;
    }
    """

    def __init__(
        self,
        model_class: type[BaseModel],
        instance: BaseModel | None = None,
        exclude: set[str] | None = None,
    ) -> None:
        super().__init__()
        self._model_class = model_class
        self._instance = instance
        self._exclude = exclude or set()

    # -- compose ------------------------------------------------------------

    def compose(self) -> ComposeResult:
        for field_name, field_info in self._model_class.model_fields.items():
            if field_name in self._exclude:
                continue
            yield from self._build_field(field_name, field_info)

    def _build_field(self, name: str, field_info: FieldInfo) -> ComposeResult:
        annotation = field_info.annotation
        description = field_info.description or ""
        required = field_info.is_required()
        label_text = name.replace("_", " ").title()
        if required:
            label_text += " *"

        # Use instance value when editing, otherwise fall back to field default
        from pydantic_core import PydanticUndefined

        if self._instance is not None:
            current_value = getattr(self._instance, name, None)
        elif field_info.default is not PydanticUndefined:
            current_value = field_info.default
        elif field_info.default_factory is not None:
            current_value = field_info.default_factory()
        else:
            current_value = None

        hint = _widget_hint(field_info)
        unwrapped, is_optional = _unwrap_optional(annotation)

        # Literal → Select
        if _is_literal(unwrapped):
            values = _get_literal_values(unwrapped)
            yield Label(f"{label_text}:")
            yield Select(
                [(str(v), v) for v in values],
                value=current_value
                if current_value is not None
                else (values[0] if values else Select.BLANK),
                allow_blank=is_optional,
                id=f"form-{name}",
            )
            return

        # list[BaseModel] → SubModelList
        is_model_list, submodel_cls = _is_list_of_model(unwrapped)
        if is_model_list and submodel_cls is not None:
            items = (
                [item.model_copy() for item in current_value] if current_value else []
            )
            yield Label(f"{label_text}:")
            yield SubModelList(
                field_name=name,
                submodel_class=submodel_cls,
                items=items,
            )
            return

        # bool → Checkbox
        if unwrapped is bool:
            yield Checkbox(
                label_text,
                value=bool(current_value) if current_value is not None else False,
                id=f"form-{name}",
            )
            return

        # textarea hint → TextArea
        if hint == "textarea":
            yield Label(f"{label_text}:")
            yield TextArea(
                str(current_value) if current_value else "",
                id=f"form-{name}",
            )
            return

        # Default → Input
        yield Label(f"{label_text}:")
        yield Input(
            value=str(current_value) if current_value is not None else "",
            placeholder=description,
            id=f"form-{name}",
        )

    # -- data extraction ----------------------------------------------------

    def get_form_data(self) -> dict[str, Any]:
        """Read current widget values and return them as a plain ``dict``."""
        data: dict[str, Any] = {}
        for field_name, field_info in self._model_class.model_fields.items():
            if field_name in self._exclude:
                continue

            annotation = field_info.annotation
            unwrapped, is_optional = _unwrap_optional(annotation)
            hint = _widget_hint(field_info)
            widget_id = f"form-{field_name}"

            # Literal → Select
            if _is_literal(unwrapped):
                widget = self.query_one(f"#{widget_id}", Select)
                value = widget.value
                data[field_name] = None if value == Select.BLANK else value
                continue

            # list[BaseModel] → SubModelList
            is_model_list, _ = _is_list_of_model(unwrapped)
            if is_model_list:
                for sub_list in self.query(SubModelList):
                    if sub_list._field_name == field_name:
                        data[field_name] = sub_list.items
                        break
                continue

            # bool → Checkbox
            if unwrapped is bool:
                widget = self.query_one(f"#{widget_id}", Checkbox)
                data[field_name] = widget.value
                continue

            # textarea → TextArea
            if hint == "textarea":
                widget = self.query_one(f"#{widget_id}", TextArea)
                data[field_name] = widget.text.strip()
                continue

            # Default → Input
            widget = self.query_one(f"#{widget_id}", Input)
            value = widget.value.strip()
            data[field_name] = None if (is_optional and not value) else value

        return data

    def validate(self) -> list[str]:
        """Check required fields and return a list of error messages."""
        errors: list[str] = []
        data = self.get_form_data()
        for field_name, field_info in self._model_class.model_fields.items():
            if field_name in self._exclude:
                continue
            if not field_info.is_required():
                continue
            value = data.get(field_name)
            if value is None or (isinstance(value, str) and not value.strip()):
                label = field_name.replace("_", " ").title()
                errors.append(f"{label} is required")
        return errors
