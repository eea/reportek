from rest_framework_nested import routers

from .views import (
    AuthTokenViewSet,
    InstrumentViewSet,
    ClientViewSet,
    ReporterViewSet,
    ReporterSubdivisionCategoryViewSet,
    ReporterSubdivisionViewSet,
    ObligationViewSet,
    ObligationSpecViewSet,
    ObligationSpecReporterViewSet,
    ReportingCycleViewSet,
    EnvelopeViewSet,
    DataFileViewSet,
    SupportFileViewSet,
    LinkViewSet,
    WorkflowViewSet,
    UploadHookView,
    UploadTokenViewSet,
    WorkspaceProfileViewSet,
    WorkspaceReporterViewSet,
    CollectionsViewSet,
)


class BulkDeleteNestedSimpleRouter(routers.NestedSimpleRouter):
    """
    Adds 'delete' to allowed methods on 'list' routes.
    """
    def __init__(self, *args, **kwargs):
        self.routes[0].mapping.update({'delete': 'destroy'})
        super().__init__(*args, **kwargs)


instruments_router = routers.SimpleRouter()
instruments_router.register(
    'instruments',
    InstrumentViewSet,
    base_name='instrument'
)


clients_router = routers.SimpleRouter()
clients_router.register(
    'clients',
    ClientViewSet,
    base_name='client'
)


reporters_router = routers.SimpleRouter()
reporters_router.register(
    'reporters',
    ReporterViewSet,
    base_name='reporter'
)

subdivision_cats_router = routers.SimpleRouter()
subdivision_cats_router.register(
    'subdivision-categories',
    ReporterSubdivisionCategoryViewSet,
    base_name='subdivision-category'
)


subdivisions_router = routers.NestedSimpleRouter(
    subdivision_cats_router, 'subdivision-categories',
    lookup='category')
subdivisions_router.register(
    'subdivisions',
    ReporterSubdivisionViewSet,
    base_name='subdivision'
)


obligations_router = routers.SimpleRouter()
obligations_router.register(
    'obligations',
    ObligationViewSet,
    base_name='obligation'
)


obligation_specs_router = routers.NestedSimpleRouter(
    obligations_router, 'obligations',
    lookup='obligation')
obligation_specs_router.register(
    'specs',
    ObligationSpecViewSet,
    base_name='obligation-spec'
)


obligation_spec_reporters_router = routers.SimpleRouter()
obligation_spec_reporters_router.register(
    'obligation-spec-reporters',
    ObligationSpecReporterViewSet,
    base_name='obligation-spec-reporter'
)


reporting_cycle_router = routers.SimpleRouter()
reporting_cycle_router.register(
    'reporting-cycles',
    ReportingCycleViewSet,
    base_name='reporting-cycle'
)


envelopes_router = routers.SimpleRouter()
envelopes_router.register(
    'envelopes',
    EnvelopeViewSet,
    base_name='envelope'
)

data_files_router = BulkDeleteNestedSimpleRouter(
    envelopes_router, 'envelopes', lookup='envelope')
data_files_router.register(
    'data-files',
    DataFileViewSet,
    base_name='envelope-data-file'
)

support_files_router = routers.NestedSimpleRouter(
    envelopes_router, 'envelopes', lookup='envelope')
support_files_router.register(
    'support-files',
    SupportFileViewSet,
    base_name='envelope-support-file'
)


links_router = routers.NestedSimpleRouter(
    envelopes_router, 'envelopes', lookup='envelope')
links_router.register(
    'links',
    LinkViewSet,
    base_name='envelope-link'
)

workflow_router = routers.NestedSimpleRouter(
    envelopes_router, 'envelopes', lookup='envelope')
workflow_router.register(
    'workflow',
    WorkflowViewSet,
    base_name='envelope-workflow'
)


upload_token_router = routers.NestedSimpleRouter(
    envelopes_router, 'envelopes', lookup='envelope')
upload_token_router.register(
    'token',
    UploadTokenViewSet,
    base_name='envelope-token'
)

upload_hooks_router = routers.SimpleRouter()
upload_hooks_router.register(
    'uploads',
    UploadHookView,
    base_name='uploads'
)


workspace_profile_router = routers.SimpleRouter()
workspace_profile_router.register(
    'workspace-profile',
    WorkspaceProfileViewSet,
    base_name='workspace'
)

workspace_reporter_router = routers.SimpleRouter()
workspace_reporter_router.register(
    'workspace-reporter',
    WorkspaceReporterViewSet,
    base_name='workspace-reporter'
)


auth_tokens_router = routers.SimpleRouter()
auth_tokens_router.register(
    'auth-token',
    AuthTokenViewSet,
    base_name='auth-token'
)

collections_router = routers.SimpleRouter()
collections_router.register(
    'collection',
    CollectionsViewSet,
    base_name='collection'
)


main_routers = [
    instruments_router,
    clients_router,
    reporters_router,
    subdivision_cats_router,
    obligations_router,
    obligation_spec_reporters_router,
    reporting_cycle_router,
    envelopes_router,
    upload_hooks_router,
    workspace_profile_router,
    workspace_reporter_router,
    auth_tokens_router,
    collections_router,
]


nested_routers = [
    data_files_router,
    support_files_router,
    links_router,
    workflow_router,
    upload_token_router,
    obligation_specs_router,
    subdivisions_router,
]
