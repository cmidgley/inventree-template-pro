""" 
    Object inspection w/recursion for the inventree-part-template plugin  

    Copyright (c) 2024 Chris Midgley
    License: MIT (see LICENSE file)
"""

from __future__ import annotations
from abc import ABC, abstractmethod

import decimal
import inspect
import re

from typing import Dict, Any, List
from djmoney.money import Money
from functools import partial
from datetime import date
from django.utils.translation import gettext_lazy as _
from django.db.models.query import QuerySet


class InspectBase(ABC):
    """
    Base class for inspection objects.  Each type of object being inspected (str, class, dict, etc)
    should implement this base class, and also be added to the InspectionmManager to detect and
    create the object.
    """
    def __init__(self, manager: InspectionManager, name: str, obj: Any, depth: int) -> None:
        """
        Initialize a new instance of the InspectBase class.

        Args:
            manager (InspectionManager): The InspectionManager instance.
            name (str): The name of the object being inspected.
            obj (Any): The object being inspected.
            depth (int): The depth of the inspection.

        Returns:
            None
        """
        self.__children: Dict[int, InspectBase] = {}
        self._depth = depth
        self._manager = manager
        self._name = name
        self._obj = obj

    def _add_child(self, name: str, value: Any) -> None:
        """
        Add a child member to this object, for objects that have sub-properties/attributes (using
        recursion).  For example, dict, list and class.

        Args:
            name (str): The name of the child object.
            value (Any): The value of the child object, that will be recursed into.
        """
        if self._manager.track_recursion(value):
            self.__children[id(value)] = InspectDuplicate(self._manager, name, None, self._depth)
        self.__children[id(value)] = self._manager.inspect_factory(name, value, self._depth)

    #
    # Abstract and virtual methods the various implementations may implement to affect the
    # formatting results of the output
    #

    @abstractmethod
    def get_format_value(self) -> str:
        """
        Gets the value of the item, for items that have values and not children items.  For example,
        a string or an int has a value, whereas a class or a dict has children.  This should contain
        the concrete value of the item without children/recursion.  If the item has no value, it should 
        return the empty string ("").  This is an abstract method that must be implemented by all subclasses.

        Returns:
            str | None: The value of the object, or empty if no value.
        """

    def get_format_prefix(self) -> str:
        """
        Gets the prefix to be displayed before the children of the object.  Default is empty string.
        Virtual method that may be overridden by subclasses.

        Returns:
            str: The prefix to be displayed.
        """
        return ""

    def get_format_postfix(self) -> str:
        """
        Gets the postfix to be displayed after the children of the object.  Default is empty string.
        Virtual method that may be overridden by subclasses.

        Returns:
            str: The postfix to be displayed.
        """
        return ""

    def get_total_children(self) -> int | None:
        """
        Gets the total number of children of the object, which may be larger than the actual
        children due to the InspectionManager.max_items limiting total items.  Default is None,
        which implies no children.  Virtual method that may be overridden by subclasses.

        
        Returns:
            int | None: The total number of children.
        """
        return None

    def get_children(self) -> List[InspectBase]:
        """
        Returns a list of children of the current object, which may be empty.  Default is empty list.
        Virtual method that may be overridden by subclasses.

        Returns:
            List[InspectBase]: A list of `InspectBase` objects representing the children.
        """
        return list(self.__children.values())

    def get_format_title(self) -> str:
        """
        Returns the title of the object, defaulting to the it's name. Virtual method that may be 
        overridden by subclasses.

        Returns:
            The format title as a string.
        """
        return self._name

    def get_format_type(self) -> str:
        """
        Returns the type of the object, defaulting to the inspected type of the object.
        Virtual method that may be overridden by subclasses.

        Returns:
            str: The format type of the object.
        """
        return type(self._obj).__name__

    def get_format_id(self) -> int:
        """
        Returns the unique identifier of the object.  If overridden, make sure that
        get_format_link_to is overridden with a matching value.  Default is the
        native Python id of the object.

        Returns:
            int: The unique identifier of the object.
        """
        return id(self._obj)

    def get_format_link_to(self) -> int | None:
        """
        If the object is a duplicate, this will return the ID of the original object.  This is
        to allow the formatter to provide links between the instances.  Default is None, which
        implies no link.  If overridden, make sure that get_format_id is overridden with a
        matching value.

        Returns:
            int | None: The format link to for the object, or None if it doesn't exist.
        """
        return None

