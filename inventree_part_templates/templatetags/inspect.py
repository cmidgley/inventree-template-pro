""" 
    Object inspection w/recursion for the inventree-part-template plugin  

    Copyright (c) 2024 Chris Midgley
    License: MIT (see LICENSE file)
"""
from __future__ import annotations
from abc import ABC, abstractmethod
import os
import decimal
import inspect
import re
from typing import Dict, Any, List
from datetime import date
from functools import partial
from django.template import loader, Context
from djmoney.money import Money
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
        self._children: List[InspectBase] = []
        self._depth = depth
        self._manager = manager
        self._name = name
        self._obj = obj

    def _add_child(self, name: str, value: Any, create_child = True) -> bool:
        """
        Add a child member to this object, for objects that have sub-properties/attributes (using
        recursion).  For example, dict, list and class.  Also skips methods/partials if they have
        been disabled in the options.

        Args:
            name (str): The name of the child object.
            value (Any): The value of the child object, that will be recursed into.

        Returns:
            bool: True if the child was (or would be if create_child is False) added, False if it was skipped.
        """
        # if we are not showing methods, skip them
        if not self._manager.options['methods'] and (inspect.ismethod(value) or
                                                     inspect.isfunction(value) or
                                                     isinstance(value, partial)):
            return False

        # if we are not showing None values, skip them
        if not self._manager.options['none'] and value is None:
            return False
        
        # if we are just counting and not adding, return success
        if not create_child:
            return True

        # if duplicate (already generated), add a InspectDuplicate instead, which allows us to link
        # back to the already rendered instance
        if self._manager.been_seen_before(value):
            self._children.append(InspectDuplicate(self._manager, name, value, self._depth))
        else:
            self._children.append(self._manager.inspect_factory(name, value, self._depth))
        
        return True

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
        Gets the prefix to be displayed before the children or a value of the object.  Default is empty string.
        Virtual method that may be overridden by subclasses.  For example, a dict (children-based) would return "{"
        whereas a method (value-based) would return "(".

        Returns:
            str: The prefix to be displayed.
        """
        return ""

    def get_format_postfix(self) -> str:
        """
        Gets the postfix to be displayed after the children of the object.  Default is empty string.
        Virtual method that may be overridden by subclasses.  For example, a dict (children-based)
        would return "}" whereas a method (value-based) would return ")".

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

    def get_children(self) -> List[InspectBase] | None:
        """
        Returns a list of children of the current object, which may be empty.  Default is empty list.
        Virtual method that may be overridden by subclasses.

        Returns:
            List[InspectBase]: A list of `InspectBase` objects representing the children.
        """
        return self._children if self.get_total_children() is not None else None

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

    def build_unique_id(self, obj_id: int) -> str:
        """
        Builds a unique identifier for the object based on the object's ID and the current
        inspection prefix index.

        Args:
            id (int): The ID of the object.

        Returns:
            str: The unique identifier for the object.
        """
        return f"Item-{InspectionManager.id_prefix_index}-{obj_id}"

    def get_format_id(self) -> str:
        """
        Returns the unique identifier of the object.  If overridden, make sure that
        get_format_link_to is overridden with a matching value.  Default is the
        native Python id of the object combined with a unique number per each use
        of inspection.

        Returns:
            int: The unique identifier of the object.
        """
        return self.build_unique_id(id(self._obj))


    def get_format_link_to(self) -> str | None:
        """
        If the object is a duplicate, this will return the ID of the original object.  This is
        to allow the formatter to provide links between the instances.  Default is None, which
        implies no link.  If overridden, make sure that get_format_id is overridden with a
        matching value.

        Returns:
            str | None: The format link to for the object, or None if it doesn't exist.
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
            if "password" in self._name.lower():
                return f'"{"*" * len(self._value)}"'
            return f'"{self._value}"'
        return str(self._value)

    def get_format_prefix(self) -> str:
        """
        For value types, the prefix is '=' such as 'name = value'.

        Returns:
            str: The format prefix of '='
        """
        return '='

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
        return f'{", ".join(self._parameters)}'

    def get_format_prefix(self) -> str:
        """
        For methods, the prefix is '(' such as 'method_name(param1, param2)'.

        Returns:
            str: The format prefix of '('
        """
        return '('

    def get_format_postfix(self) -> str:
        """
        For methods, the postfix is ')' such as 'method_name(param1, param2)'.

        Returns:
            str: The format postfix of ')'
        """
        return ')'


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
            value: Any = None
            if i < len(bound_args):
                value = bound_args[i]
            elif param.name in bound_kwargs:
                value = bound_kwargs[param.name]

            if isinstance(value, InspectionManager.WHITELIST_USE_SIMPLE_TYPE):
                value = str(value)
            else:
                value = _('({type})').format(type=type(value).__name__)
            self._parameters.append({ 'name': param.name, 'value': value })

    def get_format_title(self) -> str:
        """
        Returns the title of the object, which is the partial name with the parent method name.

        Returns:
            str: The title of the object, as name(...) -> parent
        """
        return f"{self._name}(...) -> {self._parent_name}"

    def get_format_value(self) -> str:
        """
        Returns the value for a partial, which will be a formatted string similar to:

        calling parent_name(param1=3, param2="example", native_param) 

        Values with "<name>=<value>" are defined by the partial and simple names are native to the parent.

        Returns:
            str: The parent method name and partial/parent parameters
        """
        formatted_parameters: List[str] = []
        for param in self._parameters:
            if param['value'] is None:
                formatted_parameters.append(param['name'])
            else:
                formatted_parameters.append(f"{param['name']}={str(param['value'])}")

        return ', '.join(formatted_parameters)

    def get_format_prefix(self) -> str:
        """
        For partials, the prefix is '(' such as 'method_name(param1, param2)'.

        Returns:
            str: The format prefix of '('
        """
        return '('

    def get_format_postfix(self) -> str:
        """
        For partials, the postfix is ')' such as 'method_name(param1, param2)'.

        Returns:
            str: The format postfix of ')'
        """
        return ')'

class InspectDuplicate(InspectBase):
    """
    Represents a special inspection object that references another object by ID, used when
    recursion has been detected to avoid digging too deep into the heirarchy.
    """

    def get_format_link_to(self) -> str | None:
        return self.build_unique_id(id(self._obj))

    def get_format_value(self) -> str:
        """
        Returns a simple string indicating the value is not being included because it was previously
        output during recursive inspection.

        Returns:
            str: The format value of the inspected object.
        """
        return _("(duplicated)")

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

        self._total_items = 0
        for key, value in obj.items():
            if self._add_child(key, value, depth > 0 and len(self._children) < manager.get_max_items()):
                self._total_items += 1

    def get_format_prefix(self) -> str:
        """
        Dictionary children are encapsulated in "{ ... }", so this returns "{".

        Returns:
            str: The format prefix.
        """
        return "Dict {"

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

        self._total_items = 0
        for index, item in enumerate(obj):
            if self._add_child(str(index), item, depth > 0 and index < manager.get_max_items()):
                self._total_items = self._total_items + 1

    def get_format_prefix(self) -> str:
        """
        Returns the prefix for the list, which is "[".

        Returns:
            str: The format prefix.
        """
        return "List ["

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

class InspectSet(InspectList):
    """
    Represents a inspection object for Sets, which will recurse into all members of
    the set (limited by the max_items setting in the InspectionManager).  Inherits from
    InspectList as it is the same logic, except for different prefix/postfix.
    """

    def get_format_prefix(self) -> str:
        """
        Returns the prefix for the set, which is "{".

        Returns:
            str: The format prefix.
        """
        return "Set {"

    def get_format_postfix(self) -> str:
        """
        Returns the postfix for the set, which is "}".

        Returns:

        """
        return "}"

    

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
            query_items = obj.all()[:manager.get_max_items()]

            for index, tree_item in enumerate(query_items):
                self._add_child(str(index), tree_item)

    def get_format_prefix(self) -> str:
        """
        Returns the prefix for the QuerySet, which is "[".

        Returns:
            str: The format prefix.
        """
        return "QuerySet ["

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

        self._total_items = 0

        for attr_name in dir(obj):
            # if name indicates privte/protected, skip it
            if attr_name.startswith('_') and manager.options['privates'] is False:
                continue

            # get the attr's value
            attr_value: Any | None
            try:
                attr_value = getattr(obj, attr_name, None)
            except Exception as e:   # pylint: disable=broad-except
                attr_value = _("Error: {err}").format(err=str(e))

            # skip all builtins and class definitions ('type')
            if inspect.isbuiltin(attr_value) or isinstance(attr_value, type):
                continue

            # some objects have "do_not_call_in_templates", so let's remove them since this
            # is only for template display
            if getattr(attr_value, 'do_not_call_in_templates', False):
                continue

            # this is a member we want to process
            if depth > 0:
                if self._add_child(attr_name, attr_value):
                    self._total_items += 1

    def get_format_prefix(self) -> str:
        """
        Returns the prefix for the class, which is "{".

        Returns:
            str: The format prefix.
        """
        return "Object {"

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
        return self._total_items

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

    # define a static member to track multiple uses of inspection on the same page
    id_prefix_index = 0

    def __init__(self, name: str, obj: Any, options: Dict[str, str|int|bool], context: Context) -> None:
        """
        Initializes the InspectionManager object.

        Args:
            name (str): The name of the object.
            obj (Any): The object to be inspected.
            options (Dict[str, str|int|bool]): The options to control the inspection process.
            context (Context): The Django template context to use for rendering the template (optional)
        """
        self._obj = obj
        self._processed: Dict[int, bool] = {}
        self.options = options
        self._django_context = context

        # increment our static id prefix
        InspectionManager.id_prefix_index += 1

        # build our base object, which will recurse into the children
        self._base = self.inspect_factory(name, obj, int(options['depth']) + 1)

    # some types are not appropriate for recursive formatting.  They can be added to the list here
    # which will simply get their str(obj) value.  Most can use isinstance, but some need a specific
    # name check (like __proxy__), so a second WHITELIST_USE_SIMPLE_TYPE_BY_NAME list of strings is
    # used to check for those.
    WHITELIST_USE_SIMPLE_TYPE = (
        str,
        int,
        float,
        bool,
        decimal.Decimal,
        Money,
        complex,
        re.Pattern,
        re.Match,
        date
    )
    WHITELIST_USE_SIMPLE_TYPE_BY_NAME = (
        "__proxy__"
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

        if type(obj).__name__ in self.WHITELIST_USE_SIMPLE_TYPE_BY_NAME:
            return InspectSimpleType(self, name, obj, depth - 1)
        if isinstance(obj, self.WHITELIST_USE_SIMPLE_TYPE) or obj is None:
            return InspectSimpleType(self, name, obj, depth - 1)
        if inspect.ismethod(obj) or inspect.isfunction(obj):
            return InspectMethod(self, name, obj, depth - 1)
        if isinstance(obj, partial):
            return InspectPartial(self, name, obj, depth - 1)
        if isinstance(obj, dict):
            return InspectDict(self, name, obj, depth - 1)
        if isinstance(obj, set):
            return InspectSet(self, name, obj, depth - 1)
        if isinstance(obj, list):
            return InspectList(self, name, obj, depth - 1)
        if isinstance(obj, QuerySet):
            return InspectQuerySet(self, name, obj, depth - 1)
        return InspectClass(self, name, obj, depth - 1)

    def been_seen_before(self, obj: Any) -> bool:
        """
        Check if an object has been processed and add it to the processed dictionary if not.  

        Args:
            obj (Any): The object to check.

        Returns:
            bool: True if the object was processed before, False if new.
        """
        # skip simple types
        if isinstance(obj, self.WHITELIST_USE_SIMPLE_TYPE) or obj is None:
            return False

        obj_id = id(obj)

        if obj_id in self._processed:
            return True
        self._processed[obj_id] = True
        return False

    def get_max_items(self) -> int:
        """
        Returns the maximum number of items to be displayed.

        Returns:
            int: The maximum number of items.
        """
        return int(self.options['lists'])

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
            inspection (InspectBase): The inspection object to format.

        Returns:
            str: The formatted inspection result.
        """
        # locate the path to the templates, which is relative to this file at
        # ../templates/part_templates/inspect/{style}
        current_directory = os.path.dirname(os.path.abspath(__file__))
        template_path = os.path.join(current_directory, '..', 'templates', 'part_templates', 'inspect', str(self.options['style']))

        # load the template
        frame_template = loader.get_template(os.path.join(template_path, 'inspect_frame.html'))
        object_template = loader.get_template(os.path.join(template_path, 'inspect_object.html'))

        # create context for the template
        context = {
            'inspect': self._build_context(inspection), 
            'object_template': object_template 
        }

        # use the django context to track if this is the first time our templates are rendered.
        # This can be used by the templates to decide if things like including CSS or JS should be
        # rendered
        style_first_use_key = f'{self.options["style"]}_first'
        if style_first_use_key not in self._django_context:
            self._django_context[style_first_use_key] = True
            context['first_inspection'] = True
        else:
            context['first_inspection'] = False

        # Render the template
        return frame_template.render(context)

    def _build_context(self, inspection: InspectBase) -> Dict[str, Any]:
        """
        Recursively builds the context data for the inspection object.

        Args:
            inspection (InspectBase): The inspection object to build the context data for.

        Returns:
            Dict[str, Any]: The context data for the inspection object.
        """
        context = { }
        context['title'] = inspection.get_format_title()
        context['id'] = inspection.get_format_id()
        context['type'] = inspection.get_format_type()
        context['prefix'] = inspection.get_format_prefix()
        context['link_to'] = inspection.get_format_link_to()
        context['value'] = inspection.get_format_value()
        context['postfix'] = inspection.get_format_postfix()
        context['total_children'] = inspection.get_total_children()

        # recurse into children
        inspect_children = inspection.get_children()
        if inspect_children is not None:
            children = []
            for child in inspect_children:
                children.append(self._build_context(child))
            context['children'] = children
        else:
            context['children'] = None

        return context
