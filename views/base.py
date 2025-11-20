# core/views/base.py

import json

from django.views.generic import (
    TemplateView,
    DetailView,
    ListView,
    CreateView,
    UpdateView,
    DeleteView,
    FormView,
)
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from django.shortcuts import redirect, get_object_or_404
from django_tables2 import SingleTableView, RequestConfig, SingleTableMixin
from django.http import JsonResponse

from django.utils.module_loading import import_string

from ..mixins.views import (
    FormMessagesMixin,
    BaseViewMixin,
    AjaxFormMixin,
    ActionContextMixin,
)
from core.portals import get_portal_config
from core.widgets import DashboardWidget


class BaseTemplateView(TemplateView):
    """
    Base class for template views that adds a customizable page title to the context data. This
    class extends the standard TemplateView to allow for the inclusion of a page title, which can
    be set and accessed in the template.

    Attributes:
        page_title (str): The title of the page to be included in the context.

    Methods:
        get_context_data(**kwargs): Returns the context data, including the page title.
    """

    page_title = None

    def get_context_data(self, **kwargs):
        """
        This class-level attribute holds the title of the page to be included in the context data.
        It is intended to be overridden in subclasses to provide a specific title for each template
        view.

        Attributes:
            page_title (str): The title of the page to be included in the context.
        """

        context = super().get_context_data(**kwargs)
        context["page_title"] = self.page_title
        return context


class BaseDetailView(DetailView):
    """
    Base class for detail views that adds a customizable page title to the context data. This class
    extends the standard DetailView to allow for the inclusion of a page title, which can be set
    and accessed in the template.

    Attributes:
        page_title (str): The title of the page to be included in the context.

    Methods:
        get_context_data(**kwargs): Returns the context data, including the page title.
    """

    page_title = None

    def get_context_data(self, **kwargs):
        """
        This class-level attribute holds the title of the page to be included in the context data.
        It is intended to be overridden in subclasses to provide a specific title for each template
        view.

        Attributes:
            page_title (str): The title of the page to be included in the context.
        """
        context = super().get_context_data(**kwargs)
        context["page_title"] = self.page_title
        return context


class BaseListView(ListView):
    """
    Base class for list views that supports pagination, customizable page titles, and filtering.
    This class extends the standard ListView to include features for managing the display of lists,
    including the ability to filter results based on query parameters.

    Attributes:
        paginate_by (int): The number of items to display per page.
        page_title (str): The title of the page to be included in the context.
        filterset_class (type): An optional class used for filtering the queryset.

    Methods:
        get_context_data(**kwargs): Returns the context data, including the page title and
            filterset if applicable.
        get_queryset(): Returns the filtered queryset if a filterset class is provided; otherwise,
            returns the default queryset.
    """

    paginate_by = 10
    page_title = None
    filterset_class = None

    def get_context_data(self, **kwargs):
        """
        Retrieves and returns the context data for the template, including the page title and an
        optional filterset. This method enhances the context by adding the page title and, if a
        filterset class is defined, initializes it with the current request parameters and the
        queryset.

        Args:
            self: The instance of the class.
            **kwargs: Additional keyword arguments to pass to the superclass method.

        Returns:
            dict: A dictionary containing the context data, including the page title and filterset
                if applicable.
        """

        context = super().get_context_data(**kwargs)
        context["page_title"] = self.page_title

        if self.filterset_class:
            context["filterset"] = self.filterset_class(
                self.request.GET, queryset=self.get_queryset()
            )
        return context

    def get_queryset(self):
        """
        Retrieves the queryset for the view, applying filtering if a filterset class is defined.
        This method checks for the presence of a filterset class and, if available, returns the
        filtered queryset based on the current request parameters.

        Args:
            self: The instance of the class.

        Returns:
            QuerySet: The filtered queryset if a filterset class is provided; otherwise, the
                default queryset.
        """

        if self.filterset_class:
            return self.filterset_class(self.request.GET, super().get_queryset()).qs
        return super().get_queryset()