class InspectSimpleType(InspectBase):
    """
    Represents a simple type inspection object, such as str, int, special types like Money or
    Decimal, and the None type.
    """
    def __init__(self, manager: InspectionManager, name: str, obj: Any, depth: int) -> None:
        """
        Initialize a new instance of the InspectSimpleType class.

        Args:
            manager (InspectionManager): The InspectionManager instance.
            name (str): The name of the node.
            obj (Any): The object to inspect.
            depth (int): The depth of the node in the inspection tree.
        """
        super().__init__(manager, name, obj, depth)
        self._value = str(obj)

    def get_format_value(self) -> str:
        """
        Provides the formatted value of the attribute.

        If the value is a string, it is returned within double quotes.
        Otherwise, the value is converted to a string and returned.

        Returns:
            str: The formatted value of the attribute.
        """
        if isinstance(self._value, str):
            return f'"{self._value}"'
        return str(self._value)

class InspectMethod(InspectBase):
    """
    Represents a inspection object for method calls, which includes tracking
    all parameters that are provided to the method.
    """
    def __init__(self, manager: InspectionManager, name: str, obj: Any, depth: int) -> None:
        """
        Initialize a new instance of the InspectMethod class.

        Args:
            manager (InspectionManager): The InspectionManager instance.
            name (str): The name of the object being inspected.
            obj (Any): The object being inspected.
            depth (int): The depth of the inspection.
        """
        super().__init__(manager, name, obj, depth)

        sig = inspect.signature(obj)
        self._parameters = [name for name, param in sig.parameters.items()]

    def get_format_value(self) -> str:
        """
        Returns the method parameters as a comma-deliminated string.  For example, "(one_parameter, two_parameter)".

        Returns:
            str: The list of parameters for the method.
        """
        return f'({", ".join(self._parameters)})'


class InspectPartial(InspectBase):
    """
    Represents a inspection object for partial method calls, which includes tracking
    all parameters that are provided to the method, including the name of the parent
    method and the arguments that are being provided by the partial.
    """
    def __init__(self, manager: InspectionManager, name: str, obj: Any, depth: int) -> None:
        """
        Initialize a new instance of the InspectPartial class.

        Args:
            manager (InspectionManager): The InspectionManager instance.
            name (str): The name of the object being inspected.
            obj (Any): The object being inspected.
            depth (int): The depth of the inspection.
        """
        super().__init__(manager, name, obj, depth)

        sig = inspect.signature(obj.func)
        bound_args = obj.args
        bound_kwargs = obj.keywords
        self._parameters:List[Dict[str, Any]] = []

        self._parent_name = obj.func.__name__
        for i, param in enumerate(sig.parameters.values()):
            if i < len(bound_args):
                self._parameters.append({ 'name': param.name, 'value': bound_args[i] })
            elif param.name in bound_kwargs:
                self._parameters.append({ 'name': param.name, 'value': bound_kwargs[param.name] })
            else:
                self._parameters.append({ 'name': param.name, 'value': None })

    def get_format_value(self) -> str:
        """
        Returns the value for a partial, which will be a formatted string similar to:

        calling parent_name(param1=3, param2="example", native_param) 

        Values with "<name>=<value>" are defined by the partial and simple names are native to the parent.

        Returns:
            str: The parent method name and partial/parent parameters
        """
        return _("calling {parent_name}({parameters})").format(
            parent_name=self._parent_name,
            parameters=', '.join(",".join([f"{name}={value}" if value is not None else name
                for name, value in self._parameters]))
        )

class InspectDuplicate(InspectBase):
    """
    Represents a special inspection object that references another object by ID, used when
    recursion has been detected to avoid digging too deep into the heirarchy.
    """

    def get_format_link_to(self) -> int | None:
        return id(self._obj)

    def get_format_value(self) -> str:
        """
        Returns a simple string indicating the value is not being included because it was previously
        output during recursive inspection.

        Returns:
            str: The format value of the inspected object.
        """
        return _("(previously output)")

class InspectDict(InspectBase):
    """
    Represents a inspection object for dictionaries, which will recurse into all members of
    the dictionary (limited by the max_items setting in the InspectionManager).
    """
    def __init__(self, manager: InspectionManager, name: str, obj: Any, depth: int) -> None:
        """
        Initialize a new instance of the InspectDict class.

        Args:
            manager (InspectionManager): The InspectionManager instance.
            name (str): The name of the node.
            obj (Any): The object associated with the node.
            depth (int): The depth of the node in the inspection tree.
        """
        super().__init__(manager, name, obj, depth)

        for key, value in obj.items():
            if depth > 0:
                self._add_child(key, value)
            if len(self.__children) >= manager.get_max_items():
                break
        self._total_items = len(obj)

    def get_format_prefix(self) -> str:
        """
        Dictionary children are encapsulated in "{ ... }", so this returns "{".

        Returns:
            str: The format prefix.
        """
        return "{"

    def get_format_postfix(self) -> str:
        """
        Dictionary children are encapsulated in "{ ... }", so this returns "}".

        Returns:
            str: The format postfix.
        """
        return "}"

    def get_total_children(self) -> int:
        """
        Returns the total number of children for the current object, which may be larger than
        the total number children (due to max_items)

        Returns:
            int: The total number of children.
        """
        return self._total_items

    def get_format_value(self) -> str:
        """
        Since this object has children, it does not have a value to display.

        Returns:
            str: "" as this object does not have a value.
        """
        return ""

