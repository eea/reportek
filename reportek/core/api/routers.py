from rest_framework_nested import routers

from .views import (
    InstrumentViewSet,
    ClientViewSet,
    ReporterViewSet,
    ReporterSubdivisionCategoryViewSet,
    ReporterSubdivisionViewSet,
    ObligationViewSet,
    ObligationSpecViewSet,
    ReportingCycleViewSet,
    EnvelopeViewSet,
    EnvelopeFileViewSet,
    EnvelopeWorkflowViewSet,
    UploadHookView,
    UploadTokenViewSet,
)


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

files_router = routers.NestedSimpleRouter(
    envelopes_router, 'envelopes', lookup='envelope')
files_router.register(
    'files',
    EnvelopeFileViewSet,
    base_name='envelope-file'
)

workflow_router = routers.NestedSimpleRouter(
    envelopes_router, 'envelopes', lookup='envelope')
workflow_router.register(
    'workflow',
    EnvelopeWorkflowViewSet,
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


main_routers = [
    instruments_router,
    clients_router,
    reporters_router,
    subdivision_cats_router,
    obligations_router,
    reporting_cycle_router,
    envelopes_router,
    upload_hooks_router,
]

nested_routers = [
    files_router,
    workflow_router,
    upload_token_router,
    obligation_specs_router,
    subdivisions_router,
]