class BaseTableListView(SingleTableView):
    """
    Base class for views that display a table of data with pagination and optional filtering. This
    class extends SingleTableView to provide a structured way to manage and display tabular data,
    including support for filtering and pagination.

    Attributes:
        template_name (str): The template used to render the table view.
        table_class (type): The class of the table to be displayed.
        filterset_class (type): The class used for filtering the queryset.

    Methods:
        get_table(): Retrieves the table and applies pagination based on the request parameters.
        get_queryset(): Retrieves the queryset and applies filtering if a filterset class is
            defined.
        get_context_data(**kwargs): Returns the context data, including the filterset if
            applicable.

    Args:
        self: The instance of the class.
        **kwargs: Additional keyword arguments to pass to the superclass methods.

    Returns:
        dict: A dictionary containing the context data, including the filterset and paginated
            table.
    """

    template_name = "django_tables2/bootstrap4.html"
    table_class = None
    filterset_class = None

    def get_table(self):
        """
        Retrieves the table for the view and applies pagination based on the request parameters.
        This method enhances the default table retrieval by ensuring that the table is paginated,
        allowing for better management of large datasets.

        Args:
            self: The instance of the class.

        Returns:
            Table: The paginated table object ready for rendering.
        """

        table = super().get_table()
        table.paginate(page=self.request.GET.get("page", 1), per_page=10)
        return table

    def get_queryset(self):
        """
        Retrieves the queryset for the view, applying filtering if a filterset class is defined.
        This method allows for dynamic filtering of the queryset based on request parameters,
        enabling more tailored data retrieval for the view.

        Args:
            self: The instance of the class.

        Returns:
            QuerySet: The filtered queryset if a filterset class is provided; otherwise, the
                default queryset.
        """

        queryset = super().get_queryset()
        if self.filterset_class:
            self.filterset = self.filterset_class(self.request.GET, queryset=queryset)
            return self.filterset.qs
        return queryset

    def get_context_data(self, **kwargs):
        """
        Retrieves and returns the context data for the template, including any filterset if it
        exists. This method enhances the context by adding the filterset to the context dictionary,
        allowing for better integration of filtering functionality in the view.

        Args:
            self: The instance of the class.
            **kwargs: Additional keyword arguments to pass to the superclass method.

        Returns:
            dict: A dictionary containing the context data, including the filterset if applicable.
        """

        context = super().get_context_data(**kwargs)
        if hasattr(self, "filterset"):
            context["filterset"] = self.filterset
        return context


class BaseCreateView(
    AjaxFormMixin, FormMessagesMixin, CreateView, BaseViewMixin, ActionContextMixin
):
    """
    Base class for creating views that provides success and error messages. This class extends the
    CreateView and includes functionality for displaying messages upon successful or failed
    creation of an item.

    Attributes:
        success_message (str): The message displayed upon successful creation of an item.
        error_message (str): The message displayed when there is an error during the creation
            process.
    """

    success_message = _("Successfully created.")
    error_message = _("There was an error creating the item.")

    def form_valid(self, form):
        """Handles successful form submission with a success message.

        Adds a success message to the request and calls the parent class's form_valid method.

        Args:
            form: The validated form instance.

        Returns:
            HttpResponse: The result of the parent class's form_valid method.
        """

        messages.success(self.request, self.success_message)
        return super().form_valid(form)

    def form_invalid(self, form):
        """Handles invalid form submission by displaying an error message.

        Adds an error message to the request and calls the parent class's form_invalid method.

        Args:
            form: The invalid form instance.

        Returns:
            HttpResponse: The result of the parent class's form_invalid method.
        """

        messages.error(self.request, self.error_message)
        return super().form_invalid(form)


class BaseUpdateView(FormMessagesMixin, UpdateView, BaseViewMixin, ActionContextMixin):
    """
    Base class for updating views that provides success and error messages. This class extends the
    UpdateView and includes functionality for displaying messages upon successful or failed updates
    of an item.

    Attributes:
        success_message (str): The message displayed upon successful update of an item.
        error_message (str): The message displayed when there is an error during the update
            process.
    """

    success_message = _("Successfully updated.")
    error_message = _("There was an error updating the item.")


class BaseDeleteView(DeleteView, BaseViewMixin, ActionContextMixin):
    """
    Base class for delete views that provides success and error messages upon deletion. This
    class extends the DeleteView and includes functionality to display messages based on the
    outcome of the delete operation.

    Attributes:
        success_message (str): The message displayed upon successful deletion of an item.
        error_message (str): The message displayed when there is an error during the deletion
            process.

    Methods:
        delete(request, *args, **kwargs): Attempts to delete the object and display the appropriate
            success or error message.
    """

    success_message = _("Successfully deleted.")
    error_message = _("There was an error deleting the item.")

    def delete(self, request, *args, **kwargs):
        """
        Handles the deletion of an object and displays appropriate success or error messages. This
        method attempts to delete the object and, based on the outcome, shows a success message if
        the deletion is successful or an error message if an exception occurs.

        Args:
            self: The instance of the class.
            request: The HTTP request object.
            *args: Additional positional arguments.
            **kwargs: Additional keyword arguments.

        Returns:
            HttpResponse: The response from the delete operation, typically a redirect to the
                success URL.

        Raises:
            Exception: Catches any exception that occurs during the deletion process and displays
                an error message.
        """

        try:
            response = super().delete(request, *args, **kwargs)
            if self.success_message:
                messages.success(self.request, self.success_message)
            return response
        except Exception:
            if self.error_message:
                messages.error(self.request, self.error_message)
            return redirect(self.get_success_url())