class InspectList(InspectBase):
    """
    Represents a inspection object for Lists, which will recurse into all members of
    the list (limited by the max_items setting in the InspectionManager).
    """
    def __init__(self, manager: InspectionManager, name: str, obj: Any, depth: int) -> None:
        """
        Initialize an instance of the InspectionNode class.

        Args:
            manager (InspectionManager): The InspectionManager instance.
            name (str): The name of the node.
            obj (Any): The object to be inspected.
            depth (int): The depth of the inspection.
        """
        super().__init__(manager, name, obj, depth)

        for index, item in enumerate(obj):
            if depth > 0:
                self._add_child(str(index), item)
            if index >= manager.get_max_items():
                break
        self._total_items = len(obj)

    def get_format_prefix(self) -> str:
        """
        Returns the prefix for the list, which is "[".

        Returns:
            str: The format prefix.
        """
        return "["

    def get_format_postfix(self) -> str:
        """
        Returns the postfix for the list, which is "]".

        Returns:

        """
        return "]"

    def get_total_children(self) -> int:
        """
        Returns the total number of children for the current object, which may be larger than
        the total number children (due to max_items)

        Returns:
            int: The total number of children.
        """
        return self._total_items

    def get_format_value(self) -> str:
        """
        Since this object has children, it does not have a value to display.

        Returns:
            str: "", as this object does not have a value.
        """
        return ""

class InspectQuerySet(InspectBase):
    """
    Represents a inspection object for a QuerySet, which will execute the query set to
    get the resulting values and recurse into them.  Will limit the number of items
    recursed to the max_items setting in the InspectionManager.
    """
    def __init__(self, manager: InspectionManager, name: str, obj: Any, depth: int) -> None:
        """
        Initializes the InspectQuerySet object.
        
        Args:
            manager (InspectionManager): The inspection manager.
            name (str): The name of the object.
            obj (Any): The object to inspect.
            depth (int): The current depth of the inspection.
        """
        super().__init__(manager, name, obj, depth)

        self._total_items = obj.count()
        # if we have any items, and we are to recurse into them...
        if self._total_items > 0 and depth > 0:
            # fetch the first items
            tree_items = obj.all()[manager.get_max_items()]

            for index, tree_item in enumerate(tree_items):
                self._add_child(str(index), tree_item)

    def get_format_prefix(self) -> str:
        """
        Returns the prefix for the QuerySet, which is "[".

        Returns:
            str: The format prefix.
        """
        return "["

    def get_format_postfix(self) -> str:
        """
        Returns the postfix for the QuerySet, which is "]".

        Returns:
            str: The format postfix.
        """
        return "]"

    def get_total_children(self) -> int:
        """
        Returns the total number of children for the current object, which may be larger than
        the total number children (due to max_items)

        Returns:
            int: The total number of children.
        """
        return self._total_items

    def get_format_value(self) -> str:
        """
        Since this object has children, it does not have a value to display.

        Returns:
            str: "", as this object does not have a value.
        """
        return ""

class InspectClass(InspectBase):
    """
    Represents a inspection object for instantiated class objects, which includes tracking
    all parameters that are provided to the method.  Does not limit the number
    of items recursed, but does eliminate private, protected, 'type' and 'do_not_call_in_templates'
    attributes.
    """
    def __init__(self, manager: InspectionManager, name: str, obj: Any, depth: int) -> None:
        """
        Initializes the InspectClass object.

        Args:
            manager (InspectionManager): The inspection manager.
            name (str): The name of the object.
            obj (Any): The object to inspect.
            depth (int): The current depth of the inspection.
        """
        super().__init__(manager, name, obj, depth)

        for attr_name in dir(obj):
            # if name indicates privte/protected, skip it
            if attr_name.startswith('_'):
                continue

            # get the attr's value
            attr_value: Any | None = getattr(obj, attr_name, None)

            # skip all builtins and class definitions ('type')
            if inspect.isbuiltin(attr_value) or isinstance(attr_value, type):
                continue

            # some objects have "do_not_call_in_templates", so let's remove them since this
            # is only for template display
            if getattr(attr_value, 'do_not_call_in_templates', False):
                continue

            # this is a member we want to process
            if depth > 0:
                self._add_child(attr_name, attr_value)

    def get_format_prefix(self) -> str:
        """
        Returns the prefix for the class, which is "{".

        Returns:
            str: The format prefix.
        """
        return "{"

    def get_format_postfix(self) -> str:
        """
        Returns the postfix for the class, which is "}".

        Returns:
            str: The format postfix.
        """
        return "}"

    def get_total_children(self) -> int:
        """
        Returns the total number of children for the current object, which may be larger than
        the total number children (due to max_items)

        Returns:
            int: The total number of children.
        """
        return len(self.__children)

    def get_format_value(self) -> str:
        """
        Since this object has children, it does not have a value to display.

        Returns:
            str: "", as this object does not have a value.
        """
        return ""