class BaseManageView(TemplateView, ActionContextMixin):
    """
    Base class for managing views that display multiple tables with associated configurations. This
    class extends TemplateView to provide functionality for initializing tables based on a
    configuration dictionary, retrieving their data, and rendering them in the specified template.

    Attributes:
        template_name (str): The name of the template used to render the view.
        tables_config (dict): A dictionary defining the configuration for each table, including its
            class, queryset, and pagination settings.

    Methods:
        get_tables_config(): Returns the configuration for the tables.
        get_tables(): Initializes and configures the tables based on the defined configurations.
        get_context_data(**kwargs): Returns the context data, including tables with metadata for
            rendering.
        get_create_url(table_name): Returns the URL for creating new entries in the specified
            table.

    Args:
        self: The instance of the class.
        **kwargs: Additional keyword arguments to pass to the superclass method.

    Returns:
        dict: A dictionary containing the context data, including the initialized tables with
            metadata.
    """

    template_name = None
    # Define as {'table_name': {'class': TableClass, 'queryset': QuerySet, 'paginate_by': int}}
    tables_config = {}

    def get_tables_config(self):
        """
        Retrieves the configuration for the tables defined in the `tables_config` attribute. This
        method provides access to the table configurations, which include details such as the table
        class, queryset, and pagination settings.

        Args:
            self: The instance of the class.

        Returns:
            dict: The configuration dictionary for the tables.
        """

        return self.tables_config

    def get_tables(self):
        """
        Initializes and configures the tables defined in the `tables_config` attribute. This method
        retrieves the configuration for each table, creates an instance of the corresponding table
        class, applies pagination settings, and returns a dictionary of initialized tables.

        Args:
            self: The instance of the class.

        Returns:
            dict: A dictionary containing the initialized tables, keyed by their names.
        """

        initialized_tables = {}
        for table_name, config in self.get_tables_config().items():
            table_class = config["class"]
            queryset = config["queryset"]
            paginate_by = config.get("paginate_by", 10)

            table = table_class(queryset, request=self.request)
            RequestConfig(self.request, paginate={"per_page": paginate_by}).configure(
                table
            )
            initialized_tables[table_name] = table

        return initialized_tables

    def get_context_data(self, **kwargs):
        """
        Retrieves and returns the context data for the template, including metadata for the
        initialized tables. This method enhances the context by adding information such as table
        names, creation URLs, and icons, allowing for better integration of tables in the rendered
        view.

        Args:
            self: The instance of the class.
            **kwargs: Additional keyword arguments to pass to the superclass method.

        Returns:
            dict: A dictionary containing the context data, including tables with their associated
                metadata.
        """

        context = super().get_context_data(**kwargs)
        tables = self.get_tables()

        # Include tables with metadata (e.g., create_url, icons) in context
        tables_with_metadata = [
            {
                "name": table_name.replace("_", " ").title(),
                "table": table,
                "create_url": self.get_create_url(table),
                "icon": getattr(table, "add_icon", "fas fa-plus"),
            }
            for table_name, table in tables.items()
        ]

        context.update(
            {
                "tables_with_metadata": tables_with_metadata,
            }
        )
        return context

    def get_create_url(self, table):
        """
        Retrieves the URL for creating new entries in the specified table. This method currently
        returns a placeholder URL, which can be overridden in subclasses to provide the actual
        creation URL for the table.

        Args:
            self: The instance of the class.
            table (str): The name of the table for which to retrieve the creation URL.

        Returns:
            str: The creation URL for the specified table, currently a placeholder.
        """

        return "#"


class BaseIndexByFilterTableView(SingleTableMixin, ListView, ActionContextMixin):
    """
    Base class for views that display a table filtered by a specified model object. This class
    extends SingleTableMixin and ListView to provide functionality for filtering data based on URL
    parameters, allowing for dynamic table rendering based on the resolved filter object.

    Attributes:
        lookup_keys (list): An ordered list of keys used to resolve URL parameters for filtering.
        filter_field (str): The field in the model to filter by.
        filter_model (type): The model used to resolve the lookup value.
        context_object_name_for_filter (str): The name of the context variable for the filter
            object.
        table_class (type): The table class used for rendering with django_tables2.

    Methods:
        get_filter_value(): Retrieves the filter value from the URL parameters based on the
            specified lookup keys.
        get_filter_object(filter_value): Resolves the filter object using the filter model and the
            filter value.
        get_queryset(): Filters the queryset based on the resolved filter object and filter field.
        get_context_data(**kwargs): Includes the filter object in the context for rendering.
        get_table_data(): Provides the filtered queryset to the django_tables2 table.

    Args:
        self: The instance of the class.
        **kwargs: Additional keyword arguments to pass to the superclass methods.

    Returns:
        dict: A dictionary containing the context data, including the filter object and filtered
            queryset.
    """

    # Defaults: Override these in subclasses
    lookup_keys = ["slug"]  # Ordered list of lookup keys for URL kwargs
    filter_field = None  # Field to filter by in the model
    filter_model = None  # Model to resolve the lookup value
    context_object_name_for_filter = (
        None  # Name of the context variable for the filter object
    )
    table_class = None  # Table class for django_tables2 rendering

    def get_filter_value(self):
        """
        Retrieves the filter value from the URL parameters based on the specified lookup keys. This
        method iterates through the defined lookup keys and returns the corresponding value from
        the URL kwargs, raising an error if no valid key is found.

        Args:
            self: The instance of the class.

        Returns:
            str: The filter value extracted from the URL parameters.

        Raises:
            ValueError: If no valid lookup key is found in the URL parameters.
        """

        for key in self.lookup_keys:
            if key in self.kwargs:
                return self.kwargs[key]
        raise ValueError("No valid lookup key found in URL parameters.")

    def get_filter_object(self, filter_value):
        """
        Retrieves the filter object based on the provided filter value and the specified filter
        model. This method checks if the filter model is defined, determines the appropriate lookup
        field based on the filter value, and returns the corresponding object or raises a 404 error
        if not found.

        Args:
            self: The instance of the class.
            filter_value (str): The value used to look up the filter object.

        Returns:
            object: The filter object retrieved from the filter model.

        Raises:
            ValueError: If the `filter_model` is not specified in the subclass.
            Http404: If no object matching the filter value is found in the filter model.
        """

        if not self.filter_model:
            raise ValueError("`filter_model` must be specified in the subclass.")

        # Determine if the lookup is numeric (assume PK) or not
        lookup_field = "pk" if filter_value.isdigit() else "slug"
        return get_object_or_404(self.filter_model, **{lookup_field: filter_value})

    def get_queryset(self):
        """
        Retrieves the queryset for the view, applying filtering based on the resolved filter
        object. This method checks if the filter field is specified, retrieves the filter value,
        and returns a filtered queryset based on the specified field and filter object.

        Args:
            self: The instance of the class.

        Returns:
            QuerySet: The filtered queryset based on the specified filter field and filter object.

        Raises:
            ValueError: If the `filter_field` is not specified in the subclass.
        """

        if not self.filter_field:
            raise ValueError("`filter_field` must be specified in the subclass.")

        filter_value = self.get_filter_value()
        filter_object = self.get_filter_object(filter_value)
        return self.model.objects.filter(**{self.filter_field: filter_object})

    def get_context_data(self, **kwargs):
        """
        Retrieves and returns the context data for the template, including the resolved filter
        object. This method enhances the context by adding the filter object under a specified
        context variable name, allowing for better integration of filtering functionality in the
        rendered view.

        Args:
            self: The instance of the class.
            **kwargs: Additional keyword arguments to pass to the superclass method.

        Returns:
            dict: A dictionary containing the context data, including the filter object if
            applicable.
        """

        context = super().get_context_data(**kwargs)

        filter_value = self.get_filter_value()
        filter_object = self.get_filter_object(filter_value)

        if self.context_object_name_for_filter:
            context[self.context_object_name_for_filter] = filter_object

        return context

    def get_table_data(self):
        """
        Retrieves the data for the table by obtaining the filtered queryset. This method serves as
        a bridge to access the queryset, allowing the table to be populated with the relevant data
        for display.

        Args:
            self: The instance of the class.

        Returns:
            QuerySet: The queryset containing the data for the table.
        """

        return self.get_queryset()