class InspectionManager:
    """
    The InspectionManager class is used to inspect objects and their properties, recursing into the
    objects to find properties and values according to the type of the objects, limited by depth of
    recursion and maximum items to include in a list/dict/etc.
    """
    def __init__(self, name: str, obj: Any, max_depth: int = 2, max_items: int = 5) -> None:
        """
        Initializes the InspectionManager object.

        Args:
            name (str): The name of the object.
            obj (Any): The object to be inspected.
            max_depth (int, optional): The maximum depth of recursive inspection. Defaults to 2.
            max_items (int, optional): The maximum number of items to be displayed. Defaults to 5.
        """
        self._obj = obj
        self._processed: Dict[int, bool] = {}
        self._max_items = max_items

        self._base = self.inspect_factory(name, obj, max_depth)

    # some types are not appropriate for recursive formatting.  They can be added to the blacklist here
    # which will simply get their str(obj) value
    BLACKLISTED_TYPES = (
        decimal.Decimal,
        Money,
        complex,
        re.Pattern,
        re.Match,
        date
    )

    def inspect_factory(self, name: str, obj: Any, depth: int) -> InspectBase:
        """
        Factory method to create the appropriate InspectBase subclass based on the object type.

        Args:
            name (str): The name of the object.
            obj (Any): The object to be inspected.
            depth (int): The current depth of recursive inspection.

        Returns:
            InspectBase: An instance of the appropriate InspectBase subclass.
        """
        if depth <= 0:
            raise ValueError(_("Internal error in InspectManager: Depth exceeded"))

        if isinstance(obj, (str, int, float, bool, self.BLACKLISTED_TYPES)) or obj is None:
            return InspectSimpleType(self, name, obj, depth - 1)
        if inspect.ismethod(obj):
            return InspectMethod(self, name, obj, depth - 1)
        if isinstance(obj, partial):
            return InspectPartial(self, name, obj, depth - 1)
        if isinstance(obj, dict):
            return InspectDict(self, name, obj, depth - 1)
        if isinstance(obj, list):
            return InspectList(self, name, obj, depth - 1)
        if isinstance(obj, QuerySet):
            return InspectQuerySet(self, name, obj, depth - 1)
        return InspectClass(self, name, obj, depth - 1)

    def track_recursion(self, obj: Any) -> bool:
        """
        Check if an object has been processed and add it to the processed dictionary if not.

        Args:
            obj (Any): The object to check.

        Returns:
            bool: True if the object was not processed before, False if it was already processed.
        """
        obj_id = id(obj)

        if obj_id in self._processed:
            return False
        self._processed[obj_id] = True
        return True

    def get_max_items(self) -> int:
        """
        Returns the maximum number of items to be displayed.

        Returns:
            int: The maximum number of items.
        """
        return self._max_items

    def format(self) -> str:
        """
        Formats the inspection result as a string.

        Returns:
            str: The formatted inspection result.
        """
        return self._format(self._base)

    def _format(self, inspection: InspectBase) -> str:
        """
        Recursively formats the inspection result.

        Args:
            inspect (InspectBase): The inspection object to format.

        Returns:
            str: The formatted inspection result.
        """
        children = [self._format(child) for child in inspection.get_children()]
        children_str = "\n".join(children)
        value = inspection.get_format_value() if inspection.get_format_link_to() is None else f"<a href='#{inspection.get_format_link_to()}'>{inspection.get_format_value()}</a>"

        return _("""<div class="inspect-node" id="{id}">
            <div class="inspect-title">{title}</div>
            <div class="inspect-type">({type})</div>
            <div class="inspect-value">{value}</div>
            <div class="inspect-prefix">{prefix}</div>
            <div class="inspect-children">{children}</div>
            <div class="inspect-postfix">{postfix}</div>
            </div>""").format(
                id=inspection.get_format_id(),
                title=inspection.get_format_title(),
                type=inspection.get_format_type(),
                prefix=inspection.get_format_prefix(),
                value=value,
                postfix=inspection.get_format_postfix(),
                children=children_str
            )
    