class BaseFormView(FormView, ActionContextMixin):
    """
    A base view for handling form submissions with custom success and error messages.  This view
    manages both valid and invalid form submissions, providing appropriate feedback and handling
    AJAX requests.

    Attributes:
        success_message (str): A custom success message.
        error_message (str): A custom error message.
        action (str): Action context for display purposes.

    Methods:
        form_valid(form): Handles a valid form submission, adds a success message, and manages AJAX
            responses.
        form_invalid(form): Handles an invalid form submission, adds an error message, and manages
            AJAX responses.
        get_context_data(**kwargs): Adds additional context to the template.
        get_success_url(): Determines the URL to redirect to after a successful form submission.
    """

    success_message = None
    error_message = None
    action = None  # Action context

    def form_valid(self, form):
        """
        Handles a valid form submission.
        Adds a success message and handles AJAX responses.

        Args:
            form (Form): The submitted form.

        Returns:
            HttpResponse: A response object, which may be a redirect or a JSON response for AJAX requests.
        """
        response = super().form_valid(form)

        # Add a success message if provided
        if self.success_message:
            messages.success(self.request, self.success_message)

        # Handle AJAX requests
        if self.request.is_ajax():
            return JsonResponse(
                {"success": True, "redirect_url": self.get_success_url()}
            )

        return response

    def form_invalid(self, form):
        """
        Handles an invalid form submission.
        Adds an error message and handles AJAX responses.

        Args:
            form (Form): The submitted form.

        Returns:
            HttpResponse: A response object, which may be a redirect or a JSON response for AJAX
                requests.
        """
        response = super().form_invalid(form)

        # Add an error message if provided
        if self.error_message:
            messages.error(self.request, self.error_message)

        # Handle AJAX responses
        if self.request.is_ajax():
            return JsonResponse({"success": False, "errors": form.errors}, status=400)

        return response

    def get_context_data(self, **kwargs):
        """
        Adds additional context to the template.

        Args:
            **kwargs: Additional keyword arguments.

        Returns:
            dict: The updated context dictionary.
        """
        context = super().get_context_data(**kwargs)
        if self.action:
            context["action"] = self.action
        return context

    def get_success_url(self):
        """
        Determines the URL to redirect to after a successful form submission.
        Can be overridden in subclasses or passed as a class attribute.

        Returns:
            str: The success URL.

        Raises:
            NotImplementedError: If no success_url is specified for BaseFormView.
        """
        if hasattr(self, "success_url") and self.success_url:
            return self.success_url
        raise NotImplementedError("No success_url specified for BaseFormView.")


class BaseDashboardView(BaseManageView):
    """
    BaseDashboardView: A view for displaying dashboard-like pages with dynamic widgets.
    Supports widgets as tables, charts, or text.
    """

    template_name = "dashboard/dashboard.html"
    portal_key = None
    widget_definitions = None

    def get_portal_config(self):
        return get_portal_config(self.portal_key or "")

    def get_template_names(self):
        portal_template = self.get_portal_config().get("dashboard_template")
        if portal_template:
            return [portal_template]
        return [self.template_name]

    def get_dashboard_widgets(self):
        """
        Return a list of DashboardWidget instances (or widget definitions that can
        be converted into instances). Subclasses should override this to provide
        context-aware cards. When nothing is returned the template will show an
        empty state instead of crashing.
        """
        if isinstance(self.widget_definitions, (list, tuple)):
            return list(self.widget_definitions)
        return []

    def _resolve_widget(self, definition):
        if isinstance(definition, DashboardWidget):
            return definition

        if isinstance(definition, dict):
            widget_class = definition.get("widget") or definition.get("class")
            if isinstance(widget_class, str):
                widget_class = import_string(widget_class)
            if not widget_class:
                return None
            options = definition.get("options", {})
            title = definition.get("title", widget_class.__name__)
            return widget_class(self.request, title=title, **options)

        return None

    def build_widgets(self):
        widgets = []
        for definition in self.get_dashboard_widgets():
            widget = self._resolve_widget(definition)
            if widget is None:
                continue
            widgets.append(widget.as_dict())
        widgets.sort(key=lambda widget: widget.get("priority", 10))
        return widgets

    def get_context_data(self, **kwargs):
        """
        Prepare the context data for rendering the dashboard, including widgets and their data.
        """
        context = super().get_context_data(**kwargs)
        context["widgets"] = self.build_widgets()
        return context
